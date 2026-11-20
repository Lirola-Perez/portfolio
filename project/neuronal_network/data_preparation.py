import array
import json
import os
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sqlalchemy import column
import pickle
import numpy as np


class Input:
    def __init__(self, storage_client):

        self.client = storage_client
        file_name = "master_training_data.parquet"
        self.column_names = []
        
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

    def separating(self,x,y,size=0.3) -> list:
        return train_test_split(x,y,test_size=size, random_state=42)

    def scaler(self,data,columns=None,mode:str="train",fitted_scaler=None,data_class: str | None = None):
        if mode == "train":
            scaler = StandardScaler()
        else:
            if fitted_scaler is None:
                raise ValueError("fitted_scaler must be provided when mode='test'")
            scaler = fitted_scaler

        data_formated = data.to_numpy(dtype=np.float32) if hasattr(data,"to_numpy") else np.array(data,dtype=np.float32)

        data_scaled = None
        if mode is None:
            print(f"WARNING: Please,data {mode} is not defined ['test' or 'train']")
            return
        if columns:
            index_to_scale = [self.column_names.index(name) for name in columns]
            #index_untouchted = [i for i in range(len(self.column_names)) if i not in index_to_scale]

            data_scaled = data_formated.copy().astype(np.float32)
            if mode == "train":
                data_scaled[:,index_to_scale] = scaler.fit_transform(data_formated[:,index_to_scale])
                print(f"Data {mode} shape: {data_formated.shape}")
            elif mode == "test":
                data_scaled[:,index_to_scale] = scaler.transform(data_formated[:,index_to_scale])
                print(f"Data {mode} shape: {data_formated.shape}")
        else:
            if mode == "train":
                print(f"Data {mode} shape: {data_formated.shape}")
                data_scaled = scaler.fit_transform(data_formated)
            elif mode == "test":
                print(f"Data {mode} shape: {data_formated.shape}")
                data_scaled = scaler.transform(data_formated)

        if data_class is not None:
            print(f"Updating scaler_{mode}.pkl")
            scaler_file_name = f"scaler_{mode}_{data_class}.pkl"
            # Creation of temporal folder:
            # joblib.dump(scaler_x, os.path.join(storage_path, 'scaler_x.pkl'))
            temp_local_path_scaler = self._temp_container("tmp",scaler_file_name)
            # Dumping the scaler in the temporary file
            with open(temp_local_path_scaler, "wb") as f:
                pickle.dump(scaler,f)
            # Uploading the file to backend via client:
            with open(temp_local_path_scaler, "rb") as f:
                self.client.upload(
                    main_folder="output",
                    remote_folder=f"model/{scaler_file_name}",
                    file_name=f)
        return data_scaled, scaler

    def inverted_scaler(self,scaler,data):
        return scaler.inverse_transform(data)

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
        self.column_names = list(x_matrix.columns)

        file_name = "column_list.json"
        if self.column_names:
            print(self.column_names)
            #column_path = os.path.join(self.output_path,"column_list.json")
            temp_local_file = self._temp_container(folder_name="tmp",
                                                file_name=file_name)
            print(temp_local_file)
            # Writing the file
            with open(temp_local_file, "w") as f:
                json.dump(self.column_names,f)
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
