from .idf_class import idf_project
from eppy.modeleditor import IDF
import os
import pandas as pd

class idf_parametric():
    def __init__(self,idd_path, e_proj_folder, idf_names,epw_names):
         self.idfs = idf_names
         self.epws = epw_names
         self.idd = idd_path
         self.idf_path = e_proj_folder
        
    def parametrization(self,parameters:list) -> list:
        self.files_output = []
        for parameter in parameters:
            for weather_name in self.epws:
                idf_name, type, name, value_name, range_values = parameter
                project = idf_project(self.idd,self.idf_path,idf_name,weather_name)
                idf, epw_path, idd_path = project.get_idf(idf_name,weather_name)
                object = idf.getobject(type,name)
                print(object)
            
                for var in range_values:
                    object[value_name] = var
                    print(object)
                    new_path_name, output_dir = self.save_as_parameter(idf_name,value_name,var)
                    print(new_path_name)
                    print(idf)
                    idf.saveas(new_path_name)
                    print(epw_path,idd_path,output_dir)
                    idf.run(weather=epw_path,idd=idd_path, output_directory=output_dir)
                    #self.autorun(new_path_name)
                    self.files_output.append(output_dir)
                print(self.files_output)
        return self.files_output
            
    def save_as_parameter(self, idf_name, value_name, var):
            dir,_ = os.path.splitext(self.idf_path)
            new_name = idf_name + "_" + value_name + "_" + str(var)
            new_path = dir + "/" + new_name + ".idf"
            output_dir = dir + '/output/' + new_name + '/'
            return new_path, output_dir

    def get_data(self,output_list):
        column_list = []
        data_list = []
        
        for var in output_list:
            foutname = os.path.join(var,"epluszsz.csv")
            print(foutname)
            result = pd.read_csv(foutname)
            print(result)
            columns = result.columns
            data = result.iloc[1:]
            column_list.append(columns)
            data_list.append(data)
        return column_list, data_list
        