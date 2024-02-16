"""
1. geom_disassembly
    shapelyのgeometryを分解する。
"""
from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import shapely


@dataclass
class XYZ:
    x: List[float]
    y: List[float]
    z: List[float]


class DisassemblyPoint(object):
    def pt_to_xyz(self, geom: shapely.Point) -> Tuple[float]:
        return (geom.x, geom.y)
    
    def multi_pt_to_points(self, geom: shapely.MultiPoint) -> List[shapely.Point]:
        return list(shapely.get_parts(geom))

    def multi_pt_to_xyz(self, geom: shapely.MultiPoint) -> Tuple[Tuple[float]]:
        geo_dict = geom.__geo_interface__
        return geo_dict.get('coordinates')
    
    def multi_pt_to_x_y_z(self, geom: shapely.MultiPoint, data_class: bool=False) -> XYZ:
        points = self.multi_pt_to_points(geom)
        x, y, z = [], [], []
        for point in points:
            x.append(point.x)
            y.append(point.y)
            if point.has_z:
                z.append(point.z)
            else:
                z.append(None)
        if data_class:
            return XYZ(x, y, z)
        return [x, y, z]


class DisassemblyLineString(object):
    def line_to_points(self, geom: shapely.LineString) -> List[shapely.Point]:
        lst = []
        count = shapely.get_num_points(geom)
        for i in range(count):
            pt = shapely.get_point(geom, i)
            lst.append(pt)
        return lst
    
    def line_to_xyz(self, geom: shapely.LineString) -> List[Tuple[float]]:
        return list(geom.coords)
    
    def line_to_x_y_z(self, geom: shapely.LineString, data_class: bool=False) -> List[List[float]]:
        xyz_lst = self.line_to_xyz(geom)
        x, y, z = [], [], []
        for xyz in xyz_lst:
            x.append(xyz[0])
            y.append(xyz[1])
            if len(xyz) <= 2:
                z.append(None)
            else:
                z.append(xyz[2])
        if data_class:
            return XYZ(x, y, z)
        else:
            return [x, y, z]

    def multi_line_to_points(
        self,
        geom: shapely.MultiLineString
    ) -> List[List[shapely.Point]]:
        lst = []
        for line in shapely.get_parts(geom):
            points = self.line_to_points(line)
            lst.append(points)
        return lst
    
    def multi_line_to_xyz(self, 
        geom: shapely.MultiLineString
    ) -> List[List[Tuple[float]]]:
        lst = []
        for line in shapely.get_parts(geom):
            xyz = self.line_to_xyz(line)
            lst.append(xyz)
        return lst
    
    def multi_line_to_x_y_z(self, 
        geom: shapely.MultiLineString,
        data_class: bool=False
    ) -> List[List[List[float]]]:
        parts = []
        for line in shapely.get_parts(geom):
            parts.append(self.line_to_x_y_z(line, data_class))
        return parts
        
    

@dataclass
class PolyParts:
    outer: List[float | shapely.Point]
    inners: List[float | shapely.Point]


class DisassemblyPolygon(DisassemblyLineString):
    def poly_to_points(self, geom: shapely.Polygon) -> List[shapely.Point]:
        return [shapely.Point(p) for p in geom.exterior.coords]
    
    def poly_to_xyz(self, geom: shapely.Polygon) -> List[Tuple[float]]:
        return list(geom.exterior.coords)
    
    def poly_to_x_y_z(self, geom: shapely.Polygon, data_class: bool=False) -> List[List[float]]:
        points = self.poly_to_points(geom)
        x, y, z = [], [], []
        for point in points:
            x.append(point.x)
            y.append(point.y)
            if point.has_z:
                z.append(point.z)
            else:
                z.append(None)
        if data_class:
            return XYZ(x, y, z)
        return [x, y, z]
    
    def multi_poly_to_points(
        self, 
        geom: shapely.MultiPolygon,
        data_class: bool=False
    ) -> List[List[List[float]]] | List[PolyParts]:
        lst = []
        for poly in shapely.get_parts(geom):
            outer_ring = shapely.get_exterior_ring(poly)
            outer_points = self.line_to_points(outer_ring)
            inner_count = shapely.get_num_interior_rings(poly)
            inner_rings = []
            if 1 <= inner_count:
                for i in range(inner_count):
                    inner_ring = shapely.get_interior_ring(poly, i)
                    inner_points = self.line_to_points(inner_ring)
                    inner_rings.append(inner_points)
            if data_class:
                lst.append(PolyParts(outer_points, inner_rings))
            else:
                lst.append([outer_points, inner_rings])
        return lst
    
    def _points_to_xyz(self, points: List[shapely.Point], *args) -> List[Tuple[float]]:
        line = shapely.LineString(points)
        return self.line_to_xyz(line)

    def _points_to_x_y_z(self, points: List[shapely.Point], data_class: bool=False) -> List[List[float]]:
        line = shapely.LineString(points)
        return self.line_to_x_y_z(line, data_class)
    
    def __disassembly(
        self, 
        geom: shapely.MultiPolygon,
        func: Any,
        data_class: bool=False
    ) -> List[List[List[float]]] | PolyParts:
        parts_lst = self.multi_poly_to_points(geom, True)
        lst = []
        for parts in parts_lst:
            outer = func(parts.outer, data_class)
            inners = []
            if parts.inners:
                for inner in parts.inners:
                    _inner = func(inner, data_class)
                    inners.append(_inner)
            if data_class:
                lst.append(PolyParts(outer, inners))
            else:
                lst.append([outer, inners])
        return lst
    
    def multi_poly_to_xyz(self, geom: shapely.MultiPolygon, data_class: bool=False):
        return self.__dissembly(geom, self._points_to_xyz, data_class)

    def multi_poly_to_x_y_z(self, geom: shapely.MultiPolygon, data_class: bool=False):
        return self.__dissembly(geom, self._points_to_x_y_z, data_class)
        


