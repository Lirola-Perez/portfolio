# %%
from matplotlib import axis

from object.idf_class import IdfProject
from object.idf_parametric import IdfParametric
from object.process import DataProcess
from nn.data_preparation import Input
from nn.core import NeuronalNetwork


def main():
    # configuration file name (no extention)
    parameters = "parameter_run"

    projects = IdfParametric(parameters)

    # ---------- CREATION OF THE PARAMETRIC RUNS -------------
    #projects.parametrization()
    # ---------- RUN ALL NEW FILES ---------------------------
    #projects.run_all()
    # ---------- READ THE RESULTS ----------------------------
    data = DataProcess(parameters)
    results = data.get_data()
    # ---------- ADAPTING RESULTS TO THE NN ------------------
    pre_process = Input(results)

    x, y = pre_process.one_hot()

    x_train, x_test, y_train, y_test = train_test_split(x,y, test_size=0.3, stratify=y, random_state=1)

    nn_model = NeuronalNetwork()
    nn_compiled = nn_model.buiding(len(x,axis=0),len(y,axis=0))
    nn_trained = nn_compiled.training(x_train,y_train,epochs=15)
    results = nn_trained.evaluate(x_test,y_test)

    return results

if __name__ == "__main__":
    results = main()
    #print(data)

#materials = idf.idfobjects['MATERIAL']
#print(materials)

# pretty = pp.PrettyPrinter()
# pretty.pprint(results)

# %%
