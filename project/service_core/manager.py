import json
import os
from pathlib import Path
import psycopg2
from eppy.modeleditor import IDF
from idf_class import IdfClass
from postgres_connection import get_db_connection
from psycopg2.extras import Json

DATABASE_URL = os.getenv("DATABASE_URL")

class IDFManager:

    def __init__(self,storage_client):

        self.client = storage_client
        parameters_name = "parameter_run.json"

        try:
            config_data = self.client.retrieve("parameters",parameters_name)
            # Temporary directory for dealing with the IDF and EPW data files

            temp_file = self._temp_container("parameters",parameters_name)
            with open(temp_file, "wb") as f:
                f.write(config_data)

            with open(temp_file, "r") as f:
                config_data = json.load(f)
                self.batch_id = self.parse_batch_parameters_to_postgresql(config_data)

        except FileNotFoundError:
            print(f"File 'parameter_run.json' not found in SupaBase.")

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

            # Temporary directory for dealing with the IDF and EPW data files
            temp_local_idf_file = self._temp_container(idf_name,f"{idf_name}.idf")
            temp_local_weather_file = self._temp_container(weather_name,f"{weather_name}.epw")

            # look for that file in the common_storage volume
            idf_file_binary = self.client.retrieve(idf_name,f"{idf_name}.idf")
            temp_local_idf_file.write_bytes(idf_file_binary)

            weather_file_binary = self.client.retrieve(weather_name,f"{weather_name}.epw")
            temp_local_weather_file.write_bytes(weather_file_binary)

            # --- CREATING THE IDF CLASS --------
            idf = IdfClass()        
            idf_file = idf.get_idf(Path(temp_local_idf_file),Path(temp_local_weather_file))

            # Clean up the temporary local file
            if os.path.exists(temp_local_idf_file):
                os.remove(temp_local_idf_file)
            if os.path.exists(temp_local_weather_file):
                os.remove(temp_local_weather_file)
                
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

            new_idf_name = f"{idf_name}_{weather}_{property}_{val}"

            other_properties = [p for p in all_properties if p != property]
            print(other_properties)
            
            run_sim = sim
            keys = ["other_properties","property_value","modified_idf_name"]
            values = [other_properties,val,new_idf_name]

            for x,y in keys,values:
                run_sim[x]= y 

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
            dir_filename = self._temp_container(new_idf_name,new_idf_name + "idf")

            # and now saving it.
            idf_file.saveas(dir_filename)
            # taking the IDF from the temp dir and saving in SupaBase
            with open(dir_filename, 'rb') as f:
                self.client.upload(main_folder="output",remote_folder=new_idf_name,file_name=f)


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

    def _temp_container(self,folder_name:str,file_name= None):
        # Temporary folder in container:
        temp_dir = Path(f"/tmp/{folder_name}")
        temp_dir.mkdir(parents=True,exist_ok=True)
        if not file_name:
            return Path(temp_dir)
        return Path(temp_dir / file_name)

    def key_filter(self,idf, word:str) -> list:
        key_filtered = []
        for obj in idf.idfobjects:
            word_cap = word.upper()
            if obj.startswith(word_cap):
                key_filtered.append(obj)
        return key_filtered

    def output_object_generator(self,idf,output_list:list):
        if not idf.idfobjects['Output:SQLite']:
            idf.newidfobject('OUTPUT:SQLITE',Option_Type='Simple')

        idf.newidfobject('OUTPUT:VARIABLEDICTIONARY',Key_Field='Regular')

        for item in output_list:
            idf.newidfobject('OUTPUT:VARIABLE',Key_Value='*',Variable_Name=item,Reporting_Frequency='Timestep')
        return idf


