'''
Program with a function that requests the current weather in Belfast
from OpenWeatherMap.
'''
import json
from urllib import request
import time
import json


def getCurrentWeather(weatherType, city="Belfast"):
   '''
   This function allows you to request the current
   - temperature
   - description
   - wind
   - pressure
   '''

   currentWeather = get_json(city="Belfast")
   
   weatherInfo = ""

   if weatherType == "temperature":
       weatherInfo = str(currentWeather.get("main").get("temp"))
   elif weatherType == "pressure":
       weatherInfo = str(currentWeather.get("main").get("pressure"))
   elif weatherType == "humidity":
       weatherInfo = str(currentWeather.get("main").get("humidity"))
   elif weatherType == "description":
       weatherInfo = currentWeather.get("weather")[0].get("description")
   elif weatherType == "wind":
       weatherInfo = str(currentWeather.get("wind").get("deg")) + " degrees, " + str(currentWeather.get("wind").get("speed"))  + "mph"

   return(weatherInfo)

def get_json(city="Belfast"):
   
   # Get appid from config file
   with open("/home/pi/python_scripts/enviroproject/config.json", "r") as f:
    config = json.load(f)
    appid = config["WEATHERAPI"]["APPID"]

   weatherUrl = f"http://api.openweathermap.org/data/2.5/weather?q={city},uk&units=metric&appid={appid}"
   httpResponse = request.urlopen(weatherUrl)
   currentWeather = json.load(httpResponse)
   return currentWeather

def get_sunrise(city="Belfast"):
   currentWeather = get_json(city)
   sunrise =  str(currentWeather.get("sys").get("sunrise"))   
   sunrise_time = time.strftime('%H:%M:%S', time.localtime(int(sunrise)))
   return(sunrise_time)

def get_sunset(city="Belfast"):
   currentWeather = get_json(city)
   sunset =  str(currentWeather.get("sys").get("sunset"))   
   sunset_time = time.strftime('%H:%M:%S', time.localtime(int(sunset)))
   return(sunset_time)


if __name__ == "__main__":
        
    my_list = "humidity temperature description wind pressure".split(" ")
    for item in my_list:
       print(getCurrentWeather(item))

    temperature = float(getCurrentWeather("temperature", "Belfast"))

    if temperature >=20:
        print("Go camping on cousin's farm for a month")
    elif temperature >= 15:
        print("Go for a bike ride")
    else:
        print("cry")
    print(f"Sunrise = {get_sunrise()}")

    print(f"Sunset = {get_sunset()}")
