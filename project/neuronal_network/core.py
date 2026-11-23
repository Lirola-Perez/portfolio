from tabnanny import verbose
import numpy as np
import tensorflow as tf
from backend_linker import SupabaseStorage
from pathlib import Path

# storage_path = os.getenv("STORAGE_PATH", "/common_storage/")
class NeuronalNetwork:

    def compiler(self,input_dim,output_dim):

        self.model = tf.keras.Sequential([
            tf.keras.layers.Input(shape=[input_dim]),
            tf.keras.layers.Dense(16, activation='relu'),
            tf.keras.layers.Dense(32, activation='relu'),
            # tf.keras.layers.Dropout(0.2), # leave 20% neurons die
            tf.keras.layers.Dense(32, activation='relu'),
            # there is no activation in final layer -> Regresion output
            tf.keras.layers.Dense(output_dim)
        ])
        # custom_optimizer = tf.keras.optimizers.SGD(
        #     learning_rate=0.01,
        #     momentum=0.9)
        custom_optimizer = tf.keras.optimizers.Adam(
                    learning_rate=0.01)
        
        # Compile the model
        self.model.compile(
            optimizer=custom_optimizer,
            loss='huber',             # Mean Squared Error penalizes big peaks
            metrics=['mae']         # Mean Absolute Error for easy-to-read evaluation
        )

    def training(self,x,y,epochs=10,verbose=0):

        early_stopping = tf.keras.callbacks.EarlyStopping(
            monitor='val_loss',         # watch the validation loss
            patience=30,                # stops if not improved in 10 epochs
            restore_best_weights=True   # keeps best weights
        )

        self.model.fit(x,y, epochs=epochs, callbacks=[early_stopping],verbose=verbose)

    def predict(self,x):
        return self.model.predict(x, verbose=0)

    def save_model(self):
        # model_path = os.path.join(storage_path, 'model.keras') # Use .keras extension
        file_name = 'model.keras'
        model_path = self._temp_container(folder_name="tmp",file_name=file_name)
        self.model.save(model_path)                           # Native Keras save

        client = SupabaseStorage()
        with open(model_path,"rb") as f:
            client.upload(main_folder="output",remote_folder=f"model/{file_name}",file_name=f)
            print(f"Model {model_path} saved successfully.")

    def evaluate(self,x,y,verbose=0):

        results = self.model.evaluate(x,y,verbose=verbose)
        self.model.summary()

        return results

    def _temp_container(self,folder_name:str,file_name= None):
        # Temporary folder in container:
        temp_dir = Path(f"/tmp/{folder_name}")
        temp_dir.mkdir(parents=True,exist_ok=True)
        if not file_name:
            return Path(temp_dir)
        return Path(temp_dir / file_name)

    def coefficient_test(self,columns):
        layer0 = self.model.layers[0]
        weights = layer0.get_weights()
        W0 = weights[0]  # shape: (n_features, hidden_units)
        print("=== FIRST-LAYER WEIGHT MAGNITUDE PER FEATURE ===")
        for idx, col in enumerate(columns):
            row_w = W0[idx]
            print(
                f"[{idx:2d}] {col:48s} | "
                f"max|w|={np.max(np.abs(row_w)):.6f} | "
                f"l2={np.linalg.norm(row_w):.6f}"
            )
    