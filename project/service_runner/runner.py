from ast import main
import os
import psycopg2
import subprocess
import time
import traceback
import shutil
from pathlib import Path

from eppy import IDF
from postgres_connection import get_db_connection

DATABASE_URL = os.getenv("DATABASE_URL")

class Runner:
    def __init__(self,storage_client, idd_path=None):

        if idd_path:
            self.idd_path = Path(os.path.join(idd_path,"Energy+.idd"))

        # Introduction task: Connection to backend
        self.client = storage_client

    def runner(self):

        jobs_processed = False
        
        while True:
            # Keeps the runner in endless loop
            simulation_pending = self.pending_simulation_grabber()

            if not simulation_pending:
                if jobs_processed:
                    print("All simulations completed for this batch. Exiting runner container...")
                    break
                else:
                    # Brief pause and check again
                    time.sleep(2)
                    continue

            # At least one job running in this session
            jobs_processed = True

            if simulation_pending:
                sim_id,batch_id, sim_name,weather_name = simulation_pending
                try:
                    print(f"Starting to collect data simulation number: {sim_id}...")

                    weather_file = f"{weather_name}.epw"
                    idf_file_name = f"{sim_name}.idf"

                    # Creating the temporary folder and files in container:
                    temp_local_weather_file = self._temp_container("weather",weather_file)
                    temp_local_idf_file = self._temp_container(sim_name,idf_file_name)
                    temp_local_output_dir = self._temp_container("output",sim_name)

                    # Downloading the files from supabase in the temporary folder and writing in container file:
                    supa_weather_file = self.client.retrieve("weather",weather_file)
                    temp_local_weather_file.write_bytes(supa_weather_file)

                    supa_idf_file = self.client.retrieve("output",f"{sim_name}/{idf_file_name}")
                    temp_local_idf_file.write_bytes(supa_idf_file)

                    # getting the idf file and converting into an IDF object
                    idf = self.get_idf(temp_local_idf_file,temp_local_weather_file)

                    print(f"Running simulation {sim_name} number: {sim_id}...")
                    self.update_simulation_status(sim_id,"Running")

                    # Starting the RUN
                    idf.run(weather=temp_local_weather_file,
                            idd=self.idd_path,
                            output_directory=temp_local_output_dir)

                    print(f"Simulation {sim_name} number: {sim_id} batch: {batch_id}-> COMPLETED")
                    self.update_simulation_status(sim_id,"Completed")

                    print(f"Uploading results for {sim_name}...")
                    for output_file in temp_local_output_dir.glob("*"):
                        # Skipping heavy files that aren't needed for analysis
                        if output_file.suffix in [".sql", ".eso", ".audit"]:
                            continue

                        with open(output_file, "rb") as f:
                            self.client.upload(main_folder="output",
                                                remote_folder=f"{sim_name}/{output_file.name}", 
                                                file_name=f)

                    # Clean up the temporary local file
                    if os.path.exists(temp_local_idf_file):
                        os.remove(temp_local_idf_file)
                    if os.path.exists(temp_local_weather_file):
                        os.remove(temp_local_weather_file)
                    if os.path.exists(temp_local_output_dir):
                        shutil.rmtree(temp_local_output_dir)

                except (FileNotFoundError, OSError) as e:
                    # Handle specific file/path problems
                    print(f"[{sim_id}] File system error during simulation: {e}")
                    self.update_simulation_status(sim_id, "Failed run")

                except subprocess.CalledProcessError as e:
                    # Handle specific EnergyPlus execution crashes
                    print(f"[{sim_id}] EnergyPlus binary execution failed: {e}")
                    self.update_simulation_status(sim_id, "Failed run")

                except Exception as e: # noqa: BLE001
                    # Catch-all safeguard for any other unforeseen errors
                    print(f"[{sim_id}] Simulation failed with unexpected error: {e}")
                    traceback.print_exc()
                    self.update_simulation_status(sim_id, "Failed run")

    def _temp_container(self,folder_name:str,file_name= None):
        # Temporary folder in container:
        temp_dir = Path(f"/tmp/{folder_name}")
        temp_dir.mkdir(parents=True,exist_ok=True)
        if not file_name:
            return Path(temp_dir)
        return Path(temp_dir / file_name)


    def get_idf(self,idf_path,epw_path)-> IDF:

        # 2. Set the IDD version so eppy knows how to parse it
        print(f' IDD: {self.idd_path} \n IDF: {idf_path} \n EPW: {epw_path} ')
        IDF.setiddname(self.idd_path)
        # 3. Load your IDF model
        self.idf = IDF(idfname=idf_path, epw=epw_path)
        print("IDF loaded successfully using eppy!")
        return self.idf

    def pending_simulation_grabber(self) -> tuple | None:
        "Takes just one simulation with status 'pending'"
        try: 
            with get_db_connection() as conn, conn.cursor() as cursor:
                cursor.execute(
                    """SELECT simulation_id,batch_id,idf_filename,weather FROM simulations
                    WHERE status_simulation = 'Pending'
                    LIMIT 1;"""
                )
                # Structure = [(1, 'Simulation_1'), (2, 'Simulation_2'), ...]
                simulation_to_run = cursor.fetchone()
                return simulation_to_run

        except psycopg2.OperationalError as e:
            # Handles connection drops, network failures, or database down states
            print(f"Database operational error (connection/timeout): {e}")
            return None

        except psycopg2.ProgrammingError as e:
            # Handles syntax errors in your SQL query or missing tables/columns
            print(f"Database programming error (bad SQL/schema): {e}")
            return None

        except psycopg2.DatabaseError as e:
            # Catch-all for any other database-specific errors
            print(f"General database error: {e}")
            return None

        except Exception as e: # noqa: BLE001 
            print(f"Error saving results to DB: {e}")
            return None

    def update_simulation_status(self,id:int,status:str):
        "Changes the simulation status"
        with get_db_connection() as conn, conn.cursor() as cursor:
            cursor.execute(
                """UPDATE simulations SET status_simulation = %s WHERE simulation_id = %s""",
                (status, id)
            )