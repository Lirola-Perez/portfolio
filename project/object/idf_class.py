from eppy.modeleditor import IDF
from eppy.results import readhtml
import os

class idf_project(IDF):
    def __init__(self,e_path,e_proj_path,idf_name,epw_name):
        super().__init__()
        self.idd = os.path.join(e_path, "Energy+.idd")
        self.idf_path = os.path.join(e_proj_path, "Eplusfiles/" + idf_name + ".idf")
        self.epw_path = os.path.join(e_proj_path, "Eplusfiles/weather/", epw_name + ".epw")
        self.out_path = os.path.join(e_proj_path, "Eplusfiles/output/")

    def get_idf(self):
        # 2. Set the IDD version so eppy knows how to parse it
        IDF.setiddname(self.idd)
        # 3. Load your IDF model
        self.idf = IDF(self.idf_path, self.epw_path)
        print("IDF loaded successfully using eppy!")
        return self.idf

    def get_run(self):
        self.idf.run(weather=self.epw_path,idd=self.idd,output_directory=self.out_path)
        print(f'Run successfully. Results in {self.out_path}')

    def results(self):
        foutname = os.path.join(self.out_path,"eplustbl.htm")
        # get a file handle to the html file
        filehandle = open(foutname, 'r').read()
        results =readhtml.titletable(filehandle)
        return results

    def do_saveas(self):
        dir_name,ext = os.path.splitext(self.idf_path)
        new_name = os.path.join(dir_name + "_copy.idf")
        self.idf.saveas(new_name)

    def get_type(self,name:str):
        return self.idf.idfobjects[name]

    def get_object(self,type:str,name:str):
        return self.idf.getobject(type,name)
