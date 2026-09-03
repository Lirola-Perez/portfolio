import pandas as pd
import numpy as np
import sqlite3
import os


class DataProcess:

    def get_data(self,output_list,weather_name, idf_name,value_name, value):
        all_simulations = []
        
        for enum,var in enumerate(output_list):
            geometry_info = self.get_geometry_info(var)
            print(geometry_info)
            foutname = os.path.join(var,"epluszsz.csv")
            result = pd.read_csv(foutname)

            result['weather'] = weather_name[enum]
            result['file'] = idf_name[enum]
            result[value_name[enum]] = value[enum]

            all_simulations.append(result)
        master_df = pd.concat(all_simulations, ignore_index=True)
        return master_df

    def get_geometry_info(self,output_dir):
        sql_path = os.path.join(output_dir, "eplusout.sql")
        if not os.path.exists(sql_path):
            return None
        
        conn = sqlite3.connect(sql_path)
        cursor = conn.cursor()

        cursor.execute("SELECT ZoneName, FloorArea, Volume FROM Zones;")
        zones = cursor.fetchall()

        conn.close()
        return zones