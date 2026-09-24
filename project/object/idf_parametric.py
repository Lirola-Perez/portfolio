from textwrap import indent

from .idf_class import IdfProject
from eppy.modeleditor import IDF
import sqlite3
import os
import pandas as pd
from pathlib import Path
import json

class IdfParametric():
    def __init__(self,root, idf_names, epw_names):
        self.root = root
        self.idfs = idf_names
        self.epws = epw_names
        self.output = self.root +"/output"

    def parametrization(self,parameters:list):

        for weather in self.epws:
            for parameter in parameters:
                idf_name, type, name, property, values = parameter

                for val in values:

                    project = IdfProject(self.root, idf_name, weather)
                    idf = project.get_idf(path="default")

                    run_folder = Path(f"{self.output}/{idf_name}_{weather}_{property}_{val}")
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
                    
                    idf = project.set_idf_info(idf,run_folder)
                    new_idf_name = project.get_new_idf_name()
                    run_metadata["modified_idf_name"] = new_idf_name

                    # transformation: --------------
                    print(type, name)
                    object = idf.getobject(type, name)
                    old_value = object[property] # type: ignore
                    run_metadata["old_value"] = old_value
                    # new value:
                    object[property] = val # type: ignore
                    print(object)
                    print(run_metadata)

                    with open(run_folder / "parameter.json", "w") as f:
                        json.dump(run_metadata, f, indent=4)

                    new_path = os.path.join(run_folder, new_idf_name + ".idf")
                    idf.saveas(new_path)

    def run_all(self):
        outputs = self.output_pattern_reader("*_mod.idf")
        print(outputs)
        for weather in self.epws:
            for folder_name, file_name in outputs:
                print(folder_name)
                project = IdfProject(self.root, file_name, weather)
                idf = project.get_idf(folder_name)
                idd, idf_path, epw = project.get_paths(folder_name)
                print(idd,idf,epw)
                #epw_path = os.path.join(self.weather_path, weather + ".epw")
                idf.run(weather=epw,idd=idd,output_directory=folder_name)


    def output_pattern_reader(self,pattern:str) -> list[list]:
        output_data = []
        output_dir = Path(self.output)
        if output_dir.exists():
            for sub_dir in output_dir.iterdir():
                if sub_dir.is_dir():
                    # if this folder has a _mod.idf file inside it
                    mod_files = list(sub_dir.glob(pattern))
                    mod_file = mod_files[0].stem
                    print(mod_files)
                    if mod_files:
                        output_data.append((sub_dir, mod_file))
        return output_data

                
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

    

        