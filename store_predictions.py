"""Predict traffic disruptions based on next 24h weather forecast and save predictions to file."""

import json
import os
from datetime import timedelta, datetime
from dateutil import tz

import iso8601
import pytz
from sklearn.externals import joblib

from apiharvester import APIHarvester
from models import prediction_models

FORECAST_FILE = 'data/forecasts.json'
OBSERVED_DISRUPTIONS_FILE = 'data/disruptions_observed.json'

harvester = APIHarvester()

forecasts = harvester.fmi_forecast()

# Store weather forecasts

stored_forecasts = harvester.read_datafile(FORECAST_FILE) or {}
stored_forecasts.update(forecasts)

with open(FORECAST_FILE, 'w') as f:
    json.dump(stored_forecasts, f)

# Load stored disruptions

for model in prediction_models:
    model.stored_disruptions = harvester.read_datafile(model.JSON_FILE) or {}

# Predict disruptions

for model in prediction_models:
    for timestamp, values in forecasts.iteritems():

        if timestamp in model.stored_disruptions:
            continue

        obs_time = iso8601.parse_date(timestamp)
        value_tuple = (float(values['Precipitation1h']), float(values['Temperature']), float(values['WindSpeedMS']),
                       obs_time.hour)
        # Strip extra values
        disruption_amount = model.predict(value_tuple[:model.parameters])
        model.disruptions.update({timestamp: disruption_amount})

# Store predicted disruptions

for model in prediction_models:
    model.stored_disruptions.update(model.disruptions)

    with open(model.JSON_FILE, 'w') as f:
        json.dump(model.stored_disruptions, f)


# Get and store observed disruptions

stored_observed_disruptions = harvester.read_datafile(OBSERVED_DISRUPTIONS_FILE) or {}

observed_disruptions = {}

now_time = datetime.utcnow().replace(tzinfo=tz.tzutc())

for timestamp, values in stored_forecasts.iteritems():
    obs_time = iso8601.parse_date(timestamp)
    if timedelta(0) < now_time - obs_time: #< timedelta(days=2):  #TODO
        #finnish_time = iso8601.parse_date(timestamp).astimezone(tz.gettz('Europe/Helsinki'))
        observed_disruptions[timestamp] = harvester.hsl_api(obs_time)

stored_observed_disruptions.update(observed_disruptions)

with open(OBSERVED_DISRUPTIONS_FILE, 'w') as f:
    json.dump(stored_observed_disruptions, f)
