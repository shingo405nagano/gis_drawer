from dataclasses import dataclass
import logging 
from typing import Dict
from typing import List

import numpy as np
import rasterio.io
import shapely

from apps.disassembly import geom_disassembly
from apps.spatial_reference import transform
from apps.spatial_reference import estimation_jgd_utm_from_lon



logger = logging.getLogger(__name__)


class Msg(object):
    def __bands_does_not_match(self, img_ary):
        msg = 'The number of bands does not match and cannot be converted.'
        msg += f'\n arguments shape:{img_ary.shape} != (height, width, 3)'
        logger.error(msg)

    def __image_size_does_not_match(self, img_ary1: np.ndarray, img_ary2: np.ndarray):
        """"""
        msg = 'Image size does not match.'
        msg += f"\n img1 shape: {img_ary1.shape} != img2 shape: {img_ary2.shape}"
        logger.error(msg)

    @property
    def __insufficient_number_of_dimensions(self):
        """"""
        msg = 'The shape of the 2D array is not changed.'
        logger.error(msg)



class RasterInfos(object):
    """Rasterの情報を取得する"""
    def __init__(self, ds: rasterio.io.DatasetReader):
        self.bands = len(ds.indexes)
        bounds = ds.bounds
        self.x_min = bounds.left
        self.x_max = bounds.right
        self.y_min = bounds.bottom
        self.y_max = bounds.top
        self.raster_rows = ds.height
        self.raster_cols = ds.width
        self.stats = self.__get_stats_from_bands(ds)
        if ds.crs is not None:
            self.epsg = ds.crs.to_epsg()
            self.boundary_poly = self.__poly
            self.boundary_coords = self.__poly_coords
            self.utm_epsg = self.__estinate_utm_epsg
            self.raster_width_m = self.__raster_width_m
            self.raster_height_m = self.__raster_height_m
            self.px_width_m = self.__raster_px_width_m
            self.px_height_m = self.__raster_px_height_m
        else:
            msg = f"Not georeferenced warning!!"
            logger.warning(msg)

    def __get_stats_from_bands(self, ds: rasterio.io.DatasetReader
    ) -> Dict[str, Dict[str, float]]:
        """各バンド内の数値の範囲を取得する"""
        ranges = {}
        for idx in ds.indexes:
            ary = ds.read(idx)
            dic = {
                'min': np.min(ary), 
                'mean': np.mean(ary),
                'q1': np.quantile(ary, 0.25),
                'q2': np.median(ary),
                'q3': np.quantile(ary, 0.75),
                'max': np.max(ary)
            }
            ranges[idx] = dic
        return ranges

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
    def __estinate_utm_epsg(self) -> int:
        coords = self.boundary_coords
        if self.epsg != 4326:
            transformed = transform(
                lon=coords[0][0], 
                lat=coords[0][1],
                in_epsg=self.epsg,
                out_epsg=4326)
            lon = transformed.lon
        else:
            lon = coords[0][0]
        utm_epsg = estimation_jgd_utm_from_lon(lon)
        return utm_epsg
    
    @property
    def __upper_left_point_utm(self):
        coords_lst = self.__poly_coords
        upper_left_coords = coords_lst[0]
        upper_left_point = transform(
            lon=upper_left_coords[0], 
            lat=upper_left_coords[1], 
            in_epsg=self.epsg, out_epsg=self.utm_epsg
        )
        return upper_left_point.points[0]

    @property
    def __upper_right_point_utm(self):
        coords_lst = self.__poly_coords
        upper_right_coords = coords_lst[1]
        upper_right_point = transform(
            lon=upper_right_coords[0], 
            lat=upper_right_coords[1], 
            in_epsg=self.epsg, 
            out_epsg=self.utm_epsg
        )
        return upper_right_point.points[0]
    
    @property
    def __lower_right_point_utm(self):
        coords_lst = self.__poly_coords
        lower_right_coords = coords_lst[2]
        lower_right_point = transform(
            lon=lower_right_coords[0], 
            lat=lower_right_coords[1], 
            in_epsg=self.epsg, 
            out_epsg=self.utm_epsg
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
    def summary(self):
        dic = self.__dict__
        return dic




class RasterDataSet(Msg):
    def __init__(self, dataset: rasterio.io.DatasetReader):
        super().__init__()
        self.ds = dataset
        self.__raster_ary = None
        self.__img_ary = None
        self.infos = RasterInfos(self.ds)

    def raster_ary(self, select_bands: List[int]=None, clear_cache: bool=False
    ) -> np.ndarray:
        """
        Args:
            select_bands(List[int]): 取得するBandのIndexをListで指定する
            clear_cache(bool): インスタンス変数に保存しているraster_aryを削除する
        Returns:
            np.ndarray: 出力配列の形状は右の感じ (3, 2436, 2500)
        """
        if (clear_cache == False) & (not self.__raster_ary is None):
            return self.__raster_ary
        if select_bands is None:
            return self.ds.read()
        else:
            raster = [self.ds.read(i) for i in select_bands]
            return np.array(raster)

    def img_ary(self, select_bands: List[int]=None, clear_cache: bool=False
    ) -> np.array:
        """
        Args:
            select_bands(List[int]): 取得するBandのIndexをListで指定する
            clear_cache(bool): インスタンス変数に保存しているimg_aryを削除する
        Returns:
            np.ndarray: 出力配列の形状は右の感じ (2436, 2500, 3)
        """
        if (clear_cache == False) & (not self.__img_ary is None):
            return self.__img_ary
        if select_bands is None:
            img = np.dstack(self.ds.read())
            return img
        else:
            img = np.dstack([self.ds.read(i) for i in select_bands])
            return img