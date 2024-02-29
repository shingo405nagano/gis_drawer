"""
1. geom_disassembly
    shapelyのgeometryを分解する。
"""
from dataclasses import dataclass
import logging
from typing import Any
from typing import Callable
from typing import List
from typing import NamedTuple

import shapely


FORMAT = """________ %(levelname)s LOG ________
    FuncName: %(funcName)s
    Message: %(message)s
    """
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)


@dataclass
class ResponseTypes:
    """
    分解後のデータタイプを記述している。
    """
    POINT = 0
    XYZ = 1
    X_Y_Z = 2
    WKT = 3
    WKB = 4
    MERGED_POINT = 5
    MERGED_XYZ = 6
    MERGED_X_Y_Z = 7
    MERGED_WKT = 8
    MERGED_WKB = 9


class XY(NamedTuple):
    x: float | List[float]
    y: float | List[float]


class XYZ(XY):
    x: float | List[float]
    y: float | List[float]
    z: float | List[float]



class RingsParts(NamedTuple):
    shell: shapely.LinearRing
    holes: List[shapely.LinearRing]


class PolyParts(NamedTuple):
    shell: List[XY| XYZ | shapely.Point]
    holes: List[XY| XYZ | shapely.Point]




class DisassemblyPoint(object):
    """shapely.geometry.Point あるいは shapely.geometry.MultiPoint を分解する。"""
    def xyz_from_point(self, geom: shapely.Point) -> XY | XYZ:
        if shapely.has_z(geom):
            return XYZ(geom.x, geom.y, geom.z)
        return XY(geom.x, geom.y)
    
    def points_from_multi_point(self, geom: shapely.MultiPoint) -> List[shapely.Point]:
        return list(shapely.get_parts(geom))

    def xyz_from_multi_point(self, geom: shapely.MultiPoint) -> List[XY | XYZ]:
        points = []
        for point in geom.geoms:
            xyz = self.xyz_from_point(point)
            points.append(xyz)
        return points
    
    def x_y_z_from_multi_point(self, geom: shapely.MultiPoint) -> XY | XYZ:
        x_lst, y_lst, z_lst = [], [], []
        for xyz in self.xyz_from_multi_point(geom):
            x_lst.append(xyz.x)
            y_lst.append(xyz.y)
            if type(xyz) == XYZ:
                z_lst.append(xyz.z)
        if z_lst:
            return XYZ(x_lst, y_lst, z_lst)
        return XY(x_lst, y_lst)

    def wkt_points_from_multi_point(self, geom: shapely.MultiPoint) -> List[str]:
        return [pt.wkt for pt in list(geom.geoms)]
    
    def wkb_points_from_multi_point(self, geom: shapely.MultiPoint) -> List[bytes]:
        return [pt.wkb for pt in list(geom.geoms)]




