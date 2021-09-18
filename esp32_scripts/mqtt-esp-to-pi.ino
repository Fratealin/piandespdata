// https://randomnerdtutorials.com/esp32-mqtt-publish-subscribe-arduino-ide/
// publishes weather data from esp32 to raspberry pi via mqtt
// subscribes to topics to control buzzer and led
// raspberry pi sends messages on these topics to the esp32

// download library for DHT humidity sensor
// https://www.arduinolibraries.info/libraries/dht-sensor-library
// save to Arduino libraries folder

// MQTT libraries
#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include "config.h"

WiFiClient espClient;
PubSubClient client(espClient);
long lastMsg = 0;
char msg[50];
int value = 0;

// import sensor libraries
#include "DHT.h"
#define Type DHT11
int sensePin = 18;
DHT HT(sensePin, DHT11);

float humidity;
float tempC;
float tempF;
int setupT = 500;
int dT = 500;


int ledPin = 4;
int buzzPin = 22;

// Photoresistor variables
int lightPin=35;
float lightVal;
int lux;

void setup() {
  // setup code
  Serial.begin(9600);
  HT.begin();
  delay(setupT);

  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);

  pinMode(ledPin, OUTPUT);
  pinMode(lightPin, INPUT);
  pinMode(buzzPin, OUTPUT);
}

void loop() {
  // main code, to run repeatedly:
  // get sensor values
  humidity = HT.readHumidity();
  tempC = HT.readTemperature();
  tempF = HT.readTemperature(true);

  Serial.print("Humidity: ");
  Serial.print(humidity);
  Serial.print(" Temperature (C): ");
  Serial.print(tempC);
  Serial.print(" Temperature (F): ");
  Serial.println(tempF);
  delay(dT);

  // reconnect to mqtt server if disconnected
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // send message every 10 seconds
  long now = millis();
  if (now - lastMsg > 10000) {
    lastMsg = now;
    
    // Temperature in Celsius
    tempC = HT.readTemperature();   
    
    // Convert the value to a char array
    char tempString[8];
    dtostrf(tempC, 1, 2, tempString);
    Serial.print("Temperature: ");
    Serial.println(tempString);
    client.publish("esp32/temperature", tempString);

    humidity = HT.readHumidity();
    
    // Convert the value to a char array
    char humString[8];
    dtostrf(humidity, 1, 2, humString);
    Serial.print("Humidity: ");
    Serial.println(humString);
    client.publish("esp32/humidity", humString);

    lux = getLightValue();
     char lightString[8];
     dtostrf(lux, 1, 2, lightString);
     Serial.print("Light: ");
    Serial.println(lightString);
    client.publish("esp32/light", lightString);     
   
  }  
}

double getLightValue(){
  lightVal = analogRead(lightPin);
  double Vout=lightVal*3.3/4000;
  //lux=500/(10*((3.3-Vout)/Vout));//use this equation if the LDR is in the upper part of the divider
  lux=(1089/Vout-330)/10;
  return lux;
}

void setup_wifi() {
  delay(10);
  // We start by connecting to a WiFi network
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* message, unsigned int length) {
  // gets called when mqtt message received
  Serial.print("Message arrived on topic: ");
  Serial.print(topic);
  Serial.print(". Message: ");
  String messageTemp;

  // converts mqtt message from char array to string
  for (int i = 0; i < length; i++) {
    Serial.print((char)message[i]);
    messageTemp += (char)message[i];
  }
  Serial.println();

  // If a message is received on the topic esp32/output, you check if the message is either "on" or "off". 
  // Changes the output state according to the message
  if (String(topic) == "esp32/output") {
    if(messageTemp == "on"){
      digitalWrite(ledPin, HIGH);
    }
    else if(messageTemp == "off"){
      digitalWrite(ledPin, LOW);
    }
  }

  if (String(topic) == "esp32/buzz") {
    if(messageTemp == "on"){
      digitalWrite(buzzPin, HIGH);
    }
    else if(messageTemp == "off"){
      digitalWrite(buzzPin, LOW);
    }
    else if(messageTemp == "onoff"){
      // flashed buzzer and led quickly
      digitalWrite(buzzPin, HIGH);
      digitalWrite(ledPin, HIGH);
      delay(200);
      digitalWrite(buzzPin, LOW);
      digitalWrite(ledPin, LOW);
    }
  }
  
}

void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (client.connect("ESP8266Client", mqtt_username, mqtt_password)) {
      Serial.println("connected");
      // Subscribe to a topic
      client.subscribe("esp32/output");
      client.subscribe("esp32/buzz");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}
