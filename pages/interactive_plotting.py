import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events

st.markdown("# Interaktives Plotting Tool")
st.write(
    "Mit dem interaktivem Plotting Tool können Datenpunkte eines 3D Scatter Chart ausgewählt werden und per Klick "
    "auf einen Scatter Punkt die jeweilige IV-Kurve geplottet werden. Zudem können die Daten direkt mit einem Label "
    "versehen werden. Beim Auswahl eines neuen Dataframes bitte die Seite neu laden.",
)


def label_curve(index):
    data = st.session_state.data
    if "label_tool" not in data.columns:
        data["label_tool"] = False
    data.at[index, "label_tool"] = True
    st.success(
        f"Kurven mit dem Index {index} erfolgreich als gute Kurve gelabelt",
        icon="✅",
    )


def save_labeled_dataframe():
    os.makedirs("label_tool", exist_ok=True)

    new_file_path = f"label_tool/{base_name}_labeled.pkl"
    st.session_state.data.to_pickle(new_file_path)
    st.success(f"Daten erfolgreich gespeichert unter: {new_file_path}", icon="✅")


uploaded_file = st.file_uploader("Messdaten auswählen (nur .pkl möglich)")
if uploaded_file is not None:
    if not uploaded_file.name.endswith(".pkl"):
        st.error("Aktuell werden nur .pkl Dateien akzeptiert.")
    else:
        if "data" not in st.session_state:
            st.session_state.data = pd.read_pickle(uploaded_file).reset_index()
        data = st.session_state.data
        base_name = os.path.splitext(uploaded_file.name)[0]
        st.write(base_name)

        # Korrekte Spalten 3D auswählen
        st.markdown("### Datenspalten für 3D Scatter Chart auswählen")
        # x-Achse Auswahl
        x_axis_scatter = st.selectbox(
            "Spalte für x-Achse des Charts auswählen",
            data.columns,
            index=None,
        )

        # y-Achse Auswahl
        y_axis_scatter = st.selectbox(
            "Spalte für y-Achse des Charts auswählen",
            data.columns,
            index=None,
        )

        # z-Achse Auswahl
        z_axis_scatter = st.selectbox(
            "Spalte für z-Achse des Charts auswählen",
            data.columns,
            index=None,
        )

        # Korrekte Spalten auswählen
        st.markdown("### Datenspalten für IV-Kurven auswählen")

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

        fig = px.scatter_3d(
            data,
            x=x_axis_scatter,
            y=y_axis_scatter,
            z=z_axis_scatter,
            color=z_axis_scatter,
        )
        fig.update_traces(marker=dict(size=3, color="red"))
        fig.update_layout(
            scene=dict(
                xaxis=dict(backgroundcolor="white", color="black"),
                yaxis=dict(backgroundcolor="white", color="black"),
                zaxis=dict(backgroundcolor="white", color="black"),
            ),
            paper_bgcolor="#E4E8F1",
        )
        if x_axis_scatter and y_axis_scatter and z_axis_scatter:
            selected_points = plotly_events(fig, click_event=True, hover_event=False)

            if selected_points and current_configured and voltage_configured:
                selected_index = selected_points[0]["pointNumber"]
                current_values = data.iloc[selected_index][current_column]
                voltage_values = data.iloc[selected_index][voltage_column]
                fig2 = go.Figure()
                fig2.add_trace(
                    go.Scatter(
                        x=current_values,
                        y=voltage_values,
                        mode="lines+markers",
                        name="Voltage vs Current",
                    )
                )
                fig2.update_layout(
                    title=f"IV-Kurve für den Index {selected_index}",
                    xaxis_title="Voltage [V]",
                    yaxis_title="Current [A]",
                )
                st.plotly_chart(fig2, use_container_width=True)

                if st.button("Als gute Kurven labeln"):
                    label_curve(selected_index)
                    with st.expander("Rohdaten mit Label ansehen"):
                        st.dataframe(data)
                if st.button("Rohdaten jetzt speichern"):
                    save_labeled_dataframe()

        else:
            st.write(
                "Bitte auf einen Punkt im 3D Chart klicken, um die Kurve darzustellen."
            )
