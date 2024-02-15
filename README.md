# GISで使いたいモジュールを作成しています。

## absolute_to_relative.py :
経緯度から真北の方位角と水平距離を計算します。
```py
>>> import shapely
>>> from apps.absolute_to_relative import absolute_to_relative_coords
>>> ...
>>> ...
# shapely.LineString | shapely.Polygon ならば RelatieCoordinates を返す。
>>> coords = absolute_to_relative_coords(polygon, epsg=6678, closed=True)

# shapely.MultiLineString | shapely.MultiPolygon ならば List[RelatieCoordinates] を返す。
>>> coords_lst = absolute_to_relative_coords(multi_polygon, epsg=6678, closed=True)
```
<br>


## chiriin_api.py :
国土地理院の提供しているAPIを使用する為のモジュール
https://vldb.gsi.go.jp/sokuchi/surveycalc/api_help.html

### 経緯度から標高を取得する。
```py
>>> from apps.chiriin_api import lonlat_to_altitude
>>> lon = 141.307135647
>>> lat = 41.142745499
>>> result = lonlat_to_altitude(lon, lat)
>>> print(result)
Altitude(altitude=108, source='10m')
```

### セミダイナミック補正（地殻変動補正）
```py
>>> from apps.chiriin_api import semidynamic_exe
# 今期から元期（がんき）へ
>>> lon = 141.307135647
>>> lat = 41.142745499
>>> data_year = 2023
>>> semidynamic_exe(lon, lat, data_year, time_out=30, sokuchi=0)
Fixed(lon=141.307138653, lat=41.142742044, altitude=None)

# 元期から今期へ
>>> semidynamic_exe(lon, lat, data_year, time_out=30, sokuchi=1)
Fixed(lon=141.307132642, lat=41.142748956, altitude=None)
```
<br>


## disassembly.py :
shapely.geometry.xxxのオブジェクトを分解する。
引数として渡す`resps`で戻り値の型が変わる。
 - point = List[shapely.Point]
 - xyz = List[List[x0, y0, z0], List[x1, y1, z1], ...]
 - xyz = List[List[x0, x1, ...], List[y0, y1, ...], List[z0, z1, ...]]
```py
>>> from shapely
>>> from apps.disassembly import geom_disassembly
>>> ...
>>> ...
>>> points = geom_disassembly(polygon, point)
>>> xyz = geom_disassembly(polygon, 'xyz')
>>> x, y, z = geom_disassembly(polygon, 'x_y_z')
```
<br>

## spatial_matelials.py :
空間検索で使いたい材料をまとめたファイル。
※メルカトル図法を対象としています。

### directional_rectangle
ベース地点からある方向に向かって長方形のバッファーを作成する。
```py
>>> import shapely
>>> from apps.spatial_materials import directional_rectangle
>>> lon = 141.307135647
>>> lat = 41.142745499
>>> base_point = shapely.Point(lon, lat)
>>> distance = 1000
>>> angle = 45
>>> width = 200
>>> poly: shapely.Polygon = directional_rectangle(base_point, distance, angle, width)
```

### directional_fan
ベース地点から扇状のPolygonを作成する。
```py
>>> import shapely
>>> from apps.spatial_materials import directional_fan
>>> lon = 141.307135647
>>> lat = 41.142745499
>>> base_point = shapely.Point(lon, lat)
>>> distance = 1000
>>> angle1 = 330
>>> angle2 = 30
>>> poly: shapely.Polygon = directional_fan(base_point, distance, angle1, angle2)
```


### regular_hexagon
指定座標を中心とし、指定面積の正六角形の`shapely.Polygon`を作成する。
```py
>>> import shapely
>>> from apps.spatial_materials import regular_hexagon
>>> hectare = 1.0
>>> center_x = 447701.6834848647
>>> center_y = 4632832.1148246825
>>> hexagon: shapely.Polygon = regular_hexagon(hectare, center_x, center_y)
```

### regular_hexagon_gdf
渡した`shapely.geometry.`の範囲に指定面積の正六角形の`shapely.Polygon`を、左上から
右下に向かって並べる様にListに格納。
順番に行番号と列番号を与えて`geopandas.GeoDataFrame`に入力して返す。
CRSは自分で設定してください。
```py
>>> import shapely
>>> from apps.spatial_materials import regular_hexagon_gdf
>>> ...
>>> ...
>>> hectare = 1.0
>>> hexagon_gdf = regular_hexagon_gdf(hectare, polygon, margin=10)
```