'''
Modeling the data and doing predictions from the model
'''
import math
import iso8601

import numpy as np
from sklearn import linear_model
from sklearn.externals import joblib

from apiharvester import APIHarvester


class ModelLogisticRegression(object):

    def __init__(self):
        self.logreg = None

    def generate_model(self, x, y, C=1.0):
        '''
        Generate model to predict y from x

        :return: None
        '''
        self.logreg = linear_model.LogisticRegression(C=C)
        self.logreg.fit(x, y)

    def predict(self, x):
        return self.logreg.predict(x)

    def save_model(self):
        joblib.dump(self.logreg, 'model/predictor_model.pkl')


class ModelLinear(ModelLogisticRegression):

    def generate_model(self, x, y):
        '''
        Generate model to predict y from x

        :return: None
        '''
        self.model = linear_model.LinearRegression()
        self.model.fit(x, y)

    def save_model(self):
        joblib.dump(self.model, 'model/linear.pkl')


def preprocess_data(fmi_data, hsl_data, use_hour=False):
    xx = []
    yy = []

    for timestamp in fmi_data:
        if timestamp in hsl_data:
            #print key
            fmi_values = map(float, (fmi_data[timestamp].get('r_1h'), fmi_data[timestamp].get('t2m'), fmi_data[timestamp].get('ws_10min')))
            if [x for x in fmi_values if math.isnan(x)]:
                continue
    #                    if fmi_values[0] == -1.0:
    #                        fmi_values[0] = 0  # Assuming "-1.0" rainfall means zero rain
            if not str(hsl_data[timestamp]).isdigit():
                print "HSL %s" % hsl_data[timestamp]
                continue

            if use_hour:
                obs_time = iso8601.parse_date(timestamp).replace(tzinfo=None)
                fmi_values += [obs_time.hour]

            xx.append(fmi_values)
            yy.append(int(float(hsl_data.get(timestamp))))

#    print max(hsl.values())
#    print 'Weather values: %s' % len(xx)
#    print 'Disruption values: %s' % len(yy)
#    print 'Disruption set: %s' % set(yy)

    x = np.array(xx)
    y = np.array(yy)

    return x, y


#################################


harvester = APIHarvester()

fmi_data = harvester.read_fmi_datafile()
hsl_data = harvester.read_hsl_datafile()

good_years = [2010, 2011, 2012, 2014]  # Skip 2013 as it has a public transportation strike

fmi_data2 = dict([(x, y) for (x, y) in fmi_data.iteritems() if int(x[:4]) in good_years])
hsl_data2 = dict([(x, y) for (x, y) in hsl_data.iteritems() if int(x[:4]) in good_years])

xx, yy = preprocess_data(fmi_data2, hsl_data2)

predict_model = ModelLogisticRegression()
predict_model.generate_model(xx, yy, C=1)
predict_model.save_model()

print('Model #1 saved')

xx, yy = preprocess_data(fmi_data2, hsl_data2, use_hour=True)

predict_model = ModelLinear()
predict_model.generate_model(xx, yy)
predict_model.save_model()

print('Model #2 saved')
