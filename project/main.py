# %%
from object.idf_class import idf_project
from object.idf_parametric import idf_parametric
import pandas as pd
import numpy as np
import pprint as pp

from nn.process import DataProcess

# 1. Define paths to your local EnergyPlus installation
e_idd_path = "/home/lirola/PROJECT/PORTFOLIO/energyplus"
e_idf_folder = "/home/lirola/PROJECT/PORTFOLIO/project/Eplusfiles"
idf_names_original = ['MultiStory','LBuilding-G000']
epw_names = ['Potsdam','Madrid']

def main():
    idf_names = []
    for idf_file in idf_names_original:
        project = idf_project(e_idd_path,e_idf_folder,idf_file,epw_names[0])
        idf_name = project.get_idf_info()
        idf_names.append(idf_name)


    projects = idf_parametric(e_idd_path, e_idf_folder, idf_names, epw_names)
    
    parameter_type = 'Material'
    parameter_name = 'INS - GLASS FIBER BONDED 3 IN'
    parameter_name_1 = 'HF-E5'
    parameter_values = [['Thickness', 0.03, 0.12], ['Conductivity', 0.024, 0.04]]
    parameter = [[idf_names[0], parameter_type, parameter_name, parameter_values[0][0], parameter_values[0][1:]],[idf_names[0], parameter_type, parameter_name, parameter_values[1][0], parameter_values[1][1:]],[idf_names[1],parameter_type,parameter_name_1,parameter_values[1][0],parameter_values[1][1:]]]
    
    #output_path_list, weather_list, idf_name_list, value_name_list, value_list = projects.parametrization(parameter)

    new_path_list, output_path_list, weather_list, idf_name_list, parameter_type_list, parameter_name_list, value_name_list, value_list = projects.complete_path_list(parameter)

    #print(output_path_list)
    data = DataProcess()
    master_df = data.get_data(output_path_list, weather_list, idf_name_list,value_name_list, value_list)
    print(master_df)
    #print(result_columns, result_data)
    master_df.info()

    # # See all active variables in memory
    # for name, val in list(globals().items()):
    #     if not name.startswith('_'):
    #         print(f"{name}: {type(val)}")

    return master_df

if __name__ == "__main__":
    master_df = main()
    #print(data)

#materials = idf.idfobjects['MATERIAL']
#print(materials)

# pretty = pp.PrettyPrinter()
# pretty.pprint(results)

# %%
