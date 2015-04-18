'''
Modeling the data and doing predictions from the model
'''
import math
import iso8601
import argparse

import numpy as np

from apiharvester import APIHarvester
import models

parser = argparse.ArgumentParser(description='Generate models')
#parser.add_argument('generate', help='Generate normal models', type=bool)
parser.add_argument('-o', help='Generate optimized models (slow)',
                    dest='optimized', action='store_const', const=True, default=False)
args = parser.parse_args()


def preprocess_data(fmi_data, hsl_data, use_hour=False, extra_date_params=False):
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
            if extra_date_params:
                fmi_values += [obs_time.isoweekday()]
                fmi_values += [obs_time.month]

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

# TODO: Refactor for more easy adding of models

harvester = APIHarvester()

fmi_data = harvester.read_fmi_datafile()
hsl_data = harvester.read_hsl_datafile()

good_years = ['2010', '2011', '2012', '2014']  # Skip 2013 as it has a public transportation strike

fmi_data2 = dict([(x, y) for (x, y) in fmi_data.iteritems() if x[:4] in good_years])
hsl_data2 = dict([(x, y) for (x, y) in hsl_data.iteritems() if x[:4] in good_years])

# Remove 2013 strikes from test data
bad_dates = ['2013-04-03', '2013-05-14', '2013-05-15', '2013-05-16', '2013-05-17', '2013-05-18', '2013-05-19',
             '2013-05-20', '2013-11-08']

fmi_test = dict([(x, y) for (x, y) in fmi_data.iteritems() if x[:4] not in good_years and x[:10] not in bad_dates])
hsl_test = dict([(x, y) for (x, y) in hsl_data.iteritems() if x[:4] not in good_years and x[:10] not in bad_dates])

xx3, yy3 = preprocess_data(fmi_data2, hsl_data2)

xx4, yy4 = preprocess_data(fmi_data2, hsl_data2, use_hour=True)
xx6, yy6 = preprocess_data(fmi_data2, hsl_data2, use_hour=True, extra_date_params=True)

x_test, y_test = preprocess_data(fmi_test, hsl_test, use_hour=True, extra_date_params=True)

for model in models.prediction_models:
    x_train = []
    y_train = []

    if model.parameters == 3:
        x_train = xx3
        y_train = yy3
    elif model.parameters == 4:
        x_train = xx4
        y_train = yy4
    elif model.parameters == 6:
        x_train = xx6
        y_train = yy6
    else:
        raise Exception('Model requires unsupported amount of parameters')

    if args.optimized:
        if model.name == 'Optimized Forest':
            best_score = 0
            best_params = {}
            for n_estimators in range(2, 50):
                for criterion in ['gini']:  # , 'entropy']:
                    for max_features in range(1, 7) + ['auto', 'log2']:
                        for max_depth in range(10, 40) + [None]:
                            model.kw_args = dict(n_estimators=n_estimators,
                                                 criterion=criterion,
                                                 max_features=max_features,
                                                 max_depth=max_depth)
                            model.generate_model(x_train, y_train)
                            score = model.model.score(x_test, y_test)
                            if score > best_score:
                                best_params = model.kw_args
                                best_score = score
                                print "%s -- %s" % (score, best_params)

            model.kw_args = best_params
            print "Best found params: %s" % best_params
            model.generate_model(x_train, y_train)
            model.save_model()
    else:
        model.generate_model(x_train, y_train)
        model.save_model()

    print 'Saved model %s - %s' % (model.name, model.model)

# TODO: Optimize model parameters by testing the model against year 2013
# (without strike days 2013-04-03, 2013-05-14 -- 2013-05-20, 2013-11-08)
