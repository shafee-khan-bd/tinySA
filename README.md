TinySA Spectrum Analyzer is a Python-based application designed to interface with a small spectrum analyzer device over a serial connection. The app provides live sweep display, data recording with time stamps, and a professional user interface built with Streamlit. Its modular design enables future enhancements—such as remote data access—while keeping the core functionality robust.

Table of Contents
Overview
Features
Installation
Prerequisites
Cloning the Repository
Setting Up the Virtual Environment
Installing Dependencies
Usage
Running the Application
Live Sweep Operation
Recording Data
Project Structure
Extensibility and Future Enhancements
Troubleshooting
Contributing
License

Overview
TinySA Spectrum Analyzer is built to operate a spectrum analyzer device by:

Continuously acquiring and displaying sweep data.
Allowing users to record sweeps over time with associated timestamps.
Providing intuitive controls for live data visualization and recording, including adjustable refresh rates and y-axis scaling.
The application is implemented in Python using Streamlit for the user interface and Plotly for data visualization.

Features
Live Sweep Display:

Continuously updates the sweep data in real time.
Frequency axis spans from 50 kHz to 3.0 MHz.
Magnitude is displayed in dBm with a user-adjustable y-axis range (default: -120 to 0 dBm).
Professionally styled Plotly graph with a drawn bounding box.
Data Recording:

Record sweeps along with relative timestamps (time 0 at the start of recording).
Recorded data is appended to a CSV file.
Default storage folder is platform-dependent (Windows: C:\tinySA_Data; others: ~/tinySA_Data), but can be customized.
Option to set a recording duration (or record indefinitely).
While recording, a heatmap (time vs. frequency) is displayed and refreshed every 20 seconds.
Once recording is complete (duration reached or user stopped), the sweep pauses automatically and a completion message is shown.
User Interface Controls:

Top Controls: Buttons for "Start Sweep" and "Pause Sweep".
Recording Controls (Right Panel): Data Folder path, Record Duration, "Record Data" and "Stop Recording" buttons.
Sidebar Controls: Sliders to adjust refresh rate and y-axis range for the live sweep plot.
Installation
Prerequisites
Python 3.7 or higher.
pip package manager.
Cloning the Repository
Clone the repository from GitHub:


git clone https://github.com/yourusername/tinySA.git
cd tinySA
Setting Up the Virtual Environment
Create a virtual environment to isolate the project dependencies:

 

python -m venv venv
Activate the virtual environment:

Windows:

venv\Scripts\activate

macOS/Linux:

source venv/bin/activate

Installing Dependencies
Install the required packages using the provided requirements file:


pip install -r requirements.txt
Note: If you need to generate a requirements file, it is best to do so in a clean virtual environment or use a tool like pipreqs.

Usage
Running the Application
Start the application with Streamlit:


streamlit run app.py
Open your browser and navigate to the URL provided by Streamlit (usually http://localhost:8501).

You can also use run_app.bat file to launch the app, in case you already have python environment installed.

Live Sweep Operation
Click Start Sweep to begin displaying the live spectrum sweep data.
Adjust the refresh rate and y-axis range (in dBm) using the sidebar sliders.
The live sweep plot shows data across a frequency range of 50 kHz to 3.0 MHz.

Recording Data
In the Recording Controls panel on the right, set the desired data folder (default is C:\tinySA_Data on Windows or ~/tinySA_Data on other systems) and the record duration (in seconds).
Click Record Data to start recording. During recording:
The app appends each sweep with its timestamp to a CSV file.
A heatmap of recorded data is refreshed every 20 seconds.
The live sweep display is temporarily replaced with the recorded data view.
Click Stop Recording to end the recording manually. When recording is complete (either by duration or manual stop), the sweep pauses automatically and a "Recording complete" message is displayed.
Project Structure


tinySA/
├── app.py                 # Main Streamlit UI application
├── data_service.py        # Data acquisition, live sweep, and recording logic
├── spectrum_analyzer.py   # Hardware communication layer for the spectrum analyzer
├── requirements.txt       # List of required Python packages
└── README.md              # This documentation file

Extensibility and Future Enhancements
The application is built with a modular design that separates the hardware communication, data processing, and UI layers. Future improvements could include:

Remote Data Access: Adding a REST API or WebSocket server to allow remote control and data fetching.
Advanced Data Processing: Integrating signal processing features such as peak detection or filtering.
Enhanced UI/UX: Further refining the interface for a more polished and modern look.
Error Logging: Expanding logging and error handling for robust operation.
Troubleshooting
No Live Data: Verify that the spectrum analyzer is correctly connected and that the proper serial port is selected.
Recording File Issues: Check that the designated data folder exists and that you have write permissions.
Dependency Problems: Ensure that all packages are installed in the active virtual environment by reviewing requirements.txt.
Contributing
Contributions are welcome! To contribute:

Fork the repository.
Create a new branch for your feature or bug fix.
Commit your changes and open a pull request. For major changes, please open an issue first to discuss your ideas.
License

This project is licensed under the MIT License. See the LICENSE file for details.