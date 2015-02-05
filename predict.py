from datetime import datetime, timedelta, date
from apiharvester import APIHarvester, daterange
from predictor import Model

#################################

harvester = APIHarvester()

b = Model()
b.generate_model(harvester.read_fmi_datafile(), harvester.read_hsl_datafile())

print b.predict([50, -10, 30])