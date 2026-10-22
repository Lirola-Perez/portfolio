from data_preparation import Input
from core import NeuronalNetwork


data = Input()
x,y = data.one_hot()
X,Y = data.scaler(x,y)
X_train, X_test, Y_train, Y_test = data.separating(X,Y)
print(X,Y)

# Extracting dimensions for the model:
X_features_dim = X_train.shape[1]
Y_time_dim = Y_train.shape[1]

# Preparing the model:
model = NeuronalNetwork()
model.compiler(X_features_dim,Y_time_dim)

# Training the model:
model.training(X_train,Y_train,epochs=1000)

# Evaluating the model:
results = model.evaluate(X_test,Y_test)
print(f"test loss: {results[0]} \nAccuracy: {results[1]}")