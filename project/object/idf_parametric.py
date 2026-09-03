from .idf_class import idf_project
from eppy.modeleditor import IDF
import sqlite3
import os
import pandas as pd

class idf_parametric():
    def __init__(self,idd_path, e_proj_folder, idf_names,epw_names):
         self.idfs = idf_names
         self.epws = epw_names
         self.idd = idd_path
         self.idf_path = e_proj_folder

    def parametrization(self,parameters:list):
        new_path_list, output_path_list, weather_list, idf_name_list, parameter_type_list, parameter_name_list, value_name_list, value_list = self.complete_path_list(parameters)
        for enum, new_path in enumerate(new_path_list):
            project = idf_project(self.idd, self.idf_path, idf_name_list[enum], weather_list[enum])
            idf, epw_path, idd_path = project.get_idf(idf_name_list[enum],weather_list[enum])
            # transformation: --------------
            object = idf.getobject(parameter_type_list[enum], parameter_name_list[enum])
            object[value_name_list[enum]] = value_list[enum] # type: ignore
            print(object)
            # ------------------------------
            idf.saveas(new_path)
            idf.run(weather=epw_path,idd=idd_path,output_directory=output_path_list[enum])
        return output_path_list, weather_list, idf_name_list, value_name_list, value_list

    def complete_path_list(self,parameters:list):
        new_path_list = []
        output_path_list = []
        weather_name_list = []
        idf_name_list = []
        parameter_type_list = []
        parameter_name_list = []
        value_name_list = []
        value_list = []
        for parameter in parameters:
            for weather_name in self.epws:
                idf_name, type, name, value_name, range_values = parameter
                for var in range_values:
                    new_path, output_dir = self.save_as_parameter(idf_name, weather_name, value_name, var)
                    new_path_list.append(new_path)
                    output_path_list.append(output_dir)
                    weather_name_list.append(weather_name)
                    idf_name_list.append(idf_name)
                    parameter_type_list.append(type)
                    parameter_name_list.append(name)
                    value_name_list.append(value_name)
                    value_list.append(var)
        return new_path_list, output_path_list, weather_name_list, idf_name_list, parameter_type_list, parameter_name_list, value_name_list, value_list
            
    def save_as_parameter(self, idf_name:str, weather:str, value_name:str, value):
            dir,_ = os.path.splitext(self.idf_path)
            new_name = idf_name + "_" + weather + "_" + value_name + "_" + str(value)
            new_path = dir + "/" + new_name + ".idf"
            output_dir = dir + '/output/' + new_name + '/'
            return new_path, output_dir

    # def get_geometry_info(self,output_dir):
    #     sql_path = os.path.join(output_dir, "eplusout.sql")
    #     if not os.path.exists(sql_path):
    #         return None
        
    #     conn = sqlite3.connect(sql_path)
    #     cursor = conn.cursor()

    #     cursor.execute("SELECT ZoneName, FloorArea, Volume FROM Zones;")
    #     zones = cursor.fetchall()

    #     conn.close()
    #     return zones

    # def get_data(self,output_list,weather_name, idf_name,value_name, value):
    #     all_simulations = []
        
    #     for enum,var in enumerate(output_list):
    #         geometry_info = self.get_geometry_info(var)
    #         print(geometry_info)
    #         foutname = os.path.join(var,"epluszsz.csv")
    #         result = pd.read_csv(foutname)

    #         result['weather'] = weather_name[enum]
    #         result['file'] = idf_name[enum]
    #         result[value_name[enum]] = value[enum]

    #         all_simulations.append(result)
    #     master_df = pd.concat(all_simulations, ignore_index=True)
    #     return master_df
        