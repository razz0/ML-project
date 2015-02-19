'''
Modeling the data and doing predictions from the model
'''
import math
import numpy as np
from sklearn import linear_model
from sklearn.externals import joblib


class Model(object):

    def __init__(self):
        self.logreg = None

    def generate_model(self, fmi, hsl, C=1.0):
        '''
        Generate model to predict y from x

        :param dates: date range to use for learning
        :param fmi: FMI observation data as dict
        :param hsl: HSL disruption data as dict
        :return: None
        '''
        xx = []
        yy = []

        for key in fmi:
            if key in hsl:
                #print key
                try:
                    fmi_values = map(float, (fmi[key].get('r_1h'), fmi[key].get('t2m'), fmi[key].get('ws_10min')))
                    if [x for x in fmi_values if math.isnan(x)]:
                        raise ValueError
#                    if fmi_values[0] == -1.0:
#                        fmi_values[0] = 0  # Assuming "-1.0" rainfall means zero rain
                except ValueError:
                    continue
                if not str(hsl[key]).isdigit():
                    print "HSL %s" % hsl[key]
                    continue
                xx.append(fmi_values)  # TODO: add hour
                yy.append(int(float(hsl.get(key))))

#        print max(hsl.values())
        print 'Weather values: %s' % len(xx)
        print 'Disruption values: %s' % len(yy)
        print 'Disruption set: %s' % set(yy)

        x = np.array(xx)
        y = np.array(yy)

        self.logreg = linear_model.LogisticRegression(C=C)

        # we create an instance of Neighbours Classifier and fit the data.
        self.logreg.fit(x, y)

    def predict(self, x):
        return self.logreg.predict(x)

    def save_model(self):
        joblib.dump(self.logreg, 'model/predictor_model.pkl')

