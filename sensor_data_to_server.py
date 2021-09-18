#!/usr/bin/env python3

########################################################################
# 
# Reads environmental data from enviro+ sensor on raspberry pi
# ESP32 via MQTT
# OpenWeatherMap Api
# Writes data to csv, a MySQL server on the Raspberry Pi, and sends it to Azure
# Checks for low and high values and sends an alert to the user                    
# 
########################################################################

import time
import colorsys
import sys
import ST7735
import datetime as dt
import requests
import urllib
import weather_warning_sender
import write_to_csv
import json
import sql_writer

import weatherscraper

import mqtt_to_esp32


# set variables
name = "Ali Dore"
email = "50031595@belfastmet.ac.uk"  # No one else will see this, you'll be emailed if your server stops sending data
latitude = 54.53292600186758
longitude = -5.849735364895184
location_description = "indoors"  #e.g. indoors, outdoors, garage, shed

try:
    # Transitional fix for breaking change in LTR559
    from ltr559 import LTR559
    ltr559 = LTR559()
except ImportError:
    import ltr559

from bme280 import BME280
from pms5003 import PMS5003, ReadTimeoutError as pmsReadTimeoutError, SerialTimeoutError
from enviroplus import gas
from subprocess import PIPE, Popen
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from fonts.ttf import RobotoMedium as UserFont
import logging

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

logging.info("""Sends readings from all of Enviro plus' sensors to Azure""")

# BME280 temperature/pressure/humidity sensor
bme280 = BME280()

# PMS5003 particulate sensor
pms5003 = PMS5003()
time.sleep(1.0)

# Create ST7735 LCD display class
st7735 = ST7735.ST7735(
    port=0,
    cs=1,
    dc=9,
    backlight=12,
    rotation=270,
    spi_speed_hz=10000000
)

# Initialize display
st7735.begin()

WIDTH = st7735.width
HEIGHT = st7735.height

# Set up canvas and font
img = Image.new('RGB', (WIDTH, HEIGHT), color=(0, 0, 0))
draw = ImageDraw.Draw(img)
font_size_small = 10
font_size_large = 20
font = ImageFont.truetype(UserFont, font_size_large)
smallfont = ImageFont.truetype(UserFont, font_size_small)
x_offset = 2
y_offset = 2

message = ""

# The position of the top bar
top_pos = 25

# Create a values dict to store the data
variables = ["temperature",
             "pressure",
             "humidity",
             "light",
             "oxidised",
             "reduced",
             "nh3",
             "pm1",
             "pm25",
             "pm10"]

units = ["C",
         "hPa",
         "%",
         "Lux",
         "kO",
         "kO",
         "kO",
         "ug/m3",
         "ug/m3",
         "ug/m3"]

# Define your own warning limits
# The limits definition follows the order of the variables array
# Example limits explanation for temperature:
# [4,18,28,35] means
# [-273.15 .. 4] -> Dangerously Low
# (4 .. 18]      -> Low
# (18 .. 28]     -> Normal
# (28 .. 35]     -> High
# (35 .. MAX]    -> Dangerously High
# DISCLAIMER: The limits provided here are just examples and come
# with NO WARRANTY. The authors of this example code claim
# NO RESPONSIBILITY if reliance on the following values or this
# code in general leads to ANY DAMAGES or DEATH.
limits = [[4, 18, 28, 35],
          [250, 650, 1013.25, 1015],
          [20, 30, 60, 70],
          [-1, -1, 30000, 100000],
          [-1, -1, 40, 50],
          [-1, -1, 450, 550],
          [-1, -1, 200, 300],
          [-1, -1, 50, 100],
          [-1, -1, 50, 100],
          [-1, -1, 50, 100]]

# RGB palette for values on the combined screen
palette = [(0, 0, 255),           # Dangerously Low
           (0, 255, 255),         # Low
           (0, 255, 0),           # Normal
           (255, 255, 0),         # High
           (255, 0, 0)]           # Dangerously High

