import os
import pandas as pd
from pathlib import Path
import sqlite3
from postgres_connection import get_db_connection

class SimulationData:
    def __init__(self) -> None:
        self.output_path = os.getenv("OUTPUT_PATH", "common_storage/output")


    def worker(self):

        all_simulations = []
        while True:
            table = []
            table = self.file_db_grabber()
            if table is None or not isinstance(table, pd.DataFrame):
                break
            all_simulations.append(table)

        if not all_simulations:
            print(f"WARNING: Empty master data table!")
            return pd.DataFrame()
        
        master_df = pd.concat(all_simulations, axis=0)
        print(f"Master data table successfully saved")
    
        return master_df

    def save_master_df(self, data:pd.DataFrame):

        file_path = os.path.join(self.output_path,"master_training_data.parquet")
        data.to_parquet(file_path,index=False)
        print(f"Master dataset saved successfully at {file_path}")


    def completed_data_grabber(self):

        with get_db_connection() as conn:
            with conn.cursor() as cursor:

                # Using UPDATE for update status and retrieve vars
                # Using FOR UPDATE SKIP LOCKED to avoid conflict with other containers
                cursor.execute(
                    """UPDATE simulations SET status_simulation = 'Processing'
                    WHERE simulation_id = (
                    SELECT simulation_id FROM simulations 
                    WHERE status_simulation = 'Completed'
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED)
                    RETURNING simulation_id,idf_filename,batch_id,parameters_applied;"""
                )

                simulation_row = cursor.fetchone()

                if not simulation_row:
                    return None,None

                _,_,batch_id,_ = simulation_row

                cursor.execute(
                    """SELECT output_variables FROM output_variables
                    WHERE batch_id = %s
                    """, 
                    (batch_id,),
                )
                output_variables_row = cursor.fetchone()

        return simulation_row,output_variables_row

    def file_db_grabber(self):

        reset_pivoted = []

        simulation_data,output_variables = self.completed_data_grabber()
        if simulation_data:
            sim_id,folder_name,batch_id,parameters = simulation_data
            outpath_csv = self.get_file_output_path(folder_name,"epluszsz.csv")
            property = str
            long_result = pd.DataFrame
            if outpath_csv:
                result = pd.read_csv(outpath_csv)
                property = parameters["property"]
                #old_property = f"{property}_old_value"
                result['Weather'] = parameters["weather"]
                result['File'] = parameters["idf_file"]
                result[property] = parameters["property_value"]
                result[f"{property}_old_value"] = parameters[f"{property}_old_value"]
                print(property)

                # Unifying names
                result = self.name_unifier(result)

                # Keeping only time-related rows
                result = result[result['Time'].astype(str).str.contains(':', na=False)]

                # cleaning columns with only zeros
                result = self.clean_columns(result)

                # MELTING keeping the anchor columns Time, weather, file.
                # melting all Zones variables and all values of those zones variables in one column.
                id_vars = ['Time', 'Weather', 'File', property, f"{property}_old_value" ]
                print(id_vars)
                #print(result.columns)
                # selecting all zone:variables for setting them in just one column
                value_vars = [col for col in result.columns if col not in id_vars]
                # Customized Name of the column and value
                column_variable = 'Zone_Variable'
                column_values = 'Value'
                long_result = result.melt(id_vars=id_vars, 
                                            value_vars=value_vars, 
                                            var_name=column_variable, 
                                            value_name=column_values)
                # splitting Zone Name and Variable Name
                long_result = self.split_columns(long_result,column_variable,':','Zone','Variable')

            outpath_sql = self.get_file_output_path(folder_name,"eplusout.sql")
            if outpath_sql:
                #self.inspect_sqlite_schema(outpath_sql)
                geometry = self.get_general_geometry(outpath_sql)

                long_result = self.add_geometry_to_table(long_result,geometry)

                index_list = []
                all_properties = None
                if property:
                    all_properties = [property, f"{property}_old_value"]
                    index_list = ['File', 'Zone', 'Variable', 'Weather', 'Area', 'Volume' ] + all_properties

                pivoted = long_result.pivot_table(
                    index=index_list,
                    columns='Time', 
                    values='Value'
                    )
    
                reset_pivoted = pivoted.reset_index()
    
                reset_pivoted.to_csv(os.path.join(self.output_path,folder_name, 'epluszsz_mod.csv'), index=False)

        return reset_pivoted

    def add_geometry_to_table(self,table, geometry):

        table['Area'] = table['Zone'].map(
            lambda z: geometry.get(z, {}).get('Area', None) # type: ignore
            )

        table['Volume'] = table['Zone'].map(
            lambda z: geometry.get(z, {}).get('Volume', None) # type: ignore
            )

        table = table.drop(columns=['Zone_Variable'])
        
        return table

    def name_unifier(self,data):
        column_name_clean = []
        for col in data.columns:
            parts = col.split(':')
            # 1. Skip non-output columns like 'Time', 'weather', 'file', etc.
            if len(parts) <= 1:
                column_name_clean.append(col)
                
            # 2. Global/Site variables (e.g., "Environment:Site Outdoor Air... [C]")
            elif len(parts) == 2:
                # parts[0] is the environment name, parts[1] is the variable
                column_name_clean.append(parts[1])

            # If it matches the Zone:Environment:Variable structure (3+ parts)
            else:
                zone = parts[0]
                variable_and_units = ':'.join(parts[2:]) # handles any extra colons in variable names
                column_name_clean.append(f'{zone}:{variable_and_units}')
        data.columns = column_name_clean
        return data

    def clean_columns(self,data):
        zero_cols = data.columns[(data == 0).all(axis=0)]
        return data.drop(columns=zero_cols)

    def get_file_output_path(self,folder_name:str,file_name:str) -> Path | None:
        file_path = Path(os.path.join(self.output_path, folder_name, file_name))
        if not os.path.exists(file_path):
            print(f"{folder_name}/{file_name} file not found. Run a simulation first!")
            return None
        return file_path

    def inspect_sqlite_schema(self,output_dir):
        conn_eplus = sqlite3.connect(output_dir)
        cursor = conn_eplus.cursor()
        
        # Query all table names in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        # Loop through each table and print its columns
        for table in tables:
            table_name = table[0]
            print(f"\n Table: {table_name}")
            
            cursor.execute(f"PRAGMA table_info('{table_name}');")
            columns = cursor.fetchall()
            for col in columns:
                # col[1] is the column name, col[2] is the data type
                print(f"   - {col[1]} ({col[2]})")

        cursor.close()
        conn_eplus.close()

    def get_general_geometry(self,output_dir) -> dict:
        conn = sqlite3.connect(output_dir)
        cursor = conn.cursor()

        cursor.execute("SELECT ZoneName, FloorArea, Volume FROM Zones;")
        zones = cursor.fetchall()
        geo = dict()
        for zone,area,volume in zones:
            geo[zone]={'Area':area, 'Volume':volume}
        conn.close()

        # Ensure geometry is a valid dictionary (default to empty dict if None)
        geometry = geo if geo is not None else {}

        return geometry

    def split_columns(self,data,variable:str,symbol:str,name_1:str,name_2:str):
        split_cols = data[variable].str.split(symbol, n=1, expand=True)
        # 2. Safety check: ensure we actually got 2 columns back
        if split_cols.shape[1] < 2:
            split_cols[1] = "General_Variable" # Fallback if a header lacks a colon
        data[name_1] = split_cols[0]
        data[name_2] = split_cols[1]

        return data
    
