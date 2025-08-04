"""
Helper functions for any other task outside the DataPipeline.
"""

import os
import shutil
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta, datetime


def plotly_plot_3d_power(
    dataframe: pd.DataFrame,
    ref_surface=None,
    t_surface=None,
    g_surface=None,
    scatter_label="Scatter Points",
    surface_label="Surface",
):
    """
    ## Plotting the 3D power scatter chart.

    Input Arguments:
    - pd.DataFrame

    Returns:
    - fig for plotly
    """
    scatter_trace = go.Scatter3d(
        x=dataframe["G_eff"],
        y=dataframe["T_eff"],
        z=dataframe["Pmpp"],
        mode="markers",
        marker=dict(size=2, color="red"),
        name=scatter_label,
        showlegend=True,
    )

    fig = go.Figure(data=[scatter_trace])
    if ref_surface is not None and t_surface is not None and g_surface is not None:
        surface_trace = go.Surface(
            z=ref_surface,
            x=g_surface,
            y=t_surface,
            name=surface_label,
            showscale=False,
            showlegend=True,
        )
        fig.add_trace(surface_trace)

    fig.update_layout(
        scene=dict(
            xaxis_title="G<sub>eff</sub> (W/m²)",
            yaxis_title="T<sub>eff</sub> (°C)",
            zaxis_title="P<sub>mpp</sub> (W)",
        ),
        legend=dict(title="Legend"),
    )
    return fig


def plot_random_iv_curves(
    dataframe: pd.DataFrame, current_column, voltage_column, samples=5
):
    """
    ## Plots a given number of random IV curves from a dataframe.

    Input Arguments:
    - pd.DataFrame
    - current_column: The name of the column in the dataframe that contains the current IV curves
    - voltage_column: The name of the column in the dataframe that contains the voltage curves
    - samples: The number of random IV curves to plot, default=5

    Returns:
    - fig for plotly
    """
    num_rows_to_sample = min(len(dataframe), samples)
    random_rows = dataframe.sample(n=num_rows_to_sample, random_state=42)
    fig = go.Figure()

    for index, row in random_rows.iterrows():
        current_list = row[current_column]
        voltage_list = row[voltage_column]

        fig.add_trace(
            go.Scatter(
                x=voltage_list,
                y=current_list,
                mode="lines+markers",
                name=f"Row {index}",
            )
        )
    fig.update_layout(
        title="5 Beispiel IV-Kurven aus dem Datensatz",
        xaxis_title="<i>V</i> (V)",
        yaxis_title="<i>I</i> (A)",
    )
    return fig


def plot_reconstructions(
    dataframe: pd.DataFrame, current_column, voltage_column, reconstruction_column
):
    """
    Plots a grid of 4 random IV curves from a dataframe, showing both the original
    and reconstructed currents over the voltage.

    Input Arguments:
    - dataframe: pd.DataFrame containing the data
    - current_column: The name of the column with the original current IV curves
    - voltage_column: The name of the column with the voltage curves
    - reconstruction_column: The name of the column with the reconstructed current IV curves

    Returns:
    - fig for plotly
    """
    num_rows_to_sample = min(len(dataframe), 4)
    random_rows = dataframe.sample(n=num_rows_to_sample, random_state=42)

    fig = make_subplots(
        rows=4, cols=1, subplot_titles=[f"Row {index}" for index in random_rows.index]
    )

    original_color = "green"
    reconstructed_color = "red"

    for i, (index, row) in enumerate(random_rows.iterrows()):
        current_list = row[current_column]
        voltage_list = row[voltage_column]
        reconstruction_list = row[reconstruction_column]

        row_pos = i + 1

        fig.add_trace(
            go.Scatter(
                x=voltage_list,
                y=current_list,
                mode="lines+markers",
                name="Original",
                line=dict(color=original_color),
                legendgroup="Original",
            ),
            row=row_pos,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=voltage_list,
                y=reconstruction_list,
                mode="lines+markers",
                name="Reconstructed",
                line=dict(color=reconstructed_color, dash="dash"),
                legendgroup="Reconstructed",
            ),
            row=row_pos,
            col=1,
        )

    fig.update_layout(
        title="Random IV Curves with Reconstructions",
        xaxis_title="<i>V</i> (V)",
        yaxis_title="<i>I</i> (A)",
        showlegend=True,
        legend=dict(x=1.05, y=1, traceorder="normal"),
        height=1400,
    )
    return fig


