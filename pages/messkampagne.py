import os
import datetime
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from datetime import datetime
from dotenv import load_dotenv

from tools.forecast import get_pvnode_forecast
from tools.helper import count_pmpp_pairs, schedule_measurements
from measurements.pvpm import measure_iv_curve, get_usb_ports
from measurements.sma import start_ivcurve

from apscheduler.schedulers.background import BackgroundScheduler

from sra.temperature import (
    module_from_ambient_temperature,
    cell_from_module_temperature,
)

load_dotenv()

if "scheduler" not in st.session_state:
    st.session_state.scheduler = BackgroundScheduler()
    st.session_state.jobs_completed = []
    st.session_state.scheduled_times = None
    st.session_state.forecast_df = None
    st.session_state.forecast_ready = False
    st.session_state.usb_port = None
    st.session_state.device = None


def save_iv_curve(iv_curve, project_name):
    projects_dir = os.path.join(os.getcwd(), "projects")
    folder_path = os.path.join(
        projects_dir, str(project_name), "automated_measurements"
    )
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(folder_path, f"{current_time}.pkl")
    iv_curve.to_pickle(file_path)


def get_and_save_sma_measurement(project_name):
    iv_curve = start_ivcurve(os.getenv("username_SMA"), os.getenv("pwd_SMA"))
    if iv_curve:
        curve_a_data = iv_curve.get("Curve A")
        curve_b_data = iv_curve.get("Curve B")

        if curve_a_data is not None:
            save_iv_curve(curve_a_data, project_name)

        if curve_b_data is not None:
            save_iv_curve(curve_b_data, project_name)


def get_and_save_pvpm_measurement(com_port, project_name):
    iv_curve = measure_iv_curve(com_port)
    save_iv_curve(iv_curve, project_name)


def schedule_sma_inverter(scheduled_times, project_name):
    for scheduled_time, _ in scheduled_times:
        st.session_state.scheduler.add_job(
            get_and_save_sma_measurement,
            "date",
            run_date=scheduled_time,
            args=[project_name],
        )
    st.session_state.scheduler.start()


def schedule_pvpm(scheduled_times, com_port, project_name):
    for scheduled_time, _ in scheduled_times:
        st.session_state.scheduler.add_job(
            get_and_save_pvpm_measurement,
            "date",
            run_date=scheduled_time,
            args=[com_port, project_name],
        )
    st.session_state.scheduler.start()


if "project" not in st.session_state:
    st.session_state["project"] = None

if not st.session_state.project:
    st.info("Aktuell ist kein Projekt geöffnet.")
    if st.button("Projekt auswählen"):
        st.switch_page("pages/open_project.py")
