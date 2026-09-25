from textwrap import indent

from .idf_class import IdfProject
from eppy.modeleditor import IDF
import sqlite3
import os
import pandas as pd
from pathlib import Path
import json

class IdfParametric:
    def __init__(self,parameters):
        script_dir = Path(__file__).parent
        json_file_path = str(script_dir) + "/" + str(parameters)

        with open(json_file_path + ".json", "r") as f:
            self.parameters = json.load(f)
        self.epws = self.parameters["weather_names"]
        self.root = self.parameters["root_path"]
        self.output = self.root + "/output"
        self.all_properties = list(set([simulation["property"] for simulation in self.parameters["simulations"]]))

    def parametrization(self):

        simulations = self.parameters["simulations"]

        for weather in self.epws:
            for parameters in simulations:

                idf_name = parameters["idf_file"]
                type = parameters["type"]
                name = parameters["type_name"]
                property = parameters["property"]
                values = parameters["property_value"]
                
                for val in values:

                    project = IdfProject(self.root, idf_name, weather)
                    idf = project.get_idf(path="default")

                    run_folder = Path(f"{self.output}/{idf_name}_{weather}_{property}_{val}")
                    run_folder.mkdir(parents=True, exist_ok=True)

                    run_metadata = {
                        "idf_name": idf_name,
                        "weather": weather,
                        "parameter_type": type,
                        "parameter_name": name,
                        "property_name": property,
                        "value": val,
                        "all_properties": self.all_properties,
                        "output": str(run_folder)
                    }
                    
                    idf = project.set_idf_info(idf,run_folder)
                    new_idf_name = project.get_new_idf_name()
                    run_metadata["modified_idf_name"] = new_idf_name

                    # transformation: --------------
                    print(type, name)
                    object = idf.getobject(type, name)
                    old = []
                    for property in self.all_properties:
                        old_value = object[property] # type: ignore
                        old.append(old_value)

                    run_metadata["old_values"] = old
                    # new value:
                    object[property] = val # type: ignore
                    print(object)
                    print(run_metadata)

                    with open(run_folder / "parameter.json", "w") as f:
                        json.dump(run_metadata, f, indent=4)

                    new_path = os.path.join(run_folder, new_idf_name + ".idf")
                    idf.saveas(new_path)

    def run_all(self):
        outputs = self.output_pattern_reader("*_mod.idf",self.output)
        print(outputs)
        for weather in self.epws:
            for folder_path, file_name in outputs:
                print(folder_path)
                project = IdfProject(self.root, file_name, weather)
                idf = project.get_idf(folder_path)
                idd, idf_path, epw = project.get_paths(folder_path)
                print(idd,idf,epw)
                #epw_path = os.path.join(self.weather_path, weather + ".epw")
                idf.run(weather=epw,idd=idd,output_directory=folder_path)


    def output_pattern_reader(self,pattern:str,output:str) -> list[list]:
        output_data = []
        output_dir = Path(output)
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