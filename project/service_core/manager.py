import json
import os
from pathlib import Path
from eppy.modeleditor import IDF
from idf_class import IdfClass
from psycopg2.extras import Json
from postgres_connection import get_db_connection

# Environment variables (If not set then ./common_storage)
STORAGE_PATH = Path(os.getenv("STORAGE_PATH", "./common_storage"))

class IDFManager:

    def __init__(self):
        self.storage_path = STORAGE_PATH

        try:
            with open(Path(self.storage_path, "parameter_run.json"), "r") as f:
                config_data = json.load(f)
                self.batch_id = self.parse_batch_parameters_to_postgresql(config_data)
        except FileNotFoundError as e:
            print(f"File 'parameter_run.json' not found in {self.storage_path}.")

    def parse_batch_parameters_to_postgresql(self, config_data:dict):
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """INSERT INTO simulation_batches (status,config_data)
                "VALUES (%s, %s)
                "RETURNING batch_id""",
                ("pending", Json(config_data),),
            )
            row = cursor.fetchone()
            print("Debug - fetchone result:", row)  # Let's see what prints here

            if row is None:
                raise Exception(
                    "The INSERT statement did not return a batch_id. Check your table"
                    " schema."
                )

            self.batch_id = row[0]
            conn.commit()
            return self.batch_id

        except Exception as e:
            conn.rollback()
            print(f"Error inserting parameters: {e}")
            raise e
        finally:
            cursor.close()
            conn.close()

    def load_config_from_postgresql(self) -> dict:
        '''Connect to PostgresSQL to fetch JSONB config'''
        # Open connection -------------------------
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT config_data FROM simulation_batches WHERE batch_id = %s",
            (self.batch_id,)
        )
        # to grab the row maching the batch_id
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        # Closed connection -------------------------

        if not row:
            raise ValueError(f"Batch ID {self.batch_id} not found in database")

        # request give just the values selected config_data 
        config_data = row[0]

        return config_data

    def process_idf_files(self):
        '''fetch config from PostgreSQL to process files'''
        config_data = self.load_config_from_postgresql()
        # Getting the simulations from the dictionary:
        simulations = config_data.get("simulations", [])

        list_idf_files = []
        # Looping the simulations:
        for sim in simulations:

            idf_name = sim["idf_file"]
            weather_name = sim["weather"]

            # look for that file in the common_storage volume
            idf_file_path = self.storage_path / f"{idf_name}.idf"
            weather_path = self.storage_path / f"weather/{weather_name}.epw"

            idf = IdfClass()
            idf_file = idf.get_idf(idf_file_path,weather_path)
            total_idf = [idf_file:IDF,sim:dict]
            list_idf_files.append(total_idf)

        return list_idf_files

