import os
from pathlib import Path
from postgres_connection import get_db_connection

class SimulationData:
    def __init__(self) -> None:
        self.output_path = os.getenv("OUTPUT_PATH", "common_storage/output")

    def completed_data_grabber(self):

        with get_db_connection() as conn:
            with conn.cursor() as cursor:

                cursor.execute(
                    """SELECT idf_filename FROM simulations 
                    WHERE status = 'Completed'
                    LIMIT 1"""
                )
                idf_name = cursor.fetchone()
        return idf_name

    def file_db_grabber(self):

        file_name = self.completed_data_grabber()
        Path(f"{self.output_path}/{file_name}")
    
