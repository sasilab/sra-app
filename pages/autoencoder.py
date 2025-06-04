import os
import numpy as np
import pandas as pd
import streamlit as st

from datetime import datetime
from autoencoder.functions import autoencode
from sklearn.metrics import mean_squared_error
from pipeline.functions import normalize_curve_data
from tools.helper import plot_random_iv_curves, plot_reconstructions
from tensorflow.keras.models import load_model

st.markdown("# IV Autoencoder")
st.write(
    "Mit diesem Tool kann ein IV Autoencoder über das User Interface trainiert werden. Anschließend kann das Model "
    "gespeichert werden, um es für andere Zwecke, bspw. für das Filtern von Kurven, zu verwenden. Zudem können die "
    "'Reconstructions' und die 'Codings' extrahiert werden. Also die nach dem Autoencoder wiederhergestellten Kurven "
    "sowie die Coding-Layer in der Mitte an der engsten Stelle des Autoencoders."
)

st.markdown("#### Messdaten auswählen")
st.write(
    "Die Strom- bzw. Spannungs-Werte müssen in jeder Zeile als Liste gespeichert werden. Die jeweiligen Spalten "
    "können unten ausgewählt werden. Die Daten sollten noch nicht normalisiert sein."
)
uploaded_file = st.file_uploader("Messdaten auswählen (nur .pkl möglich)")

if "autoencoder" not in st.session_state:
    st.session_state.autoencoder = None

