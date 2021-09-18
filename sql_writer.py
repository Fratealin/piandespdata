# -----------------------------------------------------------
# Uses various MySQL queries to interact with MySQL server on Raspberry Pi
# Create Database if non exists, Delete database, show column names, insert rows
# calculate average, max, minimum, and latest values etc.
# -----------------------------------------------------------

import mysql.connector
from time import sleep

import json

from mysql.connector.constants import ShutdownType

# Define a method to create MySQL users
def createUser(cursor, userName, password,
               querynum=0, 
               updatenum=0, 
               connection_num=0):
    try:
        sqlCreateUser = "CREATE USER '%s'@'localhost' IDENTIFIED BY '%s';"%(userName, password)
        cursor.execute(sqlCreateUser)
    except Exception as Ex:
        print("Error creating MySQL User: %s"%(Ex))

# Delete an User
def DeleteUser(sqlCursor, userName):

    sql_DeleteUser = "DROP USER %s;"%userName

    sqlCursor.execute(sql_DeleteUser)


class sql_writer:
    def __init__(self):
        # Get login details from config file
        with open("/home/pi/python_scripts/enviroproject/config.json", "r") as f:
            self.config = json.load(f)

        self.mydb = mysql.connector.connect(
        host=self.config["DATABASE"]["HOST"],
        user=self.config["DATABASE"]["USER"],
        password=self.config["DATABASE"]["PASSWORD"],
        database=self.config["DATABASE"]["DATABASE"]
        )

        self.mycursor = self.mydb.cursor()
    

    def create_database(self):
        self.mycursor.execute("use enviro_data")

        sql = '''CREATE TABLE IF NOT EXISTS enviro_data (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            timestamp TIMESTAMP(6) NOT NULL default CURRENT_TIMESTAMP(),
            location VARCHAR(15),
            action VARCHAR(10),
            temp DECIMAL(4,2),
            pressure DECIMAL(6,2),
            humidity DECIMAL(6,2),
            light DECIMAL(6,2),
            oxidising DECIMAL(6,2),
            reducing DECIMAL(6,2),
            nh3 DECIMAL(6,2),
            esp_temp DECIMAL(4,2),
            esp_humidity DECIMAL(4,2),
            esp_light DECIMAL(6,2),
            api_temp DECIMAL(4,2),
            api_pressure DECIMAL(6,2),
            api_humidity DECIMAL(6,2),
            weather VARCHAR(20)
            ) ENGINE=MyISAM DEFAULT CHARSET=latin1
            '''
        self.mycursor.execute(sql)
        pass

    def delete_database(self):
        self.mycursor.execute("use enviro_data")
        self.mycursor.execute("DROP database enviro_data")
        pass

    def show_databases(self):
        # Returns list
        self.mycursor.execute("SHOW databases")
        myresult = self.mycursor.fetchall()
        return myresult

    def insert_row(self, location='office', action='none', temp=20, pressure=50, humidity=50, light=50, oxidising=50, reducing=50, nh3=50, esp_temp=1, esp_humidity=1, esp_light=1, api_temp=20, api_pressure=50, api_humidity=50, weather="cloudy"):
        self.mycursor.execute("use enviro_data")        
        sql = """insert into enviro_data (location, action, temp, pressure, humidity, light, oxidising, reducing, nh3, esp_temp, esp_humidity, esp_light, api_temp, api_pressure, api_humidity, weather) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        records = (location, action, temp, pressure, humidity, light, oxidising, reducing, nh3, esp_temp, esp_humidity, esp_light, api_temp, api_pressure, api_humidity, weather)
        self.mycursor.execute(sql, records)       
        self.mydb.commit()


    def show_table(self):
        # returns list
        self.mycursor.execute("SELECT * FROM enviro_data")
        myresult = self.mycursor.fetchall()
        return myresult

    def show_latest_data(self):
        self.mycursor.execute("SELECT * FROM enviro_data ORDER BY id DESC LIMIT 1")
        myresult = self.mycursor.fetchall()
        return myresult[0]
    
    def show_min_max_av(self, calculation):
        if calculation not in ['AVG', 'MIN', 'MAX']:
            calculation = 'AVG'

        # get non numerical results
        self.mycursor.execute("SELECT id, timestamp, location, action FROM enviro_data ORDER BY id DESC LIMIT 1")
        myresult = self.mycursor.fetchall()        
        
        # get numerical results
        query = f"select {calculation}(temp), {calculation}(pressure), {calculation}(humidity), {calculation}(light), {calculation}(oxidising), {calculation}(reducing), {calculation}(nh3), {calculation}(esp_temp), {calculation}(esp_humidity), {calculation}(esp_light), {calculation}(api_temp), {calculation}(api_pressure), {calculation}(api_humidity) from enviro_data where timestamp > now() - interval 24 hour"    
        self.mycursor.execute(query)
        numerical_result = self.mycursor.fetchall()

        # get result from final column which is not numerical
        self.mycursor.execute("SELECT weather FROM enviro_data ORDER BY id DESC LIMIT 1")
        weather = self.mycursor.fetchall()
        
        # concatenate results from all columns
        result_list = myresult[0] + numerical_result[0] + weather[0]

        return result_list


    def show_column_names(self):
        self.mycursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 'enviro_data' AND TABLE_NAME = 'enviro_data'")
        myresult = self.mycursor.fetchall()
        
        # returns a list of tuples, so convert to list of strings
        column_names = []
        for column in myresult:
            column_names.append(column[0])

        return column_names

if __name__ == "__main__":
    sql_object = sql_writer()
    sql_object.create_database()
    

    sql_object.show_databases()
    latest_data = sql_object.show_latest_data()
    for item in latest_data:
            print(item)
            print("column names")
    print(sql_object.show_column_names())
    for line in sql_object.show_column_names():
        print(line)
    min = sql_object.show_min_max_av("MAX")
    for line in min:
        print(line)

