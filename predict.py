"""Command line tool for trying out the prediction models"""

import argparse

from .models import prediction_models, load_models

load_models(prediction_models)

parser = argparse.ArgumentParser(description='Predict traffic disruptions')
parser.add_argument('temperature', help='Temperature [C]', type=float)
parser.add_argument('rainfall', help='Precipitation [mm]', type=float)
parser.add_argument('windspeed', help='Wind speed [m/s]', type=float)
parser.add_argument('hour', help='Hour of the day', type=int)
args = parser.parse_args()

for model in prediction_models:
    #print 'Model %s' % (model.model)
    value_tuple = (args.rainfall, args.temperature, args.windspeed, args.hour)
    prediction = model.predict(value_tuple[:model.parameters])
    print('Model %s: %s' % (model.name, prediction))
