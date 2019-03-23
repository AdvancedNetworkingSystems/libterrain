import libterrain
DSN = "postgres://student@192.168.1.196/terrain_ans"
BI = libterrain.BuildingInterface.get_best_interface(DSN, "vaiano")
#STI = libterrain.SingleTerrainInterface(DSN, lidar_table="lidar")
area = BI.get_province_area("vaiano")
buildings = BI.get_buildings(shape=area)
a = buildings[0].coord_height()
# for i in range(1,100):
#     b = buildings[i].coord_height()
#     link = STI.get_link(source=a, destination=b)
#     print(link)
MTI = libterrain.ParallelTerrainInterface(DSN, lidar_table="lidar", processes=4)
dst_list = list(map(lambda x: x.coord_height(), buildings[1:20]))
links = MTI.get_link_parallel(a, dst_list)
print(links)
