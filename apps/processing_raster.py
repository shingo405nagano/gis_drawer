from dataclasses import dataclass
from typing import Any
from typing import List
from typing import Tuple

import cv2
import geopandas as gpd
import numpy as np
import rasterio
import shapely

from disassembly import geom_disassembly


class RasterInfos(object):
    """Rasterの情報を取得する"""
    def __init__(self, ds: rasterio.io.DatasetReader):
        self.bands = len(ds.indexes)
        self.epsg = ds.crs.to_epsg()
        bounds = ds.bounds
        self.x_min = bounds.left
        self.x_max = bounds.right
        self.y_min = bounds.bottom
        self.y_max = bounds.top
        self.raster_rows = ds.width
        self.raster_cols = ds.height
        self.boundary_poly = self.__poly
        self.boundary_coords = self.__poly_coords
        self.epsg_utm = self.__estimate_utm_epsg
        self.raster_width_m = self.__raster_width_m
        self.raster_height_m = self.__raster_height_m
        self.px_width_m = self.__raster_px_width_m
        self.px_height_m = self.__raster_px_height_m

    @property
    def __poly(self) -> shapely.Polygon:
        poly = shapely.Polygon([
            [self.x_min, self.y_max],
            [self.x_max, self.y_max],
            [self.x_max, self.y_min],
            [self.x_min, self.y_min],
            [self.x_min, self.y_max],
        ])
        return poly

    @property
    def __poly_coords(self) -> List[List[float]]:
        return geom_disassembly(self.boundary_poly, 'xyz')

    @property
    def __estimate_utm_epsg(self) -> int:
        gdf = gpd.GeoDataFrame(
                geometry=[self.boundary_poly], crs=f"EPSG:{self.epsg}")
        if self.epsg != 4326:
            gdf = gdf.to_crs(crs='EPSG:4326')
        gdf_utm = gdf.to_crs(gdf.estimate_utm_crs())
        return gdf_utm.crs.to_epsg()
    
    @property
    def __upper_left_point_utm(self):
        coords_lst = self.__poly_coords
        upper_left_coords = coords_lst[0]
        upper_left_point = transform(
            lon=upper_left_coords[0], 
            lat=upper_left_coords[1], 
            in_epsg=self.epsg, out_epsg=self.epsg_utm
        )
        return upper_left_point.points[0]

    @property
    def __upper_right_point_utm(self):
        coords_lst = self.__poly_coords
        upper_right_coords = coords_lst[1]
        upper_right_point = transform(
            lon=upper_right_coords[0], 
            lat=upper_right_coords[1], 
            in_epsg=self.epsg, out_epsg=self.epsg_utm
        )
        return upper_right_point.points[0]
    
    @property
    def __lower_right_point_utm(self):
        coords_lst = self.__poly_coords
        lower_right_coords = coords_lst[2]
        lower_right_point = transform(
            lon=lower_right_coords[0], 
            lat=lower_right_coords[1], 
            in_epsg=self.epsg, out_epsg=self.epsg_utm
        )
        return lower_right_point.points[0]

    @property
    def __raster_width_m(self):
        left = self.__upper_left_point_utm
        right = self.__upper_right_point_utm
        return abs(right.x - left.x)
    
    @property
    def __raster_height_m(self):
        top = self.__upper_right_point_utm
        bottom = self.__lower_right_point_utm
        return abs(top.y - bottom.y)
    
    @property
    def __raster_px_width_m(self):
        return self.raster_height_m / self.raster_rows
    
    @property
    def __raster_px_height_m(self):
        return self.raster_width_m / self.raster_cols

    @property
    def dictionary(self):
        dic = self.__dict__
        return dic