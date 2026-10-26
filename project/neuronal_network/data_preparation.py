
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import os
import joblib
import json

class Input:
    def __init__(self):
        self.output_path = os.getenv("OUTPUT_PATH", "common_storage/output")
        try:
            file_path = os.path.join(self.output_path,"master_training_data.parquet")
            print(file_path)
            self.data = pd.read_parquet(file_path)
            print(self.data)
        except FileNotFoundError:
            print("File Not Found. Be sure all simulations are 'Processed'.")

    def scaler(self,x,y):
        x_scaler = StandardScaler()
        y_scaler = StandardScaler()

        y_scaled = y_scaler.fit_transform(y)
        x_scaled = x_scaler.fit_transform(x)

        joblib.dump(x_scaler, os.path.join(self.output_path, "scaler_input.pkl"))
        joblib.dump(y_scaler, os.path.join(self.output_path, "scaler_output.pkl"))

        return x_scaled,y_scaled

    def separating(self,x,y):
        Xt,Xtest,Yt,Ytest = train_test_split(x,y,test_size=0.3, random_state=42)
        return Xt,Xtest,Yt,Ytest

    def one_hot(self):
        # Drop rows: missing values
        self.df = self.data.dropna(axis=0)

        # Preparing X matrix with numbers exclusively:
        dummies = pd.get_dummies(self.df[['Weather',"Variable"]], dtype=int)
        self.df = pd.concat([self.df.drop(columns=['Weather', 'Variable', 'File', 'Zone']),dummies],axis=1)
        #self.df.drop([['Weather']])
        print(dummies)

        # Selecting Y matrix exclusively form from the time columns (format 00:00)
        time_columns = [col for col in self.df.columns if ":" in str(col)]
        y_matrix = self.df[time_columns]

        # Selecting X matrix all other numbered columns except time ones.
        x_matrix = self.df.drop(columns=y_matrix)
        column_names = list(x_matrix.columns)

        if column_names:
            column_path = os.path.join(self.output_path,"column_list.json")
            print(column_path)
            with open(column_path, "w") as f:
                json.dump(column_names,f)

        y = y_matrix.to_numpy()
        x = x_matrix.to_numpy()

        return x,y



