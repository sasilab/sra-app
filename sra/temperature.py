"""
All functions for estimating the effective cell temperature of a pv module or string.

I recommend measuring the module temperature and calculating the cell temperature based on the sandia model.
"""

import numpy as np


def cell_from_module_temperature(
    data, module_type="glass/glass", mounting_type="open_rack"
):
    """
    ## Calculate effective cell temperature from module temperature.

    Input Arguments:
    - data (pandas DataFrame): DataFrame that needs the rows **T_mod** and **G_mod** (GTI).
    - module_type (str, optional): Type of module. Defaults to "glass/glass".
    - mounting_type (str, optional): Type of mounting. Defaults to "open_rack".

    Returns:
    - pandas DataFrame with added row **T_eff**

    ## Delta Temperature Map:

    | Module Type    | Mounting Type  | Delta Temperature |
    |----------------|----------------|-------------------|
    | glass/glass    | open_rack      | 3                 |
    | glass/glass    | close_mount    | 1                 |
    | glass/polymer  | open_rack      | 3                 |
    | glass/polymer  | insulated_back | 0                 |

     References
    ----------
    - [1] King, D. et al., 2004, "Sandia Photovoltaic Array Performance Model", SAND Report 3535,
    Sandia National Laboratories, Albuquerque, NM.
    - [2] Sandia SAPM model, adjusted to work with the SRA.
    https://pvlib-python.readthedocs.io/en/stable/_modules/pvlib/temperature.html#sapm_cell

    ---
    """
    df = data.copy()
    required_columns = ["T_mod", "G_mod"]
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    delta_temp_map = {
        ("glass/glass", "open_rack"): 3,
        ("glass/glass", "close_mount"): 1,
        ("glass/polymer", "open_rack"): 3,
        ("glass/polymer", "insulated_back"): 0,
    }
    delta_temp = delta_temp_map.get((module_type, mounting_type), 0)
    df["T_eff"] = df["T_mod"] + (df["G_mod"] / 1000) * delta_temp
    return df


def module_from_ambient_temperature(
    data, module_type="glass/glass", mounting_type="open_rack"
):
    """
    ## Calculate module temperature from ambient temperature.

    Input Arguments:
    - data (pandas DataFrame): DataFrame that needs the rows **T_air** and **G_mod** (GTI).
    - module_type (str, optional): Type of module. Defaults to "glass/glass".
    - mounting_type (str, optional): Type of mounting. Defaults to "open_rack".

    Returns:
    - pandas DataFrame with added row **T_mod**

    ## a and b Map:

    | Module Type    | Mounting Type  | a     | b       |
    |----------------|----------------|-------|---------|
    | glass/glass    | open rack      | -3.47 | -0.0594 |
    | glass/glass    | close mount    | -2.98 | -0.0471 |
    | glass/polymer  | open rack      | -3.56 | -0.075  |
    | glass/polymer  | insulated back | -2.81 | -0.0455 |

     References
    ----------
    - [1] King, D. et al., 2004, "Sandia Photovoltaic Array Performance Model", SAND Report 3535,
    Sandia National Laboratories, Albuquerque, NM.
    - [2] Sandia SAPM model, adjusted to work with the SRA.
    https://pvlib-python.readthedocs.io/en/stable/_modules/pvlib/temperature.html#sapm_cell
    """
    required_columns = ["T_amb", "G_mod"]
    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"Missing required column: {col}")

    if "wind_speed" not in data.columns:
        print("Warning: 'wind_speed' column is missing. Assuming 0.0 for all rows.")
        data["wind_speed"] = 0.0

    ab_map = {
        ("glass/glass", "open_rack"): (-3.47, -0.0594),
        ("glass/glass", "close_mount"): (-2.98, -0.0471),
        ("glass/polymer", "open_rack"): (-3.56, -0.075),
        ("glass/polymer", "insulated_back"): (-2.81, -0.0455),
    }
    a, b = ab_map.get((module_type, mounting_type), (-3.47, -0.0594))
    data["T_mod"] = data["G_mod"] * np.exp(a + b * data["wind_speed"]) + data["T_amb"]
    return data