class DisassemblyLineString(object):
    """shapely.geometry.LineString あるいは shapely.geometry.MultiLineString を分解する。"""
    def points_from_line(self, geom: shapely.LineString) -> List[shapely.Point]:
        return [shapely.Point(pt) for pt in list(geom.coords)]

    def wkt_from_line(self, geom: shapely.LineString) -> List[str]:
        return [shapely.Point(pt).wkt for pt in list(geom.coords)]
    
    def wkb_from_line(self, geom: shapely.LineString) -> List[bytes]:
        return [shapely.Point(pt).wkb for pt in list(geom.coords)]

    def xyz_from_line(self, geom: shapely.LineString
    ) -> List[XY[float] | XYZ[float]]:
        lst = []
        for pt in list(geom.coords):
            if len(pt) <= 2:
                lst.append(XY(*pt))
            else:
                lst.append(XYZ(*pt))
        return lst
    
    def x_y_z_from_line(self, geom: shapely.LineString) -> XY | XYZ:
        x_lst, y_lst, z_lst = [], [], []
        for xyz in self.xyz_from_line(geom):
            x_lst.append(xyz.x)
            y_lst.append(xyz.y)
            if type(xyz) == XYZ:
                z_lst.append(xyz.z)
        if z_lst:
            return XYZ(x_lst, y_lst, z_lst)
        return XY(x_lst, y_lst)
    
    def __func_multi_line(self, geom: shapely.MultiLineString, func: Callable
    ) -> List[List[XY | XYZ | shapely.Point]]:
        lst = []
        for line in shapely.get_parts(geom):
            lst.append(func(line))
        return lst

    def points_from_multi_line(self, geom: shapely.MultiLineString
    ) -> List[List[shapely.Point]]:
        return self.__func_multi_line(geom, self.points_from_line)

    def xyz_from_multi_line(self, geom: shapely.MultiLineString
    ) -> List[List[XY | XYZ]]:
        return self.__func_multi_line(geom, self.xyz_from_line)
    
    def x_y_z_from_multi_line(self, geom: shapely.MultiLineString,
    ) -> List[List[XY | XYZ]]:
        return self.__func_multi_line(geom, self.x_y_z_from_line)

    def wkt_from_multi_line(self, geom: shapely.MultiLineString
    ) -> List[List[str]]:
        return self.__func_multi_line(geom, self.wkt_from_line)
    
    def wkb_from_multi_line(self, geom: shapely.MultiLineString
    ) -> List[List[bytes]]:
        return self.__func_multi_line(geom, self.wkb_from_line)

    def __func_merge(self, geom: shapely.MultiLineString, func: Callable
    ) -> List[XY | XYZ | shapely.Point]:
        merged_lst = []
        for lst in func(geom):
            merged_lst += lst
        return merged_lst

    def merged_points_from_multi_line(self, geom: shapely.MultiLineString
    ) -> List[shapely.Point]:
        return self.__func_merge(geom, self.points_from_multi_line)

    def merged_xyz_from_multi_line(self, geom: shapely.MultiLineString
    ) -> List[XY | XYZ]:
        return self.__func_merge(geom, self.xyz_from_multi_line)
    
    def merged_x_y_z_from_multi_line(self, geom: shapely.MultiLineString
    ) -> XY | XYZ:
        x_lst, y_lst, z_lst = [], [], []
        for line in shapely.get_parts(geom):
            xyz = self.x_y_z_from_line(line)
            x_lst += xyz.x
            y_lst += xyz.y
            if type(xyz) == XYZ:
                z_lst += xyz.z
        if z_lst:
            return XYZ(x_lst, y_lst, z_lst)
        return XY(x_lst, y_lst)
        
    def merged_wkt_from_multi_line(self, geom: shapely.MultiLineString
    ) -> List[str]:
        return self.__func_merge(geom, self.wkt_from_multi_line)

    def merged_wkb_from_multi_line(self, geom: shapely.MultiLineString
    ) -> List[bytes]:
        return self.__func_merge(geom, self.wkb_from_multi_line)




