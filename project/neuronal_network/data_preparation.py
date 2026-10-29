
import json
import os

import pandas as pd
from sklearn.model_selection import train_test_split


class Input:
    def __init__(self):
        self.output_path = os.getenv("OUTPUT_PATH", "common_storage/output")
        self.storage_path = os.getenv("STORAGE_PATH", "common_storage")
        try:
            file_path = os.path.join(self.output_path,"master_training_data.parquet")
            print(file_path)
            self.data = pd.read_parquet(file_path)
            #print(self.data)
        except FileNotFoundError:
            print("File Not Found. Be sure all simulations are 'Processed'.")

    def separating(self,x,y,size=0.3):
        return train_test_split(x,y,test_size=size, random_state=42)


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



