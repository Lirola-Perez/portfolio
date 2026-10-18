import random
from pathlib import Path
from psycopg2.extras import Json
from eppy.modeleditor import IDF
from postgres_connection import get_db_connection
import os

local_eplus_path = "/home/lirola/PROJECT/PORFOLIO/energyplus/Energy+.idd"
idd_path = os.getenv("EPLUS_IDD_PATH", local_eplus_path)

class IdfClass(IDF):
        
    def get_idf(self,idf_path:Path,epw_path:Path) -> IDF:
        self.idf_path = idf_path
        self.epw_path = epw_path

        # 2. Set the IDD version so eppy knows how to parse it
        print(f' IDD: {idd_path} \n IDF: {self.idf_path} \n EPW: {self.epw_path} ')
        IDF.setiddname(idd_path)
        # 3. Load your IDF model
        self.idf = IDF(idfname=self.idf_path, epw=self.epw_path)
        print("IDF loaded successfully using eppy!")
        return self.idf
        
   