class Disassembly(DisassemblyPoint, DisassemblyPolygon):
    def __init__(self, geom: Any, response: str='point', data_class: bool=True):
        self.geom = geom
        self.response = response
        self.data_class = data_class
    
    @property
    def disassembly_point(self) -> Any:
        if self.response == 'point':
            return self.geom
        else:
            return self.pt_to_xyz(self.geom)
    
    @property
    def disassembly_multi_point(self) -> Any:
        if self.response == 'xyz':
            return self.multi_pt_to_xyz(self.geom)
        elif self.response == 'x_y_z':
            return self.multi_pt_to_x_y_z(self.geom, self.data_class)
        else:
            return self.multi_pt_to_points(self.geom)
    
    @property
    def disassembly_line(self) -> Any:
        if self.response == 'xyz':
            return self.line_to_xyz(self.geom)
        elif self.response == 'x_y_z':
            return self.line_to_x_y_z(self.geom, self.data_class)
        else:
            return self.line_to_points(self.geom)
    
    @property
    def disassembly_multi_line(self) -> Any:
        if self.response == 'xyz':
            return self.multi_line_to_xyz(self.geom)
        elif self.response == 'x_y_z':
            return self.multi_line_to_x_y_z(self.geom, self.data_class)
        else:
            return self.multi_line_to_points(self.geom)
    
    @property
    def disassembly_poly(self) -> Any:
        if self.response == 'xyz':
            return self.poly_to_xyz(self.geom)
        elif self.response == 'x_y_z':
            return self.poly_to_x_y_z(self.geom, self.data_class)
        else:
            return self.poly_to_points(self.geom)
        
    @property
    def disassembly_multi_poly(self) -> Any:
        if self.response == 'xyz':
            return self.multi_poly_to_xyz(self.geom, self.data_class)
        elif self.response == 'x_y_z':
            return self.multi_poly_to_x_y_z(self.geom, self.data_class)
        else:
            return self.multi_poly_to_points(self.geom, self.data_class)
    


def geom_disassembly(geom: Any, response: str='point', data_class: bool=True) -> Any:
    """
    Args:
        geom(Any): shapely.Point | shapely.MultiPoint | shapely.LineString 
            | shapely.MultiLineString | shapely.Polygon | shapely.MultiPolygon
        response(str): 'point' | 'xyz' | 'x_y_z' 戻り値の種類を選択
        data_class(bool): 
            MultiPolygonなどはOuter,Innerなどがあり只のListだと解りづらいので
    Returns:
        Any:
    """
    disassembly = Disassembly(geom, response, data_class)
    geom_id = shapely.get_type_id(geom)
    if geom_id == 0:
        return disassembly.disassembly_point
    elif geom_id == 1:
        return disassembly.disassembly_line
    elif geom_id == 3:
        return disassembly.disassembly_poly
    elif geom_id == 4:
        return disassembly.disassembly_multi_point
    elif geom_id == 5:
        return disassembly.disassembly_multi_line
    elif geom_id == 6:
        return disassembly.disassembly_multi_poly
    else:
        return None
