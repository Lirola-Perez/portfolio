from tabnanny import verbose

import numpy
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
import tensorflow as tf

class NeuronalNetwork:

    def buiding(self,input_dim,output_dim):

        self.model = tf.keras.Sequential(
            tf.keras.layers.Input(128, shape=[input_dim]),
            tf.keras.layers.Dense(254, activation='relu'),
            tf.keras.layers.Dense(254, activation='relu'),
            # there is no activation in final layer -> Regresion output
            tf.keras.layers.Dense(output_dim)
        )

        # Compile the model
        self.model.compile(
            optimizer='adam', 
            loss='mse',             # Mean Squared Error penalizes big peaks
            metrics=['mae']         # Mean Absolute Error for easy-to-read evaluation
        )

        return self.model

    def training(self,x,y,epochs=10,verbose=0):

        self.model.fit(x,y, epochs=epochs, verbose=verbose)

        return self.model

    def evaluate(self,x,y,verbose=0):

        self.model.evaluate(x,y,verbose=verbose)

        return self.model