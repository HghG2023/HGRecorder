import json
import requests
api_key = "b5fd4669de01d15647e891733864f31c"

def get_locations(address):
    api_url=f'https://restapi.amap.com/v3/geocode/geo?address={address}&key={api_key}&output=json&callback=showLocation'
    data=requests.get(api_url)
    data=data.text
    data=data.strip('showLocation(')
    data=data.strip(')')
    jsonData_lovation=json.loads(data)['geocodes'][0]['location']
    jsonData_citycode=json.loads(data)['geocodes'][0]['adcode']
    return jsonData_lovation,jsonData_citycode



respon = requests.get("https://restapi.amap.com/v3/weather/weatherInfo?city=110101&key={api_key}&extensions=all").text
print(respon)

# {"status":"0","info":"INVALID_USER_KEY","infocode":"10001"}