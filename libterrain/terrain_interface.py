import random
import shapely
from sqlalchemy import create_engine, and_
from psycopg2.pool import ThreadedConnectionPool
import psycopg2
from sqlalchemy.orm import sessionmaker
from geoalchemy2.functions import GenericFunction
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape, from_shape
from shapely.geometry import Point
import multiprocessing as mp
from more_itertools import chunked
from libterrain.link import Link, ProfileException
from libterrain.building import Building_CTR, Building_OSM
from libterrain.comune import Comune


class ST_MakeEnvelope(GenericFunction):
    name = 'ST_MakeEnvelope'
    type = Geometry


class BaseInterface():
    def __init__(self, DSN, lidar_table, srid='4326'):
        self.DSN = DSN
        self.srid = '4326'
        self._set_dataset()
        self.lidar_table = lidar_table
        self.srid = srid

    def _set_dataset(self):
        self.buff = 0.5
        # The size of the buffer depends on the precision of the lidar dataset
        # For 1x1m 0.5m is fine, but for other dataset such as Lyon's 30cm one,
        # another buffer might be needed


    def _profile_osm(self, param_dict, conn):
        # loop over all the orders that we have and process them sequentially.
        src = param_dict['src']  # coords must be shapely point
        #src_h = param_dict['src']['height']
        dst = param_dict['dst']  # coords must be shapely point
        #dst_h = param_dict['dst']['height']
        srid = param_dict['srid']
        lidar_table = param_dict['lidar_table']
        buff = param_dict['buff']
        cur = conn.cursor()
        #TODO: use query formatting and not string formatting
        query = """WITH buffer AS(
                                SELECT
                                ST_Buffer_Meters(
                                    ST_MakeLine(
                                                ST_GeomFromText('{2}', {0}),
                                                ST_GeomFromText('{3}', {0})
                                                ), {4}
                                ) AS line
                            ),
                            lidar AS(
                                WITH
                                patches AS (
                                    SELECT pa FROM {1}
                                    JOIN buffer ON PC_Intersects(pa, line)
                                ),
                                pa_pts AS (
                                    SELECT PC_Explode(pa) AS pts FROM patches
                                ),
                                building_pts AS (
                                    SELECT pts, line FROM pa_pts JOIN buffer
                                    ON ST_Intersects(line, pts::geometry)
                                )
                                SELECT
                                PC_Get(pts, 'z') AS z,
                                ST_Distance(pts::geometry,
                                            ST_GeomFromText('{2}', {0}),
                                            true
                                            ) as distance
                                FROM building_pts
                                )
                            SELECT DISTINCT on (lidar.distance)
                            lidar.distance,
                            lidar.z
                            FROM lidar ORDER BY lidar.distance;
                        """.format(srid, lidar_table, src['coords'].wkt, dst['coords'].wkt, buff)
        cur.execute(query)
        q_result = cur.fetchall()
        if cur.rowcount == 0:
            return None
        # remove invalid points
        # TODO: Maybe DBMS can clean this up
        profile = filter(lambda a: a[0] != -9999, q_result)
        # cast everything to float
        d, y = zip(*profile)
        y = [float(i) for i in y]
        d = [float(i) for i in d]
        profile = list(zip(d, y))
        try:
            phy_link = Link(profile, src['coords'], dst['coords'], src['height'], dst['height'])
            if phy_link and phy_link.loss > 0:
                link = {}
                link['src'] = src
                link['dst'] = dst
                link['loss'] = phy_link.loss
                link['src_orient'] = phy_link.Aorient
                link['dst_orient'] = phy_link.Borient
                return link
        except (ZeroDivisionError, ProfileException) as e:
            pass
        return None


class ParallelTerrainInterface(BaseInterface):
    def __init__(self, DSN, lidar_table, processes=2):
        super(ParallelTerrainInterface, self).__init__(DSN, lidar_table)
        self.processes = processes
        self.querier = []
        # Connection to PSQL
        self.tcp = ThreadedConnectionPool(1, 100, DSN)
        # MT Queryier
        self.workers_query_order_q = mp.Queue()
        self.workers_query_result_q = mp.Queue()
        self.conns = [self.tcp.getconn() for i in range(processes)]
        for i in range(self.processes):
            t = mp.Process(target=self._query_worker, args=[self.conns[i]])
            self.querier.append(t)
            t.daemon = True
            t.start()

    def _query_worker(self, conn):
        while(True):
            order = self.workers_query_order_q.get(block=True)
            link = self._profile_osm(order, conn)
            self.workers_query_result_q.put(link)

    def get_link_parallel(self, src, dst_list):
        """Calculate the path loss between two lists of building
        """
        links = []
        params = [{'src': src,
                   'dst': dst_list[i],
                   'srid': self.srid,
                   'lidar_table': self.lidar_table,
                   'buff': self.buff
                   }for i in range(len(dst_list))]
        # add orders in the queue
        for order in params:
            self.workers_query_order_q.put(order)
        # wait for all the orders to come back
        while len(links) < len(dst_list):
            links.append(self.workers_query_result_q.get(block=True))
        return links


class SingleTerrainInterface(BaseInterface):
    def __init__(self, DSN, lidar_table):
        super(SingleTerrainInterface, self).__init__(DSN, lidar_table)
        try:
            self.conn = psycopg2.connect(DSN)
        except psycopg2.Error:
            print("I am unable to connect to the database")

    def get_link(self, source, destination):
        params = {
            'src': source,
            'dst': destination,
            'srid': self.srid,
            'lidar_table': self.lidar_table,
            'buff': self.buff
        }
        profile = self._profile_osm(params, self.conn)
        return profile