class DisassemblyPolygon(DisassemblyLineString):
    """shapely.geometry.Polygon あるいは shapely.geometry.MultiPolygon を分解する。"""
    def repair_polygon(func):
        def wrapper(self, geom):
            if shapely.is_valid(geom):
                return func(self, geom)
            geom = shapely.make_valid(geom)
            return func(self, geom)
        return wrapper
    
    @repair_polygon
    def _single_disassembly(self, geom: shapely.Polygon) -> RingsParts:
        outer = geom.exterior
        inners = list(shapely.get_parts(geom.interiors))
        return RingsParts(outer, inners)

    def __func_single_poly(self, geom: shapely.Polygon, func: Callable
    ) -> PolyParts:
        rings_parts = self._single_disassembly(geom)
        shell = func(rings_parts.shell)
        holes = []
        if rings_parts.holes:
            for line in rings_parts.holes:
                holes.append(func(line))
        return PolyParts(shell, holes)

    def points_from_poly(self, geom: shapely.Polygon) -> PolyParts:
        return self.__func_single_poly(geom, self.points_from_line)
    
    def xyz_from_poly(self, geom: shapely.Polygon) -> PolyParts:
        return self.__func_single_poly(geom, self.xyz_from_line)
    
    def x_y_z_from_poly(self, geom: shapely.Polygon) -> PolyParts:
        return self.__func_single_poly(geom, self.x_y_z_from_line)
    
    def wkt_from_poly(self, geom: shapely.Polygon) -> PolyParts:
        return self.__func_single_poly(geom, self.wkt_from_line)
    
    def wkb_from_poly(self, geom: shapely.Polygon) -> PolyParts:
        return self.__func_single_poly(geom, self.wkb_from_line)

    def __func_multi_poly(self, geom: shapely.MultiPolygon, func: Callable
    ) -> List[PolyParts]:
        poly_parts_lst = []
        for poly in shapely.get_parts(geom):
            poly_parts_lst.append(self.__func_single_poly(poly, func))
        return poly_parts_lst

    def points_from_multi_poly(self, geom: shapely.MultiPolygon
    ) -> List[PolyParts]:
        return self.__func_multi_poly(geom, self.points_from_line)
    
    def xyz_from_multi_poly(self, geom: shapely.MultiPolygon) -> List[PolyParts]:
        return self.__func_multi_poly(geom, self.xyz_from_line)
    
    def x_y_z_from_multi_poly(self, geom: shapely.MultiPolygon
    ) -> List[PolyParts]:
        return self.__func_multi_poly(geom, self.x_y_z_from_line)

    def wkt_from_multi_poly(self, geom: shapely.MultiPolygon
    ) -> List[PolyParts]:
        return self.__func_multi_poly(geom, self.wkt_points_from_line)

    def wkb_from_multi_poly(self, geom: shapely.MultiPolygon
    ) -> List[PolyParts]:
        return self.__func_multi_poly(geom, self.wkb_from_line)
    
    def __func_merge_poly(self, geom: shapely.MultiPolygon, func: Callable
    ) -> List[Any]:
        lst = []
        for poly_parts in func(geom):
            lst += poly_parts.shell
            if poly_parts.holes:
                for hole in poly_parts.holes:
                    lst += hole
        return lst

    def merged_points_from_multi_poly(self, geom: shapely.MultiPolygon
    ) -> List[shapely.Point]:
        return self.__func_merge_poly(geom, self.points_from_multi_poly)
        
    def merged_xyz_from_multi_poly(self, geom: shapely.MultiPolygon
    ) -> List[XY | XYZ]:
        return self.__func_merge_poly(geom, self.xyz_from_poly)
    
    def merged_x_y_z_from_multi_poly(self, geom: shapely.MultiPolygon
    ) -> XY | XYZ:
        x_lst, y_lst, z_lst = [], [], []
        for xyz in self.x_y_z_from_multi_poly(geom):
            x_lst += xyz.x
            y_lst += xyz.y
            if type(XYZ) == XYZ:
                z_lst += xyz.z
        if z_lst:
            return XYZ(x_lst, y_lst, z_lst)
        return XY(x_lst, y_lst)
    
    def merged_wkt_from_multi_poly(self, geom: shapely.MultiPolygon) -> List[str]:
        return self.__func_merge_poly(geom, self.wkt_from_multi_poly)

    def merged_wkb_from_multi_poly(self, geom: shapely.MultiPolygon) -> List[bytes]:
        return self.__func_merge_poly(geom, self.wkb_from_multi_poly)




