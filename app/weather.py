url = "https://restapi.amap.com/v3/weather/weatherInfo?city=110101&key=b5fd4669de01d15647e891733864f31c&extensions=all"


import requests
import json
class Weather:
    def __init__(self):
        self.baseurl = "https://restapi.amap.com/v3/weather/weatherInfo?"
        self.api_key = "b5fd4669de01d15647e891733864f31c"
        self.city = "110101" # default to Beijing
        self.searchtype = "base"

    def get_weather(self, city=None, searchtype=None):
        if city:
            self.city = city
        if searchtype:
            self.searchtype = searchtype
        url = self.baseurl + "city=" + self.city + "&key=" + self.api_key + "&extensions=" + self.searchtype
        response = requests.get(url)
        data = response.json()
        return data

w = Weather()
print(w.get_weather(searchtype="all"))
