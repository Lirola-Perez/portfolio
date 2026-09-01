from eppy.modeleditor import IDF
from eppy.results import readhtml
import numpy as np
import pandas as pd
import os

class idf_project(IDF):
    def __init__(self,e_path:str,e_idf_folder:str,idf_name:str,epw_name:str):
        super().__init__()
        self.idd = e_path
        self.projects = e_idf_folder

    def get_idf(self,idf_name,epw_name):
        idf_path = os.path.join(self.projects, idf_name + ".idf")
        epw_path = os.path.join(self.projects, "weather/", epw_name + ".epw")
        idd_path = os.path.join(self.idd, "Energy+.idd")
        # 2. Set the IDD version so eppy knows how to parse it
        print(idf_path,epw_path)
        print(self.idd)
        IDF.setiddname(idd_path)
        # 3. Load your IDF model
        self.idf = IDF(idfname=idf_path, epw=epw_path)
        print("IDF loaded successfully using eppy!")
        return self.idf, epw_path, idd_path

    def get_info_eppy(self):
        zones = self.idf.idfobjects['ZONE']
        for zone in zones:
            print(f"Zone Name: {zone.Name}")
            print(f"  - Ceiling Height: {zone.Ceiling_Height}")
            print(f"  - Volume: {zone.Volume}")
        surfaces = self.idf.idfobjects['BUILDINGSURFACE:DETAILED']
        total_wall_area = 0.0
        total_floor_area = 0.0
        for surface in surfaces:
            if surface.Surface_Type == 'Wall':
                print(f"Wall: {surface.Name}, Area: {surface.Zone_Name}")

        windows = self.idf.idfobjects['FENESTRATIONSURFACE:DETAILED']
        for win in windows:
            print(f"Window: {win.Name}, Parent Surface: {win.Building_Surface_Name}")
            
    def get_results(self,file:str):
        self.out_path = os.path.join(self.projects, "output/")
        _,file_name = os.path.split(file)
        name, _ = os.path.splitext(file_name)
        foutname = os.path.join(self.out_path,name,"epluszsz.csv")
        print('final path: ',foutname)
        # PANDAS DataFrame Structure
        result = pd.read_csv(foutname)
        return result