class Disassemblies(DisassemblyPoint, DisassemblyPolygon):
    def __init__(self, geom: Any, response_type: int):
        super().__init__()
        self.geom = geom
        self.geom_id = self.check_geometry_type
        self.response_type = response_type
        self.disassembled = self.geom_disassembly
    
    @property
    def check_geometry_type(self) -> int:
        try:
            geom_id = shapely.get_type_id(self.geom)
            if 0 <= geom_id < 7:
                return geom_id
            else:
                logger.error("Geometry type that cannot be processed.")
                return None
        except:
            logger.error("Non-geometry was passed as an argument.")
            return None

    def _points_from(self):
        if self.geom_id is None:
            return None
        elif self.geom_id == 0:
            return self.geom
        elif self.geom_id <= 2:
            return self.points_from_line(self.geom)
        elif self.geom_id == 3:
            return self.points_from_poly(self.geom)
        elif self.geom_id == 4:
            return self.points_from_multi_point(self.geom)
        elif self.geom_id == 5:
            return self.points_from_multi_line(self.geom)
        elif self.geom_id == 6:
            return self.points_from_multi_poly(self.geom)
        return None
    
    def _xyz_from(self):
        if self.geom_id is None:
            return None
        elif self.geom_id == 0:
            return self.geom
        elif self.geom_id <= 2:
            return self.xyz_from_line(self.geom)
        elif self.geom_id == 3:
            return self.xyz_from_poly(self.geom)
        elif self.geom_id == 4:
            return self.xyz_from_multi_point(self.geom)
        elif self.geom_id == 5:
            return self.xyz_from_multi_line(self.geom)
        elif self.geom_id == 6:
            return self.xyz_from_multi_poly(self.geom)
        return None
    
    def _x_y_z_from(self):
        if self.geom_id is None:
            return None
        elif self.geom_id == 0:
            return self.geom
        elif self.geom_id <= 2:
            return self.x_y_z_from_line(self.geom)
        elif self.geom_id == 3:
            return self.x_y_z_from_poly(self.geom)
        elif self.geom_id == 4:
            return self.x_y_z_from_multi_point(self.geom)
        elif self.geom_id == 5:
            return self.x_y_z_from_multi_line(self.geom)
        elif self.geom_id == 6:
            return self.x_y_z_from_multi_poly(self.geom)
        return None
    
    def _wkt_from(self):
        if self.geom_id is None:
            return None
        elif self.geom_id == 0:
            return self.geom
        elif self.geom_id <= 2:
            return self.wkt_from_line(self.geom)
        elif self.geom_id == 3:
            return self.wkt_from_poly(self.geom)
        elif self.geom_id == 4:
            return self.wkt_from_multi_point(self.geom)
        elif self.geom_id == 5:
            return self.wkt_from_multi_line(self.geom)
        elif self.geom_id == 6:
            return self.wkt_from_multi_poly(self.geom)
        return None
    
    def _wkb_from(self):
        if self.geom_id is None:
            return None
        elif self.geom_id == 0:
            return self.geom
        elif self.geom_id <= 2:
            return self.wkb_from_line(self.geom)
        elif self.geom_id == 3:
            return self.wkb_from_poly(self.geom)
        elif self.geom_id == 4:
            return self.wkb_from_multi_point(self.geom)
        elif self.geom_id == 5:
            return self.wkb_from_multi_line(self.geom)
        elif self.geom_id == 6:
            return self.wkb_from_multi_poly(self.geom)
        return None
    
    def _merged_points_from(self):
        if self.geom_id is None:
            return None
        elif self.geom_id == 0:
            return self.geom
        elif self.geom_id <= 2:
            return self.points_from_line(self.geom)
        elif self.geom_id == 3:
            return self.points_from_poly(self.geom)
        elif self.geom_id == 4:
            return self.points_from_multi_point(self.geom)
        elif self.geom_id == 5:
            return self.merged_points_from_multi_line(self.geom)
        elif self.geom_id == 6:
            return self.merged_points_from_multi_poly(self.geom)
        return None

    def _merged_xyz_from(self):
        if self.geom_id is None:
            return None
        elif self.geom_id == 0:
            return self.geom
        elif self.geom_id <= 2:
            return self.xyz_from_line(self.geom)
        elif self.geom_id == 3:
            return self.xyz_from_poly(self.geom)
        elif self.geom_id == 4:
            return self.xyz_from_multi_point(self.geom)
        elif self.geom_id == 5:
            return self.merged_xyz_from_multi_line(self.geom)
        elif self.geom_id == 6:
            return self.merged_xyz_from_multi_poly(self.geom)
        return None
    
    def _merged_x_y_z_from(self):
        if self.geom_id is None:
            return None
        elif self.geom_id == 0:
            return self.geom
        elif self.geom_id <= 2:
            return self.x_y_z_from_line(self.geom)
        elif self.geom_id == 3:
            return self.x_y_z_from_poly(self.geom)
        elif self.geom_id == 4:
            return self.x_y_z_from_multi_point(self.geom)
        elif self.geom_id == 5:
            return self.merged_x_y_z_from_multi_line(self.geom)
        elif self.geom_id == 6:
            return self.merged_x_y_z_from_multi_poly(self.geom)
        return None

    def _merged_wkt_from(self):
        if self.geom_id is None:
            return None
        elif self.geom_id == 0:
            return self.geom
        elif self.geom_id <= 2:
            return self.wkt_from_line(self.geom)
        elif self.geom_id == 3:
            return self.wkt_from_poly(self.geom)
        elif self.geom_id == 4:
            return self.wkt_from_multi_point(self.geom)
        elif self.geom_id == 5:
            return self.merged_wkt_from_multi_poly(self.geom)
        elif self.geom_id == 6:
            return self.wkt_from_multi_poly(self.geom)
        return None
    
    def _merged_wkb_from(self):
        if self.geom_id is None:
            return None
        elif self.geom_id == 0:
            return self.geom
        elif self.geom_id <= 2:
            return self.wkb_from_line(self.geom)
        elif self.geom_id == 3:
            return self.wkb_from_poly(self.geom)
        elif self.geom_id == 4:
            return self.wkb_from_multi_point(self.geom)
        elif self.geom_id == 5:
            return self.merged_wkb_from_multi_poly(self.geom)
        elif self.geom_id == 6:
            return self.wkb_from_multi_poly(self.geom)
        return None

    @property
    def geom_disassembly(self):
        dic = {
            0: self._points_from,
            1: self._xyz_from,
            2: self._x_y_z_from,
            3: self._wkt_from,
            4: self._wkb_from,
            5: self._merged_points_from,
            6: self._merged_xyz_from,
            7: self._merged_x_y_z_from,
            8: self._merged_wkt_from,
            9: self._merged_wkb_from
        }
        return dic.get(self.response_type)()
        



