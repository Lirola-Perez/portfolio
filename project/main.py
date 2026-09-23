# %%
from object.idf_class import idf_project
from object.idf_parametric import idf_parametric
from object.process import DataProcess
from nn.data_preparation import Input

# 1. Define paths to your local EnergyPlus installation
e_idd_path = "/home/lirola/PROJECT/PORTFOLIO/energyplus"
e_idf_folder = "/home/lirola/PROJECT/PORTFOLIO/project/Eplusfiles"
e_weather_folder = "/home/lirola/PROJECT/PORTFOLIO/project/Eplusfiles/weather"
idf_names_original = [
    'MultiStory',
    'LBuilding-G000'
    ]
epw_names = [
    'Potsdam',
    'Madrid'
    ]

def main():
    idf_names = []
    for idf_file in idf_names_original:
        idf_names.append(idf_file)

    projects = idf_parametric(e_idd_path, e_idf_folder, e_weather_folder, idf_names, epw_names)
    
    parameter_type = ['Material']
    parameter_name = [
        'INS - GLASS FIBER BONDED 3 IN',
        'HF-E5'
        ]
    parameter_values = [
        ['Thickness', 0.03, 0.12]
        #['Conductivity', 0.024, 0.04]
        ]
    parameter = [
        [idf_names[0], parameter_type[0], parameter_name[0], parameter_values[0][0], parameter_values[0][1:]],
        [idf_names[1], parameter_type[0], parameter_name[1], parameter_values[0][0], parameter_values[0][1:]]
        #[idf_names[0], parameter_type[0], parameter_name[0], parameter_values[1][0], parameter_values[1][1:]],
        #[idf_names[1], parameter_type[0], parameter_name[1], parameter_values[1][0], parameter_values[1][1:]]
        ]

    #projects.parametrization(parameter)
    projects.run_all()
    
    #output_path_list, weather_list, idf_name_list, value_name_list, value_list, old_value_list = projects.parametrization(parameter)

    #new_path_list, output_path_list, weather_list, idf_name_list, parameter_type_list, parameter_name_list, value_name_list, value_list, old_value_list = projects.complete_path_list(parameter)
    #print(f'Variables to check: {value_name_list} \n {vSalue_list} \n {old_value_list}')

    #print(output_path_list)
    # data = DataProcess()
    # master_df = data.get_data(output_path_list, weather_list, idf_name_list,value_name_list, value_list, old_value_list)
    # #print(master_df)
    # master_df.info()

    # # df = Input(master_df)
    # # df.one_hot()

    # # print(df)
    # return master_df

if __name__ == "__main__":
    main()
    #print(data)

#materials = idf.idfobjects['MATERIAL']
#print(materials)

# pretty = pp.PrettyPrinter()
# pretty.pprint(results)

# %%