values = {}


# Displays data and text on the 0.96" LCD
def display_text(variable, data, unit):
    # Maintain length of list
    values[variable] = values[variable][1:] + [data]
    # Scale the values for the variable between 0 and 1
    vmin = min(values[variable])
    vmax = max(values[variable])
    colours = [(v - vmin + 1) / (vmax - vmin + 1) for v in values[variable]]
    # Format the variable name and value
    message = "{}: {:.1f} {}".format(variable[:4], data, unit)
    logging.info(message)
    draw.rectangle((0, 0, WIDTH, HEIGHT), (255, 255, 255))
    for i in range(len(colours)):
        # Convert the values to colours from red to blue
        colour = (1.0 - colours[i]) * 0.6
        r, g, b = [int(x * 255.0) for x in colorsys.hsv_to_rgb(colour, 1.0, 1.0)]
        # Draw a 1-pixel wide rectangle of colour
        draw.rectangle((i, top_pos, i + 1, HEIGHT), (r, g, b))
        # Draw a line graph in black
        line_y = HEIGHT - (top_pos + (colours[i] * (HEIGHT - top_pos))) + top_pos
        draw.rectangle((i, line_y, i + 1, line_y + 1), (0, 0, 0))
    # Write the text at the top in black
    draw.text((0, 0), message, font=font, fill=(0, 0, 0))
    st7735.display(img)


# Saves the data to be used in the graphs later and prints to the log
def save_data(idx, data):
    variable = variables[idx]
    # Maintain length of list
    values[variable] = values[variable][1:] + [data]
    unit = units[idx]
    message = "{}: {:.1f} {}".format(variable[:4], data, unit)
    logging.info(message)


