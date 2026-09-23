from sklearn.preprocessing import OneHotEncoder
import pandas as pd

class Input:
    def __init__(self, data):
        self.data = data


    def correlation(self):
        pass

    def one_hot(self):
        # Drop rows: missing values
        self.data.dropna(axis=0)
        # Drop columns: missing values

        
        pd.get_dummies(self.data[['Weather','File']])



