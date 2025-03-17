import streamlit as st
import time
import os
import platform
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from data_service import DataService

# =============================================================================
# 1. Session State Initialization
# =============================================================================
if 'data_service' not in st.session_state:
    st.session_state.data_service = DataService()
if 'sweep_running' not in st.session_state:
    st.session_state.sweep_running = False
if 'recording' not in st.session_state:
    st.session_state.recording = False
if 'last_live_fig' not in st.session_state:
    st.session_state.last_live_fig = None
if 'last_recorded_fig' not in st.session_state:
    st.session_state.last_recorded_fig = None
if 'last_record_update' not in st.session_state:
    st.session_state.last_record_update = time.time()

# =============================================================================
# 2. Default Data Folder (Platform Dependent)
# =============================================================================
if platform.system() == "Windows":
    default_folder = r"C:\tinySA_Data"
else:
    default_folder = os.path.join(os.path.expanduser("~"), "tinySA_Data")

# =============================================================================
# 3. Page Title and Top Controls
# =============================================================================
st.title("TinySA Spectrum Analyzer")

top_col1, top_col2 = st.columns([1,1])
with top_col1:
    if st.button("Start Sweep"):
        st.session_state.data_service.start_sweep()
        st.session_state.sweep_running = True
with top_col2:
    if st.button("Pause Sweep"):
        st.session_state.data_service.pause_sweep()
        st.session_state.sweep_running = False

# =============================================================================
# 4. Sidebar Controls for Spectrum Analyzer Settings and Refresh Rates
# =============================================================================
st.sidebar.header("Spectrum Analyzer Settings")

# Operating Mode (you can remove this if not needed)
mode = st.sidebar.selectbox(
    "Operation Mode",
    options=["Low Input", "High Input", "Low Output", "High Output", "Reference Generator"],
    index=0
)

# Set default frequency range based on mode:
if mode in ["Low Input", "Low Output", "Reference Generator"]:
    default_start = 100e3
    default_stop = 350e6
elif mode in ["High Input", "High Output"]:
    default_start = 240e6
    default_stop = 960e6
else:
    default_start = 100e3
    default_stop = 350e6

# Store frequency settings in session_state only once (or update when changed)
if 'freq_settings' not in st.session_state:
    st.session_state.freq_settings = {"start": default_start, "stop": default_stop, "points": 101}

start_freq = st.sidebar.number_input("Start Frequency (Hz)", value=st.session_state.freq_settings["start"], step=1000.0, format="%.0f")
stop_freq  = st.sidebar.number_input("Stop Frequency (Hz)",  value=st.session_state.freq_settings["stop"],  step=1000.0, format="%.0f")
measurement_points = st.sidebar.selectbox("Measurement Points", options=[51, 101, 145, 290], index=1)

if (start_freq != st.session_state.freq_settings["start"] or 
    stop_freq != st.session_state.freq_settings["stop"] or 
    measurement_points != st.session_state.freq_settings["points"]):
    st.session_state.freq_settings = {"start": start_freq, "stop": stop_freq, "points": measurement_points}
    st.session_state.data_service.sa.set_frequencies(start=start_freq, stop=stop_freq, points=measurement_points)

resolution_bandwidth = st.sidebar.selectbox(
    "Resolution Bandwidth",
    options=["Auto", "3 kHz", "10 kHz", "30 kHz", "100 kHz", "300 kHz", "600 kHz"],
    index=0
)

if mode == "Low Input":
    auto_attenuation = st.sidebar.checkbox("Auto Attenuation", value=True)
    if not auto_attenuation:
        input_attenuation = st.sidebar.slider("Input Attenuation (dB)", min_value=0, max_value=31, value=10, step=1)
elif mode == "Low Output":
    output_level = st.sidebar.slider("Output Level (dBm)", min_value=-76, max_value=-6, value=-40, step=1)
elif mode == "High Output":
    output_level = st.sidebar.slider("Output Level (dBm)", min_value=-38, max_value=9, value=0, step=1)

# Separate refresh rates:
live_refresh_rate   = st.sidebar.slider("Live Display Refresh Rate (sec)", 0.5, 10.0, 1.0, 0.5)
record_refresh_rate = st.sidebar.slider("Recorded Data Refresh Rate (sec)", 10.0, 60.0, 20.0, 1.0)

# Y-axis range for live sweep plot
y_range = st.sidebar.slider("Y Axis Range (dBm)", -150, 0, (-120, 0), 1)