# Displays all the text on the 0.96" LCD
def display_everything():
    draw.rectangle((0, 0, WIDTH, HEIGHT), (0, 0, 0))
    column_count = 2
    row_count = (len(variables) / column_count)
    for i in range(len(variables)):
        variable = variables[i]
        data_value = values[variable][-1]
        unit = units[i]
        x = x_offset + ((WIDTH // column_count) * (i // row_count))
        y = y_offset + ((HEIGHT / row_count) * (i % row_count))
        message = "{}: {:.1f} {}".format(variable[:4], data_value, unit)
        lim = limits[i]
        rgb = palette[0]
        for j in range(len(lim)):
            if data_value > lim[j]:
                rgb = palette[j + 1]
        draw.text((x, y), message, font=smallfont, fill=rgb)
    st7735.display(img)


# Get the temperature of the CPU for compensation
def get_cpu_temperature():
    process = Popen(['vcgencmd', 'measure_temp'], stdout=PIPE, universal_newlines=True)
    output, _error = process.communicate()
    return float(output[output.index('=') + 1:output.rindex("'")])

def sendToServer(sensor_temp, sensor_pressure, sensor_humidity, sensor_light, 
                            sensor_oxidising, sensor_reducing, sensor_nh3, sensor_pm1,
                            sensor_pm2_5, sensor_pm10):
    
    url = "https://sensata-academy-weather-station.azurewebsites.net/api/sensata-weather-station"

    jsonString = '{' + f'''
"name": "{name}",
"email": "{email}",
"latitude": {latitude},
"longitude": {longitude},
"description": "{location_description}", 
"sensor_temp": {sensor_temp}, 
"sensor_pressure": {sensor_pressure},
"sensor_humidity": {sensor_humidity}, 
"sensor_light": {sensor_light},
"sensor_oxidising": {sensor_oxidising},
"sensor_reducing": {sensor_reducing}, 
"sensor_nh3": {sensor_nh3}, 
"sensor_pm1": {sensor_pm1}, 
"sensor_pm2_5": {sensor_pm2_5}, 
"sensor_pm10": {sensor_pm10} 
''' + '}'

    headers = {'Content-type': 'application/json', 'Accept': 'application/text'}
    
    r = requests.post(url, data=jsonString, headers=headers)

    if r.status_code == 200:
        logging.info("SUCCESSFULLY sent sensor data to server")
    else: 
        logging.info("FAILED to post sensor data to server")

def main():
    # signal esp at start
    mqtt_to_esp32.control_esp("onoff")

    todaysDate = dt.datetime.now()
    baselineDate = dt.datetime.strptime("01/04/2021","%d/%m/%Y")

    sensor_temp = 0
    sensor_pressure = 0
    sensor_humidity = 0
    sensor_light = 0
    sensor_oxidising = 0
    sensor_reducing = 0
    sensor_nh3 = 0
    sensor_pm1 = 0
    sensor_pm2_5 = 0 
    sensor_pm10 = 0


    if todaysDate > baselineDate:        
        # Tuning factor for compensation. Decrease this number to adjust the
        # temperature down, and increase to adjust up
        #factor = 2.25
        factor = 0.85

        cpu_temps = [get_cpu_temperature()] * 5

        delay = 0.5  # Debounce the proximity tap
        last_page = 0

        for v in variables:
            values[v] = [1] * WIDTH

        # The main loop
        try:
            for i in range(0,3):  #first reading contains errors. Talk the 3rd
                proximity = ltr559.get_proximity()
                # Everything on one screen
                cpu_temp = get_cpu_temperature()
                # Smooth out with some averaging to decrease jitter
                cpu_temps = cpu_temps[1:] + [cpu_temp]
                avg_cpu_temp = sum(cpu_temps) / float(len(cpu_temps))
                raw_temp = bme280.get_temperature()
                raw_data = raw_temp - ((avg_cpu_temp - raw_temp) / factor)
                save_data(0, raw_data)
                display_everything()
                sensor_temp = raw_data

                raw_data = bme280.get_pressure()
                save_data(1, raw_data)
                display_everything()
                sensor_pressure = raw_data

                raw_data = bme280.get_humidity()
                save_data(2, raw_data)
                sensor_humidity = raw_data

                if proximity < 10:
                    raw_data = ltr559.get_lux()
                    sensor_light = raw_data
                else:
                    raw_data = 1
                    sensor_light = 0
                save_data(3, raw_data)
                display_everything()


                gas_data = gas.read_all()
                sensor_oxidising = gas_data.oxidising / 1000
                sensor_reducing = gas_data.reducing / 1000
                sensor_nh3 = gas_data.nh3 / 1000

                save_data(4, sensor_oxidising)
                save_data(5, sensor_reducing)
                save_data(6, sensor_nh3)
                display_everything()

                pms_data = None
                try:
                    pms_data = pms5003.read()
                except (SerialTimeoutError, pmsReadTimeoutError):
                    logging.warning("Failed to read PMS5003")
                else:
                    sensor_pm1 = float(pms_data.pm_ug_per_m3(1.0))
                    sensor_pm2_5 = float(pms_data.pm_ug_per_m3(2.5))
                    sensor_pm10 = float(pms_data.pm_ug_per_m3(10))
                    save_data(7, sensor_pm1)
                    save_data(8, sensor_pm2_5)
                    save_data(9, sensor_pm10)
                    display_everything()

            # Added by Ali

            # Calculate factor to see if you can get a more accurate value
            calculate_factor(sensor_temp, raw_temp, avg_cpu_temp, factor)

            nowDate = todaysDate.strftime("%d/%m/%Y %H:%M:%S")
            sensor_data = [sensor_temp, sensor_pressure, sensor_humidity, sensor_light, sensor_oxidising, sensor_reducing, sensor_nh3, sensor_pm1, sensor_pm2_5, sensor_pm10]

            # Get high and low limits for alerts
            file_path = '/home/pi/python_scripts/enviroproject/alerts_config.json'
            with open(file_path, 'r') as infile:
                jdata = json.load(infile)

            location = jdata['sensor']['location']
            action = jdata['sensor']['action']
            interval = jdata['sensor']['interval']
            weather = jdata['sensor']['weather']
            templow = jdata['notification']["templow"]
            humidhigh = jdata['notification']["humidhigh"]
            temphigh = jdata['notification']["temphigh"]

            timestamp = time.time()

            # Get actual weather from api
            city = "Belfast"           
            weather = weatherscraper.getCurrentWeather("description", city)
            api_temperature = weatherscraper.getCurrentWeather("temperature", city)
            api_pressure = weatherscraper.getCurrentWeather("pressure", city)
            api_humidity = weatherscraper.getCurrentWeather("humidity", city)

            # convert string values to float

            api_temperature = float(api_temperature)
            api_pressure = float(api_pressure)
            api_humidity = float(api_humidity)
            
            # write to csv
            csv_result = write_to_csv.write_csv(nowDate, timestamp, location, action, sensor_data, weather)
            print("數據寫入csv文件")

            # get esp data via mqtt
            esp_dat_dict = mqtt_to_esp32.get_esp_data()
            esp_temp = esp_dat_dict["esp32/temperature"]
            esp_humidity = esp_dat_dict["esp32/humidity"]
            esp_light = esp_dat_dict["esp32/light"]
            print(esp_temp.decode(), esp_humidity.decode(), esp_light.decode())

            # write data to sql database
            sql_object = sql_writer.sql_writer()
            # Create database if one doesn't exist
            sql_object.create_database()
            sql_object.insert_row(location, action, sensor_temp, sensor_pressure, sensor_humidity, sensor_light, sensor_oxidising, sensor_reducing, sensor_nh3, esp_temp.decode(), esp_humidity.decode(), esp_light.decode(), api_temperature, api_pressure, api_humidity, weather)
            print("數據寫入sql database")

            # Send notifications if values are above the high or low limits
            if templow["on"]:
                weather_warning_sender.lowtemp(sensor_temp, templow)
            if humidhigh["on"] == "True":
                weather_warning_sender.humidhigh(sensor_humidity, humidhigh)
            if temphigh["on"] == "True":
                weather_warning_sender.temphigh(sensor_temp, temphigh)
            

            sendToServer(sensor_temp, sensor_pressure, sensor_humidity, sensor_light, 
                           sensor_oxidising, sensor_reducing, sensor_nh3, sensor_pm1,
                           sensor_pm2_5, sensor_pm10)
            
            ## Make esp flash at end
            mqtt_to_esp32.control_esp("onoff")


            ## Signal to Arduino
            """
            try:
                import arduino
                arduino.run_arduino()

            
            
            except FileNotFoundError as e:
                print(f"Arduino not attached: {e}")
            except Exception as e:
                print(f"Other error: {e}")


            """
            



        # Exit cleanly
        except KeyboardInterrupt:
            sys.exit(0)


def calculate_factor(sensor_temp, raw_temp, avg_cpu_temp, factor):
    print(f"sensor_temp {sensor_temp}\nraw_temp {raw_temp}\navg_cpu_temp {avg_cpu_temp}")
    f = (avg_cpu_temp-raw_temp)/(raw_temp-sensor_temp)
    print(f"這兩個數字應該相同\nfactor:\n {f}\t{factor}")

    # Put actual temp here, read from a thermometer you trust:
    ACTUAL_TEMP = 17.6 

    calculated_factor = (avg_cpu_temp-raw_temp)/(raw_temp-ACTUAL_TEMP)
    print(f"Please adjust factor to:\n{calculated_factor}")

# check if internet connected
def wait_for_internet_connection():
    while True:
        try:
            response = urllib.request.urlopen('http://google.com',timeout=1)
            return
        except:    
            print("no internet connection")
            exit()
            break

if __name__ == "__main__":
    main()

