# What is it
libterrain is a Python package that provides an API to characterize RF channels by using LIDAR data stored in a PostGIS database
It is composed of two modules, one provides an API to interact with a postgis database containing vectorial data about buildings and administration areas.
The other provides an API to interact with a poincloud database containing elevation data such as lidar or srtm.

# How to install it:
This library uses python3.6. It is suggeested to set up a virtualenvironment.

1) clone the repository to your machine and change directory
```
git clone https://github.com/AdvancedNetworkingSystems/libterrain/libterrain.git
cd libterrain
```
## Release
2) Install it in release mode 
```
python setup.py install
```
## Development
2) Install it in development mode (this allows to modify the code without re-installing it at every change)
```
python setup.py develop
```

# How to use it
libterrain is composed of two main interface. The building interface is used to interact polygons of buildings. The terrain inteface to query elevation data and characterize RF links.
# Building Interface
It is implemented by two classes exposing the same interface. `CTRInterface` is used to interact with specific Italian maps, `OSMInteface` can interact with OSM raster data.
## Methods:
### `get_buildings(shape, area=None)`:
Return all the buildings contained by area (if provided) that interects with shape. 
shape can be a point: in which case the function will return the building[s] containing that point.
It can also be a polygon, in that case the function will return all the buildings contained.

### `count_buildings(shape)`:
Count the buildings intersecting with shape.

### `get_building_gid(gid)`:
Return the building with that specifc gid

### `get_province_area(name)`:
Return the shape of the administratorial area identified by name.
For example: name='firenze' to obtain the Florence municipality's area.

### `get_best_interface(cls, DSN, area_name):`  classmethod
This classmethod can be called as a constructor and will the return the best interface (the one with more buildings) for that area.


# Terrain Interface
It is used to obtain elevation profiles between two points. Moreover the library can characterize the elevation profile using some RF propagation models and estimate a LOSS.
It is composed by two classes: `SingleTerrainInterface` and `ParallelTerrainInterface`. The former expose a single threaded api wich process only one link at the time. The second one is a bulk apy that can proesses many link alltogether with an high degree of parallelism
## Methods
### `SingleTerrainInterface(DSN, lidar_table)`
To instantiate the class the DSN of the database and the name of the table containing the lidar data must be passed.

### `get_link(source, destination)`:
Calculate the visibility amoong source and destination.
The two paramenters must be in the following format:
```
{ 'coords': Shapely Point object
  'height': Integer representing the relative height of the antenna wrt the roof (height of the trellis)
  `optionals`: any optional value that will be returned in the output
}
```
The return format is the following
```
{
  'src': the same object passed as the parameter 'source'
  'dst': the same object passed as the parameter 'destination'
  'loss': LOSS expressed in dBm
  'src_orient': Pitch and Roll orientation of the source antenna
  'dst_orient': Pitch and Roll orientation of the destination antenna
 }
```

### `ParallelTerrainInterface(DSN, lidar_table, processes=2)`:
The same as the Single Thread interface, but the optional parameter `processees` sets the number of parallel process

### `get_link_parallel(src, dst_list)`:
The same as the Single Thread interface, but dst_list is a list of dst object.
It returns a list of links.

# Code example:
```python
import libterrain
DSN = "postgres://student@192.168.1.196/terrain_ans"
BI = libterrain.BuildingInterface.get_best_interface(DSN, "vaiano")
area = BI.get_province_area("vaiano")
buildings = BI.get_buildings(shape=area)
a = buildings[0].coord_height()

# Single Thread
STI = libterrain.SingleTerrainInterface(DSN, lidar_table="lidar")
for i in range(1,20):
    b = buildings[i].coord_height()
    link = STI.get_link(source=a, destination=b)
    print(link)
    
# Multi Thread
MTI = libterrain.ParallelTerrainInterface(DSN, lidar_table="lidar", processes=4)
dst_list = list(map(lambda x: x.coord_height(), buildings[1:20]))
links = MTI.get_link_parallel(a, dst_list)
print(links)


```
