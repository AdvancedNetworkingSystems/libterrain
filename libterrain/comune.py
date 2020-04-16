from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, Unicode, and_
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape, from_shape
import shapely

Base = declarative_base()


class Comune(Base):
    __tablename__ = 'comuni'
    gid = Column(Integer, primary_key=True)
    comune = Column(String)
    pro_com_t = Column(String)
    cod_prov = Column(String)
    geom = Column(Geometry('POLYGON'))

    def __repr__(self):
        return self.nome

    def shape(self):
        return to_shape(self.geom)

    @classmethod
    def get_by_gid(cls, session, gid):
        """Get building by gid
        gid: identifier of building
        """
        element = session.query(cls) \
            .filter_by(gid=gid).first()
        return element

    @classmethod
    def get_by_name(cls, session, name):
        """Get building by gid
        gid: identifier of building
        """
        element = session.query(cls) \
            .filter_by(comune=name).first()
        return element
