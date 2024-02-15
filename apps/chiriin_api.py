"""
国土地理院の提供しているAPIで情報を取得する為のモジュール
https://vldb.gsi.go.jp/sokuchi/surveycalc/api_help.html
1. lonlat_to_altitude
    経緯度から標高を取得する
2. semidynamic_exe
    セミダイナミック補正
"""
from dataclasses import dataclass
import logging
import requests
import time
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
formatter = '%(levelname)s\ntime: %(asctime)s\nfunc: %(funcName)s\nmsg: %(message)s'
logging.basicConfig(format=formatter)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class Altitude:
    altitude: float
    source: str



def lonlat_to_altitude(lon: float, lat: float, time_out: int=20) -> float:
    """国土地理院のAPIを用いて経緯度から標高を取得する。\n
    https://maps.gsi.go.jp/development/altitude_s.html \n
    Args:
        lon(flaot): 経度
        lat(float): 緯度
    Returns:
        Altitude:
            altitude(float): 標高
            source(str): データソースの分解能
    Doctest:
        >>> lonlat_to_altitude(141.307135647, 41.142745499)
        Altitude(altitude=108, source='10m')

    """
    t = time.time()
    dummy = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'
    url = 'https://cyberjapandata2.gsi.go.jp/general/dem/scripts/getelevation.php?'
    param = f'lon={lon}&lat={lat}&outtype=JSON'
    while True:
        resps = (
            requests
            .get(
                url=url + param, 
                headers={'User-Agent': dummy},
                timeout=10
            )
        )
        resps = resps.json()
        if resps.get('ErrMsg') is None:
            return Altitude(*list(resps.values()))
        else:
            logger.info(resps.get('ErrMsg'))
            time.sleep(0.5)
        if time_out < time.time() - t:
            logger.error('Failed to request.')
            return None



@dataclass
class Fixed:
    lon: float
    lat: float
    altitude: float


class SemiDynamicCorrection(object):
    def __init__(
        self, 
        lon: float, 
        lat: float, 
        data_year: int, 
        altitude: float=0, 
        time_out: float=30
    ):
        """
        Args:
            lon(float): 経度
            lat(float): 緯度
            data_year(int): データ取得年度。期首が4/1
            altitude(float): 標高
            time_out(int): 失敗を判断するまでの時間
        init:
            URL: セミダイナミック補正の指定URL
            OUTPUT_TYPE: json or xml
            SOKUCHI: 0 = [元期 -> 今期], 1 = [今期 -> 元期]
            PLACE: 0 = [経緯度], 1 = [平面直角座標系]
            HOSEI_J: 2 = [2次元補正], 3 = [3次元補正]
        """
        # 地理院セミダイナミック補正用URL
        self.URL = "http://vldb.gsi.go.jp/sokuchi/surveycalc/semidyna/web/semidyna_r.php?"
        self.SOKUCHI = 1 
        self.PLACE = 0
        self.HOSEI_J = 2
        self.lon = lon
        self.lat = lat
        self.altitude = altitude
        self.data_year = data_year
        self.time_out = time_out
    
    @property
    def get_param_file_name(self) -> str:
        """セミダイナミック補正のパラメータファイル名を取得
        https://www.gsi.go.jp/sokuchikijun/semidyna_download.html
        """
        return f"SemiDyna{self.data_year}.par"

    @property
    def request(self) -> str:
        url = self.URL
        url += f'outputType=json&'
        url += f'chiiki={self.get_param_file_name}&'
        url += f'sokuchi={self.SOKUCHI}&'
        url += f'Place={self.PLACE}&'
        url += f'Hosei_J={self.HOSEI_J}&'
        url += f'latitude={self.lat}&'
        url += f'longitude={self.lon}&'
        url += f'altitude1={self.altitude}'
        return requests.get(url, timeout=5).json()
    
    def __registration(self, resps: dict) -> Fixed:
        lon = float(resps.get('longitude'))
        lat = float(resps.get('latitude'))
        try:
            altitude = float(resps.get('altitude'))
        except Exception:
            altitude = None
        return Fixed(lon ,lat, altitude)
    
    @property
    def fix(self):
        """セミダイナミック補正の実行。"""
        t = time.time()
        while True:
            resps = self.request
            if resps.get('ErrMsg') is None:
                data = resps.get('OutputData')
                return self.__registration(data)
            else:
                logger.info(resps.get('ErrMsg'))
                time.sleep(0.9)
            if self.time_out < time.time() - t:
                return Fixed(None, None, None)


def semidynamic_exe(
    lon: float, 
    lat: float, 
    data_year: int, 
    time_out: float=30,
    sokuchi: int=1
) -> Fixed:
    """
    セミダイナミック補正の実行（2次元補正）
    https://www.gsi.go.jp/sokuchikijun/semidyna.html
    Args:
        lon(float): 経度
        lat(float): 緯度
        data_year(int): データ取得年度。期首が4/1
        time_out(int): 失敗を判断するまでの時間
        sokuchi(int): 0: 元期 -> 今期, 1: 今期 -> 元期
    Returns:
        Fixed:
            lon(float): 補正後の経度
            lat(float): 補正後の緯度
            altitude(float): 補正後の標高
    Doctest:
        >>> lat = 41.142745499
        >>> lon = 141.307135647
        >>> data_year = 2023
        >>> semidynamic_exe(lon, lat, data_year, time_out=30)
        Fixed(lon=141.307132642, lat=41.142748956, altitude=None)
    """
    semidyna = SemiDynamicCorrection(lon, lat, data_year, time_out=time_out)
    semidyna.SOKUCHI = sokuchi
    return semidyna.fix






if __name__ == '__main__':
    import doctest
    doctest.testmod()
