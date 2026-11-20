from tkinter import X

import numpy as np
from core import NeuronalNetwork
import tensorflow as tf
from data_preparation import Input
from backend_linker import SupabaseStorage
from testing import ModelTesting

#storage_path = os.getenv("STORAGE_PATH", "/common_storage/")

storage_client = SupabaseStorage()

data = Input(storage_client)

x,y = data.one_hot()

# ----- TESTING PHASE ---------------
test = ModelTesting(x,y)
# Observing the variables.
test.variable_separator(x,file_name='X_values_trained')
test.variable_separator(y,file_name='Y_values_trained')
# Correlation testing:
test.plot_correlation_temp(x)
# testing linear model L1 (Lasso) or L2(Ridge)
regularizer = test.regularizers(regularizer_type='Ridge',alpha=1)
test.variable_separator(regularizer,file_name='Linear_model_testing')

# ----- SPLITING THE DATA ------------
# splitting the data
X_train, X_test, Y_train, Y_test = data.separating(x,y,size=0.2)

# Extracting dimensions for the model:
X_features_dim = X_train.shape[1]
X_features_dim_test = X_test.shape[1]
Y_time_dim = Y_train.shape[1]
print(f"trained dim:{X_features_dim}, test dim:{X_features_dim_test}")

# ----- SCALER X and Y -----------------------
# As the input data X has many columns 0 or 1 (labels)
# those columns dont need Standarized
columns_to_scale = ["Thickness", "Conductivity"]
X_train_scaled,scaler_x = data.scaler(
    data=X_train,
    columns=columns_to_scale,
    mode="train",
    fitted_scaler=None,
    data_class="input")

X_test_scaled,_ = data.scaler(
    data=X_test,
    columns=columns_to_scale,
    mode="test",
    fitted_scaler=scaler_x)

Y_train_scaled,scaler_y = data.scaler(
    data=Y_train,
    columns=None,
    mode="train",
    fitted_scaler=None,
    data_class="output")

Y_test_scaled,_ = data.scaler(
    data=Y_test,
    columns=None,
    mode="test",
    fitted_scaler=scaler_y)

if Y_train_scaled is not None and X_train_scaled is not None:
    print(f"Checking the values standarized: Min: {X_train_scaled.min() } - Max: {X_train_scaled.max()}")
    print(f"Checking the values standarized: Min: {Y_train_scaled.min() } - Max: {Y_train_scaled.max()}")
    print(f"TRAINED SCALED X VALUES = {X_train_scaled}")
    print(f"TRAINED SCALED Y VALUES = {Y_train_scaled}")
    # graph = Graphics()
    # graph.general_scatter(X_train_scaled)


# # ----- TESTING PHASE ---------------
# test = ModelTesting(X_train_scaled,Y_train_scaled)
# # Observing the variables.
# test.variable_separator(X_train_scaled,file_name='X_values_trained')
# test.variable_separator(Y_train_scaled,file_name='Y_values_trained')
# # Correlation testing:
# test.plot_correlation_temp(X_train_scaled)
# # testing linear model L1 (Lasso) or L2(Ridge)
# regularizer = test.regularizers(regularizer_type='Ridge',alpha=1)
# test.variable_separator(regularizer,file_name='Linear_model_testing')

# ----- MODEL -----------------------
# Preparing the model:
model = NeuronalNetwork()
model.compiler(X_features_dim,Y_time_dim)

# Training the model:
model.training(X_train_scaled,Y_train_scaled,epochs=1000,verbose=0)

y_test_scaled_predicted = model.predict(X_test_scaled)

# Evaluating the model:
results = model.evaluate(X_test_scaled,Y_test_scaled, verbose=0)
print(f"test loss: {results[0]} \nMSE: {results[1]}")

y_pred = data.inverted_scaler(scaler=scaler_y,data=y_test_scaled_predicted)
y_true = data.inverted_scaler(scaler=scaler_y,data=Y_test_scaled)

print("y_pred_scaled shape:", y_test_scaled_predicted.shape)
print("y_pred min / max / std:", y_pred.min(), y_pred.max(), y_pred.std())
print("y_true min / max / std:", y_true.min(), y_true.max(), y_true.std())
print("First sample y_true[:5]:", np.round(y_true[0, :5], 3))
print("First sample y_pred[:5]:", np.round(y_pred[0, :5], 3))

# Saving the model:
model.save_model()


