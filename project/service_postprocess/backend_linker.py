import os
from supabase import Client, create_client

class SupabaseStorage:
    def __init__(self) -> None:
        SUPABASE_KEY = os.getenv("SUPABASE_KEY")
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        if SUPABASE_KEY and SUPABASE_URL:
            supabase: Client = create_client(SUPABASE_URL,SUPABASE_KEY)
            self.storage = supabase.storage

    def retrieve(self,main_folder:str, file_name: str):
        print(f"DOWNLOADING FROM SUPABASE -> Bucket: '{main_folder}', Path: '{file_name}'")
        return self.storage.from_(main_folder).download(file_name)

    def upload(self,main_folder:str,remote_folder:str, file_name):
        print(f"UPLOADING FROM SUPABASE -> Bucket: '{main_folder}', Remote folder: '{remote_folder}', Path: '{file_name}'")
        return self.storage.from_(main_folder).upload(
            path=remote_folder, 
            file=file_name,
            file_options={"upsert": "true"})

    def empty_folder(self,main_folder:str):
        print(f"CLEARING BUCKET -> Bucket: '{main_folder}'")
        try:
            # 1. List all items in the bucket root
            files = self.storage.from_(main_folder).list()
            
            if files:
                # 2. Extract their paths/names
                file_paths = [file["name"] for file in files]
                
                if file_paths:
                    # 3. Delete them explicitly
                    self.storage.from_(main_folder).remove(file_paths)
                    print(f"Successfully cleared {len(file_paths)} items from '{main_folder}'.")
        except Exception as e:  # noqa: BLE001
            print(f"Note/Warning clearing bucket: {e}")