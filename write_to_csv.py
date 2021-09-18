import csv
import os.path

def prepare_data(time, todaysDate, location, action, sensor_data, weather):
    # Round data to 1dp. Except PM data (final 3 columns) as I don't have the sensor
    sensor_data = [round(datum, 1) for datum in sensor_data[:-3]] # Creates list

    # insert non numerical data to start of list
    sensor_data.insert(0, action)
    sensor_data.insert(0, location)
    sensor_data.insert(0, todaysDate)
    sensor_data.insert(0, time)
    sensor_data.append(weather)
    return sensor_data


def write_csv(time, todaysDate, location, action, sensor_data, weather):
    
    file_name = '/home/pi/Pimoroni/enviroplus/my_sensor_data.csv'
    
    # Check if file exists
    if os.path.isfile(file_name):
        mode = 'a'
    else:
        mode = 'w'

    with open(file_name, mode, newline='') as file:
        writer = csv.writer(file)
        # If file doesn't exist, make one
        if mode == 'w':
            # write header row
            writer.writerow([ "date", "timestamp", "location", "action", "sensor_temp", "sensor_pressure", "sensor_humidity", "sensor_light", "sensor_oxidising", "sensor_reducing", "nh3", "weather"])
        
        sensor_data = prepare_data(time, todaysDate, location, action, sensor_data, weather)
        
        # write data
        writer.writerow(sensor_data)
        #print(f"數據寫入csv文件\n{sensor_data}")
        return sensor_data


        
        


