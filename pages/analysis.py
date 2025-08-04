import os
import time
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from tools.helper import (
    plotly_plot_3d_power,
    plot_random_iv_curves,
    count_filled_bins,
    count_pmpp_pairs,
)

from sra.power import (
    reference_surface,
    adjust_power_simple,
    power_calculation,
    calculate_sra_matrix,
    fit_data_to_surface_new,
)

if "project" not in st.session_state:
    st.session_state["project"] = None

if not st.session_state.project:
    st.info("Aktuell ist kein Projekt geöffnet.")
    if st.button("Projekt auswählen"):
        st.switch_page("pages/open_project.py")
else:
    st.title("SRA Berechnung")

    # data laden
    projects_dir = os.path.join(os.getcwd(), "projects")
    folder_path = os.path.join(projects_dir, st.session_state.project)

    if not os.path.exists(folder_path + "/data_effective.pkl"):
        st.error(
            "Für dieses Projekt liegen noch keine effektiven Betriebsbedingungen vor."
        )
        if st.button("Zurück zur Übersicht"):
            st.switch_page("pages/project_overview.py")
    else:
        data = pd.read_pickle(folder_path + "/data_effective.pkl")
        st.markdown("#### Projekt: " + st.session_state.project)
        st.markdown(
            "Nachfolgend kann eine SRA Berechnung durchgeführt werden. Dazu werden zunächst noch ein paar Werte der "
            "vorliegenden PV-Anlage benötigt. Die Werte sind aus dem Datenblatt zu entnehmen. Es sollten keine "
            "Indoor-Werte genutzt werden."
        )

        if os.path.exists(folder_path + "/matrix.pkl"):
            st.error(
                "Die Leistungsmatrix wurde für dieses Projekt bereits erstellt. Ein erneutes Berechnen"
                " überschreibt die aktuellen Daten."
            )

        tab1, tab2 = st.tabs(["SRA Berechnung", "Rohdaten ansehen"])

        with tab1:
            st.markdown("#### SRA Berechnung")

            p_stc = st.number_input(
                "Modul-Leistung unter STC-Bedingungen [Wp]", min_value=0.01, value=None
            )
            p_gamma = st.number_input(
                "Temperaturkoeffizient der Leistung [%/K]", max_value=-0.01, value=None
            )
            st.write(
                "Die Anzahl der Module bezieht sich auf einen String in Reihe. "
                "Strings müssen immer einzeln betrachtet werden."
            )
            anzahl_module = st.number_input(
                "Anzahl der Module", step=1, min_value=1, value=None
            )

            if (
                p_stc
                and p_gamma
                and anzahl_module
                and st.button("SRA Analyse starten", type="primary")
            ):
                # 1. Referenzfläche erstellen, basierend auf den Werten oben
                ref_surface, t_eff_grid, g_eff_grid = reference_surface(
                    p_stc, p_gamma, anzahl_module
                )

                # 2. Plot the reference surface
                fig2 = plotly_plot_3d_power(data, ref_surface, t_eff_grid, g_eff_grid)
                # st.plotly_chart(fig2, use_container_width=True)

                # 3. Die Verteilung der Daten in der Matrix berechnen
                g_values = [100, 200, 400, 500, 600, 800, 1000, 1100]
                t_values = [15, 25, 45, 50, 75]
                spatial_data = count_pmpp_pairs(data, g_values, t_values)
                is_filled = count_filled_bins(spatial_data)
                # st.write(spatial_data)

                # 4. Schauen wie ich den Fit mache (je nach Verteilung!)
                if is_filled:
                    adjusted_p_stc, adjusted_p_gamma = fit_data_to_surface_new(
                        data, p_stc, p_gamma, anzahl_module
                    )

                    matrix = calculate_sra_matrix(
                        adjusted_p_stc, adjusted_p_gamma, anzahl_module
                    )

                    # 6. Angepasste Referenzfläche erstellen, basierend auf den neuen Werten
                    adjusted_surface, t_eff_grid, g_eff_grid = reference_surface(
                        adjusted_p_stc, adjusted_p_gamma, anzahl_module
                    )
                else:
                    avg_relative_distance = adjust_power_simple(
                        data, p_stc, p_gamma, anzahl_module
                    )

                    matrix = calculate_sra_matrix(
                        p_stc, p_gamma, anzahl_module, avg_relative_distance
                    )

                    # 6. Angepasste Referenzfläche erstellen, basierend auf den neuen Werten
                    adjusted_surface, t_eff_grid, g_eff_grid = reference_surface(
                        p_stc,
                        p_gamma,
                        anzahl_module,
                        correction_factor=avg_relative_distance,
                    )

                with st.status(
                    "SRA Analyse wird durchgeführt...", expanded=True
                ) as status:
                    st.write("Referenzfläche erstellen...")
                    time.sleep(1)
                    st.write("Verteilung der Messdaten betrachten...")
                    time.sleep(1)
                    st.write("Referenzfläche an Messdaten anpassen...")
                    time.sleep(1)
                    status.update(
                        label="SRA-Leistungsmatrix erfolgreich gespeichert.",
                        state="complete",
                        expanded=False,
                    )

                # 5. Die Matrix anzeigen mit Farben (vielleicht) für die Randbereiche in denen keine Punkte sind.

                new_stc_string_power = matrix.loc["1000 W/m²", "25 °C"]
                new_stc_module_power = new_stc_string_power / anzahl_module

                single_module_matrix = matrix / anzahl_module
                single_module_matrix.to_pickle(folder_path + "/single_matrix.pkl")

                datasheet_stc_string_power = p_stc * anzahl_module

                degradation_at_stc = (
                    new_stc_string_power / datasheet_stc_string_power - 1
                ) * 100

                degradation_matrix = (matrix / datasheet_stc_string_power - 1) * 100
                degradation_matrix.to_pickle(folder_path + "/degradation_matrix.pkl")
                matrix.to_pickle(folder_path + "/matrix.pkl")

                st.markdown("#### Referenzfläche und angepasste Referenz")

                ref_surface_tab, adjusted_surface_tab = st.tabs(
                    ["Referenzfläche", "Angepasste Referenzfläche"]
                )

                with ref_surface_tab:
                    st.plotly_chart(fig2, use_container_width=True)
                with adjusted_surface_tab:
                    fig3 = plotly_plot_3d_power(
                        data, adjusted_surface, t_eff_grid, g_eff_grid
                    )
                    st.plotly_chart(fig3, use_container_width=True)

        with tab2:
            st.write(data)
