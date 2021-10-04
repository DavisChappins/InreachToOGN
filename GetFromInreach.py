import urllib.request
from os import path
from datetime import datetime
import math
import threading
import argparse
import traceback
import csv
from ogn.client import AprsClient
from ogn.parser import parse, ParseError
from datetime import datetime, timedelta
from ctypes import *
import socket
import time
import sys
import os
import os.path
import signal
import atexit

from time import sleep  

global APRSbeacon

class aircraft():
    def __init__(self):
        self.user = ''
        self.latitude = ''
        self.longitude = ''
        self.altitude = ''
        self.groundSpeed = ''
        self.heading = ''
        self.timeUTC = ''
        self.transmissionAge = ''


class getInreach():
    def __init__(self, user):
        self.user = user
        self.latitude = ''
        self.longitude = ''
        self.altitude = ''
        self.groundSpeed = ''
        self.heading = ''
        self.timeUTC = ''
        self.transmissionAge = ''
        

        url = "https://share.garmin.com/feed/share/" + user
        response = urllib.request.urlopen(url)
        data = response.read()
        text = data.decode('utf-8')
        #print(text)



        #'<Data name="Latitude">\r\n            <value>'
        #find latitude
        lat_start = text.find('<Data name="Latitude">\r\n            <value>') + len('<Data name="Latitude">\r\n            <value>')
        lat_end = text.find('</value>\r\n          </Data>\r\n          <Data name="Longitude">\r\n            <value>')
        #print(text.find('<Data name="Latitude">\r\n            <value>'))
        #print(text[lat_index:])
        lat = text[lat_start:lat_end]

        lat_f = float(lat)
        #get decimal
        lat_d = math.trunc(lat_f)
        lat_s = str(lat_d)
        #get minutes
        lat_m = round((lat_f*60) % 60,2)
        lat_m_s = "{:.2f}".format(lat_m)
        lat_m_afterDec = lat_m_s[-2:]
        #isolate minutes only
        lat_m_o = str(int(lat_m))
        lat_m_o = lat_m_o.zfill(2)
        #combine them
        lat_c = lat_s + lat_m_o + '.' + lat_m_afterDec
        #print('latitude:',lat_c) #formatted for APRS

        self.latitude = lat_c


        #find longitude
        lon_start = text.find('<Data name="Longitude">\r\n            <value>') + len('<Data name="Longitude">\r\n            <value>')
        lon_end = text.find('</value>\r\n          </Data>\r\n          <Data name="Elevation">\r\n            <value>')
        lon = text[lon_start:lon_end]

        lon_f = float(lon)
        lon_f = lon_f * -1  #only works in North America
        #get decimal
        lon_d = math.trunc(lon_f)
        lon_s = str(lon_d)
        #get minutes
        lon_m = round((lon_f*60) % 60,2)
        lon_m_s = "{:.2f}".format(lon_m)
        lon_m_afterDec = lon_m_s[-2:]
        #isolate minutes only
        lon_m_o = str(int(lon_m))
        lon_m_o = lon_m_o.zfill(2)
        #combine them
        lon_c = lon_s + lon_m_o + '.' + lon_m_afterDec
        #print('longitude:',lon_c) #formatted for APRS

        self.longitude = lon_c


        #find elevation (meters)
        elev_start = text.find('<Data name="Elevation">\r\n            <value>') + len('<Data name="Elevation">\r\n            <value>')
        elev_end = text.find(' m from MSL</value>\r\n          </Data>\r\n          <Data name="Velocity">\r\n            <value>')
        elev_s = text[elev_start:elev_end]
        elev_f = float(elev_s)
        elev = int(elev_f * 3.28084) #change to feet (from m)
        elev = "{:06d}".format(elev)
        #print('altitude:',elev)

        self.altitude = elev




        #find ground speed (comes in as km/h)
        speed_start = text.find('<Data name="Velocity">\r\n            <value>') + len('<Data name="Velocity">\r\n            <value>')
        speed_end = text.find(' km/h</value>\r\n          </Data>\r\n          <Data name="Course">\r\n            <value>')
        speed_s = text[speed_start:speed_end]
        speed_f = float(speed_s)
        speed = int(speed_f * 0.539957) #change to kts (from kmh)
        speed = "{:03d}".format(speed)
        #print('ground speed:',speed)

        self.groundSpeed = speed


        #find course
        course_start = text.find('<Data name="Course">\r\n            <value>') + len('<Data name="Course">\r\n            <value>')
        course_end = text.find(' ° True</value>\r\n          </Data>\r\n          <Data name="Valid GPS Fix">\r\n            <value>')
        course_s = text[course_start:course_end]
        course_f = float(course_s)
        course = int(course_f)
        course = "{:03d}".format(course)
        course = str(course) #format into 3 digits string leading 0s
        #print('course:',course)

        self.heading = course




        #find time UTC of transmission
        timeUTC_start = text.find('<Data name="Time UTC">\r\n            <value>') + len('<Data name="Time UTC">\r\n            <value>')
        timeUTC_end = text.find('</value>\r\n          </Data>\r\n          <Data name="Time">\r\n            <value>')
        timeUTC = text[timeUTC_start:timeUTC_end]
        #print('UTC Time:',timeUTC)
        #compare against time now
        timeUTC = datetime.strptime(timeUTC, '%m/%d/%Y %I:%M:%S %p')
        timeUTC_time = timeUTC.time()
        time_UTC_str = timeUTC_time.strftime("%H%M%S")
        #print('formatted time:',time_UTC_str)
        timeUTCnow = datetime.utcnow()
        age = timeUTCnow - timeUTC
        age_s = age.total_seconds()
        print('----',user,'----','Last Transmission:',age,'ago')
        #print('Position age (s):',age_s)

        self.timeUTC = time_UTC_str
        self.transmissionAge = age_s


        #is gps fix valid
        gps_fix_start = text.find('<Data name="Valid GPS Fix">\r\n            <value>') + len('<Data name="Valid GPS Fix">\r\n            <value>')
        gps_fix_end = text.find('</value>\r\n          </Data>\r\n          <Data name="In Emergency">\r\n            <value>')
        gps_fix = text[gps_fix_start:gps_fix_end]
        #print('GPS fix:',gps_fix)




        #text_str = str(text)
        #print(text_str)


