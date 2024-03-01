RASTER_DRIVER = "GTiff"

""" 日本のUTM座標系の範囲と対応するEPSGコード """
JGD2011_UTM_RANGE_LST = [
    [120, 126],
    [126, 132],
    [132, 138],
    [138, 144],
    [144, 150]
]
JGD2011_UTM_CODES_DICT = {
    0: 6668,
    1: 6689,
    2: 6690,
    3: 6691,
    4: 6692
}


# ------ モジュールを作成する為、一時的に使うデータ ------#
import shapely

def get_collection():
    outer_square = [[11, 0], [15, 0], [15, 15], [11, 15]]
    miss_outer_inner = [[12, 1], [14, 1], [14, 15], [12, 14]]
    outer_within = [[12, 1], [14, 1], [14, 15], [12, 14]]

    miss_poly1 = shapely.Polygon([[0, 0], [0, 10], [10, 10], [10, 5],
                                [7, 10], [5, 10], [10, 3], [10, 0], 
                                [6, 0], [0, 5], [2, 0]])
    miss_poly2 = (shapely
                .Polygon(outer_square).difference(
                        shapely.Polygon(miss_outer_inner)
                    ))
    miss_poly3 = shapely.affinity.translate(miss_poly2, xoff=5)
    poly1 = shapely.affinity.translate(
        shapely.affinity.rotate(
            shapely.Polygon(outer_square), 90
        ), xoff=-5, yoff=12
    )
    poly2_outer = shapely.affinity.translate(poly1, yoff=5)
    poly2_inner = shapely.affinity.scale(poly2_outer, xfact=0.6, yfact=0.6)
    poly2 = poly2_outer.difference(poly2_inner)
    point = shapely.Point(5, 12)
    points = shapely.MultiPoint([(1, 14), (4, 14), (7, 12)])
    line = shapely.LineString([(25, 3), (25, 10), (22, 6), (22, 15)])

    COLLECTION = shapely.GeometryCollection([
        shapely.MultiPolygon([miss_poly1, miss_poly2, poly1]),
        shapely.MultiPolygon([miss_poly3]),
        poly2,
        point,
        points,
        line
    ])
    return COLLECTION

COLLECTION_GEOMETRY = get_collection()