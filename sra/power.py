"""
All functions for estimating the power of the system based on the reference surface fit
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize


def power_calculation(
    p_mpp, p_gamma, anzahl_module, irradiance, temperature, correction_factor=0
):
    """
    ## Calculate the power based on the linear approximation

    ! This one does not work with the pipeline !

    Input Arguments:
    - p_mpp (float) : Power under stc conditions (datasheet!)
    - p_gamma (float) : Temperature coefficient of the power (STC, datasheet!)
    - anzahl_module (int) : Number of modules in the string.
    - irradiance : Irradiation values given as single values or a list or grid
    - temperature : Temperature value given as single values or a list or grid
    - correction_factor : Correction factor for a relative difference to the reference surface

    Returns:
    - The calculated power values
    """
    return (
        anzahl_module
        * p_mpp
        * irradiance
        / 1000
        * (1 + p_gamma * (temperature - 25) / 100)
    ) * (1 + correction_factor / 100)


def reference_surface(p_mpp, p_gamma, anzahl_module, correction_factor=0):
    """
    ## Calculate the reference surface power according to the datasheet of the modules.

    ! This one does not work with the pipeline !

    Input Arguments:
    - p_mpp (float) : Power under stc conditions (datasheet!)
    - p_gamma (float) : Temperature coefficient of the power (STC, datasheet!)
    - anzahl_module (int) : Number of modules in the string.

    Returns:
    - power_surface : Theoretical datasheet power for the G-T-Matrix
    - t_eff_grid : T values from 10 to 80°C as a grid
    - g_eff_grid: G values from 50 to 1200 W/m² as a grid

     References
    ----------
    - [1]
    ---
    """
    t_eff = np.linspace(10, 80, 100)
    g_eff = np.linspace(50, 1200, 100)
    t_eff_grid, g_eff_grid = np.meshgrid(t_eff, g_eff)

    power_surface = power_calculation(
        p_mpp, p_gamma, anzahl_module, g_eff_grid, t_eff_grid, correction_factor
    )
    return power_surface, t_eff_grid, g_eff_grid


def adjust_power_simple(data, p_mpp, p_gamma, anzahl_module):
    """
    ## Adjust the power surface

    ! This one does not work with the pipeline !

    Input Arguments:
    - data (pd.DataFrame) : Measured data
    - p_mpp (float) : Power under stc conditions (datasheet!)
    - p_gamma (float) : Temperature coefficient of the power (STC, datasheet!)
    - anzahl_module (int) : Number of modules in the string.

    Returns:
    - relative_distance : The relative distance between the measured data and the reference surface
    """
    data["P_theory"] = power_calculation(
        p_mpp, p_gamma, anzahl_module, data["G_eff"], data["T_eff"]
    )
    data["relative_distance"] = (
        (data["Pmpp"] - data["P_theory"]) / data["P_theory"] * 100
    )
    avg_relative_distance = data["relative_distance"].mean()
    return avg_relative_distance

def fit_data_to_surface_new(data, initial_stc_pmpp, initial_tkp, anzahl_module):
    """
    Fits the measured data to the reference surface by optimizing both STC power
    (Pmpp) and temperature coefficient (tkp) simultaneously.

    Input Arguments:
    - data (pd.DataFrame)       : Measured data, expects columns 'G_eff', 'T_eff', 'Pmpp'
    - initial_stc_pmpp (float)  : Initial guess for power under STC conditions
    - initial_tkp (float)       : Initial guess for temperature coefficient of power
    - anzahl_module (int)       : Number of modules in the string

    Returns:
    - adjusted_p_mpp (float)    : Optimized STC power
    - adjusted_p_gamma (float)  : Optimized temperature coefficient
    """
    import numpy as np
    from scipy.optimize import minimize

    # Combined loss function for both parameters
    def combined_loss(params):
        stc_pmpp, tkp = params
        predicted = power_calculation(
            stc_pmpp,
            tkp,
            anzahl_module,
            data["G_eff"],
            data["T_eff"]
        )
        return np.mean((predicted - data["Pmpp"]) ** 2)

    # Define bounds for simultaneous fitting:
    # - STC Pmpp: between 50% and 120% of the initial guess
    # - tkp     : within ±20% of the initial guess
    bounds = [
        (initial_stc_pmpp * 0.5, initial_stc_pmpp * 1.2),
        (initial_tkp * 1.2,        initial_tkp * 0.8)
    ]

    # Run optimization
    initial_guess = [initial_stc_pmpp, initial_tkp]
    result = minimize(
        combined_loss,
        x0=initial_guess,
        bounds=bounds,
        method="L-BFGS-B"
    )

    # Extract optimized parameters
    adjusted_p_mpp, adjusted_p_gamma = result.x
    return adjusted_p_mpp, adjusted_p_gamma

 
def fit_data_to_surface(data, initial_stc_pmpp, initial_tkp, anzahl_module):
    """
    ## Fits the measured data to the reference surface

    ! This one does not work with the pipeline !

    Input Arguments:
    - data (pd.DataFrame) : Measured data
    - p_mpp (float) : Power under stc conditions (datasheet!)
    - p_gamma (float) : Temperature coefficient of the power (STC, datasheet!)
    - anzahl_module (int) : Number of modules in the string.

    Returns:
    - adjusted_p_mpp (float) : Power under stc conditions, adjusted with the reference surface
    - adjusted_p_gamma (float) : Temperature coefficient of the power, adjusted with the reference surface
    """

    def stc_pmpp_loss(stc_pmpp):
        """Loss function for fitting stc_pmpp (using fixed initial tkp)"""
        predicted = power_calculation(
            stc_pmpp, initial_tkp, anzahl_module, data["G_eff"], data["T_eff"]
        )
        return np.mean((predicted - data["Pmpp"]) ** 2)

    def tkp_loss(tkp, best_stc_pmpp):
        """Loss function for fitting tkp (using best stc_pmpp)"""
        predicted = power_calculation(
            best_stc_pmpp, tkp, anzahl_module, data["G_eff"], data["T_eff"]
        )
        return np.mean((predicted - data["Pmpp"]) ** 2)

    # Schritt 1: Passe stc_pmpp an
    # Auf einen vernünftigen Bereich einschränken (z.B. 50-100% des Anfangswerts)
    bounds_stc = ((initial_stc_pmpp * 0.5, initial_stc_pmpp * 1.2),)
    result_stc = minimize(stc_pmpp_loss, initial_stc_pmpp, bounds=bounds_stc)
    adjusted_p_mpp = result_stc.x[0]

    # Schritt 2: Feinabstimmung von tkp
    # Begrenzen auf kleine Anpassung um den Anfangswert (z.B., ±20%)
    bounds_tkp = ((initial_tkp * 1.2, initial_tkp * 0.8),)
    result_tkp = minimize(
        lambda x: tkp_loss(x, adjusted_p_mpp), initial_tkp, bounds=bounds_tkp
    )
    adjusted_p_gamma = result_tkp.x[0]

    return adjusted_p_mpp, adjusted_p_gamma


def calculate_sra_matrix(p_mpp, p_gamma, anzahl_module, correction_factor=0):
    """
    ## Calculate the SRA matrix

    ! This one does not work with the pipeline !

    Input Arguments:
    - p_mpp (float) : Power under stc conditions (datasheet!)
    - p_gamma (float) : Temperature coefficient of the power (STC, datasheet!)
    - anzahl_module (int) : Number of modules in the string.
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
            power = power_calculation(
                p_mpp,
                p_gamma,
                anzahl_module,
                g,
                t,
                correction_factor,
            )
            row.append(power)
        results_list.append(row)

    columns = ["Pmpp / W"] + [f"{t} °C" for t in t_values]
    df = pd.DataFrame(results_list, columns=columns)
    df.set_index("Pmpp / W", inplace=True)
    return df