def create_new_project(project_name: str):
    """
    ## Creating a new project

    Create a new project inside the projects directory with the name of the project. " " are removed.
    If a project already exists, the user is asked if the project should be overwritten. If yes, it deletes the directory
    and adds a new one. If no, it asks for a new name in the terminal and checks again with the answer.

    Input Arguments:
    - project_name (str): The name of the project to create

    Returns:
    - Boolean success or failure state.
    """
    try:
        clean_name = project_name.replace(" ", "")
        if not clean_name:
            new_name = input("Project name cannot be empty. Enter new project name: ")
            return create_new_project(new_name)

        project_path = os.path.join("projects", clean_name)

        if os.path.exists(project_path):
            while True:
                response = input(
                    f"Project {clean_name} already exists. Overwrite? (y/n): "
                ).lower()
                if response == "y":
                    shutil.rmtree(project_path)
                    os.makedirs(project_path)
                    print(f"Project {clean_name} created")
                    return True
                elif response == "n":
                    new_name = input("Enter new project name: ")
                    return create_new_project(new_name)
                else:
                    print("Please answer 'y' or 'n'")
        else:
            os.makedirs(project_path)
            print(f"Project {clean_name} created")
            return True

    except Exception as e:
        print(f"Error creating project: {str(e)}")
        return False


def calculate_parameters(row):
    """
    ## Calculating the Curve params

    Extract the important curve params like the Pmpp, Isc, ...

    Input Arguments:
    - a DataFrame row

    Returns:
    - pd.Series with Isc, Voc, ...
    """
    current = row["Current"]
    voltage = row["Voltage"]
    isc = max(current)
    voc = max(voltage)
    power = np.array(current) * np.array(voltage)
    mpp = np.argmax(power)
    pmpp = power[mpp]
    impp = current[mpp]
    vmpp = voltage[mpp]

    return pd.Series(
        [isc, voc, pmpp, impp, vmpp],
        index=["Isc", "Voc", "Pmpp", "Impp", "Vmpp"],
    )

import ast

def calculate_parameters_new(row):
    """
    ## Calculating the Curve params

    Extract the important curve params like the Pmpp, Isc, ...

    Input Arguments:
    - a DataFrame row

    Returns:
    - pd.Series with Isc, Voc, ...
    """
    current = row["Current"]
    voltage = row["Voltage"]

    # ✅ Ensure both are actual lists
    if isinstance(current, str):
        try:
            current = ast.literal_eval(current)
        except:
            return pd.Series([None] * 5, index=["Isc", "Voc", "Pmpp", "Impp", "Vmpp"])
    if isinstance(voltage, str):
        try:
            voltage = ast.literal_eval(voltage)
        except:
            return pd.Series([None] * 5, index=["Isc", "Voc", "Pmpp", "Impp", "Vmpp"])

    # ✅ Skip if not valid numeric lists
    if not (isinstance(current, list) and isinstance(voltage, list)):
        return pd.Series([None] * 5, index=["Isc", "Voc", "Pmpp", "Impp", "Vmpp"])
    if not current or not voltage:
        return pd.Series([None] * 5, index=["Isc", "Voc", "Pmpp", "Impp", "Vmpp"])

    try:
        isc = max(current)
        voc = max(voltage)
        power = np.array(current) * np.array(voltage)
        mpp = np.argmax(power)
        pmpp = power[mpp]
        impp = current[mpp]
        vmpp = voltage[mpp]

        return pd.Series([isc, voc, pmpp, impp, vmpp], index=["Isc", "Voc", "Pmpp", "Impp", "Vmpp"])
    except Exception:
        return pd.Series([None] * 5, index=["Isc", "Voc", "Pmpp", "Impp", "Vmpp"])


def extract_curve_parameters(dataframe: pd.DataFrame):
    """
    ## Extracting the curve params

    Using the calculate_parameters function to get the curve params and storing them in the dataframe.

    Input Arguments:
    - pd.DataFrame

    Returns:
    - pd.DataFrame with added curve params
    """
    parameters = dataframe.apply(calculate_parameters, axis=1)
    data = pd.concat([dataframe, parameters], axis=1)

    return data


