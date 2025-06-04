import os
import streamlit as st

st.markdown("# Projekt öffnen")

if "project" not in st.session_state:
    st.session_state["project"] = None

if not st.session_state.project:
    st.info("Aktuell ist kein Projekt geöffnet.")
else:
    st.success(f"**{st.session_state.project}** ist derzeit geöffnet.")

projects_directory = "projects"
projekte = [
    name
    for name in os.listdir(projects_directory)
    if os.path.isdir(os.path.join(projects_directory, name))
]

option = st.selectbox(
    "Welches Projekt soll geöffnet werden?",
    projekte,
)

if st.button("Projekt öffnen und zum Projekt"):
    st.session_state["project"] = option
    st.switch_page("pages/project_overview.py")
