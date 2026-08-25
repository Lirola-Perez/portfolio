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
    
    material_type = 'Material'
    material_name = 'INS - GLASS FIBER BONDED 3 IN'
    parameter_name = 'Thickness'
    thicknesses = [0.03, 0.10]
    parameter = [material_type, material_name, parameter_name, thicknesses]
    
    #file_list = changes.parametrization(parameter)

    output = e_proj_path + 'Eplusfiles/output/'
    file_a = idf_name + '_' + parameter_name + '_' + str(thicknesses[0]) + '.idf'
    file_b = idf_name + '_' + parameter_name + '_' + str(thicknesses[1]) + '.idf'
    file_list = [file_a, file_b]
    print(file_list)

    results_list = []
    for file_path in file_list:
        results = project.get_results(file_path)
        print(type(results))
        print(results.columns)

    

if __name__ == "__main__":
    main()

#materials = idf.idfobjects['MATERIAL']
#print(materials)

# pretty = pp.PrettyPrinter()
# pretty.pprint(results)