import streamlit as st
import plotly.graph_objects as go
from measurements.pvpm import measure_iv_curve, get_usb_ports
from tools.helper import plot_random_iv_curves


if "project" not in st.session_state:
    st.session_state["project"] = None

st.title("Messung mit dem PVPM 1000CX")
st.markdown(
    "Diese Seite ermöglicht eine direkte Messung mit dem PVPM 1000CX Kennlinienschreiber."
)

st.markdown("#### Konfiguration des Kennlinienmessgerätes")
st.write(
    "Bitte daran denken das Kennlinienmessgerät in den Modus zur PC-Kommunikation zu setzen. "
    "Die Kommunikation erfolgt seriell per USB. Dazu muss der passende USB-Port angeschlossen werden. "
    "Nachfolgend können alle verbundenen Ports angezeigt werden. Falls das Gerät noch nicht angeschlossen war, "
    "bitte nun anschließen und dann die Seite neu laden (F5)."
)
st.write(
    "Falls der korrekte USB Port unbekannt ist, kann dieser über den Geräte-Manager in Windows "
    "herausgefunden werden. Wenn die Auswahlbox nicht funktioniert sind keine Geräte angeschlossen."
)

usb_port = st.selectbox(
    "USB Port angeben",
    get_usb_ports(),
    index=None,
)

if usb_port:
    if st.button("Messung starten"):
        dataframe = measure_iv_curve(com_port=usb_port)

        tab1, tab2 = st.tabs(["IV Kurve anzeigen", "Rohdaten ansehen"])
        with tab1:
            st.markdown("#### Gemessene IV-Kurve")
            fig = plot_random_iv_curves(dataframe, "Current", "Voltage", 1)
            st.plotly_chart(fig, use_container_width=True)
        with tab2:
            st.markdown("#### Rohdaten")
            st.write(dataframe)
