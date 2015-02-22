"""Predict traffic disruptions based on next 24h weather forecast and save predictions to file."""

import json
import os
from datetime import timedelta, datetime
import iso8601
from sklearn.externals import joblib
from apiharvester import APIHarvester

from models import prediction_models

FORECAST_FILE = 'data/forecasts.json'
OBSERVED_DISRUPTIONS_FILE = 'data/disruptions_observed.json'

apikey = os.environ.get('fmi_apikey')
harvester = APIHarvester(apikey=apikey)

forecasts = harvester.fmi_forecast()

for model in prediction_models:
    for timestamp, values in forecasts.iteritems():
        value_tuple = (float(values['Precipitation1h']), float(values['Temperature']), float(values['WindSpeedMS']))
        disruption_amount = model.predict(value_tuple)
        model.disruptions.update({timestamp: disruption_amount})

# Store weather forecasts

stored_forecasts = harvester.read_datafile(FORECAST_FILE) or {}
stored_forecasts.update(forecasts)

with open(FORECAST_FILE, 'w') as f:
    json.dump(stored_forecasts, f)

# Store predicted disruptions

for model in prediction_models:
    stored_disruptions = harvester.read_datafile(model.JSON_FILE) or {}
    stored_disruptions.update(model.disruptions)

    with open(model.JSON_FILE, 'w') as f:
        json.dump(stored_disruptions, f)


# Get and store observed disruptions

stored_observed_disruptions = harvester.read_datafile(OBSERVED_DISRUPTIONS_FILE) or {}

observed_disruptions = {}

for timestamp, values in stored_forecasts.iteritems():
    obs_time = iso8601.parse_date(timestamp).replace(tzinfo=None)
    now_time = datetime.utcnow()
    if timedelta(0) < now_time - obs_time < timedelta(days=2):
        observed_disruptions[timestamp] = harvester.hsl_api(iso8601.parse_date(timestamp))

stored_observed_disruptions.update(observed_disruptions)

with open(OBSERVED_DISRUPTIONS_FILE, 'w') as f:
    json.dump(stored_observed_disruptions, f)
