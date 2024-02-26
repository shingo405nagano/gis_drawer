"""
1. reprojection_raster
    rasterio.io.DatasetReaderを任意の座標系に投影変換する

2. reprojection_estimate_utm_jgd
    rasterio.io.DatasetReaderを日本のUTM座標系に投影変換する
"""
from dataclasses import dataclass
from typing import Any
from typing import Dict

import affine
import numpy as np
import rasterio
import rasterio.enums
import rasterio.io
import rasterio.warp

from apps.raster.imagery import RasterDataSet
from apps.spatial_reference import transform
from apps.spatial_reference import estimation_jgd_utm_from_lon



@dataclass
class Transformed:
    affine: affine.Affine
    width: int
    height: int


class ReProjection(object):
    def __init__(self, ds: rasterio.io.DatasetReader, out_epsg: int):
        self.ds = ds
        self.out_epsg = f"EPSG:{out_epsg}"
        self.transformed = self.transformer
        self.meta_data = self.create_metadata_dict

    @property
    def transformer(self) -> Transformed:
        aff, w, h = (
            rasterio
            .warp
            .calculate_default_transform(
                self.ds.crs, self.out_epsg, self.ds.width, 
                self.ds.height, *self.ds.bounds
            )
        )
        return Transformed(affine=aff, width=w, height=h)
    
    @property
    def create_metadata_dict(self) -> Dict[str, Any]:
        meta_data = {
            'driver': 'GTiff',
            'height': self.transformed.height,
            'width': self.transformed.width,
            'count': self.ds.count,
            'dtype': self.ds.dtypes[0],
            'crs': self.out_epsg,
            'transform': self.transformed.affine,
            'nodata': self.ds.nodata
        }
        return meta_data
    
    def create_reproj_metadata(self, resampling: int,) -> Dict[str, Any]:
        meta_data = {
            'src_transform': self.ds.transform,
            'src_crs': self.ds.crs,
            'dst_transform': self.transformed.affine,
            'dst_crs': self.out_epsg,
            'resampling': resampling
        }
        return meta_data




def re_project_raster(
    dataset: rasterio.io.DatasetReader, 
    out_epsg: int,
    resampling: int=rasterio.enums.Resampling.nearest,
    out_fp=None
) -> RasterDataSet:
    reproj = ReProjection(dataset, out_epsg)
    reproj_ds = rasterio.MemoryFile().open(**reproj.meta_data)
    for idx in dataset.indexes:
        rasterio.warp.reproject(
            source=rasterio.band(dataset, idx),
            destination=rasterio.band(reproj_ds, idx),
            **reproj.create_reproj_metadata(resampling)
        )
    # 保存する場合
    if out_fp:
        for idx in reproj_ds.indexes:
            with rasterio.open(out_fp, 'w', **reproj.meta_data) as dst:
                dst.write(reproj_ds.read(idx), idx)
    return RasterDataSet(reproj_ds)



def re_project_raster_estimate_utm(
    dataset: rasterio.io.DatasetReader, 
    resampling: int=rasterio.enums.Resampling.nearest,
    out_fp=None
) -> RasterDataSet:
    # UTM座標系の推定
    bounds = dataset.bounds
    in_epsg = dataset.crs.to_epsg()
    x = np.mean([bounds.left, bounds.right])
    y = np.mean([bounds.top, bounds.bottom])
    if in_epsg != 4326:
        x = transform(x, y, in_epsg, 4326).lon
    utm_epsg = estimation_jgd_utm_from_lon(x)
    raster_dataset = re_project_raster(dataset, utm_epsg, resampling, out_fp)
    return raster_dataset




"""
Note:
    rasterio.boundsに格納されている値を使用しているが、桁数が少ないせいかずれる。
    bounds以外に四隅の座標を取得する方法を探る。
"""