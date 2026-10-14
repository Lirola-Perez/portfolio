import random
from pathlib import Path
from psycopg2.extras import Json
from eppy.modeleditor import IDF
from .manager import IDFManager
from postgres_connection import get_db_connection
import os

local_eplus_path = "/home/lirola/PROJECT/PORFOLIO/energyplus/Energy+.idd"
idd_path = os.getenv("EPLUS_IDD_PATH", local_eplus_path)

class IdfClass(IDF):
        
    def get_idf(self,idf_path:Path,epw_path:Path):
        self.idf_path = idf_path
        self.epw_path = epw_path

        # 2. Set the IDD version so eppy knows how to parse it
        print(f' IDD: {idd_path} \n IDF: {self.idf_path} \n EPW: {self.epw_path} ')
        IDF.setiddname(idd_path)
        # 3. Load your IDF model
        self.idf = IDF(idfname=self.idf_path, epw=self.epw_path)
        print("IDF loaded successfully using eppy!")
        return self.idf
        
    def parse_idf_to_postgresql(self, idf:IDF, batch_id: int, object_key:str, attr:list):
    
        conn = get_db_connection()
        cursor = conn.cursor()

        objects = idf.idfobjects[object_key]
        
        if objects and attr:
            for obj in objects:
                properties = dict()
                for attribute in attr:
                    properties[attribute] = getattr(obj,attribute, None)
                # Grab the object's name if it has one
                obj_name = getattr(obj, "Name", "Unnamed_Object")

                cursor.execute(
                    "INSERT INTO idf_components (batch_id, object_type, object_name, properties) VALUES (%i, %s, %s, %s);",
                    (batch_id, object_key, obj_name, Json(properties),),
                )

        conn.commit()
        cursor.close()
        conn.close()
        print(f"Stored {len(objects)} {object_key} objects into PostgreSQL.")

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
     
    def set_property(self, name, property, value):
        if property in self.prop_list:
            for obj in self.objects:
                obj[property] = value
            print(self.objects)

    def sql_coding(self):
        conn = get_db_connection()            
        
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

   