def count_pmpp_pairs(df, g_values, t_values, g_tol=75, t_tol=10):
    """
    ## Counts the number of Pmpp pairs in a given bin

    This is important when checking if the measured data can be fitted to the SRA surface or not.

    Input Arguments:
    - a DataFrame with G_eff, T_eff and Pmpp
    - g_values: A list with G values (from the G-T-pairs of the matrix)
    - t_values: A list with T values (from the G-T-pairs of the matrix)
    - g_tol: The tolerance value for the G values around the given point, default 75 W/m²
    - t_tol: The tolerance value for the T values around the given point, default 10 °C

    Returns:
    - a matrix with the counted number of Pmpp pairs
    """
    counts_matrix = np.zeros((len(t_values), len(g_values)), dtype=int)

    for i, t in enumerate(t_values):
        for j, g in enumerate(g_values):
            within_tolerance = df[
                (df["G_eff"].between(g - g_tol, g + g_tol))
                & (df["T_eff"].between(t - t_tol, t + t_tol))
            ]
            counts_matrix[i, j] = within_tolerance["Pmpp"].count()

    return counts_matrix


def count_current_pairs(df, _g_values, _t_values, g_tol=75, t_tol=10):
    """
    ## Counts the number of Isc pairs in a given bin

    This is important when checking if the measured data can be fitted to the SRA surface or not.

    Input Arguments:
    - a DataFrame with G_eff, T_eff and Isc
    - _g_values: A list with G values (from the G-T-pairs of the matrix)
    - _t_values: A list with T values (from the G-T-pairs of the matrix)
    - g_tol: The tolerance value for the G values around the given point, default 75 W/m²
    - t_tol: The tolerance value for the T values around the given point, default 10 °C

    Returns:
    - a matrix with the counted number of Pmpp pairs
    """
    counts_matrix = np.zeros((len(_t_values), len(_g_values)), dtype=int)

    for i, t in enumerate(_t_values):
        for j, g in enumerate(_g_values):
            within_tolerance = df[
                (df["G_eff"].between(g - g_tol, g + g_tol))
                & (df["T_eff"].between(t - t_tol, t + t_tol))
            ]
            counts_matrix[i, j] = within_tolerance["Isc"].count()

    return counts_matrix


def count_filled_bins(matrix, threshold=4, percentage=0.15):
    """
    ## Counts if at least 15% of the bins in a given matrix are filled with at least 4 points per bin

    This is important when checking if the measured data can be fitted to the SRA surface or not.

    Input Arguments:
    - a matrix with bin counts
    - threshold: The number of points above which the bin is filled
    - percentage: The percentage of how many of the total bins should be filled

    Returns:
    - a Boolean if at least 15% of the bins are filled
    """
    filled_bins = np.sum(matrix >= threshold)
    total_bins = matrix.size
    return filled_bins / total_bins >= percentage


def schedule_measurements(df, forecast_df, num_measurements, delay):
    """
    ## Function used to schedule upcoming measurements.
    """
    current_time = datetime.now()
    end_time = current_time + timedelta(hours=24)
    forecast_24h = forecast_df[
        (forecast_df.index >= current_time) & (forecast_df.index <= end_time)
    ]
    missing_pairs = []
    for irradiance in df.index:
        for temp in df.columns:
            if df.loc[irradiance, temp] < 5:
                missing_pairs.append((irradiance, temp))
    scheduled_times = []
    last_scheduled_time = None

    for index, row in forecast_24h.iterrows():
        if len(scheduled_times) >= num_measurements:
            break
        for irradiance, temp in missing_pairs:
            if (
                float(irradiance[:-5]) - 75
                <= row["G_mod"]
                <= float(irradiance[:-5]) + 75
            ) and (float(temp[:-3]) - 10 <= row["T_eff"] <= float(temp[:-3]) + 10):
                if last_scheduled_time is None or (
                    index - last_scheduled_time
                ) >= timedelta(minutes=delay):
                    scheduled_times.append((index, row["G_mod"]))
                    last_scheduled_time = index
                    break

    return scheduled_times
