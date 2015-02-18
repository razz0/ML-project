from datetime import datetime, timedelta, date
from apiharvester import APIHarvester, daterange
from predictor import Model
from sklearn.externals import joblib

#################################

weathers = [(0, -5, 25), (30, -1, 25), (0, 10, 5)]

harvester = APIHarvester()
b = Model()
b.generate_model(harvester.read_fmi_datafile(), harvester.read_hsl_datafile())

c = joblib.load('predictor_model.pkl')

for weather in weathers:
    print '%s - Model B: %s' % (weather, b.predict(weather))
    print '%s - Model C: %s' % (weather, c.predict(weather))
