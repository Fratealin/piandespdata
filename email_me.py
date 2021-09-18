#! /usr/local/bin/python3

"""
send email with non ascii charachters
    using MIMEText
"""
import json, smtplib, sys
from email.mime.text import MIMEText

# get email credentials from config file
with open("/home/pi/python_scripts/enviroproject/config.json", "r") as f:
    config = json.load(f)
    password = config["email"]["PASSWORD"]
    address = config["email"]["ADDRESS"]
    yahoo_address = config["email"]["YAHOO_ADDRESS"]

def email_me(to, subject, message):
    text_type = 'plain' # or 'html'
    # Create message
    msg = MIMEText(message, text_type, 'utf-8')
    msg['Subject'] = subject
    msg['From'] = yahoo_address
    msg['To'] = to
    # Connect to server
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(address, password)
    # Send message
    server.send_message(msg)
    # or server.sendmail(msg['From'], msg['To'], msg.as_string())
    server.quit()
    print("大成功")
