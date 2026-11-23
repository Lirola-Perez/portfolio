import array
from http.client import VARIANT_ALSO_NEGOTIATES
import json
import re
import pandas as pd
from pathlib import Path
from pandas import DataFrame
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

    def separating(self,data_x:DataFrame,data_y:DataFrame,size=0.3) -> list[pd.DataFrame]:
        print(f"STARTING SEPARATION:")
        return train_test_split(data_x,data_y,test_size=size, random_state=42)

    def from_dataframe_to_numpy(self,data):
        return data.to_numpy()

    def scaler_rows(self,
                    data_output:np.ndarray,
                    idx_rows:dict,
                    variable_list:list[str],
                    mode:str = "train",
                    fitted_scaler= None):
        print(f"STARTING ROW SCALER")
        scaler_list = []
        data_scaled = data_output.copy().astype(np.float32)
        for variable in variable_list:
            rows = np.asarray(idx_rows[variable])
            print(f"ROW INDEXES COLLECTED: {rows}")
            if mode == "train":
                scaler = StandardScaler()
                data_scaled[rows,:] = scaler.fit_transform(data_output[rows,:])
                print(f"Data {mode} shape: {data_scaled.shape}")
                scaler_list.append(scaler)
                self.scaler_saver(scaler=scaler,mode=mode,identity=variable)
            else:
                if fitted_scaler is None:
                    raise ValueError("fitted_scaler must be provided when mode='test'")
                for scaler in fitted_scaler:
                    data_scaled[rows] = scaler.transform(data_output[rows])
        return scaler_list, data_scaled

    def inverted_row_scaler(self,data_output, idx_rows,variable_list:list[str],scaler_list):
        for variable,scaler in zip(variable_list,scaler_list):
            rows = np.asarray(idx_rows[variable])
            data_output[rows] = scaler.inverse_transform(data_output[rows])     
        return data_output

    def scaler_columns(self,
                       data_input:np.ndarray,
                       column_idx:dict,
                       mode:str="train",
                       fitted_scaler: None | list[StandardScaler]=None):
        print(f"STARTING COLUMN SCALER")
        data_scaled = data_input.copy()
        scaler_list = []
        for col_key,col_idx in column_idx.items():
            print(f"COLUMN INDEX IN SCALER: {col_key}")
            # All rows in that column:
            col_2d = data_scaled[:,[col_idx]]  # shape (N, 1)
            if mode == "train":
                scaler = StandardScaler()
                data_scaled[:,[col_idx]] = scaler.fit_transform(col_2d)
                print(f"Data {mode} shape: {data_scaled.shape}")
                scaler_list.append(scaler)
                self.scaler_saver(scaler=scaler,mode=mode,identity=f"column_{col_key}")
            else:
                if fitted_scaler is None:
                    raise ValueError("fitted_scaler must be provided when mode='test'")
                for scaler in fitted_scaler:
                    data_scaled[:,[col_idx]] = scaler.transform(col_2d)
        return scaler_list, data_scaled

    def scaler(self,data,column=None,mode:str="train",fitted_scaler=None,data_class: str | None = None):
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
        if column is not None:
            # takes the column index
            col_idx = self.column_names.index(column) if isinstance(column, str) else column
            # makes a copy of the data for being scaled
            data_scaled = data_formated.copy().astype(np.float32)
            # keeps 2D shape (N, 1) -> takes the column to be transformed
            col_slice = data_formated[:, [col_idx]]  
            if mode == "train":
                # adds the transformed column to the database
                data_scaled[:,[col_idx]] = scaler.fit_transform(col_slice)
                print(f"Data {mode} shape: {data_formated.shape}")
            elif mode == "test":#
                data_scaled[:,[col_idx]] = scaler.transform(col_slice)
                print(f"Data {mode} shape: {data_formated.shape}")
            else:
                raise ValueError(f"Unsupported mode: {mode!r}. Expected 'train' or 'test'.")

            if data_class is not None:
                column_name = self.sanitize_storage_key(column)
                self.scaler_saver(scaler,mode=mode,identity=column_name)
        else:
            if mode == "train":
                print(f"Data {mode} shape: {data_formated.shape}")
                data_scaled = scaler.fit_transform(data_formated)
            elif mode == "test":
                print(f"Data {mode} shape: {data_formated.shape}")
                data_scaled = scaler.transform(data_formated)
            else:
                raise ValueError(f"Unsupported mode: {mode!r}. Expected 'train' or 'test'.")

            if data_class is not None:
                self.scaler_saver(scaler,mode=mode)

        return data_scaled, scaler
    
    def scaler_saver(self,scaler,mode:str="train",identity=None):
        scaler_file_name = None
        print(f"Updating scaler_{mode}.pkl")
        if identity:
            name = self.sanitize_storage_key(identity)
        else:
            name = None
        scaler_file_name = f"scaler_{mode}_{name}.pkl"
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
        return scaler_file_name

    def one_hot(self):
        # Drop rows: missing values
        self.df = self.data.dropna(axis=0)

        # Preparing X matrix with numbers exclusively:
        dummies = pd.get_dummies(self.df[['Weather',"Variable"]], dtype=int)
        self.df = pd.concat([self.df.drop(columns=['Weather', 'Variable', 'File', 'Zone']),dummies],axis=1)
        #self.df.drop([['Weather']])
        print(dummies)

    def input_output_selector(self):

        # Selecting Y matrix exclusively form from the time column (format 00:00)
        time_columns = [col for col in self.df.columns if ":" in str(col)]
        y_matrix = self.df[time_columns]

        # Selecting X matrix all other numbered column except time ones.
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
                                   remote_folder=f"output/{file_name}",
                                   file_name=f)

        return x_matrix,y_matrix

    def row_index_taker(self,data:DataFrame,variable_list:list) -> dict:
        row_idx = {}
        for variable in variable_list:
            var_idx = data[variable] == 1
            row_idx[variable] = var_idx
        return row_idx

    def column_index_taker(self,data:DataFrame,variable_list:list[str]) -> dict:
        column_idx = {}
        for variable in variable_list:
            var_idx = data.columns.get_loc(variable)
            column_idx[variable] = var_idx
        return column_idx

    def _temp_container(self,folder_name:str,file_name= None):
        # Temporary folder in container:
        temp_dir = Path(f"/tmp/{folder_name}")
        temp_dir.mkdir(parents=True,exist_ok=True)
        if not file_name:
            return Path(temp_dir)
        return Path(temp_dir / file_name)

    def sanitize_storage_key(self,name: str) -> str:
        # Replace any character outside letters, numbers, underscore, hyphen, or dot with '_'
        cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", name)
        # Collapse repeated underscores and trim leading/trailing underscores
        cleaned = re.sub(r"_+", "_", cleaned).strip("_")
        return cleaned
