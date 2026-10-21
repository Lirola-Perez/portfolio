
import pandas as pd
import os

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

    def correlation(self):
        pass

    def one_hot(self):
        # Drop rows: missing values
        self.df = self.data.dropna(axis=0)

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



