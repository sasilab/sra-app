import os

import pandas as pd
import streamlit as st

from tools.helper import plot_random_iv_curves


if "project" not in st.session_state:
    st.session_state["project"] = None
if not st.session_state.project:
    st.info("Aktuell ist kein Projekt geöffnet.")
    if st.button("Projekt auswählen"):
        st.switch_page("pages/open_project.py")
else:
    st.title(st.session_state.project)
    projects_dir = os.path.join(os.getcwd(), "projects")
    folder_path = os.path.join(projects_dir, st.session_state.project)

    st.markdown(
        "Mit dem Selbstreferenzierungsalgorithmus (SRA) kann die Leistung eines PV-Strings unter Freifeldbedingungen "
        "bestimmt werden. Benötigt werden die gemessenen IV-Kurven, ein paar Parameter aus dem Datenblatt, sowie die "
        "zeitgleich gemessenen Betriebsbedingungen."
    )

    data_is_filtered = (
        True if os.path.exists(folder_path + "/data_filtered.pkl") else False
    )
    effective_data_is_calculated = (
        True if os.path.exists(folder_path + "/data_effective.pkl") else False
    )
    power_matrix_is_calculated = (
        True if os.path.exists(folder_path + "/matrix.pkl") else False
    )
    checkliste = st.container(border=True)
    with checkliste:
        st.markdown("#### Checkliste zur Projektbearbeitung")
        st.checkbox(
            "Filtern der Daten nach homogenen Betriebsbedingungen",
            value=data_is_filtered,
            disabled=True,
        )
        if not data_is_filtered:
            if st.button("Filtern der Daten jetzt durchführen", type="primary"):
                st.switch_page("pages/filtering.py")

        st.checkbox(
            "Berechnung der effektiven Betriebsbedingungen",
            value=effective_data_is_calculated,
            disabled=True,
        )
        if data_is_filtered and not effective_data_is_calculated:
            if st.button(
                "Berechnung der effektiven Betriebsbedingungen jetzt vornehmen",
                type="primary",
            ):
                st.switch_page("pages/betriebsbedingungen.py")
        st.checkbox(
            "SRA Leistungsmatrix berechnen",
            value=power_matrix_is_calculated,
            disabled=True,
        )
        if (
            data_is_filtered
            and effective_data_is_calculated
            and not power_matrix_is_calculated
        ):
            if st.button(
                "Berechnung der SRA Leistungsmatrix jetzt vornehmen", type="primary"
            ):
                st.switch_page("pages/analysis.py")

    if power_matrix_is_calculated:
        st.markdown("## Projekt-Ergebnisse")

        power_matrix = pd.read_pickle(folder_path + "/matrix.pkl")
        single_module_matrix = pd.read_pickle(folder_path + "/single_matrix.pkl")
        power_degradation_matrix = pd.read_pickle(
            folder_path + "/degradation_matrix.pkl"
        )

        new_stc_string_power = power_matrix.loc["1000 W/m²", "25 °C"]
        new_stc_module_power = single_module_matrix.loc["1000 W/m²", "25 °C"]
        power_degradation = power_degradation_matrix.loc["1000 W/m²", "25 °C"]

        current_matrix_is_calculated = (
            True if os.path.exists(folder_path + "/current_matrix.pkl") else False
        )
        if current_matrix_is_calculated:
            current_matrix = pd.read_pickle(folder_path + "/current_matrix.pkl")
            current_degradation_matrix = pd.read_pickle(
                folder_path + "/current_degradation_matrix.pkl"
            )
            new_stc_current = current_matrix.loc["1000 W/m²", "25 °C"]
            current_degradation = current_degradation_matrix.loc["1000 W/m²", "25 °C"]

            a, b, c = st.columns(3)

            a.metric(
                "STC String-Leistung",
                f"{new_stc_string_power:.2f} W",
                f"{power_degradation:.2f} % Leistungsverlust",
                border=True,
            )
            b.metric(
                "STC Modul-Leistung",
                f"{new_stc_module_power:.2f} W",
                f"{power_degradation:.2f} % Leistungsverlust",
                border=True,
            )
            c.metric(
                "STC Kurzschlussstrom",
                f"{new_stc_current:.2f} A",
                f"{current_degradation:.2f} % Verlust",
                border=True,
            )
        else:
            a, b = st.columns(2)

            a.metric(
                "STC String-Leistung",
                f"{new_stc_string_power:.2f} W",
                f"{power_degradation:.2f} % Leistungsverlust",
                border=True,
            )
            b.metric(
                "STC Modul-Leistung",
                f"{new_stc_module_power:.2f} W",
                f"{power_degradation:.2f} % Leistungsverlust",
                border=True,
            )

        st.markdown("#### Ergebnismatrix nach DIN EN 61853-1")
        st.dataframe(power_matrix, width=2000)
