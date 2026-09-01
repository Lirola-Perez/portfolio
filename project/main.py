from object.idf_class import idf_project
from object.idf_parametric import idf_parametric
import pandas as pd
import numpy as np
import pprint as pp

# 1. Define paths to your local EnergyPlus installation
e_idd_path = "/home/lirola/PROJECT/PORTFOLIO/energyplus"
e_idf_folder = "/home/lirola/PROJECT/PORTFOLIO/project/Eplusfiles"
idf_names = ['MultiStory']
epw_names = ['Potsdam','Madrid']

def main():
    #projects = idf_projects(e_idd_path,e_idf_folder,idf_names,epw_names)
    projects = idf_parametric(e_idd_path, e_idf_folder, idf_names, epw_names)
    
    parameter_type = 'Material'
    parameter_name = 'INS - GLASS FIBER BONDED 3 IN'
    parameter_values = [['Thickness', 0.03, 0.12], ['Conductivity', 0.024, 0.04]]
    parameter = [[idf_names[0], parameter_type, parameter_name, parameter_values[0][0], parameter_values[0][1:]],[idf_names[0], parameter_type, parameter_name, parameter_values[1][0], parameter_values[1][1:]]]
    
    output_path_list, weather_list, idf_name_list, value_name_list, value_list = projects.parametrization(parameter)
    #output_path_list = ['/home/lirola/PROJECT/PORTFOLIO/project/Eplusfiles/output/MultiStory_Madrid_Thickness_0.03/', '/home/lirola/PROJECT/PORTFOLIO/project/Eplusfiles/output/MultiStory_Potsdam_Thickness_0.1/']
    master_df = projects.get_data(output_path_list, weather_list, idf_name_list,value_name_list, value_list)
    #print(result_columns, result_data)
    master_df.info()


if __name__ == "__main__":
    main()

#materials = idf.idfobjects['MATERIAL']
#print(materials)

# pretty = pp.PrettyPrinter()
# pretty.pprint(results)