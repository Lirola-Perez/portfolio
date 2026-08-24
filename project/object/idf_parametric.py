#from idf_class import idf_project
import os
from eppy.modeleditor import IDF
#from project.object.idf_class import idf_project

class idf_parametric():
    def __init__(self,idf_project):
        self.idf_project = idf_project
        
    def parametric_insulation(self,material_name:str, thickness:list):
        self.idf = self.idf_project.get_idf()
        dir_name = self.idf_project.idf_path
        #print(dir_name)
        #print(self.idf)
        material_type = 'Material'
        
        insulation = self.idf.getobject(material_type,material_name)
        print(insulation)
        for thick in thickness:
            insulation.Thickness = thick
            self.do_saveas_param(thick,dir_name)

    def do_saveas_param(self, var, dir):
            dir_name,ext = os.path.splitext(dir)
            #print(dir_name,ext)
            new_name = dir_name + "_" + str(var) + ".idf"
            print(new_name)
            self.idf.saveas(new_name)

    def result_read(self,name):
        pass

    def get_object(self,name):
        pass