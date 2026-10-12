from sklearn.preprocessing import OneHotEncoder
import pandas as pd

class Input:
    def __init__(self, data):
        self.df = data

    def correlation(self):
        pass

    def one_hot(self):
        # Drop rows: missing values
        self.df = self.df.dropna(axis=0)

        dummies = pd.get_dummies(self.df[['Weather',"Variable"]], dtype=int)
        self.df = pd.concat([self.df.drop(columns=['Weather', 'Variable', 'File', 'Zone']),dummies],axis=1)
        #self.df.drop([['Weather']])
        print(dummies)

        col_names = [col for col in self.df.columns if ":" in str(col)]
        y_matrix = self.df[col_names]
        x_matrix = self.df.drop(columns=y_matrix)
        y = y_matrix.to_numpy()
        x = x_matrix.to_numpy()

        return x,y



