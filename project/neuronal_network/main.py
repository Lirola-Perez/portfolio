from tkinter import X

import numpy as np
from core import NeuronalNetwork
import tensorflow as tf
from data_preparation import Input
from backend_linker import SupabaseStorage
from testing import ModelTesting

#storage_path = os.getenv("STORAGE_PATH", "/common_storage/")

input_columns=['Thickness', 
        'Conductivity', 
        'Weather_Madrid', 
        'Weather_Potsdam', 
        'Variable_Cooling Zone Relative Humidity [%]', 
        'Variable_Cooling Zone Temperature [C]', 
        'Variable_Des Cool Mass Flow [kg/s]', 
        'Variable_Des Heat Load [W]', 
        'Variable_Des Heat Mass Flow [kg/s]', 
        'Variable_Des Sens Cool Load [W]', 
        'Variable_Heating Zone Relative Humidity [%]', 
        'Variable_Heating Zone Temperature [C]']

input_columns_to_scale = ["Thickness", "Conductivity"]
output_columns_to_scale = ['Variable_Cooling Zone Relative Humidity [%]', 
                      'Variable_Cooling Zone Temperature [C]', 
                      'Variable_Des Cool Mass Flow [kg/s]', 
                      'Variable_Des Heat Load [W]', 
                      'Variable_Des Heat Mass Flow [kg/s]', 
                      'Variable_Des Sens Cool Load [W]', 
                      'Variable_Heating Zone Relative Humidity [%]', 
                      'Variable_Heating Zone Temperature [C]']

storage_client = SupabaseStorage()

data = Input(storage_client)

data.one_hot()
x,y = data.input_output_selector()

# print(f"COLUMN INDEXES COLLECTED: {column_idx}")
# print(f"ROW INDEXES COLLECTED: {row_idx}")

# ----- TESTING PHASE ---------------
# test = ModelTesting(x,y)
# # Observing the variables.
# test.variable_separator(x,file_name='X_values_trained')
# test.variable_separator(y,file_name='Y_values_trained')
# # Correlation testing:
# test.plot_correlation_temp(x)
# # testing linear model L1 (Lasso) or L2(Ridge)
# regularizer = test.regularizers(regularizer_type='Ridge',alpha=1)
# test.variable_separator(regularizer,file_name='Linear_model_testing')

# ----- SPLITING THE DATA ------------
# splitting the data
X_train, X_test, Y_train, Y_test = data.separating(x,y,size=0.2)

# taking the indexes:
row_idx_train = data.row_index_taker(data=X_train,variable_list=output_columns_to_scale)
row_idx_test = data.row_index_taker(data=X_test,variable_list=output_columns_to_scale)
column_idx = data.column_index_taker(data=X_train,variable_list=input_columns_to_scale)

X_train = data.from_dataframe_to_numpy(X_train)
X_test = data.from_dataframe_to_numpy(X_test)
Y_train = data.from_dataframe_to_numpy(Y_train)
Y_test = data.from_dataframe_to_numpy(Y_test)

# Extracting dimensions for the model:
X_features_dim = X_train.shape[1]
X_features_dim_test = X_test.shape[1]
Y_time_dim = Y_train.shape[1]
print(f"trained dim:{X_features_dim}, test dim:{X_features_dim_test}")

# ----- SCALER X and Y -----------------------
# As the input data X has many columns 0 or 1 (labels)
# those columns dont need Standarized

scaler_list_x, X_train_scaled = data.scaler_columns(
    X_train,
    column_idx,
    mode="train",
    fitted_scaler=None)

_, X_test_scaled = data.scaler_columns(
    X_test,
    column_idx,
    mode="test",
    fitted_scaler=scaler_list_x)

scaler_list_y, Y_train_scaled = data.scaler_rows(
    Y_train,
    row_idx_train,
    variable_list=output_columns_to_scale,
    mode="train",
    fitted_scaler=None)

_, Y_test_scaled = data.scaler_rows(
    Y_test,
    row_idx_test,
    variable_list=output_columns_to_scale,
    mode="test",
    fitted_scaler=scaler_list_y)

print("FINAL Y_train_scaled shape/min/max/mean/std:",
    Y_train_scaled.shape,
    float(Y_train_scaled.min()),
    float(Y_train_scaled.max()),
    float(Y_train_scaled.mean()),
    float(Y_train_scaled.std()))
print("FINAL Y_test_scaled shape/min/max/mean/std:",
    Y_test_scaled.shape,
    float(Y_test_scaled.min()),
    float(Y_test_scaled.max()),
    float(Y_test_scaled.mean()),
    float(Y_test_scaled.std()))


# ----- MODEL -----------------------
# Preparing the model:
model = NeuronalNetwork()
model.compiler(X_features_dim,Y_time_dim)

# Training the model:
model.training(X_train_scaled,Y_train_scaled,epochs=1000,verbose=0)

# -------------------------
# 1. Inspect first-layer weight magnitude per input column
model.coefficient_test(columns=input_columns)
# -----------------------------

y_test_scaled_predicted = model.predict(X_test_scaled)

# Evaluating the model:
results = model.evaluate(X_test_scaled,Y_test_scaled, verbose=0)
print(f"test loss: {results[0]} \nMSE: {results[1]}")

y_pred = None
y_true = None

# for name,sigma,mu in zip(output_columns_to_scale,sigma_list,mu_list):
#     cols_v_x = output_columns_to_scale.index(name)
#     y_pred = y_test_scaled_predicted * sigma + mu
#     y_true = Y_test_scaled * sigma + mu

y_pred = data.inverted_row_scaler(
    y_test_scaled_predicted,
    idx_rows=row_idx_test,
    variable_list=output_columns_to_scale,
    scaler_list=scaler_list_y)

y_true = data.inverted_row_scaler(
    Y_test_scaled,
    idx_rows=row_idx_test,
    variable_list=output_columns_to_scale,
    scaler_list=scaler_list_y)

# for column,scaler_y in zip(output_columns_to_scale,scaler_y_list):
#     y_pred = data.inverted_scaler(scaler=scaler_y,data=y_pred,column=column)

# for column,scaler_y in zip(output_columns_to_scale,scaler_y_list):
#     y_true = data.inverted_scaler(scaler=scaler_y,data=y_true,column=column)

if y_true is not None and y_pred is not None:
    print("y_pred_scaled shape:", y_test_scaled_predicted.shape)
    print("y_pred min / max / std:", y_pred.min(), y_pred.max(), y_pred.std())
    print("y_true min / max / std:", y_true.min(), y_true.max(), y_true.std())
    print("First sample y_true[:5]:", np.round(y_true[0, :5], 3))
    print("First sample y_pred[:5]:", np.round(y_pred[0, :5], 3))

    col_mse = np.mean((y_true - y_pred) ** 2, axis=0)      # shape: (144,)
    col_max_abs = np.max(np.abs(y_true - y_pred), axis=0)  # shape: (144,)
    worst_cols = np.argsort(col_mse)[::-1][:10]

    for c in worst_cols:
        print(
            f"col={c:3d} | mse={col_mse[c]:12.2f} | max_err={col_max_abs[c]:10.2f} | "
            f"true=[{y_true[:, c].min():.2f}, {y_true[:, c].max():.2f}] | "
            f"pred=[{y_pred[:, c].min():.2f}, {y_pred[:, c].max():.2f}]"
        )

# Saving the model:
model.save_model()


