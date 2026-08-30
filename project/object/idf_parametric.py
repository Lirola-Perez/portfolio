import enum
import os
from eppy.modeleditor import IDF

class idf_parametric():
    def __init__(self,idf_project):
        self.project = idf_project
        self.idf = idf_project.get_idf()
        
    def parametrization(self,parameters:list) -> list:
        type, name, self.vaue_name, self.range_values = parameters
        object = self.get_object(type,name)
        print(object)
        self.files_param = []

        for var in self.range_values:
            object[self.vaue_name] = var
            new_path_name = self.do_saveas_param(var)
            self.autorun(new_path_name)
            self.files_param.append(new_path_name)
        print(self.files_param)
        return self.files_param
            
    def do_saveas_param(self, var) -> str:
            dir,_ = os.path.splitext(self.project.idf_path)
            new_name = dir + "_" + self.vaue_name + "_" + str(var) + ".idf"
            print(new_name)
            self.idf.saveas(new_name)
            return new_name

    def autorun(self,idf_name:str):
        dir,name_file = os.path.split(idf_name)
        name,_ = os.path.splitext(name_file)
        output_dir = dir + '/output/' + name + '/'
        idf = IDF(idf_name,self.project.epw_path)
        idf.run(weather=self.project.epw_path,idd=self.project.idd,output_directory=output_dir)

    def get_object(self,type:str,name:str):
        got_object = self.idf.getobject(type,name)
        return got_object

    def get_data(self,file_list):
        column_list = []
        data_list = []
        for var in file_list:
            print(var)
            results = self.project.get_results(var)
            #print(results)
            columns = results.columns
            data = results.iloc[1:]
            column_list.append(columns)
            data_list.append(data)
        return column_list, data_list
        