
from project.service_core.idf_class import IdfClass
from project.service_core.manager import IDFManager


manager = IDFManager()
list_idf_files = manager.process_idf_files()