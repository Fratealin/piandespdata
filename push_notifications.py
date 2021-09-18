
'''
Send push notifications and Sms using Pushbullet
'''

from pushbullet import Pushbullet
import json

# get email credentials from config file
with open("/home/pi/python_scripts/enviroproject/config.json", "r") as f:
    config = json.load(f)
    accessToken = config["pushbullet"]["ACCESSTOKEN"]
    deviceName = config["pushbullet"]["DEVICENAME"]
    num = config["pushbullet"]["NUMBER"]

# Connect to Pushbullet
pb = Pushbullet(accessToken)

def sendPush(message): 
    # This will tell you the device name
    print(pb.devices)
    dev = pb.get_device(deviceName) # Get device
    push = dev.push_note('警告',message) # Send message
        

def sendSms(message, num=num):           
    device = pb.devices[0] # Get device
    push = pb.push_sms(device, num, message) # Send message
        
