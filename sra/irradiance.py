"""
All functions for estimating the cell irradiance (the effective irradiance at the cell level) of a pv module or string.

The estimation is based on the Isc of the pv system. Might need external calibration.
"""


def effective_irradiance(data, isc_calibrated, isc_alpha):
    """
    ## Calculate effective cell irradiance.

    Input Arguments:
    - data (pandas DataFrame): DataFrame that needs the rows **Isc** and **G_mod** (GTI).
    - isc_calibration (float): Short circuit current at standard test conditions (STC) or calibrated Isc value.
    - isc_alpha (float): Temperature coefficient of the given module.

    Returns:
    - pandas DataFrame with added row **G_eff**

     References
    ----------
    - [1]
    ---
    """
    df = data.copy()
    required_columns = ["Isc", "G_mod"]
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    if not isc_calibrated or not isc_alpha:
        raise ValueError(f"Missing required argument: isc_calibrated or isc_alpha")

    df["G_eff"] = (
        df["Isc"]
        / isc_calibrated
        * 1000
        / (1 + ((isc_alpha * (df["T_eff"] - 25)) / 100))
    )
    return df
