"""
The SRA can be used in two ways.

1. as a pipeline directly in the code (see main.py)
2. with a user interface (see app.py)

This is the app file which allows to run the GUI application. It is built with Streamlit and only
requires python.

Run in your terminal: **streamlit run app.py** to start the GUI!
"""

import streamlit as st


pages = {
    "Einführung & Setup": [
        st.Page("pages/welcome.py", title="Einführung"),
        st.Page("pages/open_project.py", title="Bestehendes Projekt öffnen"),
        st.Page("pages/new_project.py", title="Neues Projekt erstellen"),
    ],
    "SRA & Projektbearbeitung": [
        st.Page("pages/project_overview.py", title="Projekt im Überblick"),
        st.Page("pages/filtering.py", title="Daten filtern"),
        st.Page("pages/betriebsbedingungen.py", title="Effektive Betriebsbedingungen"),
        st.Page("pages/analysis.py", title="SRA Berechnung"),
    ],
    "Messungen": [
        st.Page("pages/pvpm.py", title="PVPM 1000CX"),
        st.Page("pages/sma.py", title="SMA Wechselrichter"),
        st.Page("pages/messkampagne.py", title="Messkampagne planen"),
    ],
    "Tools": [
        st.Page(
            "pages/interactive_plotting.py",
            title="Interaktives Plotting und Label Tool",
        ),
        st.Page("pages/forecast.py", title="Forecast"),
        st.Page("pages/autoencoder.py", title="IV Autoencoder"),
    ],
}
pg = st.navigation(pages)
pg.run()
