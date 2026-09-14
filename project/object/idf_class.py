from eppy.modeleditor import IDF
import os

class idf_project(IDF):
    def __init__(self,e_path:str,e_idf_folder:str,idf_name:str,epw_name:str):
        super().__init__()
        self.idd = e_path
        self.projects = e_idf_folder
        self.idf_name = idf_name
        self.epw_name = epw_name

    def get_idf(self):
        idd_path, idf_path, epw_path = self.get_paths()
        # 2. Set the IDD version so eppy knows how to parse it
        print(f' IDD: {idd_path} \n IDF: {idf_path} \n EPW: {epw_path} ')
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

    def get_paths(self):
        idf_path = os.path.join(self.projects, self.idf_name + '.idf')
        epw_path = os.path.join(self.projects, "weather/", self.epw_name + ".epw")
        idd_path = os.path.join(self.idd, "Energy+.idd")
        return idd_path, idf_path, epw_path

    def set_idf_info(self,idf,path):
        # new_name = self.idf_name + '_mod'
        # new_idf = os.path.join(self.projects, new_name + '.idf')
        timestep = idf.idfobjects['Timestep'][0]
        if timestep.Number_of_Timesteps_per_Hour != 6:
            timestep.Number_of_Timesteps_per_Hour = 6
            print(timestep)

        sim_control = idf.idfobjects['SIMULATIONCONTROL'][0]
        print(f'Do Zone Sizing Calculation: {sim_control.Do_Zone_Sizing_Calculation}')

        if sim_control.Do_System_Sizing_Calculation.lower() == 'no':
            sim_control.Do_System_Sizing_Calculation='YES'
        print(f'Do System Sizing Calculation: {sim_control.Do_System_Sizing_Calculation}')
        
        if sim_control.Run_Simulation_for_Sizing_Periods.lower() == 'no':
            sim_control.Run_Simulation_for_Sizing_Periods='YES'
        print(f'Run Simulation for Sizing Periods: {sim_control.Run_Simulation_for_Sizing_Periods}')

        print(f'Run Simulation for Weather File Run Periods: {sim_control.Run_Simulation_for_Weather_File_Run_Periods}')

        filtered = self.key_filter('Output:Variable')
        for item in filtered:
            idf.idfobjects[item].clear()
            print(idf.idfobjects[item])
        output_list = [
            'Site Outdoor Air Drybulb Temperature', 
            'Zone Outdoor Air Drybulb Temperature', 
            'Site Outdoor Air Wetbulb Temperature', 
            'Site Wind Speed', 
            'Zone Outdoor Air Wind Speed', 
            'Zone Air Temperature', 
            'Zone Air System Sensible Heating Energy', 
            'Zone Air System Sensible Cooling Energy'
            ]
        self.output_object_generator(output_list)
        idf.saveas(path)
        return idf

    def key_filter(self,word:str) -> list:
        key_filtered = []
        for key in self.idf.idfobjects.keys():
            word_cap = word.upper()
            if key.startswith(word_cap):
                key_filtered.append(key)
        return key_filtered

    def output_object_generator(self,output_list:list):
        if not self.idf.idfobjects['Output:SQLite']:
            self.idf.newidfobject('OUTPUT:SQLITE',Option_Type='Simple')

        self.idf.newidfobject('OUTPUT:VARIABLEDICTIONARY',Key_Field='Regular')

        for item in output_list:
            self.idf.newidfobject('OUTPUT:VARIABLE',Key_Value='*',Variable_Name=item,Reporting_Frequency='Timestep')

    def new_idf_name(self):
        return self.idf_name + '_mod'