import datetime
import streamlit as st
import plotly.graph_objects as go
from tools.forecast import get_pvnode_forecast


if "project" not in st.session_state:
    st.session_state["project"] = None

st.title("Forecast der Betriebsbedingungen")
st.markdown("#### By pvnode.com")
st.markdown(
    "Darstellung eines Forecasts der Betriebsbedingungen (G und T) des heutigen Tages und der nächsten 2 Tage. "
    "Hilfreich unter anderem für die Planung von Messkampagnen."
)

st.markdown("#### Standort")
st.write(
    "Nachfolgend den Standort der Anlage eingeben. Aktuell ist der Forecast auf den Standort "
    "des ZME voreingestellt."
)
latitude = st.number_input(
    "Längengrad", min_value=0.00000001, value=50.264, disabled=True
)
longitude = st.number_input(
    "Breitengrad", min_value=0.00000001, value=10.949, disabled=True
)

st.markdown("#### Ausrichtung der Anlage")
slope = st.number_input("Neigung der Module", min_value=1, value=20)
orientation = st.number_input("Azimut-Ausrichtung ab Norden", min_value=1, value=164)

if latitude and longitude and slope and orientation:
    if st.button("Forecast abrufen"):
        dataframe = get_pvnode_forecast(latitude, longitude, slope, orientation)
        current_time = datetime.datetime.now()

        st.markdown("#### Forecast der Bestrahlungsstärke in Modulebene")
        fig_gti = go.Figure()
        fig_gti.add_trace(
            go.Scatter(
                x=dataframe.index, y=dataframe["GTI"], name="GTI (W/m²)", mode="lines"
            )
        )
        fig_gti.add_shape(
            type="line",
            x0=current_time,
            y0=0,
            x1=current_time,
            y1=max(dataframe["GTI"]),
            line=dict(color="red", width=2),
        )
        fig_gti.update_layout(xaxis_title="Timestamp", yaxis_title="GTI (W/m²)")
        st.plotly_chart(fig_gti, use_container_width=True)

        st.markdown("#### Forecast der Umgebungstemperatur")
        fig_temp = go.Figure()
        fig_temp.add_trace(
            go.Scatter(
                x=dataframe.index, y=dataframe["temp"], name="Temp (°C)", mode="lines"
            )
        )
        fig_temp.add_shape(
            type="line",
            x0=current_time,
            y0=0,
            x1=current_time,
            y1=max(dataframe["temp"]),
            line=dict(color="red", width=2),
        )
        fig_temp.update_layout(
            xaxis_title="Timestamp",
            yaxis_title="Temperature (°C)",
        )
        st.plotly_chart(fig_temp, use_container_width=True)
