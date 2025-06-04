import numpy as np
from pipeline.functions import normalize_curve_data
import streamlit as st
import pandas as pd
import time
import os
import json


if "project" not in st.session_state:
    st.session_state["project"] = None

with st.sidebar:
    st.write("Aktuelles Projekt:")
    st.write(st.session_state.project)

st.markdown("# Neues Projekt erstellen")
st.write(
    "Um mit dem SRA oder den anderen Tools zu arbeiten, muss ein Projekt angelegt und konfiguriert werden.",
    "Beginne damit einen Namen für das Projekt auszuwählen:",
)
projects_directory = "projects"
projekte = [
    name
    for name in os.listdir(projects_directory)
    if os.path.isdir(os.path.join(projects_directory, name))
]
title = st.text_input("Names des Projektes", value=None)

# Projektnamen einstellen
if title in projekte:
    st.error(
        "Ein Projekt mit diesem Namen existiert bereits.",
        icon=None,
    )
elif title and title not in projekte:
    st.success("Projektname akzeptiert.", icon="✅")

    st.write(
        "Als nächstes muss das Projekt konfiguriert werden.",
    )

    # Projektparameter eingeben
    if title and title not in projekte:
        st.markdown("### Projektparameter einstellen")
        st.write(
            "Der Isc-Kalibrierwert ist entweder der Isc aus dem Datenblatt unter STC-Bedingungen oder ein selbst "
            "ermittelter Kalibrierwert (bsp. durch eine Indoor-Messung oder Outdoor-Kalibrierung).",
        )
        isc_calib = st.number_input("Isc-Kalibrierwert [A]", min_value=0.01, value=None)
        st.write("Nachfolgend sind alle Parameter aus dem Datenblatt zu entnehmen.")
        isc_alpha = st.number_input(
            "Temperaturkoeffizient des Isc [%/K]", min_value=0.01, value=None
        )

        p_stc = st.number_input(
            "Modul-Leistung unter STC-Bedingungen [Wp]", min_value=0.01, value=None
        )
        p_gamma = st.number_input(
            "Temperaturkoeffizient der Leistung [%/K]", max_value=-0.01, value=None
        )
        st.write(
            "Bezieht sich auf einen String in Reihe. Strings müssen immer einzeln betrachtet werden."
        )
        anzahl_module = st.number_input(
            "Anzahl der Module", step=1, min_value=1, value=None
        )
        st.write("Nachfolgend den Standort der Anlage eingeben.")
        latitude = st.number_input("Längengrad", min_value=0.00000001, value=None)
        longitude = st.number_input("Breitengrad", min_value=0.00000001, value=None)

        st.write("Und zu guter Letzt die Bauform der Anlage.")
        built_type_options = [
            "glass/glass & open rack",
            "glass/glass & close mount",
            "glass/polymer & open rack",
            "glass/polymer & insulated back",
        ]
        built_type = st.selectbox(
            "Bauform der Anlage eingeben.",
            built_type_options,
            index=None,
        )

        if None not in [
            isc_calib,
            isc_alpha,
            p_stc,
            p_gamma,
            anzahl_module,
            latitude,
            longitude,
            built_type,
        ]:
            st.success("Konfiguration erfolgreich ausgefüllt.", icon="✅")

            # Daten hochladen
            st.markdown("### Messdaten hochladen")
            st.write(
                "Nachfolgend müssen die Messdaten hochgeladen werden. Benötigt wird die IV-Kurve des Strings sowie "
                "die Temperatur und Bestrahlungsstärke während der Messung. Alle weiteren für den SRA oder andere Tools"
                " benötigten Funktionen werden automatisch berechnet und gespeichert."
            )
            uploaded_file = st.file_uploader("Messdaten auswählen (nur .pkl möglich)")
            if uploaded_file is not None:
                if not uploaded_file.name.endswith(".pkl"):
                    st.error("Aktuell werden nur .pkl Dateien akzeptiert.")
                else:
                    dataframe = pd.read_pickle(uploaded_file)
                    st.write(dataframe)

                    # Korrekte Spalten auswählen
                    st.markdown("### Datenspalten auswählen")

                    st.write(
                        "Um intern die korrekten Berechnungen durchzuführen, müssen die Spalten der "
                        "Eingabedaten nachfolgend angegeben werden."
                    )

                    # Temperatur Auswahl
                    temperature_options = [
                        "Umgebungstemperatur (T_amb)",
                        "Modul-Temperatur (T_mod)",
                        "Zell-Temperatur (T_eff)",
                    ]
                    temperature = st.radio(
                        "Welche Temperatur ist in den Messdaten vorhanden?",
                        temperature_options,
                        index=None,
                    )

                    if temperature:
                        temperature_column = st.selectbox(
                            "Spalte mit gewählter Temperatur auswählen",
                            dataframe.columns,
                            index=None,
                        )
                    else:
                        temperature_column = None

                    # Bestrahlungsstärke Auswahl
                    irradiance_options = [
                        "Globale Bestrahlungsstärke in Modulebene (GTI bzw. G_mod)",
                        "Zell-Bestrahlungsstärke (G_eff)",
                    ]
                    irradiance = st.radio(
                        "Welche Bestrahlungsstärke ist in den Messdaten vorhanden?",
                        irradiance_options,
                        index=None,
                    )

                    if irradiance:
                        irradiance_column = st.selectbox(
                            "Spalte mit gewählter Bestrahlungsstärke auswählen",
                            dataframe.columns,
                            index=None,
                        )
                    else:
                        irradiance_column = None

                    # Current Auswahl
                    current_column = st.selectbox(
                        "Spalte mit Strom-Messungen der IV-Kennlinie auswählen",
                        dataframe.columns,
                        index=None,
                    )
                    current_configured = False
                    if current_column:
                        if not isinstance(dataframe.iloc[0][current_column], list):
                            st.error(
                                f"Die Daten in der Spalte **{current_column}** liegen nicht als Liste vor."
                            )
                        else:
                            current_configured = True

                    # Voltage Auswahl
                    voltage_column = st.selectbox(
                        "Spalte mit Spannungs-Messungen der IV-Kennlinie auswählen",
                        dataframe.columns,
                        index=None,
                    )
                    voltage_configured = False
                    if voltage_column:
                        if not isinstance(dataframe.iloc[0][voltage_column], list):
                            st.error(
                                f"Die Daten in der Spalte **{voltage_column}** liegen nicht als Liste vor."
                            )
                        else:
                            voltage_configured = True

                    if (
                        None
                        not in [
                            temperature_column,
                            irradiance_column,
                            current_column,
                            voltage_column,
                        ]
                        and current_configured
                        and voltage_configured
                    ):
                        if not isinstance(dataframe.iloc[0][current_column], list):
                            st.error(
                                f"Die Daten in der Spalte **{current_column}** liegen nicht als Liste vor."
                            )
                        if not isinstance(dataframe.iloc[0][voltage_column], list):
                            st.error(
                                f"Die Daten in der Spalte **{voltage_column}** liegen nicht als Liste vor."
                            )
                        st.success("Felder erfolgreich ausgefüllt.", icon="✅")
                        if st.button("Projekt anlegen"):
                            projects_dir = os.path.join(os.getcwd(), "projects")
                            folder_path = os.path.join(projects_dir, title)
                            subfolder_path = os.path.join(folder_path, "raw_data")
                            processed_path = os.path.join(folder_path, "data")

                            def create_project_directory():
                                if not os.path.exists(folder_path):
                                    os.makedirs(folder_path)
                                if not os.path.exists(subfolder_path):
                                    os.makedirs(subfolder_path)
                                if not os.path.exists(processed_path):
                                    os.makedirs(processed_path)

                            def save_dataframe(path, df):
                                df.to_pickle(os.path.join(path, "data.pkl"))

                            def write_config_file():
                                config_data = {
                                    "isc_calib": isc_calib,
                                    "isc_alpha": isc_alpha,
                                    "p_stc": p_stc,
                                    "p_gamma": p_gamma,
                                    "anzahl_module": anzahl_module,
                                    "temperature": temperature,
                                    "temperature_column": temperature_column,
                                    "irradiance_": irradiance,
                                    "irradiance_column": irradiance_column,
                                    "current_column": current_column,
                                    "voltage_column": voltage_column,
                                    "latitude": latitude,
                                    "longitude": longitude,
                                    "built_type": built_type,
                                }

                                # Save the dictionary as a json file in the new folder
                                with open(
                                    os.path.join(folder_path, "config.json"), "w"
                                ) as f:
                                    json.dump(config_data, f)

                            def rename_columns(data):
                                if temperature == "Umgebungstemperatur (T_amb)":
                                    new_temp_column = "T_amb"
                                elif temperature == "Modul-Temperatur (T_mod)":
                                    new_temp_column = "T_mod"
                                elif temperature == "Zell-Temperatur (T_eff)":
                                    new_temp_column = "T_eff"

                                if (
                                    irradiance
                                    == "Globale Bestrahlungsstärke in Modulebene (GTI bzw. G_mod)"
                                ):
                                    new_irr_column = "G_mod"
                                elif irradiance == "Zell-Bestrahlungsstärke (G_eff)":
                                    new_irr_column = "G_eff"

                                new_column_names = {
                                    current_column: "Current",
                                    voltage_column: "Voltage",
                                    temperature_column: new_temp_column,
                                    irradiance_column: new_irr_column,
                                }
                                return data.rename(columns=new_column_names)

                            def extract_iv_parameters(data):
                                def calculate_parameters(row):
                                    current = row["Current"]
                                    voltage = row["Voltage"]
                                    Isc = max(current)
                                    Voc = max(voltage)
                                    power = np.array(current) * np.array(voltage)
                                    mpp = np.argmax(power)
                                    Pmpp = power[mpp]
                                    Impp = current[mpp]
                                    Vmpp = voltage[mpp]

                                    return pd.Series(
                                        [Isc, Voc, Pmpp, Impp, Vmpp],
                                        index=["Isc", "Voc", "Pmpp", "Impp", "Vmpp"],
                                    )

                                parameters = data.apply(calculate_parameters, axis=1)
                                data = pd.concat([data, parameters], axis=1)

                                return data

                            with st.status(
                                "Projekt wird erstellt...", expanded=True
                            ) as status:
                                st.write("Projektordner erstellen...")
                                create_project_directory()
                                time.sleep(1)
                                st.write("Rohdaten speichern...")
                                save_dataframe(subfolder_path, dataframe)
                                time.sleep(1)
                                st.write("Config-Datei erstellen...")
                                write_config_file()
                                time.sleep(1)
                                st.write("Bearbeite DataFrame...")
                                dataframe = rename_columns(dataframe)
                                dataframe = normalize_curve_data(dataframe)
                                dataframe = extract_iv_parameters(dataframe)
                                save_dataframe(processed_path, dataframe)
                                st.session_state.project = title
                                st.switch_page("pages/2_Projekt_öffnen.py")
