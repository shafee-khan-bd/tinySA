import streamlit as st
import time
import os
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from data_service import DataService

# -------------------------------------------------------------
# 1. Session State Initialization
# -------------------------------------------------------------
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

st.title("TinySA Spectrum Analyzer")

# -------------------------------------------------------------
# 2. Top Controls
# -------------------------------------------------------------
top_col1, top_col2 = st.columns([1,1])
with top_col1:
    if st.button("Start Sweep"):
        st.session_state.data_service.start_sweep()
        st.session_state.sweep_running = True
with top_col2:
    if st.button("Pause Sweep"):
        st.session_state.data_service.pause_sweep()
        st.session_state.sweep_running = False

# -------------------------------------------------------------
# 3. Layout: Plot on the left, Recording on the right
# -------------------------------------------------------------
plot_col, rec_col = st.columns([3, 1])

with rec_col:
    st.subheader("Recording Controls")
    dest_folder = st.text_input("Data Folder", "C:\\tinySA_Data")
    record_duration = st.number_input("Record Duration (sec)", min_value=0, value=60, step=1)
    if st.button("Record Data"):
        duration = record_duration if record_duration > 0 else None
        st.session_state.data_service.start_recording(record_duration=duration, dest_folder=dest_folder)
        st.session_state.recording = True

    if st.button("Stop Recording"):
        st.session_state.data_service.stop_recording()
        st.session_state.recording = False

# Sidebar controls for refresh rate and y-axis range
refresh_rate = st.sidebar.slider("Refresh Rate (sec)", 0.5, 10.0, 1.0, 0.5)
y_range = st.sidebar.slider("Y Axis Range (dBm)", -150, 0, (-120, 0), 1)

chart_placeholder = plot_col.empty()
status_placeholder = plot_col.empty()

def create_live_figure(data, y_min, y_max):
    freq_vals = np.linspace(50e3, 3e6, len(data))
    trace = go.Scatter(x=freq_vals, y=data, mode='lines', name='Sweep Data')
    layout = go.Layout(
        title="Live Spectrum Sweep",
        xaxis=dict(title="Frequency (Hz)", range=[50e3, 3e6]),
        yaxis=dict(title="Magnitude (dBm)", range=[y_min, y_max]),
        shapes=[dict(
            type="rect",
            x0=50e3, y0=y_min,
            x1=3e6, y1=y_max,
            line=dict(color="Black", width=2)
        )]
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
        yaxis=dict(title="Time (sec)", autorange="reversed")
    )
    return go.Figure(data=[heatmap], layout=layout)

# -------------------------------------------------------------
# 4. MAIN LOGIC: Check if recording ended
# -------------------------------------------------------------
if st.session_state.recording:
    # First, check if the background thread has already stopped.
    if not st.session_state.data_service.recording:
        # The data_service finished recording (duration reached or user stopped).
        st.session_state.recording = False
        st.session_state.sweep_running = False
        st.session_state.data_service.pause_sweep()
        st.success("Recording complete. Sweep has been paused.")
    else:
        # Still recording
        status_placeholder.info("Recording in progress... (updates every 20 seconds)")

        # Update recorded figure every 20 seconds
        current_time = time.time()
        if current_time - st.session_state.last_record_update >= 20:
            st.session_state.last_record_update = current_time
            record_file = st.session_state.data_service.record_file_path
            if record_file and os.path.exists(record_file):
                st.session_state.last_recorded_fig = create_recorded_figure(record_file)

        # Display the last recorded figure if available; else show the last live figure
        if st.session_state.last_recorded_fig:
            chart_placeholder.plotly_chart(st.session_state.last_recorded_fig, use_container_width=True)
        else:
            # fallback to last live fig if no recorded data is available
            if st.session_state.last_live_fig:
                chart_placeholder.plotly_chart(st.session_state.last_live_fig, use_container_width=True)
            else:
                chart_placeholder.text("Waiting for data...")

        # Sleep and rerun
        time.sleep(1)
        st.rerun()

else:
    # Not recording => show live sweep
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
                chart_placeholder.text("Waiting for data...")

        time.sleep(refresh_rate)
        st.rerun()
    else:
        # Sweep is paused, just show the last figure if we have one
        if st.session_state.last_live_fig:
            chart_placeholder.plotly_chart(st.session_state.last_live_fig, use_container_width=True)
        else:
            chart_placeholder.text("Sweep is paused. Press 'Start Sweep' to begin.")
