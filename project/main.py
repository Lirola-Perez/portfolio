from object.idf_class import idf_project
from object.idf_parametric import idf_parametric
import pprint as pp

# 1. Define paths to your local EnergyPlus installation
eplus_path = "/home/lirola/PROJECT/PORTFOLIO/energyplus/"
eplus_project_path = "/home/lirola/PROJECT/PORTFOLIO/project/Eplusfiles/"
project_name = 'MultiStory'
weather_name = 'Potsdam'

def main():
    project = idf_project(eplus_path,eplus_project_path,project_name,weather_name)
    
    material_type = 'Material'
    insulation = 'INS - GLASS FIBER BONDED 3 IN'
    thicknesses = [0.03, 0.06, 0.10, 0.20]
    changes = idf_parametric(project)

    changes.parametric_insulation(insulation, thicknesses)
    print(insulation)
    



if __name__ == "__main__":
    main()

#materials = idf.idfobjects['MATERIAL']
#print(materials)

# pretty = pp.PrettyPrinter()
# pretty.pprint(results)