# =============================================================================
# 5. Recording Controls (Right Column)
# =============================================================================
plot_col, rec_col = st.columns([3, 1])
with rec_col:
    st.subheader("Recording Controls")
    dest_folder = st.text_input("Data Folder", default_folder)
    record_duration = st.number_input("Record Duration (sec, 0 for indefinite)", min_value=0.0, value=60.0, step=0.1)
    record_interval = st.number_input("Recording Interval (sec)", min_value=0.1, value=1.0, step=0.1)
    if st.button("Record Data"):
        duration = record_duration if record_duration > 0 else None
        st.session_state.data_service.start_recording(record_duration=duration, dest_folder=dest_folder, record_interval=record_interval)
        st.session_state.recording = True
    if st.button("Stop Recording"):
        st.session_state.data_service.stop_recording()
        st.session_state.recording = False

# =============================================================================
# 6. Functions for Creating Figures
# =============================================================================
def create_live_figure(data, y_min, y_max):
    freq_vals = st.session_state.data_service.sa.frequencies
    trace = go.Scatter(x=freq_vals, y=data, mode='lines', name='Sweep Data')
    layout = go.Layout(
        title="Live Spectrum Sweep",
        xaxis=dict(title="Frequency (Hz)", range=[start_freq, stop_freq]),
        yaxis=dict(title="Magnitude (dBm)", range=[y_min, y_max]),
        paper_bgcolor='white',
        plot_bgcolor='White',
        margin=dict(l=50, r=50, t=50, b=50),
        shapes=[{
            "type": "rect",
            "x0": start_freq, "y0": y_min,
            "x1": stop_freq, "y1": y_max,
            "line": {"color": "Black", "width": 2}
        }]
    )
    return go.Figure(data=[trace], layout=layout)

def create_recorded_figure(file_path):
    df = pd.read_csv(file_path)
    time_vals = df["time"].values
    freq_vals = np.array([float(col) for col in df.columns[1:]])
    z_data = df.iloc[:, 1:].values
    heatmap = go.Heatmap(x=freq_vals, y=time_vals, z=z_data, colorbar=dict(title="dBm"))
    layout = go.Layout(
        title="Recorded Sweep Data (Time vs Frequency)",
        xaxis=dict(title="Frequency (Hz)"),
        yaxis=dict(title="Time (sec)", autorange="reversed"),
        margin=dict(l=50, r=50, t=50, b=50),
        plot_bgcolor='white'
    )
    return go.Figure(data=[heatmap], layout=layout)

# =============================================================================
# 7. Main Display Logic
# =============================================================================
chart_placeholder = plot_col.empty()
status_placeholder = plot_col.empty()

if st.session_state.recording:
    if not st.session_state.data_service.recording:
        st.session_state.recording = False
        st.session_state.sweep_running = False
        st.session_state.data_service.pause_sweep()
        st.success("Recording complete. Sweep has been paused.")
    else:
        status_placeholder.info("Recording in progress...")
        current_time = time.time()
        if current_time - st.session_state.last_record_update >= record_refresh_rate:
            st.session_state.last_record_update = current_time
            record_file = st.session_state.data_service.record_file_path
            if record_file and os.path.exists(record_file):
                st.session_state.last_recorded_fig = create_recorded_figure(record_file)
        if st.session_state.last_recorded_fig:
            chart_placeholder.plotly_chart(st.session_state.last_recorded_fig, use_container_width=True)
        else:
            if st.session_state.last_live_fig:
                chart_placeholder.plotly_chart(st.session_state.last_live_fig, use_container_width=True)
            else:
                chart_placeholder.text("Waiting for data...")
        time.sleep(1)
        st.rerun()
else:
    if st.session_state.sweep_running:
        latest_data = st.session_state.data_service.get_latest_data()
        if latest_data is not None:
            live_fig = create_live_figure(latest_data, y_range[0], y_range[1])
            st.session_state.last_live_fig = live_fig
            chart_placeholder.plotly_chart(live_fig, use_container_width=True)
        else:
            if st.session_state.last_live_fig:
                chart_placeholder.plotly_chart(st.session_state.last_live_fig, use_container_width=True)
            else:
                chart_placeholder.text("Waiting for live data...")
        time.sleep(live_refresh_rate)
        st.rerun()
    else:
        if st.session_state.last_live_fig:
            chart_placeholder.plotly_chart(st.session_state.last_live_fig, use_container_width=True)
        else:
            chart_placeholder.text("Sweep is paused. Press 'Start Sweep' to begin.")
