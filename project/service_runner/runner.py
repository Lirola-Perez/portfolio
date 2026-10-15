import os
from pathlib import Path
from sqlite3 import connect

from decorator import contextmanager
import psycopg2
from postgres_connection import get_db_connection
from eppy import IDF

local_eplus_path = "/home/lirola/PROJECT/PORFOLIO/energyplus/Energy+.idd"
local_weather_path = "/home/lirola/PROJECT/PORFOLIO/project/common_storage/weather"

class Runner:
    def __init__(self) -> None:
        self.output_path = Path(os.getenv("OUTPUT_PATH", "/common_storage/output"))
        self.idd_path = Path(os.getenv("EPLUS_IDD_PATH", local_eplus_path))

    def runner(self):
        simulations = self.simulation_grabber()

        for sim_id, sim_name, weather_name in simulations:
            print(f"Starting to collect data simulation number: {sim_id}...")
            weather_path = Path(os.getenv("WEATHER_PATH",local_weather_path))
            weather_total_path = Path(os.path.join(weather_path,weather_name))
            sim_output_path = Path(f"{self.output_path}/{sim_name}")
            sim_total_path = Path(f"{sim_output_path}/{sim_name}.idf")

            idf = self.get_idf(sim_total_path,weather_total_path)

            print(f"Running simulation {sim_name} number: {sim_id}...")
            idf.run(weather=weather_total_path,
                    idd=self.idd_path,
                    output_directory=sim_output_path)
            print(f"Simulation {sim_name} number: {sim_id} -> COMPLETED")




    def get_idf(self,idf_path:Path,epw_path:Path)-> IDF:
        self.idf_path = idf_path
        self.epw_path = epw_path

        # 2. Set the IDD version so eppy knows how to parse it
        print(f' IDD: {self.idd_path} \n IDF: {self.idf_path} \n EPW: {epw_path} ')
        IDF.setiddname(self.idd_path)
        # 3. Load your IDF model
        self.idf = IDF(idfname=self.idf_path, epw=epw_path)
        print("IDF loaded successfully using eppy!")
        return self.idf


    def simulation_grabber(self)-> list[tuple]:

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """SELECT simulation_id,idf_filename,weather FROM simulations
                    WHERE status = 'pending';"""
                )
                # Structure = [(1, 'Simulation_1'), (2, 'Simulation_2'), ...]
                simulations_to_run = cursor.fetchall()

        return simulations_to_run