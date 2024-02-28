"""

"""

from typing import Any
from typing import Dict
from typing import NamedTuple

import affine
import numpy as np
import rasterio
import rasterio.io
import rasterio.enums
import rasterio.warp

from apps.raster.imagery import RasterDataSet
from apps.settings import RASTER_DRIVER


def adjustment_length(
    length: float, 
    raster_length: float, 
    cell_length: float
) -> float:
    """
    RasterのResamplingに使用する。\n
    セルサイズを距離で指定した場合、セルのサイズで全体のサイズを割切れない場合が
    ほとんどなので、指定距離を調整して余りを少なくする。
    """
    new_cell_length = cell_length / length
    cells, modulo = divmod(raster_length, new_cell_length)
    length += modulo / cells
    return length


class KernelSize(NamedTuple):
    x_cells: float
    y_cells: float


def kernel_size_from_length(
    length: float,
    raster_height: float,
    raster_width: float,
    px_height: float,
    px_width: float, 
) -> KernelSize:
    """
    指定距離に対応するのセル数を数える
    Args:
        length(float): 新たなCellの1辺の長さ
        raster_height(float): Rasterの高さ
        raster_width(float): Rasterの幅
        px_height(float): Cellの高さ
        px_width(float): Cellの幅
    """
    # 行方向のセルを数える
    height = adjustment_length(length, raster_height, px_height)
    x_cells = px_height / height
    # 列方向のセルを数える
    width = adjustment_length(length, raster_width, px_width)
    y_cells = px_width / width
    return KernelSize(x_cells, y_cells)


class AryShape(NamedTuple):
    pages: int
    rows: int
    cols: int


def ary_shape_from_px_size( 
    length: float,
    pages: int,
    rows: int,
    cols: int,
    height: float,
    width: float,
    px_height: float,
    px_width: float, 
) -> AryShape:
    """
    指定距離サイズのセルになるような配列の形状を計算する。 \n
    Args:
        length(float): 新たなCellの1辺の長さ
        pages(int): 次元数
        rows(int): オリジナルのRasterの行数
        cols(int): オリジナルのRasterの列数
        height(float): オリジナルのRasterの高さ
        width(float): オリジナルのRasterの幅
        px_height(float): オリジナルのCellの高さ
        px_width(float): オリジナルのCellの幅
    Returns:
    """
    kernel_size = kernel_size_from_length(
        length=length,
        raster_height=height,
        raster_width=width,
        px_height=px_height,
        px_width=px_width
    )
    rows = round(rows * kernel_size.x_cells)
    cols = round(cols * kernel_size.y_cells)
    return AryShape(pages, rows, cols)


def affine_transformer(
    ds: rasterio.io.DatasetReader,
    new_cols: int,
    new_rows: int
) -> affine.Affine:
    x = ds.width / new_cols
    y = ds.height / new_rows
    scaled = ds.transform.scale(x, y)
    return ds.transform * scaled


def create_meta_data(
    ds: rasterio.io.DatasetReader, 
    new_cols: int,
    new_rows: int
) -> Dict[str, Any]:
    transformed = affine_transformer(ds, new_cols, new_rows)
    meta_data = {
        'driver': RASTER_DRIVER,
        'height': new_rows,
        'width': new_cols,
        'count': ds.count,
        'dtype': ds.dtypes[0],
        'crs': ds.crs,
        'transform': transformed,
        'nodata': ds.nodata
    }
    return meta_data


def resample(
    ds: rasterio.io.DatasetReader, 
    new_cell_length: float,
    resampling: int=rasterio.enums.Resampling.bilinear
) -> np.ndarray:
     # ラスターの大きさを測る
    dataset = RasterDataSet(ds)
    infos = dataset.infos
    # 新たな配列のサイズを計算する
    ary_shape = ary_shape_from_px_size(
        length=new_cell_length,
        pages=infos.bands,
        rows=infos.raster_rows,
        cols=infos.raster_cols,
        height=infos.raster_height_m,
        width=infos.raster_width_m,
        px_height=infos.px_height_m,
        px_width=infos.px_width_m,
    )
    new_ary = ds.read(out_shape=ary_shape, resampling=resampling)
    return new_ary


def resample_raster(
    ds: rasterio.io.DatasetReader, 
    new_cell_length: float, 
    resampling: int=rasterio.enums.Resampling.nearest,
    out_fp: str=None
) -> np.ndarray:
    new_ary = resample(ds, new_cell_length, resampling)
    shape = new_ary.shape
    
    meta_data = create_meta_data(ds, new_cols=shape[2], new_rows=shape[1])
    
    new_ds = rasterio.MemoryFile().open(**meta_data)
    for idx, ary in zip(new_ds.indexes, new_ary):
        new_ds.write(ary, idx)
    
    if out_fp:
        for idx in new_ds.indexes:
            with rasterio.open(out_fp, 'w', **meta_data) as dst:
                dst.write(new_ds.read(idx), idx)
    return new_ds


