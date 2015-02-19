from datetime import datetime, timedelta, date
from apiharvester import APIHarvester, daterange
from predictor import Model

#################################

harvester = APIHarvester()

good_years = [2010, 2011, 2012, 2014]  # Skip 2013 as it has a public transportation strike

fmi_data = dict([(x, y) for (x, y) in harvester.read_fmi_datafile().iteritems() if int(x[:4]) in good_years])
hsl_data = dict([(x, y) for (x, y) in harvester.read_hsl_datafile().iteritems() if int(x[:4]) in good_years])

predict_model = Model()
predict_model.generate_model(fmi_data, hsl_data, C=100.0)
predict_model.save_model()

print('Model saved')