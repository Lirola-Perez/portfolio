import json
import os
from pathlib import Path
from typing import cast

import psycopg2
from eppy.modeleditor import IDF
from idf_class import IdfClass
from postgres_connection import get_db_connection
from psycopg2.extras import Json
from supabase import Client,create_client
import tempfile

DATABASE_URL = os.getenv("DATABASE_URL")

# Initialize Supabase Client
SUPABASE_URL: str = os.getenv("SUPABASE_URL") #type: ignore
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY") #type: ignore
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class IDFManager:

    def __init__(self):

        self.parameters_bucket = 'parameters'
        self.idfs_bucket = "idf-files"
        self.weather_bucket = "weather"
        self.output_bucket = "output"
        parameters_name = 'parameter_run.json'

        try:
            self.storage_path = supabase.storage
            print(self.storage_path)
            self.output_path = self.storage_path.from_(self.output_bucket)
            self.weather_file_binary = self.storage_path.from_(self.weather_bucket)
            self.idf_files_path = self.storage_path.from_(self.idfs_bucket)
        except Exception as e:
            print(f"Folders in SupaBase storage missing {self.idfs_bucket}, {self.weather_bucket}, {self.output_bucket}: Exception: {e}")

        try:
            config_data = self.storage_path.from_(self.parameters_bucket).download(parameters_name)
            # Temporary directory for dealing with the IDF and EPW data files
            temp_dir = tempfile.mkdtemp()
            temp_file = Path(temp_dir, "parameter_run.json")
            with open(temp_file, "wb") as f:
                f.write(config_data)

            with open(temp_file, "r") as f:
                config_data = json.load(f)
                self.batch_id = self.parse_batch_parameters_to_postgresql(config_data)

        except FileNotFoundError:
            print(f"File 'parameter_run.json' not found in SupaBase.")

    def parse_batch_parameters_to_postgresql(self, config_data:dict):

        try:
            with get_db_connection() as conn, conn.cursor() as cursor:

                cursor.execute(
                    """INSERT INTO simulation_batches (config_data)
                    VALUES (%s)
                    RETURNING batch_id""",
                    (Json(config_data),),
                )
                row = cursor.fetchone()
                print("Debug - fetchone result:", row)  # Let's see what prints here

                if row is None:
                    raise ValueError(
                        "The INSERT statement did not return a batch_id. Check your table"
                        " schema."
                    )

                self.batch_id = row[0]
                return self.batch_id

        except psycopg2.OperationalError as e:
            # Handles connection drops, network failures, or database down states
            print(f"Database operational error (connection/timeout): {e}")
            raise

        except psycopg2.ProgrammingError as e:
            # Handles syntax errors in your SQL query or missing tables/columns
            print(f"Database programming error (bad SQL/schema): {e}")
            raise

        except psycopg2.DatabaseError as e:
            # Catch-all for any other database-specific errors
            print(f"General database error: {e}")
            raise

        except Exception as e: # noqa: BLE001
            print(f"Error saving results to DB: {e}")
            raise

    def load_config_from_postgresql(self) -> dict:
        '''Connect to PostgresSQL to fetch JSONB config'''
        # Open connection -------------------------
        with get_db_connection() as conn, conn.cursor() as cursor:
            cursor.execute(
                "SELECT config_data FROM simulation_batches WHERE batch_id = %s",
                (self.batch_id,)
            )
            # to grab the row maching the batch_id
            row = cursor.fetchone()
        # Closed connection -------------------------

        if not row:
            raise ValueError(f"Batch ID {self.batch_id} not found in database")

        # request give just the property_values selected config_data 
        config_data = row[0]

        return config_data

    def process_idf_files(self):
        '''fetch config from PostgreSQL to process files'''
        config_data = self.load_config_from_postgresql()
        # Getting the simulations from the dictionary:
        simulations = config_data.get("simulations", [])
        output_list = config_data.get("output_list", [])
        all_properties = config_data.get("all_properties",[])

        # Looping the simulations:
        for sim in simulations:

            idf_name = sim["idf_file"]
            weather_name = sim["weather"]

            print(idf_name)

            # look for that file in the common_storage volume
            idf_file_binary = self.idf_files_path.download(f"{idf_name}.idf")
            weather_file_binary = self.weather_file_binary.download(f"{weather_name}.epw")

            # Temporary directory for dealing with the IDF and EPW data files
            temp_dir = tempfile.mkdtemp()
            idf_file_path = os.path.join(temp_dir,f"{idf_name}.idf")
            weather_file_path = os.path.join(temp_dir,f"{weather_name}.epw")

            with open(idf_file_path, "wb") as f:
                f.write(idf_file_binary)

            with open(weather_file_path, "wb") as f:
                f.write(weather_file_binary)

            # --- CREATING THE IDF CLASS --------
            idf = IdfClass()        
            idf_file = idf.get_idf(Path(idf_file_path),Path(weather_file_path))
            # -----------------------------------
            # Setting general simulation common configuration
            # Simulation config // output variables
            idf_file = self.set_idf_info(idf_file,output_list)
            self.parametrization(idf_file,sim,all_properties)

    def parametrization(self,idf_file:IDF,sim:dict,all_properties:list):
        # Function to add/change the files with new parameters and 
        # create new directories and files.

        idf_name = sim["idf_file"]
        type = sim["type"]
        type_name = sim["type_name"]
        property = sim["property"]
        property_values = sim["property_value"]
        weather = sim["weather"]
        
        for val in property_values:

            # run_folder = Path(f"{self.output_path}/{idf_name}_{weather}_{property}_{val}")
            # run_folder.mkdir(parents=True, exist_ok=True)

            new_idf_name = f"{idf_name}_{weather}_{property}_{val}"

            other_properties = [p for p in all_properties if p != property]
            print(other_properties)
            
            run_sim = sim
            # Include all other_properties adjusted from other idfs
            run_sim["other_properties"] = other_properties
            # Include value changed from this idf
            run_sim["property_value"] = val
            # Include the new name
            run_sim["modified_idf_name"] = new_idf_name

            # transformation: --------------
            print(type, type_name)
            object = idf_file.getobject(type, type_name)
            old_value = object[property] # type: ignore

            run_sim[f"{property}_old_value"] = old_value
            # new value:
            object[property] = val # type: ignore
            print(object)
            print(run_sim)

            # taking other properties
            other_values = []
            for prop in other_properties:
                object = idf_file.getobject(type, type_name)
                val = object[prop] # type:ignore
                if val: 
                    other_values.append(val)
                else:
                    other_values.append(None)
            run_sim["other_values"] = other_values

            status = "Pending"
            try:
                with get_db_connection() as conn, conn.cursor() as cursor:
                    cursor.execute(
                        """INSERT INTO simulations (batch_id,idf_filename,weather,status_simulation,parameters_applied)
                            VALUES (%s,%s,%s,%s,%s)
                            RETURNING simulation_id;
                            """,
                            (self.batch_id,new_idf_name,weather,status,Json(run_sim),),
                    )
                    simulation = cursor.fetchone()
                    # Connection automatic closed
                    if simulation:
                        simulation_id = simulation[0]

                        cursor.execute(
                            """INSERT INTO idf_components (simulation_id,
                            type_class,
                            type_name,
                            property_name,
                            property_value,
                            old_property_value,
                            weather,
                            other_properties,
                            other_values) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s);""",
                            (simulation_id,
                            type,
                            type_name,
                            property,
                            val,
                            old_value,
                            weather,
                            other_properties,
                            other_values,),
                        )
            except psycopg2.OperationalError as e:
                # Handles connection drops, network failures, or database down states
                print(f"Database operational error (connection/timeout): {e}")
                raise
    
            except psycopg2.ProgrammingError as e:
                # Handles syntax errors in your SQL query or missing tables/columns
                print(f"Database programming error (bad SQL/schema): {e}")
                raise
    
            except psycopg2.DatabaseError as e:
                # Catch-all for any other database-specific errors
                print(f"General database error: {e}")
                raise
    
            except Exception as e: # noqa: BLE001 
                print(f"Error saving results to DB: {e}")
                raise

            # Creating a temporary directory and saving IDF temporary in it:
            with tempfile.TemporaryDirectory() as temp_dir:
                dir_filename = os.path.join(new_idf_name, new_idf_name + ".idf")
                new_path = os.path.join(temp_dir, dir_filename)

                # Creating the local subfolder inside temp_dir if it doesn't exist
                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                # and now saving it.
                idf_file.saveas(new_path)
                # taking the IDF from the temp dir and saving in SupaBase
                with open(new_path, 'rb') as f:
                    self.storage_path.from_(self.output_bucket).upload(
                        path=dir_filename,
                        file=f,
                        file_options={"upsert": "true"})

    def set_idf_info(self,idf:IDF,output_list:list):

        timestep = idf.idfobjects['Timestep'][0]
        if timestep.Number_of_Timesteps_per_Hour != 6:
            timestep.Number_of_Timesteps_per_Hour = 6
            print(timestep)

        sim_control = idf.idfobjects['SIMULATIONCONTROL'][0]
        print(f'Do Zone Sizing Calculation: {sim_control.Do_Zone_Sizing_Calculation}')

        if sim_control.Do_System_Sizing_Calculation.lower() == 'no':
            sim_control.Do_System_Sizing_Calculation='YES'
        print(f'Do System Sizing Calculation: {sim_control.Do_System_Sizing_Calculation}')
        
        if sim_control.Run_Simulation_for_Sizing_Periods.lower() == 'no':
            sim_control.Run_Simulation_for_Sizing_Periods='YES'
        print(f'Run Simulation for Sizing Periods: {sim_control.Run_Simulation_for_Sizing_Periods}')

        print(f'Run Simulation for Weather File Run Periods: {sim_control.Run_Simulation_for_Weather_File_Run_Periods}')

        filtered = self.key_filter(idf,'Output:Variable')
        for item in filtered:
            idf.idfobjects[item].clear()
            print(idf.idfobjects[item])

        self.output_object_generator(idf, output_list)
        return idf

    def key_filter(self,idf, word:str) -> list:
        key_filtered = []
        for SUPABASE_KEY in idf.idfobjects:
            word_cap = word.upper()
            if SUPABASE_KEY.startswith(word_cap):
                key_filtered.append(SUPABASE_KEY)
        return key_filtered

    def output_object_generator(self,idf,output_list:list):
        if not idf.idfobjects['Output:SQLite']:
            idf.newidfobject('OUTPUT:SQLITE',Option_Type='Simple')

        idf.newidfobject('OUTPUT:VARIABLEDICTIONARY',Key_Field='Regular')

        for item in output_list:
            idf.newidfobject('OUTPUT:VARIABLE',Key_Value='*',Variable_Name=item,Reporting_Frequency='Timestep')
        return idf


