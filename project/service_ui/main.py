# %%
from matplotlib import axis

from service_core.idf_class import IdfClass, BaseType, Material
from service_core.idf_parametric import IdfParametric, IdfManager
from service_core.process import DataProcess

def main():

    idf_test = IdfClass()
    idf = idf_test.get_idf("/home/lirola/PROJECT/PORTFOLIO","MultiStory","Madrid")
    #print(idf.idfobjects["Material"])
    type = Material(idf)
    value = type.get_properties("E2 - 1 / 2 IN SLAG OR STONE", "Thickness")
    #materials = type.get_properties()
    print(value)
    #type.set_property("Thickness",232322323)

    # idf_test.get_idf("/home/lirola/PROJECT/PORTFOLIO","MultiStory","Madrid")
    # value = idf_test.set_search("Material",["Thickness","Conductivity"])
    # values = idf_test.get_type_property_()
    # value = idf_test.get_target("Material","Thickness")
    # print(value)
    # idf_test.assign_to_objects([1.5,0.05])
    # values = idf_test.get_type_property_()
    # print(values)
    # # configuration file name (no extention)
    # parameters = "parameter_run"

    # manager = IdfManager(idf_test)
    # manager.set_values("Material","Thickness",[0.2,0.03,100])

    # projects = IdfParametric(parameters)

    # ---------- CREATION OF THE PARAMETRIC RUNS -------------
    #projects.parametrization()
    # ---------- RUN ALL NEW FILES ---------------------------
    #projects.run_all()
    # ---------- READ THE RESULTS ----------------------------
    # data = DataProcess(parameters)
    # results = data.get_data()
    # ---------- ADAPTING RESULTS TO THE NN ------------------
    # pre_process = Input(results)

    # x, y = pre_process.one_hot()

    # x_train, x_test, y_train, y_test = train_test_split(x,y, test_size=0.3, stratify=y, random_state=1)

    # nn_model = NeuronalNetwork()
    # nn_compiled = nn_model.buiding(len(x,axis=0),len(y,axis=0))
    # nn_trained = nn_compiled.training(x_train,y_train,epochs=15)
    # results = nn_trained.evaluate(x_test,y_test)

    # return results

if __name__ == "__main__":
    #results = main()
    main()
    #print(data)

#materials = idf.idfobjects['MATERIAL']
#print(materials)

# pretty = pp.PrettyPrinter()
# pretty.pprint(results)

# %%