def openClient():
    global APRSbeacon
    while True:
        try:
            packet_b = sock_file.readline().strip()
            packet_str = packet_b.decode(errors="replace") #if ignore_decoding_error else packet_b.decode()
            #print(packet_str)
            APRSbeacon = parse(packet_str)
            #print(APRSbeacon)
        except:
            pass
        '''except ParseError as e:
            print('Error, {}'.format(e.message))
            print('aprs parse error')
            pass
            
        except NotImplementedError as e:
            print('{}: {}'.format(e, raw_message))
            print('aprs not implemented error')
            pass
            
        except KeyboardInterrupt:
            print('\nStop ogn gateway')
            client.disconnect()
            pass'''
    #time.sleep(1)



#main


APRS_SERVER_PUSH = 'glidern2.glidernet.org'
APRS_SERVER_PORT =  14580 #10152
APRS_USER_PUSH = 'INREACH'
BUFFER_SIZE = 1024
APRS_FILTER = 'g/ALL'

traffic_list = []

####------APRS encode----
#def APRS_encode():
    
#Get most recent user list from Github
urllib.request.urlretrieve("https://raw.githubusercontent.com/DavisChappins/InreachToOGN/main/user.csv", "user.csv")
print('Downloading user.csv from https://raw.githubusercontent.com/DavisChappins/InreachToOGN/main/user.csv')

#assign Github user list to user
with open('user_github.csv', 'r') as read_obj:
    csv_reader = csv.reader(read_obj)
    user = list(csv_reader)


#localhost for testing
#sock_localhost = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#sock_localhost.connect(('localhost', 14580))

#####-----connect to to the APRS server-------------------- works
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((APRS_SERVER_PUSH, APRS_SERVER_PORT))

#self.sock_file = self.sock.makefile('rb')
sock_file = sock.makefile('rb')

data = sock.recv(BUFFER_SIZE)
print("APRS Login reply:  ", data) #server response


#####-----login to APRS server ---------------- works
login = 'user INREACH pass 25002 vers InreachPushClient 0.9 filter r/33/-112/10 \n'
login = login.encode(encoding='utf-8', errors='strict')
sock.send(login)

data = sock.recv(BUFFER_SIZE)
print("APRS Login reply:  ", data) #server response

#callsign/pass generator at https://www.george-smart.co.uk/aprs/aprs_callpass/


#old user list
#user = 'JoeSilvasi' # JoeSilvasi , z15 , 6Q5VG
'''user = {0:['JoeSilvasi','AB2436','Joe Silvasi'],
        1:['z15','A3950B','Bryce Sammeter'],
        2:['6Q5VG','A6355B','Bruce Dage'],
        3:['LOV2AV8','A08E6B','Randy Acree'],
        4:['SteveKoerner','A39421','Steve Koerner'],
        5:['JohnJsGliderFlights','A39427','John Johnson']
        }'''


# https://share.garmin.com/z15 #

startTime = time.time()
#Separate thread for listening to OGN data
AprsThread = threading.Thread(target=openClient)
AprsThread.daemon = True
AprsThread.start()


