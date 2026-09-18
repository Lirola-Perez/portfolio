from sre_compile import isstring

import pandas as pd
import numpy as np
import sqlite3
import os

class DataProcess:

    def get_data(self,output_list,weather_name, idf_name, value_name, value):
        all_simulations = []
        
        for enum,var in enumerate(output_list):
            #print(enum, var)
            geometry= self.get_geometry_info(var)
            print(geometry)
            foutname = os.path.join(var,"epluszsz.csv")
            result = pd.read_csv(foutname)
            # Unifying names
            new_columns = self.name_unifier(result)
            result.columns = new_columns
            
            # Keeping only time-related rows
            result = result[result['Time'].astype(str).str.contains(':', na=False)]

            result['Weather'] = weather_name[enum]
            result['File'] = idf_name[enum]
            result[value_name[enum]] = value[enum]

            # MELTING keeping the anchor columns Time, weather, file.
            # melting all Zones variables and all values of those zones variables in one column.
            id_vars = ['Time', 'Weather', 'File', value_name[enum]]
            print(id_vars)
            value_vars = [col for col in result.columns if col not in id_vars]
            
            long_result = result.melt(id_vars=id_vars, value_vars=value_vars, var_name='Zone_Variable', value_name='Value')
            
            split_cols = long_result['Zone_Variable'].str.split(':', n=1, expand=True)
            print(split_cols)
            # 2. Safety check: ensure we actually got 2 columns back
            if split_cols.shape[1] < 2:
                print(split_cols)
                split_cols[1] = "General_Variable" # Fallback if a header lacks a colon
            long_result['Zone'] = split_cols[0]
            long_result['Variable'] = split_cols[1]

            # Ensure geometry is a valid dictionary (default to empty dict if None)
            safe_geometry = geometry if geometry is not None else {}

            long_result['Area'] = long_result['Zone'].map(
                lambda z: safe_geometry.get(z, {}).get('Area', None)
            )

            long_result['Volume'] = long_result['Zone'].map(
                            lambda z: safe_geometry.get(z, {}).get('Volume', None)
                        )

            long_result = long_result.drop(columns=['Zone_Variable'])

            pivoted = long_result.pivot_table(
                index=['File', 'Weather','Zone', 'Area', 'Volume', 'Variable',value_name[enum]],
                columns='Time', 
                values='Value'
                )

            pivoted.to_csv(os.path.join(var, 'epluszsz_mod.csv'), index=False)

            all_simulations.append(pivoted)

        master_df = pd.concat(all_simulations, axis=0)

        return master_df

    def name_unifier(self,result):
        new_columns = []
        for col in result.columns:
            parts = col.split(':')
            # 1. Skip non-output columns like 'Time', 'weather', 'file', etc.
            if len(parts) <= 1:
                new_columns.append(col)
                
            # 2. Global/Site variables (e.g., "Environment:Site Outdoor Air... [C]")
            elif len(parts) == 2:
                # parts[0] is the environment name, parts[1] is the variable
                new_columns.append(parts[1])

            # If it matches the Zone:Environment:Variable structure (3+ parts)
            else:
                zone = parts[0]
                variable_and_units = ':'.join(parts[2:]) # handles any extra colons in variable names
                new_columns.append(f'{zone}:{variable_and_units}')

        return new_columns

    def get_geometry_info(self,output_dir):
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

            return geo
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