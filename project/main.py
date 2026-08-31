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
    value_name = 'Thickness'
    value_name_1 = 'Conductivity'
    values = [0.03, 0.10]
    #parameter = [[idf_names[0], parameter_type, parameter_name, value_name, values]]
    parameter = [[idf_names[0], parameter_type, parameter_name, value_name, values],[idf_names[0], parameter_type, parameter_name, value_name_1, values]]
    
    output_path_list = projects.parametrization(parameter)
    #output_path_list = ['/home/lirola/PROJECT/PORTFOLIO/project/Eplusfiles/output/MultiStory_Madrid_Thickness_0.03/', '/home/lirola/PROJECT/PORTFOLIO/project/Eplusfiles/output/MultiStory_Potsdam_Thickness_0.1/']
    result_columns, result_data = projects.get_data(output_path_list)
    print(result_columns, result_data)


if __name__ == "__main__":
    main()

#materials = idf.idfobjects['MATERIAL']
#print(materials)

# pretty = pp.PrettyPrinter()
# pretty.pprint(results)