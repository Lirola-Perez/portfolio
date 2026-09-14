from .idf_class import idf_project
from eppy.modeleditor import IDF
import sqlite3
import os
import pandas as pd

class idf_parametric():
    def __init__(self,idd_path, e_proj_folder, idf_names, epw_names):
         self.idfs = idf_names
         self.epws = epw_names
         self.idd = idd_path
         self.idf_path = e_proj_folder

    def parametrization(self,parameters:list):
        new_path_list, output_path_list, weather_list, idf_name_list, parameter_type_list, parameter_name_list, value_name_list, value_list = self.complete_path_list(parameters)
        print(new_path_list)
        for enum, new_path in enumerate(new_path_list):
            print(idf_name_list)
            project = idf_project(self.idd, self.idf_path, idf_name_list[enum], weather_list[enum])
            idf, epw_path, idd_path = project.get_idf()
            idf = project.set_idf_info(idf,new_path)
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

    

        