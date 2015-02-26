'''
Modeling the data and doing predictions from the model
'''
import math
import iso8601

import numpy as np

from apiharvester import APIHarvester
import models


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
                obs_time = iso8601.parse_date(timestamp)
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

xx3, yy3 = preprocess_data(fmi_data2, hsl_data2)

xx4, yy4 = preprocess_data(fmi_data2, hsl_data2, use_hour=True)

for model in models.prediction_models:
    if model.parameters == 3:
        model.generate_model(xx3, yy3)
    elif model.parameters == 4:
        model.generate_model(xx4, yy4)

    model.save_model()
    print 'Saved model %s' % model.name
