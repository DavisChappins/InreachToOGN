import urllib.request
from os import path
from datetime import datetime, timedelta
from time import sleep
from ctypes import *
import math
import threading
import argparse
import traceback
import csv
import socket
import time
import sys
import os
import signal
import atexit
import psutil
import logging
import requests

global APRSbeacon

def restart_program():
    """Restarts the current program, with file objects and descriptors cleanup"""
    try:
        p = psutil.Process(os.getpid())
        for handler in p.get_open_files() + p.connections():
            os.close(handler.fd)
    except Exception as e:
        logging.error(e)
    python_exe = sys.executable
    os.execl(python_exe, python_exe, *sys.argv)

# Helper function to send the APRS sentence to the API endpoint
def send_to_api(message):
    url = "https://soaringsattracker.com/api/positions/"
    # Use the provided API key
    api_key = "soaring_sattracker_api_key_2025_03_18_v1"
    headers = {
        'X-API-Key': api_key,
        'HTTP_X_API_KEY': api_key
    }
    payload = {"ogn_packet": message}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print("API POST response:", response.status_code)
    except Exception as e:
        print("Error posting to API:", e)

class aircraft():
    def __init__(self):
        self.user = ''
        self.latitude = ''
        self.latitudeNS = ''
        self.longitude = ''
        self.longitudeEW = ''
        self.altitude = ''
        self.groundSpeed = ''
        self.heading = ''
        self.timeUTC = ''
        self.transmissionAge = 10000