else:
    st.title("Messkampagne planen")
    st.markdown(
        "Mit diesem Tool können Messkampagnen für fehlende G-T-Bedingungen geplant und automatisiert ausgeführt "
        "werden. Dazu muss vorher die Leistungsmatrix mit dem SRA für ein Projekt berechnet werden. Anschließend kann "
        "bestimmt werden, für welche G-T-Bedingungen noch Messwerte benötigt werden. Durch einen Forecast können die "
        "Zeiten bestimmt werden, an denen die fehlenden Bedingungen möglicherweise erreicht werden. Anschließend "
        "können die Messungen geplant werden."
    )

    # 1. Projekt laden
    projects_dir = os.path.join(os.getcwd(), "projects")
    folder_path = os.path.join(projects_dir, st.session_state.project)

    if not os.path.exists(folder_path + "/matrix.pkl"):
        st.error("Für dieses Projekt liegen noch keine Ergebnismatrix vor.")
        if st.button("Zurück zur Übersicht"):
            st.switch_page("pages/project_overview.py")
    else:
        matrix = pd.read_pickle(folder_path + "/matrix.pkl")
        st.markdown("#### Ergebnismatrix nach DIN EN 61853-1")
        st.dataframe(matrix, width=2000)

    # 2. Fehlende Messpunkte bestimmen
    st.markdown("#### Anzahl an Messungen für die Ergebnismatrix")
    g_values = [100, 200, 400, 500, 600, 800, 1000, 1100]
    t_values = [15, 25, 45, 50, 75]
    data = pd.read_pickle(folder_path + "/data_effective.pkl")
    spatial_data = count_pmpp_pairs(data, g_values, t_values).transpose()
    df = pd.DataFrame(spatial_data, columns=[0, 1, 2, 3, 4])
    df["Pmpp / W"] = [
        "100 W/m²",
        "200 W/m²",
        "400 W/m²",
        "500 W/m²",
        "600 W/m²",
        "800 W/m²",
        "1000 W/m²",
        "1100 W/m²",
    ]
    df.set_index("Pmpp / W", inplace=True)
    df.rename(
        columns={0: "15 °C", 1: "25 °C", 2: "45 °C", 3: "50 °C", 4: "75 °C"},
        inplace=True,
    )
    st.dataframe(df, width=2000)

    # 3. Messgerät auswählen
    st.markdown("#### Konfiguration des Messgerätes")
    st.write(
        "Bitte hier auswählen, mit welchem Messgerät die Messungen durchgeführt werden sollen."
    )
    device = st.selectbox(
        "Messgerät auswählen",
        ["SMA Wechselrichter", "PVPM Kennlinienschreiber"],
        index=None,
    )
    if device == "PVPM Kennlinienschreiber":
        usb_port = st.selectbox(
            "USB Port angeben",
            get_usb_ports(),
            index=None,
        )
        st.session_state.usb_port = usb_port

    # 4. Forecast für Anlage ausgeben
    st.markdown("#### Standort der Anlage")
    latitude = st.number_input(
        "Längengrad", min_value=0.00000001, value=50.264, disabled=True
    )
    longitude = st.number_input(
        "Breitengrad", min_value=0.00000001, value=10.949, disabled=True
    )

    st.markdown("#### Ausrichtung der Anlage")
    slope = st.number_input("Neigung der Module", min_value=1, value=20)
    orientation = st.number_input(
        "Azimut-Ausrichtung ab Norden", min_value=1, value=164
    )

    st.markdown("#### Konfiguration der Anlage")

    module_type = st.selectbox(
        "Modul-Typ eingeben", ("glass/glass", "glass/polymer"), index=None
    )

    bauform = st.selectbox(
        "Bauform eingeben",
        ("open_rack", "insulated_back", "close_mount"),
        index=None,
    )

    if (
        latitude
        and longitude
        and slope
        and orientation
        and device
        and module_type
        and bauform
    ):
        st.markdown("#### Konfiguration der Messroutine")
        num_measurements = st.slider("Wie viele Messungen?", 1, 100, 5, step=1)
        delay_minutes = st.slider(
            "Wie viel Delay zwischen den Messungen?", 15, 60, 15, step=15
        )
        if (
            st.button("Forecast und optimal Messzeitpunkte berechnen", type="primary")
            and num_measurements
            and delay_minutes
        ):
            dataframe = get_pvnode_forecast(
                latitude, longitude, slope, orientation, forecast_days=1
            )
            dataframe.rename(columns={"GTI": "G_mod", "temp": "T_amb"}, inplace=True)
            current_time = datetime.now()

            # 5. Teff berechnen
            dataframe = module_from_ambient_temperature(dataframe, module_type, bauform)
            dataframe = cell_from_module_temperature(dataframe, module_type, bauform)

            # 6. Messzeiten für Messungen bestimmen
            scheduled_times = schedule_measurements(
                df, dataframe, num_measurements, delay_minutes
            )

            st.session_state.forecast_df = dataframe
            st.session_state.scheduled_times = scheduled_times
            st.session_state.forecast_ready = True

    if st.session_state.forecast_ready:
        dataframe = st.session_state.forecast_df
        scheduled_times = st.session_state.scheduled_times

        st.markdown(
            "#### Forecast der Bestrahlungsstärke mit ausgewählten Messzeitpunkten"
        )
        fig_gti = go.Figure()
        fig_gti.add_trace(
            go.Scatter(
                x=dataframe.index,
                y=dataframe["G_mod"],
                name="GTI (W/m²)",
                mode="lines",
            )
        )
        if scheduled_times:
            times, values = zip(*scheduled_times)
            fig_gti.add_trace(
                go.Scatter(
                    x=times,
                    y=values,
                    mode="markers",
                    marker=dict(color="green", size=10),
                    name="Ausgewählte Messzeitpunkte",
                )
            )
        fig_gti.add_shape(
            type="line",
            x0=datetime.now(),
            y0=0,
            x1=datetime.now(),
            y1=max(dataframe["G_mod"]),
            line=dict(color="red", width=2),
        )
        fig_gti.update_layout(xaxis_title="Timestamp", yaxis_title="GTI (W/m²)")
        st.plotly_chart(fig_gti, use_container_width=True)

        st.markdown("#### Forecast der Temperatur mit ausgewählten Messzeitpunkten")
        fig_temp = go.Figure()
        fig_temp.add_trace(
            go.Scatter(
                x=dataframe.index,
                y=dataframe["T_eff"],
                name="Temp (°C)",
                mode="lines",
            )
        )
        if scheduled_times:
            times, _ = zip(*scheduled_times)
            temp_values = [dataframe.loc[time, "T_eff"] for time in times]
            fig_temp.add_trace(
                go.Scatter(
                    x=times,
                    y=temp_values,
                    mode="markers",
                    marker=dict(color="green", size=10),
                    name="Ausgewählte Messzeitpunkte",
                )
            )
        fig_temp.add_shape(
            type="line",
            x0=datetime.now(),
            y0=0,
            x1=datetime.now(),
            y1=max(dataframe["T_eff"]),
            line=dict(color="red", width=2),
        )
        fig_temp.update_layout(xaxis_title="Timestamp", yaxis_title="Temperature (°C)")
        st.plotly_chart(fig_temp, use_container_width=True)

    if st.session_state.forecast_ready:
        if not st.session_state.scheduler.get_jobs():
            if st.button("Messkampagnen starten und Messungen planen", type="primary"):
                if device == "PVPM Kennlinienschreiber":
                    schedule_pvpm(
                        st.session_state.scheduled_times,
                        st.session_state.usb_port,
                        st.session_state.project,
                    )
                else:
                    schedule_sma_inverter(
                        st.session_state.scheduled_times, st.session_state.project
                    )
                st.rerun()
        else:
            if st.button("Messkampagne abbrechen"):
                st.session_state.scheduler.remove_all_jobs()
                st.session_state.jobs_completed = []
                st.session_state.scheduler.shutdown(wait=False)
                st.rerun()

    if "scheduler" in st.session_state:
        st.markdown("#### Geplante Messungen:")
        if st.session_state.scheduler.get_jobs():
            for job in st.session_state.scheduler.get_jobs():
                st.write(f"Job ID: {job.id}, Scheduled Time: {job.next_run_time}")
        else:
            st.write("Aktuell sind keine Messungen geplant.")

        if st.session_state.scheduled_times and len(
            st.session_state.jobs_completed
        ) == len(st.session_state.scheduled_times):
            st.write("Alle Messungen wurden erfolgreich abgeschlossen.")
            st.session_state.scheduler.shutdown(wait=False)
