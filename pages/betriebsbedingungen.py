import os
import time
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from sra.temperature import (
    cell_from_module_temperature,
    module_from_ambient_temperature,
)
from sra.current import (
    fit_current_data_to_surface,
    calculate_sra_current_matrix,
    adjust_current_simple,
)
from sra.irradiance import effective_irradiance

from tools.helper import count_current_pairs, count_filled_bins

if "project" not in st.session_state:
    st.session_state["project"] = None

if not st.session_state.project:
    st.info("Aktuell ist kein Projekt geöffnet.")
    if st.button("Projekt auswählen"):
        st.switch_page("pages/open_project.py")
else:
    st.title("Effektive Betriebsbedingungen berechnen")

    st.markdown("#### Projekt: " + st.session_state.project)
    st.markdown(
        "Um später die Leistungsmatrix mit dem SRA zu bestimmen, müssen die Betriebsbedingungen zunächst "
        "in die effektiven (für die Zelle wirksamen) Bedingungen umgerechnet werden. Genauer geht es darum die "
        "effektive Zelltemperatur $T_{eff}$ und effektive Bestrahlungsstärke $G_{eff}$ aus den gegebenen Messdaten zu "
        "berechnen."
    )

    projects_dir = os.path.join(os.getcwd(), "projects")
    folder_path = os.path.join(projects_dir, st.session_state.project)

    if not os.path.exists(folder_path + "/data_filtered.pkl"):
        st.error("Für dieses Projekt liegen noch keine gefilterten Daten vor.")
        if st.button("Zurück zur Übersicht"):
            st.switch_page("pages/project_overview.py")
    else:
        if "data_filtered" not in st.session_state:
            st.session_state.data_filtered = pd.read_pickle(
                folder_path + "/data_filtered.pkl"
            )

        if os.path.exists(folder_path + "/data_effective.pkl"):
            st.error(
                "Die effektiven Betriebsbedingungen wurden für dieses Projekt bereits erstellt. Ein erneutes Berechnen"
                " überschreibt die aktuellen Daten."
            )

        tab1, tab2 = st.tabs(["Konfiguration", "Rohdaten ansehen"])

        with tab1:
            # Temperatur Auswahl
            st.markdown("#### Temperatur Konfiguration")
            temperature_options = [
                "Umgebungstemperatur $T_{amb}$",
                "Modul-Temperatur $T_{mod}$",
            ]
            temperature = st.radio(
                "Welche Temperatur ist in den Messdaten vorhanden?",
                temperature_options,
                index=None,
            )

            temperature_column = st.selectbox(
                "Spalte mit gewählter Temperatur auswählen",
                st.session_state.data_filtered.columns,
                index=None,
            )

            module_type = st.selectbox(
                "Modul-Typ eingeben", ("glass/glass", "glass/polymer"), index=None
            )

            bauform = st.selectbox(
                "Bauform eingeben",
                ("open_rack", "insulated_back", "close_mount"),
                index=None,
            )

            st.markdown("#### Bestrahlungsstärke Konfiguration")

            irradiance_column = st.selectbox(
                "Spalte mit Modul-Bestrahlungsstärke auswählen",
                st.session_state.data_filtered.columns,
                index=None,
            )

            st.markdown(
                "Der $I_{SC,STC}$ ist aus dem Datenblatt unter STC-Bedingungen zu entnehmen."
            )
            isc_calib = st.number_input(
                "Kurschlussstrom $I_{SC,STC}$ [A]", min_value=0.01, value=None
            )
            isc_alpha = st.number_input(
                "Temperaturkoeffizient des $I_{SC}$ [%/K]",
                min_value=0.01,
                value=None,
            )

            st.markdown("#### Windgeschwindigkeit hinterlegen (optional)")

            wind_column = st.selectbox(
                "Spalte mit Windgeschwindigkeit auswählen (optional)",
                st.session_state.data_filtered.columns,
                index=None,
            )

            if (
                temperature_column
                and module_type
                and bauform
                and irradiance_column
                and isc_calib
                and isc_alpha
            ):
                if st.button("Effektive Betriebsbedingungen berechnen", type="primary"):
                    new_column = (
                        "T_amb"
                        if temperature == "Umgebungstemperatur $T_{amb}$"
                        else "T_mod"
                    )
                    new_column_names = {
                        temperature_column: new_column,
                        irradiance_column: "G_mod",
                    }
                    st.session_state.data_filtered = (
                        st.session_state.data_filtered.rename(
                            columns=new_column_names
                        ).copy()
                    )

                    if new_column == "T_amb":
                        st.session_state.data_filtered = (
                            module_from_ambient_temperature(
                                st.session_state.data_filtered, module_type, bauform
                            ).copy()
                        )

                    st.session_state.data_filtered = cell_from_module_temperature(
                        st.session_state.data_filtered, module_type, bauform
                    ).copy()
                    st.session_state.data_filtered = effective_irradiance(
                        st.session_state.data_filtered, isc_calib, isc_alpha
                    ).copy()

                    st.session_state.data_filtered.to_pickle(
                        os.path.join(folder_path, "data_effective.pkl")
                    )

                    try:
                        g_values = [100, 200, 400, 500, 600, 800, 1000, 1100]
                        t_values = [15, 25, 45, 50, 75]
                        spatial_data = count_current_pairs(
                            st.session_state.data_filtered, g_values, t_values
                        )

                        if count_filled_bins(spatial_data):
                            adjusted_isc_stc, adjusted_alpha = (
                                fit_current_data_to_surface(
                                    st.session_state.data_filtered, isc_calib, isc_alpha
                                )
                            )
                            current_matrix = calculate_sra_current_matrix(
                                adjusted_isc_stc, adjusted_alpha
                            )
                        else:
                            avg_relative_distance = adjust_current_simple(
                                st.session_state.data_filtered, isc_calib, isc_alpha
                            )
                            current_matrix = calculate_sra_current_matrix(
                                isc_calib, isc_alpha, avg_relative_distance
                            )
                        current_degradation_matrix = (
                            current_matrix / isc_calib - 1
                        ) * 100
                        current_degradation_matrix.to_pickle(
                            folder_path + "/current_degradation_matrix.pkl"
                        )
                        current_matrix.to_pickle(folder_path + "/current_matrix.pkl")
                    except Exception as e:
                        print(e)

                    with st.status(
                        "$T_{eff}$ und $G_{eff}$ werden berechnet...", expanded=True
                    ) as status:
                        st.write("$T_{eff}$ berechnen...")
                        time.sleep(1)
                        st.write("$G_{eff}$ berechnen...")
                        time.sleep(1)
                        st.write("Daten speichern...")
                        time.sleep(1)
                        status.update(
                            label="$T_{eff}$ und $G_{eff}$ erfolgreich gespeichert.",
                            state="complete",
                            expanded=False,
                        )
        with tab2:
            st.write(st.session_state.data_filtered)
