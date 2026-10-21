from grabber import SimulationData


data = SimulationData()

all_data = data.worker()
data.save_master_aux(all_data)