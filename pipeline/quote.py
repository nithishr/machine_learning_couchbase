import os
import pickle

import pandas as pd


class Model(object):
    # Constructor
    # Constructor loads "regression_model" into memory as noted in the
    # pickle_path line. Using that in memory file, getPrediction processes
    # the file sent to it using the model in memory

    def __init__(self):
        pickle_path = os.path.join(os.path.dirname(__file__), "regression_model.pkl")
        f = open(pickle_path, "rb")
        self.pipeline = pickle.load(f)
        f.close()

    # Method to predict the insurance quote
    def getPrediction(self, age, sex, bmi, children, smoker, region):
        test_data = {
            "age": age,
            "sex": sex,
            "bmi": bmi,
            "children": children,
            "smoker": smoker,
            "region": region,
        }
        return self.pipeline.predict(pd.DataFrame([test_data]))[0]
