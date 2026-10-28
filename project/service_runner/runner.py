import os
import time
import traceback
from pathlib import Path
from postgres_connection import get_db_connection
from eppy import IDF

local_eplus_path = "/home/lirola/PROJECT/PORFOLIO/energyplus/Energy+.idd"
local_weather_path = "/home/lirola/PROJECT/PORFOLIO/project/common_storage/weather"

class Runner:
    def __init__(self):
        self.output_path = Path(os.getenv("OUTPUT_PATH", "/common_storage/output"))
        self.idd_path = Path(os.getenv("EPLUS_IDD_PATH", local_eplus_path))

    def runner(self):
        
        while True:
            # Keeps the runner in endless loop
            simulation_pending = self.pending_simulation_grabber()

            if not simulation_pending:
                # No jobs available right now; sleep briefly and check again
                # 
                time.sleep(5)
                continue

            if simulation_pending:
                sim_id,batch_id, sim_name,weather_name = simulation_pending
                try:
                    print(f"Starting to collect data simulation number: {sim_id}...")
                    weather_path = Path(os.getenv("WEATHER_PATH",local_weather_path))
                    weather_total_path = Path(f"{weather_path}/{weather_name}.epw")
                    sim_output_path = Path(f"{self.output_path}/{sim_name}")
                    sim_total_path = Path(f"{sim_output_path}/{sim_name}.idf")

                    idf = self.get_idf(sim_total_path,weather_total_path)

                    print(f"Running simulation {sim_name} number: {sim_id}...")
                    self.update_simulation_status(sim_id,"Running")
                    idf.run(weather=weather_total_path,
                            idd=self.idd_path,
                            output_directory=sim_output_path)
                    
                    print(f"Simulation {sim_name} number: {sim_id} batch: {batch_id}-> COMPLETED")
                    self.update_simulation_status(sim_id,"Completed")

                except Exception as e:
                    print(f"[{sim_id}] Simulation failed with error: {e}")
                    traceback.print_exc()
                    self.update_simulation_status(sim_id,"Failed")


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


    def pending_simulation_grabber(self) -> tuple | None:
        "Takes just one simulation with statusn 'pending'"
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """SELECT simulation_id,batch_id,idf_filename,weather FROM simulations
                    WHERE status_simulation = 'Pending'
                    OR status_simulation = 'Failed'
                    LIMIT 1;"""
                )
                # Structure = [(1, 'Simulation_1'), (2, 'Simulation_2'), ...]
                simulation_to_run = cursor.fetchone()
                    
        return simulation_to_run

    def update_simulation_status(self,id:int,status:str):
        "Changes the simulaition status"
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """UPDATE simulations SET status_simulation = %s WHERE simulation_id = %s""",
                    (status, id)
                )