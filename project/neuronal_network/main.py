import os
import joblib
import pickle
from core import NeuronalNetwork
from data_preparation import Input
from sklearn.preprocessing import StandardScaler
from backend_linker import SupabaseStorage

#storage_path = os.getenv("STORAGE_PATH", "/common_storage/")

storage_client = SupabaseStorage()

data = Input(storage_client)

x,y = data.one_hot()
# splitting the data
X_train, X_test, Y_train, Y_test = data.separating(x,y)

# Extracting dimensions for the model:
X_features_dim = X_train.shape[1]
X_features_dim_test = X_test.shape[1]
Y_time_dim = Y_train.shape[1]
print(f"trained dim:{X_features_dim}, test dim:{X_features_dim_test}")

# Normalizing and Standarizing
scaler = StandardScaler()

print("X_train shape:", X_train.shape)  # Should show (N, 144)
print("X_test shape:", X_test.shape)    # Probably showing (N, 14)

# Apply standarization to the INPUT DATA
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
scaler_x_file_name = "scaler_x.pkl"
scaler_y_file_name = "scaler_y.pkl"
# joblib.dump(scaler, os.path.join(storage_path, 'scaler_x.pkl'))
temp_local_path_scaler_x = data._temp_container("tmp",scaler_x_file_name)

with open(temp_local_path_scaler_x, "wb") as f:
    pickle.dump(X_test_scaled,f)

with open(temp_local_path_scaler_x, "rb") as f:
    storage_client.upload("output",f"model/{scaler_x_file_name}",f)

# EXCEPTION: If OUPUT data is very heterogeneuos -> Standarize
Y_train_scaled = scaler.fit_transform(Y_train)
Y_test_scaled = scaler.transform(Y_test)
#joblib.dump(scaler, os.path.join(storage_path, 'scaler_y.pkl'))
temp_local_path_scaler_y = data._temp_container("tmp",scaler_y_file_name)

with open(temp_local_path_scaler_y, "wb") as f:
    pickle.dump(Y_test_scaled,f)

with open(temp_local_path_scaler_y, "rb") as f:
    storage_client.upload("output",f"model/{scaler_y_file_name}",f)

# Preparing the model:
# DESCRIPTION:
# 105.300 weights (trainable parameters)
# net with 652 neurons total
model = NeuronalNetwork()
model.compiler(X_features_dim,Y_time_dim)

# Training the model:
model.training(X_train_scaled,Y_train_scaled,epochs=1000)

# Evaluating the model:
results = model.evaluate(X_test_scaled,Y_test_scaled)
print(f"test loss: {results[0]} \nMSE: {results[1]}")

# Saving the model:
model.save_model()

# Convert them back to your original scale!
#real_predictions = scaler_y.inverse_transform(scaled_predictions)

