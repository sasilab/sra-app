"""
Helper functions for working specifically with the DataPipeline.
"""

import numpy as np
import pandas as pd


def normalize_curve_data(
    data: pd.DataFrame,
    current_column_name: str = "Current",
    voltage_column_name: str = "Voltage",
    number_of_steps: int = 100,
) -> pd.DataFrame:
    """
    ## Normalize Curve Data

    Input Arguments:
    - data (pandas DataFrame): DataFrame that needs the rows **Isc** and **G_mod** (GTI).
    - current_column_name (str): Name of the column with Current values. Default "Current".
    - voltage_column_name (str): Name of the column with Voltage values. Default "Voltage.
    - number_of_steps (int): How many steps (on the x-axis) to use for the normalization. Default 100.

    Returns:
    - pandas DataFrame with added columns **Current_normalized** and **Voltage_normalized**
    """
    df = data.copy()
    list_values = np.linspace(0, 1, number_of_steps).tolist()

    df.loc[:, "Voltage_standardized"] = [list_values for _ in range(len(df))]
    df.loc[:, "Current_normalized"] = df[current_column_name].apply(
        lambda x: [i / max(x) for i in x]
    )
    df.loc[:, "Voltage_normalized"] = df[voltage_column_name].apply(
        lambda x: [i / max(x) for i in x]
    )
    df.loc[:, "Current_normalized"] = df.apply(
        lambda row: np.interp(
            list_values, row["Voltage_normalized"], row["Current_normalized"]
        ),
        axis=1,
    )
    df.loc[:, "Voltage_normalized"] = df["Voltage_standardized"]
    df = df.drop(columns=["Voltage_standardized"])
    return df