if uploaded_file is not None:
    if not uploaded_file.name.endswith(".pkl"):
        st.error("Aktuell werden nur .pkl Dateien akzeptiert.")
    else:
        if "data" not in st.session_state:
            st.session_state.data = pd.read_pickle(uploaded_file).reset_index()

        data = st.session_state.data

        # Current Auswahl
        current_column = st.selectbox(
            "Spalte mit Strom-Messungen der IV-Kennlinie auswählen",
            data.columns,
            index=None,
        )
        current_configured = False
        if current_column:
            if not isinstance(data.iloc[0][current_column], list):
                st.error(
                    f"Die Daten in der Spalte **{current_column}** liegen nicht als Liste vor."
                )
            else:
                current_configured = True
        # Voltage Auswahl
        voltage_column = st.selectbox(
            "Spalte mit Spannungs-Messungen der IV-Kennlinie auswählen",
            data.columns,
            index=None,
        )
        voltage_configured = False
        if voltage_column:
            if not isinstance(data.iloc[0][voltage_column], list):
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

        if "Current_normalized" in st.session_state.data.columns:
            st.markdown("#### Normalisierte IV-Kurven")
            fig = plot_random_iv_curves(
                data,
                current_column="Current_normalized",
                voltage_column="Voltage_normalized",
            )
            st.plotly_chart(fig, use_container_width=True)
            if current_configured and voltage_configured:
                if st.button("Daten erneut normalisieren"):
                    data = normalize_curve_data(
                        data,
                        current_column_name=current_column,
                        voltage_column_name=voltage_column,
                        number_of_steps=number_of_steps,
                    )
                    st.session_state.data = data
                    st.rerun()
        else:
            if current_configured and voltage_configured:
                if st.button("Daten normalisieren und fortfahren"):
                    data = normalize_curve_data(
                        data,
                        current_column_name=current_column,
                        voltage_column_name=voltage_column,
                        number_of_steps=number_of_steps,
                    )
                    st.session_state.data = data
                    tab1, tab2 = st.tabs(["Normalisierte IV-Kurven", "Rohdaten"])
                    with tab1:
                        st.markdown("#### Normalisierte IV-Kurven")
                        fig = plot_random_iv_curves(
                            data,
                            current_column="Current_normalized",
                            voltage_column="Voltage_normalized",
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    with tab2:
                        st.dataframe(data, width=2000)

    st.markdown("#### Konfiguration des Autoencoders")
    st.write(
        "Anschließend kann der Autoencoder konfiguriert werden. Die wichtigsten Architektur-Eigenschaften sind "
        "einstellbar. Weitere Konfigurationsmöglichkeiten sind dem Autoencoder Repository auf Gitlab zu entnehmen."
    )

    n_codings = st.slider(
        "Anzahl Neuronen in der Coding Layer (Mitte)",
        min_value=2,
        max_value=50,
        step=1,
        value=7,
    )
    n_layers = st.slider(
        "Anzahl an Zwischenschichten bis zur Coding Layer",
        min_value=2,
        max_value=20,
        step=1,
        value=3,
    )
    decrease_mode = st.selectbox(
        "Wie sollen die Schichten bis zur Coding Layer reduziert werden?",
        ["linear", "exponentiell"],
        index=0,
    )
    dropout = st.checkbox("Dropout verwenden", value=False, key="dropout")
    if dropout:
        dropout_rate = st.slider(
            "Dropout Rate",
            min_value=0.1,
            max_value=0.9,
            value=0.2,
            key="dropout_rate",
        )
    else:
        dropout_rate = 0

    st.markdown("#### Training konfigurieren")
    epochen = st.slider(
        "Anzahl an Epochen für das Training",
        min_value=20,
        max_value=1000,
        step=20,
        value=100,
    )
    batch_size = st.slider(
        "Batch-Größe für das Training",
        min_value=16,
        max_value=256,
        step=16,
        value=32,
    )
    early_stopping = st.checkbox(
        "Early Stopping benutzen", value=True, key="early_stopping"
    )
    if early_stopping:
        early_stopping_patience = st.slider(
            "Early Stopping Patience", min_value=1, max_value=20, value=10
        )
    else:
        early_stopping_patience = 0

    if "Current_normalized" in st.session_state.data.columns:
        st.divider()
        if st.button(
            "Autoencoder Training starten", type="primary", use_container_width=True
        ):
            progress_placeholder = st.empty()
            text_placeholder = st.empty()

            def progress_callback(epoch, total_epochs, train_rmse, test_rmse):
                progress = int((epoch / total_epochs) * 100)

                # Update the progress bar and text in their respective placeholders
                with progress_placeholder.container():
                    st.progress(progress)

                with text_placeholder.container():
                    st.text(
                        f"Epoche {epoch}/{total_epochs} - Train RMSE: {train_rmse:.4f}, Test RMSE: {test_rmse:.4f}"
                    )

            ae_df, history, autoencoder = autoencode(
                st.session_state.data,
                target_feature="Current_normalized",
                epochs=epochen,
                n_codings=n_codings,
                n_layers=n_layers,
                use_early_stopping=early_stopping,
                early_stopping_patience=early_stopping_patience,
                decrease_mode=decrease_mode,
                batch_size=batch_size,
                use_dropout=dropout,
                dropout_rate=dropout_rate,
                progress_callback=progress_callback,
            )

            st.session_state.autoencoder = autoencoder

            st.markdown("#### Ergebnis")
            model_directory = os.path.join(os.getcwd(), "autoencoder_training")
            if not os.path.exists(model_directory):
                os.makedirs(model_directory)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_name = f"model_{n_codings}codings_{n_layers}layers_{timestamp}.keras"
            model_path = os.path.join(model_directory, model_name)
            autoencoder.model.save(model_path)
            text_placeholder.success(
                f"Training erfolgreich abgeschlossen. Das Model wurde gespeichert unter "
                f"{model_path}.",
                icon="✅",
            )

            with st.expander("Rohdaten ansehen"):
                st.dataframe(ae_df)

            fig2 = plot_reconstructions(
                ae_df,
                current_column="Current_normalized",
                voltage_column="Voltage_normalized",
                reconstruction_column="reconstruction",
            )
            st.plotly_chart(fig2, use_container_width=True)

    else:
        st.error("Die Daten müssen zuerst normalisiert werden.")
