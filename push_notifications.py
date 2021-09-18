
'''
Push notification to phone
https://iotdesignpro.com/projects/home-security-system-using-raspberry-pi-and-pir-sensor-with-push-notification-alert
'''

from pushbullet import Pushbullet
accessToken = "o.WnYMXcniHRVzGJSKmT4AUZE8eQJED0Js"
deviceName = 'Samsung SM-A415F'
pb = Pushbullet(accessToken)


def sendPush(message):

    
    # This will tell you the device name
    print(pb.devices)

    if 1==1:
        dev = pb.get_device(deviceName)
        push = dev.push_note('警告',message)
        

def sendSms(message, num="+447878346435"):    
    # This will tell you the device name
    #print(pb.devices)
        
    device = pb.devices[0]
    push = pb.push_sms(device, num, message)
        
