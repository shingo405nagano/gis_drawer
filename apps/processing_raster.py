from dataclasses import dataclass
from typing import Any
from typing import List
from typing import Tuple

import cv2
import geopandas as gpd
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import rasterio
import shapely

from disassembly import geom_disassembly


class RasterInfos(object):
    """Rasterの情報を取得する"""
    def __init__(self, ds: rasterio.io.DatasetReader):
        self.epsg = ds.crs.to_epsg()
        bounds = ds.bounds
        self.x_min = bounds.left
        self.x_max = bounds.right
        self.y_min = bounds.bottom
        self.y_max = bounds.top
        self.raster_rows = ds.width
        self.raster_cols = ds.height
        self.raster_x_len_m = self.x_max - self.x_min
        self.raster_y_len_m = self.y_max - self.y_min
        self.px_x_len_m = self.raster_x_len_m / self.raster_rows
        self.px_y_len_m = self.raster_y_len_m / self.raster_cols
        self.boundary_poly = self.__poly
        self.boundary_coords = self.__poly_coords
        self.epsg_utm = self.__estimate_utm_epsg

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
    def dictionary(self):
        dic = self.__dict__
        return dic