class getInreach():
    def __init__(self, user):
        self.user = user
        self.latitude = ''
        self.latitudeNS = ''
        self.longitude = ''
        self.longitudeEW = ''
        self.altitude = ''
        self.groundSpeed = ''
        self.heading = ''
        self.timeUTC = ''
        self.transmissionAge = 10000
        self.ICAO = ''
        
        try:
            url = "https://share.garmin.com/feed/share/" + user
            req = urllib.request.Request(
                url, 
                data=None, 
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
                }
            )
            response = urllib.request.urlopen(req)
            data = response.read()
            text = data.decode('utf-8')
        except Exception as e:
            print('getinreach error', e)
            pass

        try:
            # Parse latitude
            lat_start = text.find('<Data name="Latitude">\r\n            <value>') + len('<Data name="Latitude">\r\n            <value>')
            lat_end = text.find('</value>\r\n          </Data>\r\n          <Data name="Longitude">\r\n            <value>')
            lat = text[lat_start:lat_end]

            lat_f = float(lat)
            lat_d = math.trunc(lat_f)
            if lat_d > 0:
                lat_m = round((lat_f * 60) % 60, 2)
                self.latitudeNS = 'N'
            else:
                lat_m = round((lat_f * -1 * 60) % 60, 2)
                self.latitudeNS = 'S'
                lat_d = abs(lat_d)

            lat_s = str(lat_d)
            lat_m_s = "{:.2f}".format(lat_m)
            lat_m_afterDec = lat_m_s[-2:]
            lat_m_o = str(int(lat_m)).zfill(2)
            lat_c = lat_s + lat_m_o + '.' + lat_m_afterDec
            self.latitude = lat_c

            # Parse longitude
            lon_start = text.find('<Data name="Longitude">\r\n            <value>') + len('<Data name="Longitude">\r\n            <value>')
            lon_end = text.find('</value>\r\n          </Data>\r\n          <Data name="Elevation">\r\n            <value>')
            lon = text[lon_start:lon_end]

            lon_f = float(lon)
            lon_d = math.trunc(lon_f)
            if lon_d > 0:
                lon_m = round((lon_f * 60) % 60, 2)
                self.longitudeEW = 'E'
            else:
                lon_m = round((lon_f * -1 * 60) % 60, 2)
                self.longitudeEW = 'W'
                lon_d = abs(lon_d)

            lon_s = str(lon_d)
            if abs(lon_d) < 100:
                lon_s = lon_s.zfill(3)
            lon_m_s = "{:.2f}".format(lon_m)
            lon_m_afterDec = lon_m_s[-2:]
            lon_m_o = str(int(lon_m)).zfill(2)
            lon_c = lon_s + lon_m_o + '.' + lon_m_afterDec
            self.longitude = lon_c

            # Parse elevation (in meters, then convert to feet)
            elev_start = text.find('<Data name="Elevation">\r\n            <value>') + len('<Data name="Elevation">\r\n            <value>')
            elev_end = text.find(' m from MSL</value>\r\n          </Data>\r\n          <Data name="Velocity">\r\n            <value>')
            elev_s = text[elev_start:elev_end]
            elev_f = float(elev_s)
            elev = int(elev_f * 3.28084)
            elev = "{:06d}".format(elev)
            self.altitude = elev

            # Parse ground speed (from km/h to knots)
            speed_start = text.find('<Data name="Velocity">\r\n            <value>') + len('<Data name="Velocity">\r\n            <value>')
            speed_end = text.find(' km/h</value>\r\n          </Data>\r\n          <Data name="Course">\r\n            <value>')
            speed_s = text[speed_start:speed_end]
            speed_f = float(speed_s)
            speed = int(speed_f * 0.539957)
            speed = "{:03d}".format(speed)
            self.groundSpeed = speed

            # Parse course
            course_start = text.find('<Data name="Course">\r\n            <value>') + len('<Data name="Course">\r\n            <value>')
            course_end = text.find(' ° True</value>\r\n          </Data>\r\n          <Data name="Valid GPS Fix">\r\n            <value>')
            course_s = text[course_start:course_end]
            course_f = float(course_s)
            course = int(course_f)
            course = "{:03d}".format(course)
            self.heading = course

            # Parse time UTC of transmission
            timeUTC_start = text.find('<Data name="Time UTC">\r\n            <value>') + len('<Data name="Time UTC">\r\n            <value>')
            timeUTC_end = text.find('</value>\r\n          </Data>\r\n          <Data name="Time">\r\n            <value>')
            timeUTC = text[timeUTC_start:timeUTC_end]
            timeUTC = datetime.strptime(timeUTC, '%m/%d/%Y %I:%M:%S %p')
            timeUTC_time = timeUTC.time()
            time_UTC_str = timeUTC_time.strftime("%H%M%S")
            timeUTCnow = datetime.utcnow().replace(microsecond=0)
            age = timeUTCnow - timeUTC
            age_s = age.total_seconds()
            print('----', user, '----', 'Last Transmission:', age, 'ago')
            self.timeUTC = time_UTC_str
            self.transmissionAge = age_s

            # Check for valid GPS fix (parsing only)
            gps_fix_start = text.find('<Data name="Valid GPS Fix">\r\n            <value>') + len('<Data name="Valid GPS Fix">\r\n            <value>')
            gps_fix_end = text.find('</value>\r\n          </Data>\r\n          <Data name="In Emergency">\r\n            <value>')
            gps_fix = text[gps_fix_start:gps_fix_end]
        except:
            print('error parsing:', user)
            pass

def openClient():
    global APRSbeacon
    while True:
        try:
            packet_b = sock_file.readline().strip()
            packet_str = packet_b.decode(errors="replace")
            APRSbeacon = parse(packet_str)
        except:
            pass

def WatchDog():
    while True:
        time.sleep(120)
        try:
            r = requests.get('http://glidern3.glidernet.org:14501/status.json')
            print('Scanning APRS server for Inreach connectivity')
            t = r.text
            s = 'INREACHa'
            found = t.find(s)
            if found > 0:
                print('Still connected,', found)
            else:
                print('Not found, restarting program')
                time.sleep(1)
                restart_program()
        except:
            print('error scanning APRS server')
            pass

APRS_SERVER_PUSH = 'glidern3.glidernet.org'
APRS_SERVER_PORT = 14580
APRS_USER_PUSH = 'INREACHa'
BUFFER_SIZE = 1024
APRS_FILTER = 'g/ALL'

