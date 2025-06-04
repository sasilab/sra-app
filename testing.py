"""
Main function to call the autoencoder from other repos.

Use autoencode() to train the model.

Required inputs:
- df: pandas DataFrame
- target_feature: str -> the column name of the target feature, e.g. "IV_Current_normalized"
                      -> list of floats

Architecture Options:
- n_codings: int -> number of codings in the middle (default: 10)
- n_layers: int -> number of layers between input and codings (default: 6)
- decrease_mode: str -> whether to decrease the number of neurons linearly or exponentially (default: "linear")
- use_dropout: bool -> whether to use dropout (default: False)
- dropout_rate: float -> dropout rate (default: 0.1)

Training Options:
- use_early_stopping: bool -> whether to use early stopping (default: False)
- early_stopping_patience: int -> patience for early stopping (default: 10)
- epochs: int -> number of epochs to train the model (default: 400)
- batch_size: int -> batch size for training the model (default: 32)
"""

import numpy as np
import pandas as pd

from autoencoder.autoencoder import Autoencoder
from pipeline.functions import normalize_curve_data
from sklearn.model_selection import train_test_split


def autoencode(df, target_feature, **kwargs):
    """
    Train an autoencoder on the given DataFrame and target feature.
    """
    test_size = 0.2

    X = np.array(df[target_feature].tolist()).astype(np.float32)
    X_train, X_test, train_indices, test_indices = train_test_split(
        X,
        np.arange(X.shape[0]),
        test_size=test_size,
        random_state=None,
    )
    input_size = X_train.shape[1]

    # Initialize and build the autoencoder
    autoencoder = Autoencoder(
        input_size=input_size, X_train=X_train, X_test=X_test, **kwargs
    )

    # Run the autoencoder
    history = autoencoder.run()

    # Reconstruct the curves
    all_predictions = autoencoder.model.predict(X)
    df["reconstruction"] = all_predictions.tolist()

    # Get the codings
    codings = autoencoder.get_coding_layer(X)
    df["codings"] = codings.tolist()

    return df, history


def calculate_rmse(original, reconstructed):
    """Calculate RMSE between original and reconstructed data."""
    return np.sqrt(np.mean((original - reconstructed) ** 2, axis=1))


# Load and normalize data
df_ = pd.read_pickle("data/Dataset4000Updated.pkl")
df_ = normalize_curve_data(df_)

# Split the DataFrame into df1 and df2
df1, df2 = train_test_split(df_, test_size=0.5, random_state=42)

# Train the autoencoder on df1
new_df1, history_ = autoencode(
    df1,
    target_feature="Current_normalized",
    epochs=100,
    n_codings=7,
    n_layers=5,
    use_early_stopping=True,
    early_stopping_patience=10,
)

# Use the trained model to reconstruct df2
X_df2 = np.array(df2["Current_normalized"].tolist()).astype(np.float32)
reconstructed_df2 = history_["model"].predict(X_df2)

rmse_df2 = calculate_rmse(X_df2, reconstructed_df2)

# Add reconstruction to df2
df2["reconstruction"] = reconstructed_df2.tolist()
df2["rmse"] = rmse_df2

print(df2)

import matplotlib.pyplot as plt
import matplotlib

matplotlib.use("TkAgg")

plt.scatter(df2["Gut"], df2["rmse"])
plt.show()
