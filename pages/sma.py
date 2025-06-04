import os
import streamlit as st
from dotenv import load_dotenv
from measurements.sma import start_ivcurve
from tools.helper import plot_random_iv_curves

load_dotenv()


if "project" not in st.session_state:
    st.session_state["project"] = None

st.title("Messung mit dem SMA Wechselrichter")
st.markdown("Diese Seite ermöglicht eine direkte Messung mit dem SMA Wechselrichter.")

st.markdown("#### Konfiguration des Wechselrichters")
st.write(
    "Die Kommunikation kann nur erfolgen, wenn der Computer im Netzwerk der Hochschule Coburg "
    "registriert ist und damit aktiv verbunden ist. In diesem Fall, da wir nur einen SMA Wechselrichter besitzen, "
    "ist alles voreingestellt. Die Zugangsdaten (für den Fall, dass ein anderer WR angesprochen werden muss), "
    "können direkt im Code (Umgebungsvariablen) geändert werden. Aktuell ist das Programm so eingestellt, dass nur die "
    "IV-Kurve des zweiten Strings angezeigt wird, da nur ein String angeschlossen ist. Bei Bedarf bitte im Code "
    "anpassen."
)
if st.button("Messung starten"):
    curve_a, curve_b = start_ivcurve(
        username=os.getenv("username_SMA"), password=os.getenv("pwd_SMA")
    )
    tab1, tab2 = st.tabs(["IV Kurve anzeigen", "Rohdaten ansehen"])
    with tab1:
        st.markdown("#### Gemessene IV-Kurve")

        fig = plot_random_iv_curves(curve_b, "Current", "Voltage", 1)
        st.plotly_chart(fig, use_container_width=True)
    with tab2:
        st.markdown("#### Rohdaten")
        st.write(curve_b)
