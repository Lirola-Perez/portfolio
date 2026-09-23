from textwrap import indent

from .idf_class import idf_project
from eppy.modeleditor import IDF
import sqlite3
import os
import pandas as pd
from pathlib import Path
import json

class idf_parametric():
    def __init__(self,idd_path, e_proj_folder, e_weather_folder, idf_names, epw_names):
         self.idfs = idf_names
         self.epws = epw_names
         self.idd = idd_path
         self.idf_path = e_proj_folder
         self.weather_path = e_weather_folder

    def parametrization(self,parameters:list):

        for weather in self.epws:
            for parameter in parameters:
                idf_name, type, name, property, values = parameter

                for val in values:
                    run_folder = Path(f"{self.idf_path}/output/{idf_name}_{weather}_{property}_{val}")
                    run_folder.mkdir(parents=True, exist_ok=True)

                    run_metadata = {
                        "idf_name": idf_name,
                        "parameter_type": type,
                        "parameter_name": name,
                        "property_name": property,
                        "value": val,
                        "old_value": 0,
                        "output": str(run_folder)
                    }

                    project = idf_project(self.idd, self.idf_path, idf_name, weather)
                    idf = project.get_idf()
                    idf, new_idf_name = project.set_idf_info(idf)
                    run_metadata["modified_idf_name"] = new_idf_name

                    # transformation: --------------
                    print(type, name)
                    object = idf.getobject(type, name)
                    print(object)
                    old_value = object[property] # type: ignore
                    run_metadata["old_value"] = old_value
                    # new value:
                    object[property] = val # type: ignore

                    with open(run_folder / "parameter.json", "w") as f:
                        json.dump(run_metadata, f, indent=4)

                    new_path = os.path.join(run_folder, new_idf_name + ".idf")
                    idf.saveas(new_path)

    def run_all(self):
        outputs = self.read_idf_folder()
        for weather in self.epws:
            for folder_name, file_name in outputs:
                project = idf_project(self.idd, folder_name, file_name, weather)
                idf = project.get_idf()
                idd_path, _, _ = project.get_paths()
                epw_path = os.path.join(self.weather_path, weather + ".epw")
                idf.run(weather=epw_path,idd=idd_path,output_directory=folder_name)
                    
    def read_idf_folder(self):
        run_folders = []
        output_dir = Path(f"{self.idf_path}/output/")
        if output_dir.exists():
            for sub_dir in output_dir.iterdir():
                if sub_dir.is_dir():
                    # if this folder has a _mod.idf file inside it
                    mod_files = list(sub_dir.glob("*_mod.idf"))
                    mod_file = mod_files[0].stem
                    print(mod_files)
                    if mod_files:
                        run_folders.append((sub_dir, mod_file))
        return run_folders

                
        # new_path_list, output_path_list, weather_list, idf_name_list, parameter_type_list, parameter_name_list, value_name_list, value_list, old_value_list = self.complete_path_list(parameters)
        # print(new_path_list)
        # print(old_value_list)
        # for enum, new_path in enumerate(new_path_list):
        #     print(idf_name_list)
        #     project = idf_project(self.idd, self.idf_path, idf_name_list[enum], weather_list[enum])
        #     idf, epw_path, idd_path = project.get_idf()
        #     idf = project.set_idf_info(idf,new_path)
        #     # transformation: --------------
        #     object = idf.getobject(parameter_type_list[enum], parameter_name_list[enum])
        #     old_value_list[enum] = object[value_name_list[enum]] # type: ignore
        #     #print(old_value_list)
        #     object[value_name_list[enum]] = value_list[enum] # type: ignore
        #     #print(object)
        #     #print(old_value_list)
        #     # ------------------------------
        #     idf.saveas(new_path)
        #     idf.run(weather=epw_path,idd=idd_path,output_directory=output_path_list[enum])

        # return output_path_list, weather_list, idf_name_list, value_name_list, value_list, old_value_list

    # def complete_path_list(self,parameters:list):
    #     new_path_list = []
    #     output_path_list = []
    #     weather_name_list = []
    #     idf_name_list = []
    #     parameter_type_list = []
    #     parameter_name_list = []
    #     value_name_list = []
    #     value_list = []
    #     old_value_list = []
    #     for parameter in parameters:
    #         for weather_name in self.epws:
    #             idf_name, type, name, property, values = parameter
    #             for var in values:
    #                 new_path, output_dir = self.save_as_parameter(idf_name, weather_name, property, var)
    #                 new_path_list.append(new_path)
    #                 output_path_list.append(output_dir)
    #                 weather_name_list.append(weather_name)
    #                 idf_name_list.append(idf_name)
    #                 parameter_type_list.append(type)
    #                 parameter_name_list.append(name)
    #                 value_name_list.append(property)
    #                 value_list.append(var)
    #                 old_value_list.append(999)
    #     return new_path_list, output_path_list, weather_name_list, idf_name_list, parameter_type_list, parameter_name_list, value_name_list, value_list, old_value_list
            
    # def save_as_parameter(self, idf_name:str, weather:str, property:str, value):
    #         dir,_ = os.path.splitext(self.idf_path)
    #         new_name = idf_name + "_" + weather + "_" + property + "_" + str(value)
    #         new_path = dir + "/" + new_name + ".idf"
    #         output_dir = dir + '/output/' + new_name + '/'
    #         return new_path, output_dir

    

        