import json
import os
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sqlalchemy import column

class Input:
    def __init__(self, storage_client):

        self.client = storage_client
        file_name = "master_training_data.parquet"
        
        try:
            file_binary = self.client.retrieve(main_folder="output",
                                 file_name= f"output/{file_name}")

            print(f"Downloaded bytes length: {len(file_binary) if file_binary else 'None'}")
            print(f"First 100 bytes: {file_binary[:100] if file_binary else 'Empty'}")
            
            # file_path = os.path.join(self.output_path,"master_training_data.parquet")
            # print(file_path)
            temp_local_file = self._temp_container(folder_name="tmp",
                                                   file_name=file_name)
            temp_local_file.write_bytes(file_binary)
            self.data = pd.read_parquet(str(temp_local_file))

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

        file_name = "column_list.json"
        if column_names:
            #column_path = os.path.join(self.output_path,"column_list.json")
            temp_local_file = self._temp_container(folder_name="tmp",
                                                file_name=file_name)
            print(temp_local_file)
            # Writing the file
            with open(temp_local_file, "w") as f:
                json.dump(column_names,f)
            # Opening the file as binary for uploading in supabase
            with open(temp_local_file, "rb") as f:
                self.client.upload(main_folder="output",
                                   remote_folder=f"output/{file_name}" ,
                                   file_name=f)

        y = y_matrix.to_numpy()
        x = x_matrix.to_numpy()

        return x,y

    def _temp_container(self,folder_name:str,file_name= None):
        # Temporary folder in container:
        temp_dir = Path(f"/tmp/{folder_name}")
        temp_dir.mkdir(parents=True,exist_ok=True)
        if not file_name:
            return Path(temp_dir)
        return Path(temp_dir / file_name)
