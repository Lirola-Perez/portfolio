import os
from manager import IDFManager
from backend_linker import SupabaseStorage

backend_use = os.getenv("BACKEND_STORAGE_CLOUD","true")
EPLUS_IDD_PATH = os.getenv("EPLUS_IDD_PATH","/usr/local/EnergyPlus-23.1.0/")

if backend_use:
    storage_client = SupabaseStorage()
else:
    local_folder = os.getenv("BACKEND_STORAGE_LOCAL_PATH")
    storage_client = local_folder


manager = IDFManager(storage_client)
manager.process_idf_files()