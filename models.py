"""Prediction models for traffic disruption prediction based on weather forecast"""


class PredictionModel(object):
    """Prediction model skeleton"""

    def __init__(self, name, json_file, parameters, **model_kwargs):
        self.name = name
        self.JSON_FILE = json_file
        self.parameters = parameters
        self.model_kwargs = model_kwargs
        self.disruptions = {}
        self.stored_disruptions = {}
        self.model = self  # Prediction model

    def predict(self, *args):
        return 0

    def generate_model(self, x, y):
        pass

    def save_model(self):
        pass

    def load_model(self):
        pass


class ScikitPredictor(PredictionModel):
    """Pre-calculated Scikit-learn prediction model"""

    def __init__(self, name, json_file, parameters, model_file, **model_kwargs):
        super(ScikitPredictor, self).__init__(name, json_file, parameters, **model_kwargs)
        self.model = None
        self.filename = model_file

    def predict(self, *args):
        val = self.model.predict(*args)
        if type(val) == list:
            return val[0]
        else:
            return int(val)

    def save_model(self):
        from sklearn.externals import joblib
        joblib.dump(self.model, self.filename)

    def load_model(self):
        from sklearn.externals import joblib
        try:
            self.model = joblib.load(self.filename)
        except IOError:
            pass


class ModelNN(ScikitPredictor):

    def generate_model(self, x, y):
        '''
        Generate model to predict y from x

        :return: None
        '''
        from sklearn.neighbors import KNeighborsRegressor

        self.model = KNeighborsRegressor(**self.model_kwargs)
        self.model.fit(x, y)

        print self.model


class ModelLogisticRegression(ScikitPredictor):

    def generate_model(self, x, y):
        '''
        Generate model to predict y from x

        :return: None
        '''
        from sklearn import linear_model

        self.model = linear_model.LogisticRegression(**self.model_kwargs)
        self.model.fit(x, y)


class ModelLinearRegression(ScikitPredictor):

    def generate_model(self, x, y):
        '''
        Generate model to predict y from x

        :return: None
        '''
        from sklearn import linear_model

        self.model = linear_model.LinearRegression(**self.model_kwargs)
        self.model.fit(x, y)


def init_models():
    """
    Initialize models and return them as list

    :return: list of PredictionModel
    """
    models = []
    models.append(PredictionModel('0-model', 'data/disruptions_model0.json', 3))
    #models.append(ScikitPredictor('Logistic Regression', 'data/disruptions_logistic_regression.json', 3, 'model/logistic.pkl'))
    models.append(ModelLogisticRegression('Logistic Regression', 'data/disruptions_logistic_regression_2.json', 4, 'model/logistic2.pkl', C=1.0))
    models.append(ModelLinearRegression('Linear Regression', 'data/disruptions_linear_regression.json', 4, 'model/linear.pkl'))
    #models.append(ScikitPredictor('Linear Regression', 'data/disruptions_linear_regression_2.json', 3, 'model/linear2.pkl'))
    models.append(ModelNN('2NN', 'data/2nn.json', 4, 'model/2nn.pkl', n_neighbors=2))
    models.append(ModelNN('3NN', 'data/3nn.json', 4, 'model/3nn.pkl', n_neighbors=3))
    models.append(ModelNN('4NN', 'data/4nn.json', 4, 'model/4nn.pkl', n_neighbors=4))

    return models


def load_models(models):
    """
    Import models from generated pickle files.

    :parameter models: list of PredictionModel
    """
    for model in models:
        model.load_model()


def generate_models(models, xx, yy):
    """
    Generate and save models to pickle files.

    @type  models: list[PredictionModel]
    """
    for model in models:
        model.generate_model(xx, yy)
        model.save_model()
        print 'Saved model %s' % model.name


prediction_models = init_models()

