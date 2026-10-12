from zipfile import Path

from eppy.modeleditor import IDF
import os

class IdfClass(IDF):
        
    def get_idf(self,root, idf_name:str,epw_name:str,path="default"):
        self.root = root
        self.idf_name = idf_name
        self.epw_name = epw_name
        self.project_folder = self.root + "/project/Eplusfiles"

        self.get_paths(path)
        # 2. Set the IDD version so eppy knows how to parse it
        print(f' IDD: {self.idd_path} \n IDF: {self.idf_path} \n EPW: {self.epw_path} ')
        IDF.setiddname(self.idd_path)
        # 3. Load your IDF model
        self.idf = IDF(idfname=self.idf_path, epw=self.epw_path)
        print("IDF loaded successfully using eppy!")
        return self.idf

    def get_paths(self,path):
        if path == "default":
            path_final = self.project_folder
        else:
            path_final = path
        self.idf_path = os.path.join(path_final, self.idf_name + '.idf')
        self.epw_path = os.path.join(self.project_folder, "weather", self.epw_name + ".epw")
        self.idd_path = os.path.join(self.root,"energyplus", "Energy+.idd")
        self.out_path = os.path.join(self.project_folder, "output")

class BaseType():
    def __init__(self,idf:IDF):
        self.idf = idf

    def get_type(self,type_name):
        return self.idf.idfobjects[type_name]

    def set_type(self, type_name, val):
        if hasattr(self.idf, type_name):
            setattr(self.idf, type_name, val)
        else:
            raise AttributeError(f"Field '{type_name}' does not exist.")

class Material(BaseType):
    def __init__(self,idf):
        super().__init__(idf)

        self.objects = self.get_type("Material")
        self.prop_list = ['Roughness',
                    'Thickness',
                    'Conductivity',
                    'Density', 
                    'Specific_Heat',
                    'Thermal_Absorptance', 
                    'Solar_Absorptance',
                    'Visible_Absorptance']
        
    def get_dict_(self):
        self.materials = dict()
        for obj in self.objects:
            material = obj["Name"]
            prop_dict = {}
            for key in self.prop_list:
                prop_dict[key] = obj[key]
            self.materials[material] = prop_dict

    def get_properties(self, name,property):
        self.get_dict_()
        print(self.materials)
        if self.materials[name]:
            return self.materials[name][property]

    def adapter(self):
        pass

    #################################

    def set_property(self, name, property, value):
        if property in self.list_prop:
            for obj in self.objects:
                obj[property] = value
            print(self.objects)
    
    def get_type_property_(self):
        values = []
        for obj in self.objects:
            if isinstance(self.current_property,list):
                value = [getattr(obj, p, None) for p in self.current_property]
                values.append(value)
            else:
                values.append(getattr(obj, self.current_property, None))
        return values

    def assign_to_objects(self,val):
        for obj in self.objects:
            if isinstance(self.current_property,str) and isinstance(val,str | int):
                setattr(obj,self.current_property, val)
            elif isinstance(self.current_property, list) and isinstance(val,list):
                for num,p in enumerate(self.current_property):
                    setattr(obj,p,val[num])
        return self.idf

    def get_target(self,type,property):
        return getattr(self.idf.idfobjects,property,None)

    # def assign_to_idf(self,id:str, val:list|str|float):
    #     for obj in self.objects:
    #         if obj[:] == id:
    #             if isinstance(val,list):
    #                 for v in val:
    #                     if isinstance(self.current_property,str):
    #                         setattr(obj,self.current_property,v)




    # def get_info_eppy(self):
    #     zones = self.idf.idfobjects['ZONE']
    #     for zone in zones:
    #         print(f"Zone Name: {zone.Name}")
    #         print(f"  - Ceiling Height: {zone.Ceiling_Height}")
    #         print(f"  - Volume: {zone.Volume}")
    #     surfaces = self.idf.idfobjects['BUILDINGSURFACE:DETAILED']
    #     total_wall_area = 0.0
    #     total_floor_area = 0.0
    #     for surface in surfaces:
    #         if surface.Surface_Type == 'Wall':
    #             print(f"Wall: {surface.Name}, Area: {surface.Zone_Name}")

    #     windows = self.idf.idfobjects['FENESTRATIONSURFACE:DETAILED']
    #     for win in windows:
    #         print(f"Window: {win.Name}, Parent Surface: {win.Building_Surface_Name}")

    

    def set_idf_info(self,idf,path):
        # new_name = self.idf_name + '_mod'
        new_name = self.get_new_idf_name()
        new_idf_path = os.path.join(path, new_name + '.idf')
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
        idf.saveas(new_idf_path)
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

    def get_new_idf_name(self):
        return self.idf_name + '_mod'