while True:

    #timers#
    timer_now = time.time()
    timer = timer_now - startTime
    fiveMinuteTimer = timer % 300   #300 seconds in 5 min, if >299.9 then action
    threeMinuteTimer = timer % 180   #180 seconds in 3 min, if >179.9 then action
    #print('fiveMinuteTimer',fiveMinuteTimer)
    #print('threeMinuteTimer',threeMinuteTimer)
    timenow = datetime.utcnow().strftime("%H%M%S")
    #print(round(fiveMinuteTimer,2))
    #####-----read data from APRS server
    #openClient() #run separate thread to read APRS data
    '''try:
        packet_b = sock_file.readline().strip()
        packet_str = packet_b.decode(errors="replace") #if ignore_decoding_error else packet_b.decode()
        #print(packet_str)
        APRSbeacon = parse(packet_str)
        #print(APRSbeacon)
    except ParseError as e:
        print('Error, {}'.format(e.message))
        break
    except NotImplementedError as e:
        print('{}: {}'.format(e, raw_message))
        break'''

    #get inreach
    if threeMinuteTimer > 179.9: #179.9, 3 minutes is 180 seconds
        print('Local time:',datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),'Uptime:',int(timer//3600),'hours',int((timer%3600)//60),'minutes',int((timer%3600)%60),'seconds')
        
        for i in range(1,len(user)):
            #print('--------',user[i][0],'--------')
            #traffic_list = aircraft()
            inreach = getInreach(user[i][0])
            #traffic_list[i] = inreach
            #print(traffic_list[i].user)

            #APRS_TEST = "FLRDDBA99>APRS,qAS,YMCF:/174125h2700.02S/15100.88E'000/000/A=001368 !W01! id06DDBA99 +000fpm +0.0rot 44.4dB 0e +1.1kHz gps2x3"

            APRS_TEST_1st = "FLRDDBA99>APRS,qAS,Inreach:/"
            APRS_TEST_2nd = "h3300.02N/11200.88W'000/000/A=001368 !W01! id06DDBA99 +000fpm +0.0rot 11.1dB 0e +0.0kHz gps2x3\n"
            APRS_TEST = APRS_TEST_1st + timenow + APRS_TEST_2nd
            #sock.send(APRS_TEST.encode())

            if inreach.transmissionAge < 2000: #30 mins and recent, only
                print('Tracking',user[i][0],inreach.user,inreach.transmissionAge,'seconds ago')

                #test encode parameters: -- works
                ICAO = 'ICA' + user[i][1]           #   'FLRDDBA99'
                APRS_stuff = '>APRS,qAS,Inreach:/'
                time_UTC = inreach.timeUTC              
                lat = inreach.latitude + 'N'        #   '3300.02N'
                lon = inreach.longitude + 'W'       #   '11200.00W'
                ac_type = "'"
                heading = inreach.heading           #   '000' 
                speed = inreach.groundSpeed         #   '000'
                #print('speed',speed)
                alt = inreach.altitude              #   '001368'
                ICAO_id = 'id3D'+ ICAO[3:]
                climb = ' +' + '000' 
                turn = ' +' + '0.0' 
                sig_stren = ' ' + '10.0' 
                errors = '0e'
                offset = '+' + '0.0' 
                gps_stren = ' gps2x3'
                newline = '\n'
                
                
                if lat != 0 and lon != 0:
                    encode_ICAO = ICAO + '>APRS,qAS,Inreach:/' + time_UTC + 'h' + lat + '/' + lon + ac_type + heading + '/' + speed + '/' + 'A=' + alt + ' !W00! ' + ICAO_id + climb + 'fpm' + turn + 'rot' + sig_stren + 'dB ' + errors + ' ' + offset + 'kHz' + gps_stren + newline
                    print('sending data:',encode_ICAO)
                    #print(APRS_TEST)

                    #print('sending encode_test_ICAO',encode_ICAO)
                    try:
                        sock.send(encode_ICAO.encode())
                        time.sleep(.1)
                        sock.send(encode_ICAO.encode())
                    except:
                        print('error encoding somehow')
                        pass
                        
                     
                    #sock_localhost.send(encode_test_ICAO.encode())
        #APRS_KEEPALIVE = "FLR010101>APRS,qAS,NONE:/" + timenow + "h0000.02S/00000.88E'000/000/A=001368 !W00! id3D010101 +000fpm +0.0rot 11.1dB 0e +1.1kHz gps2x3"
        try:
            sock.send('#keepalive\n'.encode())
            #print('Sending APRS keep alive')
        except:
            print('error encoding somehow')
        time.sleep(2)
    time.sleep(.09)
    #time.sleep(300) #temporary for testing

#while loop end---
