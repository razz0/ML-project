"""Prediction models for traffic disruption prediction based on weather forecast"""

import json
import os

import numpy as np
from sklearn import linear_model
from sklearn.externals import joblib


class PredictionModel(object):
    """Prediction model skeleton"""

    def __init__(self, name, json_file, model_parameters):
        self.name = name
        self.JSON_FILE = json_file
        self.parameters = model_parameters
        self.disruptions = {}
        self.stored_disruptions = {}

    def predict(self, *args):
        return 0


class ScikitPredictor(PredictionModel):
    """Pre-calculated Scikit-learn prediction model"""

    def __init__(self, name, json_file, model_parameters, model_file):
        try:
            self.model = joblib.load(model_file)
        except IOError:
            self.model = None

        super(ScikitPredictor, self).__init__(name, json_file, model_parameters)

    def predict(self, *args):
        val = self.model.predict(*args)
        if type(val) == list:
            return val[0]
        else:
            return int(val)


def init_models():
    models = []
    models.append(PredictionModel('0-model', 'data/disruptions_model0.json', 3))
    models.append(ScikitPredictor('Logistic Regression', 'data/disruptions_logistic_regression.json', 3, 'model/logistic.pkl'))
    models.append(ScikitPredictor('Logistic Regression 2', 'data/disruptions_logistic_regression_2.json', 4, 'model/logistic2.pkl'))
    models.append(ScikitPredictor('Linear Regression 2', 'data/disruptions_linear_regression.json', 4, 'model/linear.pkl'))
    models.append(ScikitPredictor('Linear Regression', 'data/disruptions_linear_regression_2.json', 3, 'model/linear2.pkl'))
    models.append(ScikitPredictor('2NN', 'data/2nn.json', 4, 'model/2nn.pkl'))
    models.append(ScikitPredictor('4NN', 'data/4nn.json', 4, 'model/4nn.pkl'))

    return models


prediction_models = init_models()

