APPS_DIR = r"G:/マイドライブ/Projects/gis_drawer"

TRUE_IMG_HIROSAKI = "datasets/images_HIROSAKI/2023-08-10-00_00_2023-08-10-23_59_Sentinel-2_L2A_True_color.tiff"
B8_IMG_HIROSAKI = "datasets/images_HIROSAKI/2023-08-10-00_00_2023-08-10-23_59_Sentinel-2_L2A_B08_(Raw).tiff"

TRUE_IMG_AOMORI = "datasets/images_AOMORI/2023-08-10-00_00_2023-08-10-23_59_Sentinel-2_L2A_True_color.tiff"
B8_IMG_AOMORI = "datasets/images_AOMORI/2023-08-10-00_00_2023-08-10-23_59_Sentinel-2_L2A_B08_(Raw).tiff"

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
