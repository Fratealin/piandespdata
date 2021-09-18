import email_me
import push_notifications
LOW_LIGHT = 4000
LOW_TEMP = 30

def send_warning(sensor_light, sensor_temp):
    message = []
    if sensor_light<LOW_LIGHT:
        message.append(f"天不亮了，请把苗子拿到阳光之下:\n{sensor_light:.0f} 勒克斯")
    
    if sensor_temp<LOW_TEMP:
        message.append(f"天氣變冷了，有結霜的危險，請注意把苗子拿到戶內:\n{sensor_temp:.1f} 摄氏")
        
    if len(message) >0:
        email_me.email_me("ali_dore@gmail.com", "來自樹莓派的氣象警告","\n\n".join(message))
        push_notifications.sendPush("\n".join(message))

def lowtemp(sensor_temp, templow):
    message = []
    if sensor_temp<=templow["value"]:
        message.append(f"天氣變冷了，有結霜的危險，請注意把苗子拿到戶內:\n{sensor_temp:.1f} 摄氏")
        email_me.email_me("ali_dore@gmail.com", "來自樹莓派的氣象警告","\n\n".join(message))
        push_notifications.sendPush("\n".join(message))

def humidhigh(sensor_humidity, humidhigh):
    message = []
    if sensor_humidity>=humidhigh["value"]:
        message.append(f"Very humid: {sensor_humidity:.1f} %.\nOpen window or turn on dehumidifier")
        email_me.email_me("ali_dore@gmail.com", "來自樹莓派的氣象警告","\n\n".join(message))
        #push_notifications.sendPush("\n".join(message))

def temphigh(sensor_temp, temphigh):
    message = []
    if sensor_temp>=temphigh["value"]:
        message.append(f"{temphigh['msg']}\n{sensor_temp:.1f} degrees.")
        email_me.email_me("ali_dore@gmail.com", "來自樹莓派的氣象警告","\n\n".join(message))

    
    
    
    