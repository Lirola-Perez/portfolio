import json
import os
from pathlib import Path
from eppy.modeleditor import IDF
from idf_class import IdfClass
from psycopg2.extras import Json
from postgres_connection import get_db_connection

# Environment variables (If not set then ./common_storage)
STORAGE_PATH = Path(os.getenv("STORAGE_PATH", "./common_storage"))
OUTPUT_PATH = Path(os.getenv("OUTPUT_PATH", "/common_storage/output"))
IDF_PATH = Path(os.getenv("IDF_PATH", "/common_storage/idf_files"))
WEATHER_PATH = Path(os.getenv("WEATHER_PATH", "/common_storage/weather"))

class IDFManager:

    def __init__(self):
        self.storage_path = STORAGE_PATH
        self.output_path = OUTPUT_PATH
        self.idf_files_path = IDF_PATH
        self.idf_weather_path = WEATHER_PATH

        try:
            with open(Path(self.storage_path, "parameter_run.json"), "r") as f:
                config_data = json.load(f)
                self.batch_id = self.parse_batch_parameters_to_postgresql(config_data)
        except FileNotFoundError as e:
            print(f"File 'parameter_run.json' not found in {self.storage_path}.")

    def parse_batch_parameters_to_postgresql(self, config_data:dict):
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO simulation_batches (config_data)
                    VALUES (%s)
                    RETURNING batch_id""",
                    (Json(config_data),),
                )
                row = cursor.fetchone()
                print("Debug - fetchone result:", row)  # Let's see what prints here
    
                if row is None:
                    raise Exception(
                        "The INSERT statement did not return a batch_id. Check your table"
                        " schema."
                    )
    
                self.batch_id = row[0]
                return self.batch_id

    def load_config_from_postgresql(self) -> dict:
        '''Connect to PostgresSQL to fetch JSONB config'''
        # Open connection -------------------------
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
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

            # look for that file in the common_storage volume
            idf_file_path = self.idf_files_path / f"{idf_name}.idf"
            weather_path = self.idf_weather_path / f"weather/{weather_name}.epw"

            # --- CREATING THE IDF CLASS --------
            idf = IdfClass()        
            idf_file = idf.get_idf(idf_file_path,weather_path)
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

            run_folder = Path(f"{self.output_path}/{idf_name}_{weather}_{property}_{val}")
            run_folder.mkdir(parents=True, exist_ok=True)

            other_properties = [p for p in all_properties if p != property]
            print(other_properties)
            
            run_sim = sim
            # Include all other_properties adjusted from other idfs
            run_sim["other_properties"] = other_properties
            # Include value changed from this idf
            run_sim["property_value"] = val
            
            new_idf_name = f"{idf_name}_{weather}_{property}_{val}"
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

            with get_db_connection() as conn:
                with conn.cursor() as cursor:
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
                conn.commit()

            new_path = os.path.join(run_folder, new_idf_name + ".idf")
            idf_file.saveas(new_path)

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
        for key in idf.idfobjects.keys():
            word_cap = word.upper()
            if key.startswith(word_cap):
                key_filtered.append(key)
        return key_filtered

    def output_object_generator(self,idf,output_list:list):
        if not idf.idfobjects['Output:SQLite']:
            idf.newidfobject('OUTPUT:SQLITE',Option_Type='Simple')

        idf.newidfobject('OUTPUT:VARIABLEDICTIONARY',Key_Field='Regular')

        for item in output_list:
            idf.newidfobject('OUTPUT:VARIABLE',Key_Value='*',Variable_Name=item,Reporting_Frequency='Timestep')
        return idf


