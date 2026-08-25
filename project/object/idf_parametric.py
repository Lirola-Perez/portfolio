import os
from eppy.modeleditor import IDF

class idf_parametric():
    def __init__(self,idf_project):
        self.idf = idf_project.get_idf()
        self.dir = idf_project.idf_path
        self.epw = idf_project.epw_path
        self.idd = idf_project.idd
        self.out = idf_project.out_path
        
    def parametrization(self,parameters:list):
        type, name, self.parameter, range_values = parameters  
        object = self.get_object(type,name)

        for var in range_values:
            object[self.parameter] = var
            new_path_name = self.do_saveas_param(var)
            self.autorun(new_path_name)
            
    def do_saveas_param(self, var) -> str:
            dir,_ = os.path.splitext(self.dir)
            new_name = dir + "_" + self.parameter + "_" + str(var) + ".idf"
            print(new_name)
            self.idf.saveas(new_name)
            return new_name

    def autorun(self,idf_name:str):
        dir,name_file = os.path.split(idf_name)
        name,_ = os.path.splitext(name_file)
        output_dir = dir + '/output/' + name + '/'
        idf = IDF(idf_name,self.epw)
        idf.run(weather=self.epw,idd=self.idd,output_directory=output_dir)

    def get_object(self,type:str,name:str):
        got_object = self.idf.getobject(type,name)
        return got_object