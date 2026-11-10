import os
from supabase import Client, create_client

class SupabaseStorage:
    def __init__(self) -> None:
        SUPABASE_KEY = os.getenv("SUPABASE_KEY")
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        if SUPABASE_KEY and SUPABASE_URL:
            self.supabase: Client = create_client(SUPABASE_URL,SUPABASE_KEY)

    def retrieve(self,main_folder:str, file_name: str):
        return self.supabase.storage.from_("buckets").download(f"{main_folder}/{file_name}")

    def upload(self,main_folder:str,remote_folder:str, file_name):
        return self.supabase.storage.from_("buckets").upload(
            path=remote_folder, 
            file=f"{main_folder}/{file_name}",
            file_options={"upsert": "true"})