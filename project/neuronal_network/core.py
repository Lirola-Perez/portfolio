import os
from backend_linker import SupabaseStorage
import tensorflow as tf
from pathlib import Path

# storage_path = os.getenv("STORAGE_PATH", "/common_storage/")
class NeuronalNetwork:

    def compiler(self,input_dim,output_dim):

        self.model = tf.keras.Sequential([
            tf.keras.layers.Input(shape=[input_dim]),
            tf.keras.layers.Dense(254, activation='relu'),
            tf.keras.layers.Dense(254, activation='relu'),
            # there is no activation in final layer -> Regresion output
            tf.keras.layers.Dense(output_dim)
        ])

        # Compile the model
        self.model.compile(
            optimizer='adam',
            loss='mse',             # Mean Squared Error penalizes big peaks
            metrics=['mae']         # Mean Absolute Error for easy-to-read evaluation
        )

        #return self.model

    def training(self,x,y,epochs=10,verbose=0):

        self.model.fit(x,y, epochs=epochs, verbose=verbose)

        #return self.model

    def save_model(self):
        # model_path = os.path.join(storage_path, 'model.keras') # Use .keras extension
        file_name = 'model.keras'
        model_path = self._temp_container(folder_name="tmp",file_name=file_name)
        self.model.save(model_path)                           # Native Keras save

        client = SupabaseStorage()
        with open(model_path,"wb") as f:
            f.write(self.model)
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
    