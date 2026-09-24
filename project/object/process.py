from enum import unique
from sre_compile import isstring
from .idf_parametric import IdfParametric as param

import pandas as pd
import numpy as np
import sqlite3
import os

class DataProcess:

    def get_data(self,output_list,weather_name, idf_name, value_name, value, old_value_list):
        all_simulations = []

        compress_value_name = list(set(value_name))
        compress_old_value = list(set(old_value_list))

        for enum,var in enumerate(output_list):
        
            foutname = os.path.join(var,"epluszsz.csv")
            result = pd.read_csv(foutname)

            for param_name, default_val in zip(compress_value_name, compress_old_value):  # or your baseline values
                if param_name not in result.columns:
                    result[param_name] = (default_val)

            result['Weather'] = weather_name[enum]
            result['File'] = idf_name[enum]
            result[value_name[enum]] = value[enum]
            #print(result[value_name[enum]], value[enum])

            # Unifying names
            result = self.name_unifier(result)
            
            # Keeping only time-related rows
            result = result[result['Time'].astype(str).str.contains(':', na=False)]

            # cleaning columns with only zeros
            result = self.clean_columns(result)

            # MELTING keeping the anchor columns Time, weather, file.
            # melting all Zones variables and all values of those zones variables in one column.
            id_vars = ['Time', 'Weather', 'File']
            for parameter_name in list(set(value_name)):
                id_vars.append(parameter_name)
            print(id_vars)
            #print(result.columns)
            #print(result)
            value_vars = [col for col in result.columns if col not in id_vars]

            column_variable = 'Zone_Variable'
            column_values = 'Value'
            long_result = result.melt(id_vars=id_vars, 
                                      value_vars=value_vars, 
                                      var_name=column_variable, 
                                      value_name=column_values)

            long_result = self.split_columns(long_result,column_variable,':','Zone','Variable')

            geometry= self.get_general_geometry(var)
            # print(geometry)

            long_result['Area'] = long_result['Zone'].map(
                lambda z: geometry.get(z, {}).get('Area', None) # type: ignore
                )

            long_result['Volume'] = long_result['Zone'].map(
                lambda z: geometry.get(z, {}).get('Volume', None) # type: ignore
                )

            long_result = long_result.drop(columns=['Zone_Variable'])

            id_vars.append('Area')
            id_vars.append('Volume')
            id_vars.append('Zone')
            id_vars.append('Variable')
            value_n = list(set(value_name))
            index_list = ['File', 'Weather','Zone', 'Area', 'Volume', 'Variable'] + value_n
            print(index_list)
            pivoted = long_result.pivot_table(
                index=index_list,
                columns='Time', 
                values='Value'
                )

            reset_pivoted = pivoted.reset_index()

            reset_pivoted.to_csv(os.path.join(var, 'epluszsz_mod.csv'), index=False)

            all_simulations.append(reset_pivoted)

        master_df = pd.concat(all_simulations, axis=0)

        return master_df

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

    def get_general_geometry(self,output_dir):
        # self.inspect_sqlite_schema(output_dir)
        sql_path = self.get_sql_output_path(output_dir)

        if sql_path:
            conn = sqlite3.connect(sql_path)
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
        else:
            print(f'failed to get geometry from eplusout.sql {output_dir}')

    def inspect_sqlite_schema(self,output_dir):
        sql_path = self.get_sql_output_path(output_dir)
        if sql_path:
            conn = sqlite3.connect(sql_path)
            cursor = conn.cursor()
            
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
                
            conn.close()
        else:
            print(f'failed to inspect eplusout.sql {output_dir}')

    def get_sql_output_path(self,output_dir:str) -> str | None:
        sql_path = os.path.join(output_dir, "eplusout.sql")
        if not os.path.exists(sql_path):
            print("SQLite file not found. Run a simulation first!")
            return None
        return sql_path

    def clean_columns(self,data):
        zero_cols = data.columns[(data == 0).all(axis=0)]
        return data.drop(columns=zero_cols)

    def split_columns(self,data,variable:str,symbol:str,name_1:str,name_2:str):
        split_cols = data[variable].str.split(symbol, n=1, expand=True)
        # 2. Safety check: ensure we actually got 2 columns back
        if split_cols.shape[1] < 2:
            split_cols[1] = "General_Variable" # Fallback if a header lacks a colon
        data[name_1] = split_cols[0]
        data[name_2] = split_cols[1]

        return data
