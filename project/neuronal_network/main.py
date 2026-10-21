from data_preparation import Input
from core import NeuronalNetwork


data = Input()
X,Y = data.one_hot()
print(X,Y)

# 
num_features = X.shape[1]
dim_Y = Y.shape[1]
print(num_features,dim_Y)

model = NeuronalNetwork()
model.buiding(num_features,dim_Y)
model.training(X,Y,epochs=1000)
results = model.evaluate(X,Y)
print(f"test loss: {results[0]} \n Accuracy: {results[1]}")