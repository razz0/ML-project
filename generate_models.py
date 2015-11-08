'''
Modeling the data and doing predictions from the model
'''
import math
import iso8601
import argparse

import numpy as np

from .apiharvester import APIHarvester
from . import models

parser = argparse.ArgumentParser(description='Generate models')
#parser.add_argument('generate', help='Generate normal models', type=bool)
parser.add_argument('-o', help='Generate optimized models (slow)',
                    dest='optimized', action='store_const', const=True, default=False)
parser.add_argument('-v', help='Add verbosity',
                    dest='verbose', action='store_const', const=True, default=False)
args = parser.parse_args()


def preprocess_data(fmi_data, hsl_data, use_hour=False, extra_date_params=False):
    '''
    Format data to numpy arrays.

    :param fmi_data:
    :param hsl_data:
    :param use_hour:
    :param extra_date_params:
    :return: features in order: [precipitation (1h), air temperature, wind speed (10 min average),
                                 hour, day of week, month].
    '''
    xx = []
    yy = []

    for timestamp in fmi_data:
        if timestamp in hsl_data:
            fmi_values = list(map(float, (fmi_data[timestamp].get('r_1h'), fmi_data[timestamp].get('t2m'), fmi_data[timestamp].get('ws_10min'))))
            if [x for x in fmi_values if math.isnan(x)]:
                continue
            if fmi_values[0] == -1.0:
                fmi_values[0] = 0  # Assuming "-1.0" rainfall means zero rain
            if not str(hsl_data[timestamp]).isdigit():
                print("HSL %s" % hsl_data[timestamp])
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

# TODO: Refactor for more easy adding of parameters?

harvester = APIHarvester()

fmi_data = harvester.read_fmi_datafile()
hsl_data = harvester.read_hsl_datafile()

good_years = ['2010', '2011', '2012', '2014']  # Skip 2013 as it has a public transportation strike

fmi_data2 = dict([(x, y) for (x, y) in fmi_data.items() if x[:4] in good_years])
hsl_data2 = dict([(x, y) for (x, y) in hsl_data.items() if x[:4] in good_years])

# Remove 2013 strikes from test data
bad_dates = ['2013-04-03', '2013-05-14', '2013-05-15', '2013-05-16', '2013-05-17', '2013-05-18', '2013-05-19',
             '2013-05-20', '2013-11-08']

fmi_test = dict([(x, y) for (x, y) in fmi_data.items() if x[:4] not in good_years and x[:10] not in bad_dates])
hsl_test = dict([(x, y) for (x, y) in hsl_data.items() if x[:4] not in good_years and x[:10] not in bad_dates])

xx3, yy3 = preprocess_data(fmi_data2, hsl_data2)

xx4, yy4 = preprocess_data(fmi_data2, hsl_data2, use_hour=True)
xx6, yy6 = preprocess_data(fmi_data2, hsl_data2, use_hour=True, extra_date_params=True)

x_test, y_test = preprocess_data(fmi_test, hsl_test, use_hour=True, extra_date_params=True)

def _save_model(generated_model):
    generated_model.save_model()
    print('Saved model %s - %s' % (generated_model.name, generated_model.model))

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

    if model.name == 'Optimized Forest':
        if args.optimized:
            best_score = 0
            best_params = {}
            for n_estimators in range(2, 50):
                if args.verbose:
                    print("Calculating models for %s trees" % n_estimators)
                for criterion in ['gini', 'entropy']:
                    for max_features in range(1, 7):  # + ['auto', 'log2']:
                        for max_depth in list(range(3, 15)) + [None]:
                            for class_weight in [None]:  # ['auto', None]:
                                model.model_kwargs = dict(n_estimators=n_estimators,
                                                          criterion=criterion,
                                                          max_features=max_features,
                                                          max_depth=max_depth,
                                                          class_weight=class_weight)
                                model.generate_model(x_train, y_train)
                                score = model.model.score(x_test, y_test)
                                if score > best_score:
                                    best_params = model.model_kwargs
                                    best_score = score
                                    print("%s -- %s" % (score, best_params))

            model.model_kwargs = best_params
            print("Best found params: %s" % best_params)
            # Best found params:
            # {'max_features': 2, 'n_estimators': 38, 'criterion': 'gini', 'max_depth': 10, 'class_weight': None}
            print("Feature importances: %s" % model.model.feature_importances_)
            # Feature importances: [ 0.08076559  0.30474923  0.14358273  0.19469095  0.1400464   0.1361651 ]
            model.generate_model(x_train, y_train)
            _save_model(model)
    else:
        if not args.optimized:
            model.generate_model(x_train, y_train)
            _save_model(model)

