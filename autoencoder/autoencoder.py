"""
The main Autoencoder class used to build the Autoencoder.
"""

import os
import warnings
import numpy as np
import tensorflow as tf
from keras.models import Sequential, Model
from hyperopt import hp, fmin, tpe, Trials, STATUS_OK
from keras.layers import Input, Dense, Dropout, Lambda

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

warnings.filterwarnings("ignore", category=UserWarning)


class Autoencoder:
    """
    ## Main class to build and train an Autoencoder.

    Please see **functions.py** to know how to actually use this class!
    """

    def __init__(
        self,
        input_size,
        n_codings=10,
        n_layers=6,
        epochs=400,
        batch_size=32,
        decrease_mode="linear",
        use_dropout=False,
        dropout_rate=0.1,
        use_early_stopping=False,
        early_stopping_patience=10,
        n_evaluations=10,
        X_train=None,
        X_test=None,
        verbose=1,
    ):
        self.input_size = input_size
        self.n_codings = n_codings
        self.n_layers = n_layers
        self.epochs = epochs
        self.batch_size = batch_size
        self.decrease_mode = decrease_mode
        self.use_dropout = use_dropout
        self.dropout_rate = dropout_rate
        self.use_early_stopping = use_early_stopping
        self.early_stopping_patience = early_stopping_patience
        self.n_evaluations = n_evaluations
        self.X_train = np.array(X_train)
        self.X_test = np.array(X_test)
        self.verbose = verbose
        self.model = None

    def compute_layer_sizes(self):
        sizes = [self.input_size]
        if self.decrease_mode == "linear":
            decrement = (self.input_size - self.n_codings) // (self.n_layers + 1)
            sizes.extend(
                [self.input_size - i * decrement for i in range(1, self.n_layers + 1)]
            )
        elif self.decrease_mode == "exponential":
            factor = (self.n_codings / self.input_size) ** (1 / (self.n_layers + 1))
            sizes.extend(
                [
                    int(self.input_size * (factor**i))
                    for i in range(1, self.n_layers + 1)
                ]
            )
        return sizes + [self.n_codings]

    def build_model(self):
        """
        Build a standard autoencoder model.
        """
        model = Sequential()
        if self.use_dropout:
            model.add(Dropout(self.dropout_rate, input_shape=(self.input_size,)))

        sizes = self.compute_layer_sizes()
        model.add(Dense(sizes[0], activation="relu", input_shape=(self.input_size,)))
        for size in sizes[1:]:
            model.add(Dense(size, activation="relu"))
        for size in reversed(sizes[:-1]):
            model.add(Dense(size, activation="relu"))
        model.add(Dense(self.input_size, activation="sigmoid"))

        model.compile(optimizer="adam", loss="mse")
        return model

    def get_coding_layer(self, data):
        """Extracts the coding layer for the given data."""
        middle_layer_index = len(self.model.layers) // 2 - 1
        coding_model = Model(
            inputs=self.model.inputs,
            outputs=self.model.layers[middle_layer_index].output,
        )
        return coding_model.predict(data)

    def train(self, progress_callback=None):
        """Trains the model and returns the training history."""
        callbacks = []
        if self.use_early_stopping:
            callbacks.append(
                tf.keras.callbacks.EarlyStopping(
                    monitor="val_loss",
                    patience=self.early_stopping_patience,
                    mode="min",
                )
            )

        class RMSECallback(tf.keras.callbacks.Callback):
            def __init__(self, X_train, X_test, progress_callback):
                super().__init__()
                self.X_train = X_train
                self.X_test = X_test
                self.progress_callback = progress_callback

            def on_epoch_end(self, epoch, logs=None):
                train_predictions = self.model.predict(self.X_train)
                test_predictions = self.model.predict(self.X_test)

                train_rmse = np.sqrt(np.mean((self.X_train - train_predictions) ** 2))
                test_rmse = np.sqrt(np.mean((self.X_test - test_predictions) ** 2))

                if self.progress_callback:
                    self.progress_callback(
                        epoch + 1, self.params["epochs"], train_rmse, test_rmse
                    )

        callbacks.append(RMSECallback(self.X_train, self.X_test, progress_callback))

        history = self.model.fit(
            self.X_train,
            self.X_train,
            validation_data=(self.X_test, self.X_test),
            epochs=self.epochs,
            batch_size=self.batch_size,
            shuffle=True,
            callbacks=callbacks,
            verbose=self.verbose,
        )

        return history

    def build_and_train_model(self, progress_callback=None):
        """
        Builds and trains the model.
        """
        self.model = self.build_model()

        history = self.train(progress_callback=progress_callback)
        val_loss = np.min(history.history["val_loss"])

        return {"loss": val_loss, "status": STATUS_OK, "model": self.model}

    def update_params_and_train(self, params):
        """
        Updates the parameters and trains the model.
        """
        self.n_codings = int(params["n_codings"])
        self.n_layers = int(params["n_layers"])
        self.decrease_mode = params["decrease_mode"]
        return self.build_and_train_model()

    def run(self, progress_callback=None):
        """
        Runs the model.
        """
        return self.build_and_train_model(progress_callback=progress_callback)
