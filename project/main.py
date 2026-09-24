# %%
from object.idf_class import IdfProject
from object.idf_parametric import IdfParametric
from object.process import DataProcess
from nn.data_preparation import Input


def main():

    parameters = "parameter_run"

    projects = IdfParametric(parameters)
    
    #projects.parametrization()
    #projects.run_all()
    
    data = DataProcess(parameters)
    results = data.get_data()

    return results

if __name__ == "__main__":
    results = main()
    #print(data)

#materials = idf.idfobjects['MATERIAL']
#print(materials)

# pretty = pp.PrettyPrinter()
# pretty.pprint(results)

# %%
