from object.idf_class import idf_project
from object.idf_parametric import idf_parametric
import pandas as pd
import numpy as np
import pprint as pp

# 1. Define paths to your local EnergyPlus installation
e_path = "/home/lirola/PROJECT/PORTFOLIO/energyplus"
e_proj_path = "/home/lirola/PROJECT/PORTFOLIO/project/"
idf_name = 'MultiStory'
epw_name = 'Potsdam'

def main():
    project = idf_project(e_path,e_proj_path,idf_name,epw_name)
    changes = idf_parametric(project)
    
    parameter_type = 'Material'
    parameter_name = 'INS - GLASS FIBER BONDED 3 IN'
    value_name = 'Thickness'
    values = [0.03, 0.10]
    parameter = [parameter_type, parameter_name, value_name, values]
    
    #file_list = changes.parametrization(parameter)
    file_list = ['/home/lirola/PROJECT/PORTFOLIO/project/Eplusfiles/MultiStory_Thickness_0.03.idf', '/home/lirola/PROJECT/PORTFOLIO/project/Eplusfiles/MultiStory_Thickness_0.1.idf']
    result_columns, result_data = changes.get_data(file_list)
    print(result_columns, result_data)


if __name__ == "__main__":
    main()

#materials = idf.idfobjects['MATERIAL']
#print(materials)

# pretty = pp.PrettyPrinter()
# pretty.pprint(results)