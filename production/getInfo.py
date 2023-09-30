#!/usr/bin/python
import sys
import board
import adafruit_dht

import os
import time
import pymysql as mdb
import pymysql.cursors
import datetime

import logging

logger = logging.Logger("get_info")

databaseUsername = os.getenv("DB_USER")
databasePassword = os.getenv("DB_PASSWD")
databaseName = "WordpressDB"  # do not change unless you named the Wordpress database with some other name

pinNum = board.D4  # if not using pin number 4, change here
sensor = adafruit_dht.DHT22(pinNum)


def saveToDatabase(temperature, humidity):
    logger.info("Saving to database")
    con = mdb.connect(
        host="localhost",
        user=databaseUsername,
        password=databasePassword,
        database=databaseName,
    )
    currentDate = datetime.datetime.now().date()

    now = datetime.datetime.now()
    midnight = datetime.datetime.combine(now.date(), datetime.time())
    minutes = ((now - midnight).seconds) / 60  # minutes after midnight, use datead$

    logger.info("Create db connection")
    with con:
        cur = con.cursor()
        logger.info("Inserting record")
        cur.execute(
            "INSERT INTO temperatures (temperature,humidity, dateMeasured, hourMeasured) VALUES (%s,%s,%s,%s)",
            (temperature, humidity, currentDate, minutes),
        )

        print("Saved temperature")
        return "true"


def readInfo():
    num_retries = 15
    while num_retries > 0:
        print(f"Number of retries remaining: {num_retries}")
        try:
            # Print the values to the serial port
            temperature_c = sensor.temperature
            temperature_f = temperature_c * (9 / 5) + 32
            humidity = sensor.humidity
            print(
                "Temp: {:.1f} F / {:.1f} C    Humidity: {}% ".format(
                    temperature_f, temperature_c, humidity
                )
            )
            break  # do not repeat if successful

        except RuntimeError as error:
            # Errors happen fairly often, DHT's are hard to read, just keep going
            print(error.args[0])
            time.sleep(2.0)
            num_retries -= 1

        except Exception as error:
            sensor.exit()
            raise error

    print("Temperature: %.1f C" % temperature_f)
    print("Humidity:    %s %%" % humidity)

    if humidity is not None and temperature_f is not None:
        return saveToDatabase(temperature_f, humidity)  # success, save the readings
    else:
        print("Failed to get reading. Try again!")
        sys.exit(1)


if __name__ == "__main__":
    # check if table is created or if we need to create one
    try:
        logger.info("Open sql file")
        queryFile = open("createTable.sql", "r")

        logger.info("Create db connection to create table")
        con = mdb.connect(
            host="localhost",
            user=databaseUsername,
            password=databasePassword,
            database=databaseName,
        )
        currentDate = datetime.datetime.now().date()

        with con:
            line = queryFile.readline()
            query = ""
            while line != "":
                query += line
                line = queryFile.readline()

            cur = con.cursor()
            cur.execute(query)

            # now rename the file, because we do not need to recreate the table everytime this script is run
        queryFile.close()
        os.rename("createTable.sql", "createTable.sql.bkp")

    except IOError:
        logger.info("Temperature table already present")
        pass  # table has already been created
    except Exception as e:
        logger.info(f"Error {e}. Occured during table creation")

    status = readInfo()  # get the readings