startTime = time.time()
traffic_list = []
shortuser = []   # for rapid updates
longuser = []    # for infrequent updates
erroruser = []   # for users with parsing errors

# Download the most recent user list from GitHub
urllib.request.urlretrieve("https://soaringsattracker.com/inreachcsv", "Inreachuser.csv")
print('Downloading Inreachuser https://soaringsattracker.com/inreachcsv')
time.sleep(2)

# Load the user list from CSV
with open('Inreachuser.csv', 'r') as read_obj:
    csv_reader = csv.reader(read_obj)
    user = list(csv_reader)
    print(user)

# Connect to the APRS server
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((APRS_SERVER_PUSH, APRS_SERVER_PORT))
sock_file = sock.makefile('rb')
data = sock.recv(BUFFER_SIZE)
print("APRS Login reply:  ", data)

# Login to the APRS server
login = 'user INREACHa pass 25067 vers InreachPushClient 1.0 filter r/33/-112/10 \n'
login = login.encode(encoding='utf-8', errors='strict')
sock.send(login)
data = sock.recv(BUFFER_SIZE)
print("APRS Login reply:  ", data)

if data == b'':
    print('No response from APRS server, restarting program in 5s')
    time.sleep(5)
    restart_program()

# Start background threads for receiving APRS data and connection watchdog
AprsThread = threading.Thread(target=openClient)
AprsThread.daemon = True
AprsThread.start()

WatchdogThread = threading.Thread(target=WatchDog)
WatchdogThread.daemon = True
WatchdogThread.start()

L = 0  # Loop counter for long-term running

# Initial user sorting
print('Running initial sort')
for i in range(1, len(user)):
    time.sleep(2)
    sort_inreach = getInreach(user[i][0])
    sort_inreach.ICAO = user[i][1]
    if sort_inreach.transmissionAge < 172800 and sort_inreach.transmissionAge != 10000:
        print(sort_inreach.user, ' last pos is within 2 days, adding to short list')
        shortuser.append(sort_inreach)
        print('shortlist length', len(shortuser))
    elif sort_inreach.transmissionAge == 10000:
        print(sort_inreach.user, ' adding to error list')
        erroruser.append(sort_inreach.user)
        print('erroruser length', len(erroruser), erroruser)
    else:
        print(sort_inreach.user, ' last pos is longer than 2 days, adding to long list')
        longuser.append(sort_inreach)
        print('longlist length', len(longuser))
        
    if i % 10 == 0:
        try:
            sock.send('#keepalive\n'.encode())
            print('Sending APRS keep alive at user', i)
        except:
            print('error sending keepalive')
            pass 

