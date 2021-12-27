#Import libraries
from urllib.request import urlopen
import urllib
import urllib.parse
import requests
from bs4 import BeautifulSoup
import sqlite3
import json
import csv
from flask import Flask, flash, redirect, render_template, request, session
import time
import os
import sys
import logging
import datalib

#Set start and end years
start_year = 1975
end_year = 2022

#Fetch data from datalib file
states = datalib.states
months = datalib.months
full_months = datalib.full_months
mapped_months = datalib.mapped_months
select_params = datalib.select_params
units = datalib.units
mapped_params = datalib.mapped_params
param_units = datalib.param_units
weather_data_collected = datalib.weather_data_collected
zipdata_collected = datalib.zipdata_collected
headers = datalib.url_headers

#Set logging config
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

#Create flask app
app = Flask(__name__)

#Used to check if zipcode data has been collected
fhand = open('zipcount.json')
zipcount_data = json.load(fhand)

#Check if API keys set
if not os.environ.get("API_KEY_GEO"):
    raise RuntimeError("API_KEY_GEO not set")
elif not os.environ.get("API_KEY_WEA"):
    raise RuntimeError("API_KEY_WEA not set")

#Flask app route
@app.route('/', methods = ['GET', 'POST'])
def index():
    '''
    Flask route for index.

    GET: Returns index.html.

    POST:
        IF map form submitted: Return results.html
        IF chart form submitted: Return chart.html
    '''
    #Connect to database
    conn = sqlite3.connect('weatherdb.sqlite')
    cur = conn.cursor()

    if request.method == 'POST':
        #If month/map form submitted
        if 'monthform' in request.form:
            #Get user input
            full_month = request.form.get('month')
            month = mapped_months[full_month]
            year = request.form.get('year')

            #Create table name (concatenation)
            tablename = month + str(year) + 'weather'

            #Data to be sent to results.html
            data = {}
            values = []
            cities = []
            states = []
            zips = []

            #Set up for queries
            columns = [
                'max_temp', 'min_temp', 'avg_temp', 'wind_chill',
                'heat_index', 'precipitation', 'snow_depth', 'wind_speed',
                'wind_gust', 'visibility', 'cloud_cover', 'relative_humidity'
            ]
            queries = ['MAX', 'MIN']

            for i in range(0, 12):
                #If low temp, then take the min, else, take max
                if columns[i] == 'min_temp':
                    qv = 'MIN(' + columns[i] + ')'
                else:
                    qv = 'MAX(' + columns[i] + ')'

                #Query database and get zipcode and data value
                query = (
                    'SELECT zipcode, ' + qv +
                    ' FROM ' + tablename +
                    ' WHERE length(' + columns[i] + ') > 0'
                )

                weatherdata = cur.execute(query).fetchall()
                zipcode = weatherdata[0][0]

                value = weatherdata[0][1]
                if zipcode == None:
                    zipcode = ""
                    value = "No data available"
                    city = ""
                    state = ""
                    values.append(value)
                    cities.append(city)
                    states.append(state)
                    zips.append(zipcode)
                    data['lat' + str(i + 1)] = 0
                    data['lng' + str(i + 1)] = 0
                    continue

                #Get associated city and state
                city = cur.execute('''
                    SELECT city
                    FROM cities
                    WHERE city_id =
                    (SELECT city_id
                    FROM zipcodes
                    WHERE zipcode = ?)
                    ''', (zipcode, )).fetchone()[0]

                state = cur.execute('''
                    SELECT state
                    FROM states
                    WHERE state_id =
                    (SELECT state_id
                    FROM zipcodes
                    WHERE zipcode = ?)
                    ''', (zipcode, )).fetchone()[0]

                #Get geocoding API key
                key = os.environ.get("API_KEY_GEO")

                #Make geocode url
                base_url = "https://maps.googleapis.com/maps/api/geocode/json?"
                params = {}
                params['address'] = zipcode
                params['key'] = key
                url = base_url + urllib.parse.urlencode(params)

                #Open json returned by geocode API and read it
                latlng = urlopen(url).read().decode()
                js = json.loads(latlng)

                #Extract latitude and longitude
                lat = js["results"][0]["geometry"]["location"]["lat"]
                print('LAT TYPE', type(lat))
                lng = js["results"][0]["geometry"]["location"]["lng"]

                #Insert into dictionary
                data['lat' + str(i + 1)] = lat
                data['lng' + str(i + 1)] = lng

                #To be used for labels
                values.append(value)
                cities.append(city)
                states.append(state)
                zips.append(zipcode)

            #Create labels through concatenation
            lbldata = {}
            titles = [
                "Max High Temp", "Min Low Temp",
                "Max Avg Temp", "Max Wind Chill",
                "Max Heat Index", "Highest Precipitation",
                "Highest Snow Depth", "Highest Wind Speed",
                "Highest Wind Gusts", "Highest Visibility",
                "Highest Cloud Cover", "Highest Relative Humidity"
            ]

            for i in range(0, 12):
                lbldata['lbl' + str(i + 1)] = (titles[i] + ': ' + \
                    str(values[i]) + ', ' + str(cities[i]) + ', ' + \
                    str(states[i]) + ' ' + str(zips[i]))


            #Return results page with map, pass data into the page
            return render_template(
                'results.html', data = data, months = full_months,
                lbldata = json.dumps(lbldata), month = full_month,
                year = year, years = range(start_year, end_year),
                select_params = select_params
            )

        #If chart form submitted
        elif 'paramform' in request.form:
            #Labels: x-values
            labels = range(start_year, end_year)

            #Values: y-values
            values = []

            #Get user parameter
            user_param = request.form.get('param')

            #Map it to parameter in database
            data_param = mapped_params[user_param]

            #Get units for parameter
            user_units = param_units[user_param]

            for year in range(start_year, end_year):
                #Total for year
                yrsum = 0

                #Number of months (some years don't have data for all months)
                month_count = 0
                for month in months:
                    tablename = month + str(year)  + 'weather'

                    #Get avg of selected parameter for each year
                    avg = cur.execute('\
                        SELECT AVG(' + data_param + ') \
                        FROM ' + tablename).fetchone()[0]

                    #Try/except used in case there is no data for that month
                    #Ex. As of Oct 2021, there is no data for Nov 2021
                    try:
                        yrsum += avg
                        month_count += 1
                    except TypeError:
                        continue
                yravg = yrsum / month_count

                #Add value to list
                values.append(round(yravg, 3))

            #Max value to be displayed on y-axis
            max = 130

            #Return chart
            return render_template(
                'chart.html', select_params = select_params,
                labels = labels, values = values, max = max,
                months = full_months, years = range(start_year, end_year),
                user_param = user_param, user_units = user_units
            )
    else:
        #Return homepage with form
        return render_template(
            'index.html', months = full_months,
            years = range(start_year, end_year),
            select_params = select_params
        )
    cur.close()