def geom_disassembly(geom: Any, response_type: int) -> Any:
    """
    """
    disassemblies = Disassemblies(geom, response_type)
    return disassemblies.disassembled
    


if __name__ == '__main__':
    # import doctest
    # doctest.testmod()
    main_square = [
        shapely.Point(0, 0),
        shapely.Point(10, 0),
        shapely.Point(10, 10),
        shapely.Point(0, 10),
    ]
    inner_square_1 = [
        shapely.Point(1, 1),
        shapely.Point(3, 1),
        shapely.Point(3, 3),
        shapely.Point(1, 3),
    ]
    inner_square_2 = [
        shapely.Point(5, 5),
        shapely.Point(7, 5),
        shapely.Point(7, 7),
        shapely.Point(5, 7),
    ]
    outer_square = [
        shapely.Point(11, 0),
        shapely.Point(15, 0),
        shapely.Point(15, 15),
        shapely.Point(11, 15),
    ]
    outer_within = [
        shapely.Point(12, 1),
        shapely.Point(14, 1),
        shapely.Point(14, 14),
        shapely.Point(12, 14),
    ]

    poly1 = shapely.Polygon(shell=main_square)
    poly2 = shapely.Polygon(shell=main_square, holes=[inner_square_1, inner_square_2])
    poly3 = shapely.Polygon(shell=outer_square, holes=[outer_within])
    m_poly = shapely.MultiPolygon([poly2, poly3])