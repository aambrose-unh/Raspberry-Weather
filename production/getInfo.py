#!/usr/bin/python
import sys
import board
import adafruit_dht

import subprocess 
import re 
import os 
import time 
import MySQLdb as mdb 
import datetime

databaseUsername = os.getenv("DB_USER")
databasePassword = os.getenv("DB_PASSWD")
databaseName = "WordpressDB" #do not change unless you named the Wordpress database with some other name

pinNum = board.D4 #if not using pin number 4, change here
sensor = adafruit_dht.DHT22(pinNum)

def saveToDatabase(temperature,humidity):

	con=mdb.connect("localhost", databaseUsername, databasePassword, databaseName)
        currentDate=datetime.datetime.now().date()

        now=datetime.datetime.now()
        midnight=datetime.datetime.combine(now.date(),datetime.time())
        minutes=((now-midnight).seconds)/60 #minutes after midnight, use datead$

	
        with con:
                cur=con.cursor()
		
                cur.execute("INSERT INTO temperatures (temperature,humidity, dateMeasured, hourMeasured) VALUES (%s,%s,%s,%s)",(temperature,humidity,currentDate, minutes))

		print "Saved temperature"
		return "true"


def readInfo():

	num_retries = 15
	while num_retries > 0:
	    print(f"Number of retries remaining: {num_retries}")
	    try:
	        # Print the values to the serial port
	        temperature_c = sensory.temperature
	        temperature_f = temperature_c * (9 / 5) + 32
	        humidity = sensory.humidity
	        print(
	            "Temp: {:.1f} F / {:.1f} C    Humidity: {}% ".format(
	                temperature_f, temperature_c, humidity
	            )
	        )
		continue # do not repeat if successful
	
	    except RuntimeError as error:
	        # Errors happen fairly often, DHT's are hard to read, just keep going
	        print(error.args[0])
	        time.sleep(2.0)
		num_retries -= 1
	    except Exception as error:
	        sensory.exit()
	        raise error

	print "Temperature: %.1f C" % temperature
	print "Humidity:    %s %%" % humidity

	if humidity is not None and temperature is not None:
		return saveToDatabase(temperature,humidity) #success, save the readings
	else:
		print 'Failed to get reading. Try again!'
		sys.exit(1)


#check if table is created or if we need to create one
try:
	queryFile=file("createTable.sql","r")

	con=mdb.connect("localhost", databaseUsername,databasePassword,databaseName)
        currentDate=datetime.datetime.now().date()

        with con:
		line=queryFile.readline()
		query=""
		while(line!=""):
			query+=line
			line=queryFile.readline()
		
		cur=con.cursor()
		cur.execute(query)	

        	#now rename the file, because we do not need to recreate the table everytime this script is run
		queryFile.close()
        	os.rename("createTable.sql","createTable.sql.bkp")
	

except IOError:
	pass #table has already been created
	

status=readInfo() #get the readings
