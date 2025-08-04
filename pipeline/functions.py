"""
Helper functions for working specifically with the DataPipeline.
"""

import numpy as np
import pandas as pd


def normalize_curve_data_old(
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
    df = df.sort_values(by="Voltage_normalized")
    
    df.loc[:, "Current_normalized"] = df.apply(
        lambda row: np.interp(
            list_values, row["Voltage_normalized"], row["Current_normalized"]
        ),
        axis=1,
    )
    df.loc[:, "Voltage_normalized"] = df["Voltage_standardized"]
    df = df.drop(columns=["Voltage_standardized"])
    return df


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

    Input:
    - data (DataFrame): Contains voltage and current array columns
    - current_column_name (str): Column name for current arrays
    - voltage_column_name (str): Column name for voltage arrays
    - number_of_steps (int): Steps to interpolate on a normalized voltage axis [0, 1]

    Returns:
    - DataFrame with 'Current_normalized' and 'Voltage_normalized' columns
    """
    df = data.copy()
    standard_x = np.linspace(0, 1, number_of_steps).tolist()
    df["Voltage_standardized"] = [standard_x] * len(df)

    # Normalize each row
    def sort_and_normalize(row):
        voltage = row[voltage_column_name]
        current = row[current_column_name]

        # Sort by voltage ascending
        paired = sorted(zip(voltage, current))
        sorted_voltage, sorted_current = zip(*paired)

        # Normalize to [0,1]
        norm_voltage = [v / max(sorted_voltage) for v in sorted_voltage]
        norm_current = [i / max(sorted_current) if max(sorted_current) > 0 else 0 for i in sorted_current]

        # Interpolate to standard x-axis
        interpolated_current = np.interp(standard_x, norm_voltage, norm_current)
        return pd.Series([interpolated_current, standard_x])

    df[["Current_normalized", "Voltage_normalized"]] = df.apply(sort_and_normalize, axis=1)
    df.drop(columns=["Voltage_standardized"], inplace=True)
    return df
