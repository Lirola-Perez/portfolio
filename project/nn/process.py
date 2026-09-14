import pandas as pd
import numpy as np
import sqlite3
import os


class DataProcess:

    def get_data(self,output_list,weather_name, idf_name,value_name, value):
        all_simulations = []
        
        for enum,var in enumerate(output_list):
            #print(enum, var)
            geometry_info = self.get_geometry_info(var)
            #print(geometry_info)
            foutname = os.path.join(var,"epluszsz.csv")
            result = pd.read_csv(foutname)

            result['weather'] = weather_name[enum]
            result['file'] = idf_name[enum]
            result[value_name[enum]] = value[enum]
            #print(result)
            all_simulations.append(result)
            #print(all_simulations)
        master_df = pd.concat(all_simulations, ignore_index=True)
        return master_df

    def get_geometry_info(self,output_dir):
        self.inspect_sqlite_schema(output_dir)
        sql_path = os.path.join(output_dir, "eplusout.sql")
        if not os.path.exists(sql_path):
            return None
        
        conn = sqlite3.connect(sql_path)
        cursor = conn.cursor()

        cursor.execute("SELECT ZoneName, FloorArea, Volume FROM Zones;")
        zones = cursor.fetchall()

        conn.close()
        return zones

    def inspect_sqlite_schema(self,output_dir):
        sql_path = os.path.join(output_dir, "eplusout.sql")
        if not os.path.exists(sql_path):
            print("SQLite file not found. Run a simulation first!")
            return
            
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