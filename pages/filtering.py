import os
import time
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from tensorflow.keras.models import load_model
from sklearn.metrics import mean_squared_error
from pipeline.functions import normalize_curve_data
from tools.helper import plotly_plot_3d_power, plot_random_iv_curves


if "project" not in st.session_state:
    st.session_state["project"] = None

if "loaded_model" not in st.session_state:
    st.session_state["loaded_model"] = None
    st.session_state["model_name"] = None

if not st.session_state.project:
    st.info("Aktuell ist kein Projekt geöffnet.")
    if st.button("Projekt auswählen"):
        st.switch_page("pages/open_project.py")
else:
    st.title("Filtern der Daten")

    # data laden
    projects_dir = os.path.join(os.getcwd(), "projects")
    folder_path = os.path.join(projects_dir, st.session_state.project)

    if "dataframe" not in st.session_state:
        data = pd.read_pickle(folder_path + "/data.pkl")
        st.session_state.dataframe = data

    st.markdown("#### Projekt: " + st.session_state.project)
    st.markdown(
        "Für die SRA Berechnung ist es wichtig, homogene Betriebsbedingungen (insbesondere der "
        "Bestrahlungsstärke) sicherzustellen. Dazu müssen die gemessenen IV-Kurven gefiltert werden. "
        "Es ist möglich diese durch ein bestehendes Label in den Messdaten zu filtern. Außerdem können die Daten "
        "durch einen automatisierten Autoencoder-Filterungsprozess gefiltert werden."
    )

    if os.path.exists(folder_path + "/data_filtered.pkl"):
        st.error(
            "Der Datensatz wurde bereits gefiltert. Erneutes Filtern überschreibt die vorhandenen Daten."
        )

    tab_label, tab_autoencoder, tab_no_filter, tab_raw = st.tabs(
        [
            "Filtern nach Label",
            "Filtern durch Autoencoder",
            "Ohne Filtern speichern",
            "Rohdaten ansehen",
        ]
    )

    with tab_label:
        st.markdown("#### Filtern nach Label")
        st.markdown(
            "Die einfachste Möglichkeit zu filtern ist das 'Filtern nach Label'. Hier werden die Daten einfach "
            "durch ein gegebenes Label (Merkmal) gefiltert, das in den Messdaten vorhanden sein muss. Das Label "
            "muss in binärer Form als True/False-Wert angegeben sein."
        )
        label_to_filter = st.selectbox(
            "Label zum Filtern auswählen",
            st.session_state.dataframe.columns,
            index=None,
        )
        if label_to_filter and st.button("Daten filtern und speichern", type="primary"):
            filtered_data = st.session_state.dataframe[
                st.session_state.dataframe[label_to_filter] == True
            ].copy()
            filtered_data.to_pickle(folder_path + "/data_filtered.pkl")
            with st.status("Daten werden gespeichert...", expanded=True) as status:
                st.write("Daten filtern...")
                time.sleep(1)
                st.write("Daten speichern...")
                status.update(
                    label="Daten erfolgreich gespeichert.",
                    state="complete",
                    expanded=False,
                )

            st.markdown("#### Daten vor dem Filtern")
            broken_data = st.session_state.dataframe[
                st.session_state.dataframe[label_to_filter] == False
            ].copy()
            st.plotly_chart(
                plot_random_iv_curves(broken_data, "Current", "Voltage", 5),
                use_container_width=True,
            )

            st.markdown("#### Daten nach dem Filtern")
            st.plotly_chart(
                plot_random_iv_curves(filtered_data, "Current", "Voltage", 5),
                use_container_width=True,
            )
    with tab_autoencoder:
        st.markdown("#### Automatisiertes Autoencoder Filtern")
        st.markdown(
            "Ein weitere Möglichkeit zum Filtern der Daten ist das Filtern mit einem Autoencoder. Das Filtering "
            "erfolgt 'Unsupervised', also ohne vorherig festgelegtes Label. Dieser Filter basiert NICHT auf einem "
            "binären Klassifikator. Stattdessen sollte vorher ein Autoencoder mit ausschließlich 'guten Kurven' "
            "trainiert werden (siehe Seite 'Autoencoder'). Anschließend kann das Model geladen und dann zum "
            "Filtern verwendet werden."
        )
        model_directory = os.path.join(os.getcwd(), "autoencoder_training")
        model_files = [f for f in os.listdir(model_directory) if f.endswith(".keras")]
        selected_model_file = st.selectbox(
            "Gespeichertes Model auswählen", model_files, index=0
        )

        if st.button("Model auswählen"):
            model_path = os.path.join(model_directory, selected_model_file)
            loaded_model = load_model(model_path)
            st.session_state["loaded_model"] = loaded_model
            st.session_state["model_name"] = selected_model_file
            print(load_model)

        if st.session_state.loaded_model:
            st.info(f"Das Model {st.session_state.model_name} wurde geladen.")

        if "Current_normalized" in st.session_state.dataframe.columns:
            st.markdown("#### Normalisierte IV-Kurven")
            fig = plot_random_iv_curves(
                st.session_state.dataframe,
                current_column="Current_normalized",
                voltage_column="Voltage_normalized",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Current Auswahl
            current_column = st.selectbox(
                "Spalte mit Strom-Messungen der IV-Kennlinie auswählen",
                st.session_state.dataframe.columns,
                index=None,
            )
            current_configured = False
            if current_column:
                if not isinstance(
                    st.session_state.dataframe.iloc[0][current_column], list
                ):
                    st.error(
                        f"Die Daten in der Spalte **{current_column}** liegen nicht als Liste vor."
                    )
                else:
                    current_configured = True
            # Voltage Auswahl
            voltage_column = st.selectbox(
                "Spalte mit Spannungs-Messungen der IV-Kennlinie auswählen",
                st.session_state.dataframe.columns,
                index=None,
            )
            voltage_configured = False
            if voltage_column:
                if not isinstance(
                    st.session_state.dataframe.iloc[0][voltage_column], list
                ):
                    st.error(
                        f"Die Daten in der Spalte **{voltage_column}** liegen nicht als Liste vor."
                    )
                else:
                    voltage_configured = True

            number_of_steps = st.slider(
                "Anzahl der Messpunkte nach der Normalisierung",
                min_value=50,
                max_value=500,
                step=10,
                value=100,
            )
            if current_configured and voltage_configured:
                if st.button("Daten normalisieren und fortfahren", type="primary"):
                    st.session_state.dataframe = normalize_curve_data(
                        st.session_state.dataframe,
                        current_column_name=current_column,
                        voltage_column_name=voltage_column,
                        number_of_steps=number_of_steps,
                    )
                    tab1, tab2 = st.tabs(["Normalisierte IV-Kurven", "Rohdaten"])
                    with tab1:
                        st.markdown("#### Normalisierte IV-Kurven")
                        fig = plot_random_iv_curves(
                            st.session_state.dataframe,
                            current_column="Current_normalized",
                            voltage_column="Voltage_normalized",
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    with tab2:
                        st.dataframe(st.session_state.dataframe, width=2000)

        if (
            st.session_state.loaded_model
            and "Current_normalized" in st.session_state.dataframe.columns
        ):
            X_new = np.array(
                st.session_state.dataframe["Current_normalized"].tolist()
            ).astype(np.float32)
            reconstructed_new = st.session_state.loaded_model.predict(X_new)
            st.session_state.dataframe["reconstruction"] = reconstructed_new.tolist()
            errors = [
                mean_squared_error(original, reconstructed) * 1000
                for original, reconstructed in zip(X_new, reconstructed_new)
            ]
            st.session_state.dataframe["error"] = errors
            if "sorted_df" not in st.session_state:
                sorted_df = st.session_state.dataframe.sort_values(
                    by="error", ascending=True
                ).reset_index()
                st.session_state["sorted_df"] = sorted_df

            st.markdown("#### Reconstruction Fehler als Filter-Parameter")
            st.markdown(
                "Im nachfolgenden Chart ist der Fehler der Rekonstruktion der IV-Kurven in sortierter Reihenfolge "
                "über dem Index aufgetragen. Der Fehler wird berechnet als RMSE zwischen der Eingabe IV-Kurve und "
                "der Rekonstruktion dieser Kurve durch den Autoencoder. Wenn das Model ausschließlich mit guten "
                "Kurven trainiert wurde, sollte der Fehler von guten Kurven nach der Rekonstruktion sehr niedrig "
                "sein. Alle anderen Kurven kann der Autoencoder nicht sauber rekonstruieren, der Fehler ist dann "
                "sehr hoch. Ich empfehle den Schwellwert auf einen der ersten deutlichen 'Knicke' zu setzen."
            )

            fig = px.scatter(
                st.session_state.sorted_df,
                x=st.session_state.sorted_df.index,
                y="error",
                title="Reconstruction Fehler aller IV-Kurven (aufsteigend)",
                labels={
                    "_index": "Index, sortiert",
                    "error": "Reconstruction Fehler",
                },
            )
            st.plotly_chart(fig, use_container_width=True)
            min_error = st.session_state.dataframe["error"].min()
            max_error = st.session_state.dataframe["error"].max()
            threshold = st.number_input(
                "Schwellwert für Filterung wählen",
                min_value=float(min_error),
                max_value=float(max_error),
                value=float(min_error),
            )
            if threshold and st.button("Filtern und speichern"):
                below_threshold = st.session_state.dataframe[
                    st.session_state.dataframe["error"] <= threshold
                ]
                above_threshold = st.session_state.dataframe[
                    st.session_state.dataframe["error"] > threshold
                ]
                below_threshold.to_pickle(folder_path + "/data_filtered.pkl")
                with st.status("Daten werden gespeichert...", expanded=True) as status:
                    st.write("Daten filtern...")
                    time.sleep(1)
                    st.write("Daten speichern...")
                    status.update(
                        label="Daten erfolgreich gespeichert.",
                        state="complete",
                        expanded=False,
                    )

                sorted_df = st.session_state.dataframe.sort_values(
                    by="error", ascending=True
                ).reset_index()
                sorted_df["above_threshold"] = sorted_df["error"] > threshold

                fig = px.scatter(
                    sorted_df,
                    x=sorted_df.index,
                    y="error",
                    color="above_threshold",
                    title="Reconstruction Fehler aller IV-Kurven (aufsteigend) mit Schwellwert",
                    labels={"_index": "Index", "error": "Reconstruction Fehler"},
                )
                st.plotly_chart(fig, use_container_width=True)

                if not below_threshold.empty:
                    st.markdown("#### 10 zufällige IV Kurven unter dem Schwellwert")
                    below = plot_random_iv_curves(
                        below_threshold,
                        "Current_normalized",
                        "Voltage_normalized",
                        samples=10,
                    )
                    st.plotly_chart(below, use_container_width=True)

                if not above_threshold.empty:
                    st.markdown("#### 10 zufällige IV Kurven über dem Schwellwert")
                    above = plot_random_iv_curves(
                        above_threshold,
                        "Current_normalized",
                        "Voltage_normalized",
                        samples=10,
                    )
                    st.plotly_chart(above, use_container_width=True)
    with tab_no_filter:
        st.markdown("#### Speichern ohne zu Filtern")
        st.markdown(
            "Alternativ können die Daten auch ohne vorheriges Filtern gespeichert werden. Beispielsweise weil die "
            "Daten bereits in gefilterter Form vorliegen."
        )
        if st.button("Daten ohne Filtern speichern", type="primary"):
            st.session_state.dataframe.to_pickle(folder_path + "/data_filtered.pkl")
            with st.status("Daten werden gespeichert...", expanded=True) as status:
                st.write("Daten werden nicht gefiltert...")
                time.sleep(1)
                st.write("Daten speichern...")
                status.update(
                    label="Daten erfolgreich gespeichert.",
                    state="complete",
                    expanded=False,
                )
    with tab_raw:
        st.write(st.session_state.dataframe)
