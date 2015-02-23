"""Prediction models for traffic disruption prediction based on weather forecast"""

import json
import os
from sklearn.externals import joblib


class PredictionModel(object):
    """Prediction model skeleton"""
    JSON_FILE = ''
    name = ''
    disruptions = {}
    stored_disruptions = {}
    parameters = 0

    def __init__(self, name, json_file, model_parameters):
        self.name = name
        self.JSON_FILE = json_file
        self.parameters = model_parameters

    def predict(self, *args):
        return 0


class ScikitPredictor(PredictionModel):
    """Pre-calculated Scikit-learn prediction model"""

    def __init__(self, name, json_file, model_parameters, model_file):
        self.model = joblib.load(model_file)
        super(ScikitPredictor, self).__init__(name, json_file, model_parameters)

    def predict(self, *args):
        val = self.model.predict(*args)
        if type(val) == list:
            return val[0]
        else:
            return int(val)


def init_models():
    model0 = PredictionModel('0-model', 'data/disruptions_model0.json', 3)
    model1 = ScikitPredictor('Logistic Regression', 'data/disruptions_logistic_regression.json', 3, 'model/predictor_model.pkl')
    model2 = ScikitPredictor('Linear Regression', 'data/disruptions_linear_regression.json', 3, 'model/linear.pkl')

    return [model0, model1, model2]


prediction_models = init_models()

