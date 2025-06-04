import os
import streamlit as st

st.markdown("# SRAandTools")
st.write(
    "**SRAandTools** ist das neue User Interface des SRA sowie eine Sammlung verschiedener Tools, die im Laufe der "
    "Zeit in den Projekten KickPV und PV-Feldlab entstanden sind."
)
st.divider()
st.markdown("### Links zu den nützlichsten Funktionen:")
left, middle, right = st.columns(3, border=False)
if left.button("Neues SRA Projekt für eine Analyse erstellen"):
    st.switch_page("pages/new_project.py")
if middle.button("Messkampagne für SRA Analyse planen"):
    st.switch_page("pages/messkampagne.py")
if right.button("Interaktives Plotting und Label Tool"):
    st.switch_page("pages/interactive_plotting.py")

st.divider()
st.markdown("### Oder ein Bestehendes Projekt auswählen:")

column = st.container(border=False)
column_left, column_middle, column_right = column.columns(3)

projects_directory = "projects"
if not os.path.exists(projects_directory):
    os.makedirs(projects_directory)
projekte = [
    name
    for name in os.listdir(projects_directory)
    if os.path.isdir(os.path.join(projects_directory, name))
]

if len(projekte) == 0:
    column.write("Es wurden noch keine Projekte erstellt.")


def select_project_and_switch_page(_projekt):
    st.session_state.project = _projekt
    st.switch_page("pages/project_overview.py")


limited_projekte = projekte[:5]

for projekt in limited_projekte:
    if column_left.button(projekt):
        select_project_and_switch_page(projekt)

limited_projekte_middle = projekte[5:10]

for projekt in limited_projekte_middle:
    if column_middle.button(projekt):
        select_project_and_switch_page(projekt)

limited_projekte_right = projekte[10:15]

for projekt in limited_projekte_right:
    if column_right.button(projekt):
        select_project_and_switch_page(projekt)
