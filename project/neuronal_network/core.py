import os

import tensorflow as tf

storage_path = os.getenv("STORAGE_PATH", "/common_storage/")
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
        model_path = os.path.join(storage_path, 'model.keras') # Use .keras extension
        self.model.save(model_path)                           # Native Keras save
        print(f"Model {model_path} saved successfully.")

    def evaluate(self,x,y,verbose=0):

        results = self.model.evaluate(x,y,verbose=verbose)
        self.model.summary()

        return results