timer_now = time.time()
timer = timer_now - startTime
print('Initial sort complete:', datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
      'Uptime:', int((timer % 3600) // 60), 'minutes', int((timer % 3600) % 60), 'seconds')

print('Shortuser length:', len(shortuser))
print('Longuser length', len(longuser))
print('Error users', len(erroruser), 'Delete the following users:', erroruser)

num = 0  # Even/odd counter
i = 0    # Iterator for shortuser list
z = 0    # Iterator for longuser list

# Initialize a variable to track the start of a shortuser cycle
short_cycle_start = time.time()

while True:
    timer_now = time.time()
    timer = timer_now - startTime
    timenow = datetime.utcnow().strftime("%H%M%S")
    
    shortlen = len(shortuser)
    longlen = len(longuser)
    
    # If we've reached the end of the shortuser list and we're in the shortuser branch, wait if needed
    if num % 2 == 0 and i == shortlen:
        elapsed = time.time() - short_cycle_start
        if elapsed < 60:
            wait_time = 60 - elapsed
            while wait_time > 0:
                print("Waiting for", int(wait_time), "seconds...")
                sleep_interval = min(5, wait_time)
                time.sleep(sleep_interval)
                wait_time -= sleep_interval
        print("Resetting shortuser list.")
        i = 0
        short_cycle_start = time.time()
    
    if z == longlen:
        print('###################################### longuser user list reset at', z)
        z = 0
    
    if num % 2 == 0:
        # Process shortuser list
        inreach = getInreach(shortuser[i].user)
        time.sleep(3)
        if inreach.transmissionAge < 600:
            print('Tracking', shortuser[i].user, inreach.transmissionAge, 'seconds ago')
            ICAO = 'ICA' + shortuser[i].ICAO
            time_UTC = inreach.timeUTC              
            lat = inreach.latitude + inreach.latitudeNS
            lon = inreach.longitude + inreach.longitudeEW
            ac_type = "'"
            heading = inreach.heading
            speed = inreach.groundSpeed
            alt = inreach.altitude
            ICAO_id = 'id3D' + ICAO[3:]
            climb = ' +' + '000'
            turn = ' +' + '0.0'
            sig_stren = ' ' + '0.0'
            errors = '0e'
            offset = '+' + '0.0'
            gps_stren = ' gps2x3'
            newline = '\n'
            
            if lat != 0 and lon != 0:
                encode_ICAO = (ICAO + '>OGINRE,qAS,Inreach:/' + time_UTC + 'h' +
                               lat + '/' + lon + ac_type + heading + '/' +
                               speed + '/' + 'A=' + alt + ' !W00! ' +
                               ICAO_id + climb + 'fpm' + turn + 'rot' +
                               sig_stren + 'dB ' + errors + ' ' + offset +
                               'kHz' + gps_stren + newline)
                print('sending data:', encode_ICAO)
                try:
                    # Send to APRS server
                    sock.send(encode_ICAO.encode())
                    time.sleep(0.1)
                    sock.send(encode_ICAO.encode())
                except:
                    print('error sending position')
                    pass
                # Also send to the API endpoint
                send_to_api(encode_ICAO)
        i += 1
    else:
        # Process longuser list
        if longlen > 0:
            inreach = getInreach(longuser[z].user)
            time.sleep(3)
            if inreach.transmissionAge < 600:
                print('Tracking', longuser[z].user, inreach.transmissionAge, 'seconds ago')
                ICAO = 'ICA' + longuser[z].ICAO
                time_UTC = inreach.timeUTC              
                lat = inreach.latitude + inreach.latitudeNS
                lon = inreach.longitude + inreach.longitudeEW
                ac_type = "'"
                heading = inreach.heading
                speed = inreach.groundSpeed
                alt = inreach.altitude
                ICAO_id = 'id3D' + ICAO[3:]
                climb = ' +' + '000'
                turn = ' +' + '0.0'
                sig_stren = ' ' + '0.0'
                errors = '0e'
                offset = '+' + '0.0'
                gps_stren = ' gps2x3'
                newline = '\n'
                
                if lat != 0 and lon != 0:
                    encode_ICAO = (ICAO + '>OGINRE,qAS,Inreach:/' + time_UTC + 'h' +
                                   lat + '/' + lon + ac_type + heading + '/' +
                                   speed + '/' + 'A=' + alt + ' !W00! ' +
                                   ICAO_id + climb + 'fpm' + turn + 'rot' +
                                   sig_stren + 'dB ' + errors + ' ' + offset +
                                   'kHz' + gps_stren + newline)
                    print('sending data:', encode_ICAO)
                    try:
                        sock.send(encode_ICAO.encode())
                        time.sleep(0.1)
                        sock.send(encode_ICAO.encode())
                    except:
                        print('error sending position')
                        pass
                    # Also send to the API endpoint
                    send_to_api(encode_ICAO)
            z += 1
        else:
            print("No long-term users available, skipping longuser branch.")
    
    num += 1
    if L % 10 == 0:
        print('Local time:', datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
              'Uptime:', int(timer // 3600), 'hours', int((timer % 3600) // 60),
              'minutes', int((timer % 3600) % 60), 'seconds')
        try:
            sock.send('#keepalive\n'.encode())
            print('Sending APRS keep alive at loop', L)
        except:
            print('error sending keepalive at loop', L)
            pass 
    L += 1
    time.sleep(0.09)