def get_zipcodes(state):
    '''
    Help on get_zipcodes():

        Input: One argument - 'state'
            The name of any US state.
            Ex. "California"
                "New York"
        Usage: get_weather(state)

        Output: Writes to database file (weatherdb.sqlite). Fetches all zip
        codes for the given state from zipcodestogo.com and inserts them into
        the database.
    '''
    #Connect to database
    conn = sqlite3.connect('weatherdb.sqlite')
    cur = conn.cursor()

    #Create tables for zipcodes
    cur.executescript('''
        CREATE TABLE IF NOT EXISTS states (
            state_id INTEGER,
            state TEXT NOT NULL UNIQUE,
            PRIMARY KEY(state_id)
        );

        CREATE TABLE IF NOT EXISTS cities (
            city_id INTEGER,
            city TEXT NOT NULL,
            PRIMARY KEY(city_id)
        );

        CREATE TABLE IF NOT EXISTS zipcodes (
            zipcode TEXT,
            state_id INTEGER NOT NULL,
            city_id INTEGER NOT NULL,
            PRIMARY KEY(zipcode),
            FOREIGN KEY(state_id) REFERENCES states(state_id),
            FOREIGN KEY(city_id) REFERENCES cities(city_id)
        )
        ''')

    #Select number of zipcodes per state (ex. Alabama has 838 zipcodes)
    db_zipcount = cur.execute('''
        SELECT COUNT(zipcode)
        FROM zipcodes
        WHERE state_id =
        (SELECT state_id
        FROM states
        WHERE state = ?)
        ''', (state, )).fetchone()[0]

    #If there aren't enough zipcodes in the database, add the missing ones
    if db_zipcount < zipcount_data[state]:
        print(state)

        #Get HTML and parse with bs
        url = "https://www.zipcodestogo.com/" + state.replace(" ", "%20") + '/'
        r = requests.get(url=url, headers=headers)
        html = r.content
        # print(url)
        # html = urlopen(url).read()
        soup = BeautifulSoup(html, 'html.parser')

        #Access table in the leftcol div
        my_table = soup.find("div", {"id": "leftCol"})\
            .find('table', {'class': 'inner_table'})

        count = 0
        index = 0

        #Insert state into database
        cur.execute('INSERT OR IGNORE INTO states (state) VALUES (?)', (state, ))

        #Access table rows
        rows = my_table.findChildren('tr')
        for row in rows:
            #Access table data
            cells = row.findChildren('td')

            #Count number of cells
            for cell in cells:
                count += 1

                #Skip first five cells (they're just headers)
                if count < 6:
                    continue

                #Get value
                value = cell.string

                index = count - 5  #Column number (first has zipcode, second has city)
                if (index % 4) == 1:
                    zipcode = value
                if (index % 4) == 2:
                    city = value
                    cur.execute('''
                        SELECT city_id
                        FROM cities
                        WHERE city = ?
                        ''', (city, ))
                    try:
                        #Check if city is already in database, and if so, pass
                        data = cur.fetchone()[0]
                        pass
                    except:
                        #Otherwise insert into database
                        cur.execute('''
                            INSERT INTO cities (city)
                            VALUES (?)
                            ''', (value, ))

                if (index % 4) == 3:
                    #Insert into zipcodes database
                    state_id = cur.execute('''
                        SELECT state_id
                        FROM states WHERE
                        state = ?
                        ''', (state, )).fetchone()[0]

                    city_id = cur.execute('''
                        SELECT city_id
                        FROM cities
                        WHERE city = ?
                        ''', (city, )).fetchone()[0]

                    cur.execute('''
                        INSERT OR IGNORE INTO zipcodes
                        VALUES (?, ?, ?)
                        ''', (zipcode, state_id, city_id))

                conn.commit()

    else:
        #State already has all zipcode data
        print('Already got', state)

    cur.close()


