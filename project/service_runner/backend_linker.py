import os
from supabase import Client, create_client

class SupabaseStorage:
    def __init__(self) -> None:
        SUPABASE_KEY = os.getenv("SUPABASE_KEY")
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        if SUPABASE_KEY and SUPABASE_URL:
            self.supabase: Client = create_client(SUPABASE_URL,SUPABASE_KEY)

    def retrieve(self,main_folder:str, file_name: str):
        return self.supabase.storage.from_(main_folder).download(file_name)

    def upload(self,main_folder:str,remote_folder:str, file_name):
        return self.supabase.storage.from_(main_folder).upload(
            path=remote_folder, 
            file=file_name,
            file_options={"upsert": "true"})