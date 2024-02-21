from dataclasses import dataclass

import numpy as np



@dataclass
class ColorRanges:
    lower_thres: np.ndarray
    upper_thres: np.ndarray


class ColorMaskHSV(object):
    def __range_100(self, value: int) -> int:
        return int((value / 100) * 255)
    
    def __range_360(self, value: int) -> int:
        return int((value / 360) * 255)
    
    def create_color_range(
        self, 
        hlw: int, hup: int, 
        slw: int=0, sup: int=100,
        vlw: int=0, vup: int=100
    ) -> ColorRanges:
        lower = np.array([
            self.__range_360(hlw), 
            self.__range_100(slw), 
            self.__range_100(vlw)
        ])
        upper = np.array([
            self.__range_360(hup), 
            self.__range_100(sup),
            self.__range_100(vup)
        ])
        return ColorRanges(lower, upper)

    @property
    def green_range(self) -> ColorRanges:
        return self.create_color_range(60, 120)
    
    @property
    def light_green_range(self) -> ColorRanges:
        """田んぼなどが分かりやすくなる"""
        return self.create_color_range(60, 89)
    
    @property
    def dark_green_range(self) -> ColorRanges:
        """森林などが分かりやすくなる"""
        return self.create_color_range(90, 119)
    
    @property
    def blue_range(self) -> ColorRanges:
        return self.create_color_range(150, 249)
    
    @property
    def warm_range(self) -> ColorRanges:
        """建物や道路、地面が対象"""
        return self.create_color_range(1, 59)
    
    @property
    def red_range(self) -> ColorRanges:
        """建物や地面が対象"""
        return self.create_color_range(1, 29)
    
    @property
    def orange_range(self) -> ColorRanges:
        return self.create_color_range(30, 59)