def get_weather():
    '''
    Help on get_weather():

        Input: None
        Usage: get_weather()

        Output: Writes to database file (weatherdb.sqlite). Inserts historical
        weather data for each month for every zipcode in the US (collected
        using the get_zipcodes() function) from the provided start and end
        years (1970 to 2021).
    '''
    #Connect to database
    conn = sqlite3.connect('weatherdb.sqlite')
    cur = conn.cursor()

    #Retrieve a list of all zipcodes
    ziplist = cur.execute('SELECT zipcode FROM zipcodes').fetchall()

    #Get API key and add it to base url
    weather_key = os.environ.get("API_KEY_WEA")

    #Create weather table
    for year in range(start_year, end_year):
        #Counter to track progress
        wr_count = 0
        iter = 0

        startyr = str(year)
        endyr = str(year + 1)
        base_url = "https://weather.visualcrossing.com/\
        VisualCrossingWebServices/rest/services/weatherdata/historysummary?\
        aggregateHours=24&combinationMethod=aggregate&maxStations=-1&\
        maxDistance=-1&minYear=" + startyr + "&maxYear=" + endyr + "&\
        chronoUnit=months&breakBy=self&dailySummaries=false&contentType=csv&\
        unitGroup=us&locationMode=single&key=" + weather_key + "&dataElements\
        =default&"

        logging.info('===== YEAR: ' + str(year) + ' =====')

        for month in months:
            tablename = month + str(year)  + 'weather'
            cur.execute('''
            CREATE TABLE IF NOT EXISTS ''' + tablename + '''(
                zipcode TEXT,
                max_temp FLOAT,
                min_temp FLOAT,
                avg_temp FLOAT,
                wind_chill FLOAT,
                heat_index FLOAT,
                precipitation FLOAT,
                snow_depth FLOAT,
                wind_speed FLOAT,
                wind_gust FLOAT,
                visibility FLOAT,
                cloud_cover FLOAT,
                relative_humidity FLOAT,
                PRIMARY KEY(zipcode)
            )
            ''')

        for z in ziplist:
            zipcode = z[0]

            if iter >= 0:
                logging.info("===== ZIPCODE: " +  zipcode +  " =====")

                try:
                    #Encode url parameters
                    params = {}
                    params['locations'] = zipcode
                    url = base_url + urllib.parse.urlencode(params)
                except:
                    logging.error(" Failed to encode params at", zipcode)

                try:
                    #Open url and read data
                    logging.debug("\tbefore opening url")
                    r = requests.get(url=url, headers=headers)
                    logging.debug("\topened url")
                    data = r.content.decode('utf-8')
                    logging.debug("\tread data")
                except:
                    logging.error(" Failed to open/read url data at", zipcode)

                #Write data to a csv file so it can be more easily accessed
                try:
                    fh = open('data.csv', 'w')
                    logging.debug("\topened data.csv (w)")
                except:
                    logging.error(" Failed to open data.csv at", zipcode)
                try:
                    fh.write(data)
                    logging.debug("\twrote to data.csv")
                except:
                    logging.error(" Failed to write data to csv file at", zipcode)
                try:
                    fh.close()
                    logging.debug("\tclosed data.csv")
                except:
                    logging.error(" Failed to close data.csv at", zipcode)

                #Open the csv file and create a csv DictReader
                try:
                    fh1 = open('data.csv')
                    logging.debug("\topened data.csv (r)")
                    reader = csv.DictReader(fh1)
                    logging.debug("\tcreated DictReader")
                except:
                    logging.error(" Failed to open data.csv at", zipcode)

                #Insert data into database
                try:
                    for row in reader:
                        month = row['Period']
                        tablename = month + str(year)  + 'weather'
                        maxtemp = row['Maximum Temperature']
                        mintemp = row['Minimum Temperature']
                        avgtemp = row['Temperature']
                        windchill = row['Wind Chill']
                        heatindex = row['Heat Index']
                        precip = row['Precipitation']
                        snow = row['Snow Depth']
                        windspeed = row['Wind Speed']
                        windgust = row['Wind Gust']
                        visibility = row['Visibility']
                        clouds = row['Cloud Cover']
                        humidity = row['Relative Humidity']
                        cur.execute('INSERT OR IGNORE INTO ' + tablename + '''
                            (zipcode, max_temp, min_temp,
                            avg_temp, wind_chill, heat_index,
                            precipitation, snow_depth, wind_speed,
                            wind_gust, visibility, cloud_cover,
                            relative_humidity) VALUES (?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?, ?, ?)''',
                            (zipcode, maxtemp, mintemp, avgtemp,
                            windchill, heatindex, precip, snow,
                            windspeed, windgust, visibility, clouds, humidity))
                    logging.debug("\tinserted")
                except:
                    logging.error(" Failed to insert into database at", zipcode)

                #Close file, url, and commit to database
                try:
                    fh1.close()
                    logging.debug("\tclosed data.csv (r)")

                    conn.commit()
                    logging.debug("\tclosed conn")

                    r.close()
                    logging.debug("\tclosed url")
                except:
                    logging.error(" Failed to close file/database/url at", zipcode)

            #Counter for progress
            wr_count += 1
            if wr_count == 1000:
                iter += 1
                print(f'    Iteration for 1K records: {iter} ...')
                wr_count = 0

        logging.info(str(year) + ' completed')

    cur.close()


#Get zipcode data (if not already collected)
if zipdata_collected == False:
    for state in states:
       get_zipcodes(state)

#Check if data has already been collected
if weather_data_collected == False:
    get_weather()

#Close json file
fhand.close()
