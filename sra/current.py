"""
All functions for estimating the current of the system based on the reference surface fit
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize


def current_calculation(
    current_stc, current_alpha, irradiance, temperature, correction_factor=0
):
    """
    ## Calculate the current based on the linear approximation

    ! This one does not work with the pipeline !

    Input Arguments:
    - current_stc (float) : Isc under stc conditions (datasheet!)
    - current_alpha (float) : Temperature coefficient of the Isc (STC, datasheet!)
    - irradiance : Irradiation values given as single values or a list or grid
    - temperature : Temperature value given as single values or a list or grid
    - correction_factor : Correction factor for a relative difference to the reference surface

    Returns:
    - The calculated current values
    """
    return (
        current_stc * irradiance / 1000 * (1 + current_alpha * (temperature - 25) / 100)
    ) * (1 + correction_factor / 100)

def fit_current_data_to_surface(data, initial_isc_stc, initial_alpha):
    """
    Fits the measured Isc data to the reference surface by optimizing both
    the STC short-circuit current (Isc_stc) and its temperature coefficient (alpha)
    simultaneously.

    Input Arguments:
    - data (pd.DataFrame)      : Measured data, expects columns 'G_mod', 'T_eff', 'Isc'
    - initial_isc_stc (float) : Initial guess for Isc under STC conditions
    - initial_alpha (float)    : Initial guess for temperature coefficient of Isc

    Returns:
    - adjusted_isc_stc (float): Optimized Isc under STC conditions
    - adjusted_alpha (float)   : Optimized temperature coefficient of Isc
    """
    import numpy as np
    from scipy.optimize import minimize

    # Combined loss function for simultaneous fitting
    def combined_loss(params):
        isc_stc, alpha = params
        predicted = current_calculation(
            isc_stc,
            alpha,
            data["G_mod"],
            data["T_eff"]
        )
        return np.mean((predicted - data["Isc"]) ** 2)

    # Bounds:
    # - Isc_stc between 50% and 120% of its initial guess
    # - alpha within ±20% of its initial guess
    bounds = [
        (initial_isc_stc * 0.5, initial_isc_stc * 1.2),
        (initial_alpha * 1.2,        initial_alpha * 0.8)
    ]

    # Initial parameter vector
    initial_guess = [initial_isc_stc, initial_alpha]

    # Optimize using L-BFGS-B which supports bounds
    result = minimize(
        combined_loss,
        x0=initial_guess,
        bounds=bounds,
        method="L-BFGS-B"
    )

    # Unpack optimized parameters
    adjusted_isc_stc, adjusted_alpha = result.x
    return adjusted_isc_stc, adjusted_alpha

 
def fit_current_data_to_surface_old(data, initial_isc_stc, initial_alpha):
    """
    ## Fits the measured Isc data to the reference surface

    ! This one does not work with the pipeline !

    Input Arguments:
    - data (pd.DataFrame) : Measured data
    - initial_isc_stc (float) : Isc under stc conditions (datasheet!)
    - initial_alpha (float) : Temperature coefficient of the Isc (STC, datasheet!)

    Returns:
    - adjusted_isc_stc (float) : Isc under stc conditions, adjusted with the reference surface
    - adjusted_p_gamma (float) : Temperature coefficient of the Isc, adjusted with the reference surface
    """

    def stc_isc_loss(stc_isc):
        """Loss function for fitting isc_stc (using fixed initial tkp)"""
        predicted = current_calculation(
            stc_isc, initial_alpha, data["G_mod"], data["T_eff"]
        )
        return np.mean((predicted - data["Isc"]) ** 2)

    def alpha_loss(alpha, best_stc_isc):
        """Loss function for fitting tkp (using best stc_pmpp)"""
        predicted = current_calculation(
            best_stc_isc, alpha, data["G_mod"], data["T_eff"]
        )
        return np.mean((predicted - data["Isc"]) ** 2)

    # Schritt 1: Passe Isc_stc an
    # Auf einen vernünftigen Bereich einschränken (z.B. 50-100% des Anfangswerts)
    bounds_stc = ((initial_isc_stc * 0.5, initial_isc_stc * 1.2),)
    result_stc = minimize(stc_isc_loss, initial_isc_stc, bounds=bounds_stc)
    adjusted_isc_stc = result_stc.x[0]

    # Schritt 2: Feinabstimmung von alpha
    # Begrenzen auf kleine Anpassung um den Anfangswert (z.B., ±20%)
    bounds_tkp = ((initial_alpha * 0.8, initial_alpha * 1.2),)
    result_tkp = minimize(
        lambda x: alpha_loss(x, adjusted_isc_stc), initial_alpha, bounds=bounds_tkp
    )
    adjusted_isc = result_tkp.x[0]

    return adjusted_isc_stc, adjusted_isc


def calculate_sra_current_matrix(isc_stc, alpha, correction_factor=0):
    """
    ## Calculate the SRA matrix for the current

    ! This one does not work with the pipeline !

    Input Arguments:
    - isc_stc (float) : Isc under stc conditions (datasheet!)
    - alpha (float) : Temperature coefficient of the Isc (STC, datasheet!)
    - correction_factor : Correction factor for a relative difference to the reference surface

    Returns:
    - pd.DataFrame with the given power at the g-t-pairs
    """
    g_values = [100, 200, 400, 500, 600, 800, 1000, 1100]
    t_values = [15, 25, 45, 50, 75]
    results_list = []

    for g in g_values:
        row = [f"{g} W/m²"]
        for t in t_values:
            current = current_calculation(
                isc_stc,
                alpha,
                g,
                t,
                correction_factor,
            )
            row.append(current)
        results_list.append(row)

    columns = ["Isc / A"] + [f"{t} °C" for t in t_values]
    df = pd.DataFrame(results_list, columns=columns)
    df.set_index("Isc / A", inplace=True)
    return df


def adjust_current_simple(data, isc_stc, alpha):
    """
    ## Adjust the power surface

    ! This one does not work with the pipeline !

    Input Arguments:
    - data (pd.DataFrame) : Measured data
    - isc_stc (float) : Isc under stc conditions (datasheet!)
    - alpha (float) : Temperature coefficient of the Isc (STC, datasheet!)

    Returns:
    - relative_distance : The relative distance between the measured data and the reference surface
    """
    data["Isc_theory"] = current_calculation(
        isc_stc, alpha, data["G_mod"], data["T_eff"]
    )
    data["relative_distance"] = (
        (data["Isc"] - data["Isc_theory"]) / data["Isc_theory"] * 100
    )
    avg_relative_distance = data["relative_distance"].mean()
    return avg_relative_distance
