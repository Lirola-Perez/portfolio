import os
import sqlite3
from pathlib import Path
from sqlalchemy import column
from supabase import Client, create_client

import pandas as pd
import psycopg2
from postgres_connection import get_db_connection

DATABASE_URL = os.getenv("DATABASE_URL")

# Initialize Supabase Client
SUPABASE_URL: str = os.getenv("SUPABASE_URL") #type: ignore
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY") #type: ignore
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


class SimulationData:
    def __init__(self) -> None:
        self.output_bucket = "output"
        self.output_path = supabase.storage
        
    def worker(self):

        all_simulations = []

        while True:
            
            table = self.file_db_grabber()

            if table is None or not isinstance(table, pd.DataFrame):
               print("NO TABLE GRABBED!")
               break

            self.result_data_grabber(table)

            all_simulations.append(table)

        if not all_simulations:
            print("WARNING: Empty master data table or simulations already 'Processed'!")
            return pd.DataFrame()
        
        master_df = pd.concat(all_simulations, axis=0)
        self.save_master_df(master_df)
        #self.save_master_aux(master_df)

        column_names = [col for col in list(master_df.columns) if ":" not in str(col)]
        print(column_names)
        if column_names:
            self.save_in_supabase_storage("column_list.txt",column_names,output_bucket=self.output_bucket)

        return master_df

    def save_master_df(self, data:pd.DataFrame):
        if not data.empty:
            self.save_in_supabase_storage("master_training_data.parquet",data,self.output_bucket,data.to_parquet)

    def save_master_aux(self, data:pd.DataFrame):
            if not data.empty:
                self.save_in_supabase_storage("master_training_data.csv",data,self.output_bucket,data.to_csv)

    def save_in_supabase_storage(self,file_name:str,file_data,output_bucket:str,file_function=None):
        local_file_path = "data"
        if not file_data.empty:
            # 1. Save temporarily to local ephemeral storage (/tmp/)
            local_file_path = os.path.join("tmp",file_name)
            if file_function:
                file_function(local_file_path, index=False)
            else:
                with open(local_file_path, "wb") as f:
                    f.write(file_data)
            
            # 2. Read the local file and upload it to Supabase Storage
            with open(local_file_path, "rb") as f:
                self.output_path.from_(output_bucket).upload(
                    path=file_name,
                    file=f,
                    file_options={"upsert": "true"}  # Overwrite if it already exists
                )
            print(f"{file_name} uploaded successfully to Supabase bucket: {output_bucket}")
            
            # 3. Clean up the temporary local file
            if os.path.exists(local_file_path):
                os.remove(local_file_path)
        else:
            print(f"No new {local_file_path} in supabase generated.")

    def completed_data_grabber(self):

        try:
            with get_db_connection() as conn, conn.cursor() as cursor:
                
                # Using UPDATE for update status and retrieve vars
                # Using FOR UPDATE SKIP LOCKED to avoid conflict with other containers
                cursor.execute(
                    """UPDATE simulations SET status_simulation = 'Processed'
                    WHERE simulation_id = (
                    SELECT simulation_id FROM simulations 
                    WHERE status_simulation = 'Completed'
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED)
                    RETURNING simulation_id,idf_filename,batch_id,parameters_applied;"""
                )

                simulation_row = cursor.fetchone()

                if not simulation_row:
                    return None

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

        return simulation_row

    def result_data_grabber(self,results:pd.DataFrame):

        results_json = results.to_json(orient="records")
        #print(results_json)

        try:
            with get_db_connection() as conn, conn.cursor() as cursor:
            
                    # 1. Update the claimed row with BOTH the status AND the results JSON
                    cursor.execute(
                        """
                            UPDATE simulations 
                            SET status_simulation = 'Results', 
                                results = %s
                            WHERE simulation_id = (
                                SELECT simulation_id 
                                FROM simulations 
                                WHERE status_simulation = 'Processed'
                                LIMIT 1
                                FOR UPDATE SKIP LOCKED
                            );
                        """,
                        (results_json,),
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

    def file_db_grabber(self) -> pd.DataFrame | None:

        all_properties = []
        long_result = None
        simulation_data = self.completed_data_grabber()
        if simulation_data:
            _,folder_name,_,parameters = simulation_data
            outpath_csv = self.get_file_output_path(folder_name,"epluszsz.csv")
            #print(outpath_csv)
            property = str
            long_result = pd.DataFrame()
            if outpath_csv:
                result = pd.read_csv(outpath_csv)
                property = parameters["property"]
                #old_property = f"{property}_old_value"
                result['Weather'] = parameters["weather"]
                result['File'] = parameters["idf_file"]
                result[property] = parameters["property_value"]
                result[f"{property}_old_value"] = parameters[f"{property}_old_value"]
                print(property)
                # Other properties
                other_properties = parameters["other_properties"]
                other_values = parameters["other_values"]
                print(other_properties,other_values)

                if other_properties:
                    for enum,prop in enumerate(other_properties):
                        result[prop] = other_values[enum]

                # Unifying names
                result = self.name_unifier(result)

                # Keeping only time-related rows
                result = result[result['Time'].astype(str).str.contains(':', na=False)]

                # cleaning columns with only zeros
                result = self.clean_columns(result)

                all_properties = [property] + other_properties
                # MELTING keeping the anchor columns Time, weather, file.
                # melting all Zones variables and all values of those zones variables in one column.
                id_vars = ['Time', 'Weather', 'File' ] + all_properties
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

                long_result = self.preparing_table(long_result,all_properties)

                long_result = self.save_in_supabase_storage("epluszsz_mod.csv",long_result,self.output_bucket,long_result.to_scv)

                #long_result.to_csv(os.path.join(self.output_path,folder_name, 'epluszsz_mod.csv'), index=False)
            #print(long_result)
        return long_result

    def preparing_table(self,table, all_properties):

        index_list = ['File', 'Zone', 'Variable', 'Weather', 'Area', 'Volume' ] + all_properties

        pivoted = table.pivot_table(
            index=index_list,
            columns='Time', 
            values='Value'
            )

        reset_pivoted = pivoted.reset_index()

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

    def get_file_output_path(self,output_bucket,file_name:str):

        file_binary = supabase.storage.from_(output_bucket).download(file_name)

        # 1. Save temporarily to local ephemeral storage (/tmp/)
        local_file_path = os.path.join("/tmp", file_name)
        with open(local_file_path,'wb') as f:
            f.write(file_binary)

        return local_file_path

        # if not os.path.exists(file_path):
        #     print(f"{folder_name}/{file_name} file not found. Run a simulation first!")
        #     return None
        # return final_file_path

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
        geo = {}
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
    
