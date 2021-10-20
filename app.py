import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

import datetime as dt
from dateutil.relativedelta import relativedelta

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)
Base.classes.keys()

# # Save reference to the table
Measurements = Base.classes.measurement
Stations = Base.classes.station



app = Flask(__name__)


@app.route("/")
def welcome():
    return (
        f"<h1>Welcome to the Climate API!</h1>"
        f"<h2>Avalable Routes:<h2/>"
        f"/api/v1.0/precipitation<br/>"
        f"api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end><br/>"

        f"<h2>Route Dictionaries:</h2>"
        f"<ol><li><a href=http://127.0.0.1:5000/api/v1.0/precipitation>"
        f"Precipitation </a></li><br/><br/>"
        f"<li><a href=http://127.0.0.1:5000/api/v1.0/stations>"
        f"Weather Stations</a></li><br/><br/>"
        f"<li><a href=http://127.0.0.1:5000/api/v1.0/tobs>"
        f"Temperatures in the last 12 months</a></li><br/><br/>"
        f"<li><a href=http://127.0.0.1:5000/api/v1.0/2017-08-23>"
        f"When given the start only, calculate average, and maximum temperature for all dates greater than and equal to the start date</a></li><br/><br/>"
        f"<li><a href=http://127.0.0.1:5000/api/v1.0/2016-08-23/2017-08-23>"
        f"When given the start and the end date, calculate the minimum, average, and maximum temperature for dates between the start and end date inclusive</a></li></ol><br/>"
       
    
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Query to retrieve the last 12 months of precipitation data and return the results."""
    # Create our session (link) from Python to the DB.
    session = Session(engine)


    date = session.query(Measurements.date).order_by(Measurements.date.desc()).first()
    (latest_date, ) = date
    latest_date = dt.datetime.strptime(latest_date, '%Y-%m-%d')
    latest_date = latest_date.date()
    year_ago = latest_date - relativedelta(years=1)


    date_prcp = session.query(Measurements.date, Measurements.prcp).filter(Measurements.date >= year_ago).all()

    session.close()

    precipication = []
    for date, prcp in date_prcp:
        if prcp != None:
            prcp_dict = {}
            prcp_dict[date] = prcp
            precipication.append(prcp_dict)

    # Return the JSON representation of dictionary.
    return jsonify(precipication)


@app.route("/api/v1.0/stations")
def stations():
    """Return a JSON list of stations from the dataset."""
    session = Session(engine)


    stations = session.query(Stations.station, Stations.name,
                             Stations.latitude, Stations.longitude, Stations.elevation).all()

    session.close()

    all_stations = []
    for station, name, latitude, longitude, elevation in stations:
        station_dict = {}
        station_dict["station"] = station
        station_dict["name"] = name
        station_dict["latitude"] = latitude
        station_dict["longitude"] = longitude
        station_dict["elevation"] = elevation
        all_stations.append(station_dict)

    return jsonify(all_stations)



@app.route("/api/v1.0/tobs")
def tobs():
    """Query for the dates and temperature observations from a year from the last data point for the most active station."""
    session = Session(engine)

    # Calculate the date 1 year ago from the last data point in the database.
    date = session.query(Measurements.date).order_by(Measurements.date.desc()).first()
    (latest_date, ) = date
    latest_date = dt.datetime.strptime(latest_date, '%Y-%m-%d')
    latest_date = latest_date.date()
    year_ago = latest_date - relativedelta(years=1)

    # Find the most active station.
    most_active = session.query(Measurements.station).group_by(Measurements.station).\
        order_by(func.count().desc()).first()


    (station_id, ) = most_active
    print(
        f"The station id of the most active station is {station_id}.")

    
    date_prec = session.query(Measurements.date, Measurements.tobs).filter(
        Measurements.station == station_id).filter(Measurements.date >= year_ago).all()

    session.close()

    temperatures = []
    for date, temp in date_prec:
        if temp != None:
            temp_dict = {}
            temp_dict[date] = temp
            temperatures.append(temp_dict)
   
    return jsonify(temperatures)

@app.route('/api/v1.0/<start>', defaults={'end': None})
@app.route("/api/v1.0/<start>/<end>")
def start_end(start, end):
    """Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start or start-end range."""
    """When given the start only, calculate TMIN, TAVG, and TMAX for all dates greater than and equal to the start date."""
    """When given the start and the end date, calculate the TMIN, TAVG, and TMAX for dates between the start and end date inclusive."""

    session = Session(engine)

    if end != None:
        temps = session.query(func.min(Measurements.tobs), func.avg(Measurements.tobs), func.max(Measurements.tobs)).\
            filter(Measurements.date >= start).filter(Measurements.date <= end).all()
    else:
        temps = session.query(func.min(Measurements.tobs), func.avg(Measurements.tobs), func.max(Measurements.tobs)).\
            filter(Measurements.date >= start).all()

    session.close()

    # Convert the query results to a list.
    list_of_temps = []
    na = False
    for min, average, max in temps:
        if min == None or average == None or max == None:
            no_temperature_data = True
        list_of_temps.append(min)
        list_of_temps.append(average)
        list_of_temps.append(max)
    # Return the JSON representation of dictionary.
    if na == True:
        return f"No temperature data found for the given date range. Try another date range."
    else:
        return jsonify(list_of_temps)







if __name__ == '__main__':
    app.run(debug=True)
