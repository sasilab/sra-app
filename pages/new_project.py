import os
import time
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from tools.helper import extract_curve_parameters, plot_random_iv_curves


if "project" not in st.session_state:
    st.session_state["project"] = None

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
    st.write("Als nächstes müssen die Messdaten hochgeladen werden.")

    # Daten hochladen
    st.markdown("### Messdaten hochladen")
    st.write(
        "Nachfolgend müssen die Messdaten hochgeladen werden. Benötigt werden die IV-Kurven des Strings sowie "
        "die Temperatur und Bestrahlungsstärke während der Messung."
    )

    # File Upload
    uploaded_file = st.file_uploader("Messdaten auswählen (nur .pkl möglich)")
    if uploaded_file is not None:
        if not uploaded_file.name.endswith(".pkl"):
            st.error("Aktuell werden nur .pkl Dateien akzeptiert.")
        else:
            dataframe = pd.read_pickle(uploaded_file)
            st.write(dataframe)

            # Korrekte Spalten auswählen
            st.markdown("### Datenspalten für IV-Kurven auswählen")
            st.write(
                "Für die Darstellung und Verarbeitung der IV-Kurven müssen diese in als Liste im übergebenen DataFrame"
                " gespeichert werden."
            )

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

            if current_configured and voltage_configured:
                st.success("IV-Kurven erfolgreich ausgewählt.", icon="✅")
                st.plotly_chart(
                    plot_random_iv_curves(dataframe, current_column, voltage_column, 5),
                    use_container_width=True,
                )

                if st.button("Projekt anlegen und speichern"):
                    projects_dir = os.path.join(os.getcwd(), "projects")

                    # Create the directory with the new title
                    folder_path = os.path.join(projects_dir, title)
                    if not os.path.exists(folder_path):
                        os.makedirs(folder_path)

                    # Rename the columns of current and voltage
                    new_column_names = {
                        current_column: "Current",
                        voltage_column: "Voltage",
                    }
                    dataframe = dataframe.rename(columns=new_column_names).copy()

                    # Extract curve params
                    dataframe = extract_curve_parameters(dataframe)

                    dataframe.to_pickle(os.path.join(folder_path, "data.pkl"))

                    with st.status(
                        "Projekt wird erstellt...", expanded=False
                    ) as status:
                        st.write("Projektordner erstellen...")
                        time.sleep(1)
                        st.write("Rohdaten speichern...")
                        time.sleep(1)
                        st.write("Bearbeite DataFrame...")
                        st.session_state.project = title

                    time.sleep(1)
                    st.switch_page("pages/project_overview.py")
