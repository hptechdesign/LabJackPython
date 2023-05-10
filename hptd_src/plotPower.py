import u6
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore

# Define the sampling rate and duration of the acquisition
sampling_rate = 100  # Hz
duration = 0.5  # seconds

# Connect to the LabJack U6
d = u6.U6()

# Configure the first analog input channel as a differential input for voltage measurements
d.getFeedback(u6.PortDirWrite(Direction=[0, 0]))
d.getFeedback(u6.DAC0_8(Value=0))
d.getFeedback(u6.DAC1_8(Value=0))
d.getAIN(positiveChannel=0, resolutionIndex=1, gainIndex=0, differential=True)

# Configure the second analog input channel as a differential input for current measurements
d.getFeedback(u6.PortDirWrite(Direction=[0, 0]))
d.getFeedback(u6.DAC0_8(Value=0))
d.getFeedback(u6.DAC1_8(Value=0))
d.getAIN(positiveChannel=2, resolutionIndex=1, gainIndex=0, differential=True)

# Initialize the PyQTGraph plot
app = QtWidgets.QApplication([])
win = pg.GraphicsLayoutWidget(title="Real-time Power Measurements")
win.resize(1000, 600)
win.setWindowTitle('Real-time Power Measurements')
win.show()
pg.setConfigOptions(antialias=True)
voltage_plot = win.addPlot(title="Voltage")
voltage_plot.setRange(xRange=[0, duration], yRange=[-10, 10])
voltage_plot.setLabel('bottom', 'Time (s)')
voltage_plot.setLabel('left', 'Voltage (V)')
current_plot = win.addPlot(title="Current")
current_plot.setRange(xRange=[0, duration], yRange=[-0.1, 0.1])
current_plot.setLabel('bottom', 'Time (s)')
current_plot.setLabel('left', 'Current (A)')
power_plot = win.addPlot(title="Power")
power_plot.setRange(xRange=[0, duration], yRange=[-1, 1])
power_plot.setLabel('bottom', 'Time (s)')
power_plot.setLabel('left', 'Power (W)')
voltage_curve = voltage_plot.plot(pen='r')
current_curve = current_plot.plot(pen='g')
power_curve = power_plot.plot(pen='b')

# Initialize the data arrays
voltage_data = np.zeros(int(sampling_rate*duration))
current_data = np.zeros(int(sampling_rate*duration))
power_data = np.zeros(int(sampling_rate*duration))

# Define the update function for the real-time plot
def update():
    global voltage_data, current_data, power_data
    voltage = d.getAIN(positiveChannel=0, resolutionIndex=1, gainIndex=0, differential=True)
    current = d.getAIN(positiveChannel=2, resolutionIndex=1, gainIndex=0, differential=True)*0.2
    power = voltage * current
    voltage_data = np.append(voltage_data[1:], voltage)
    current_data = np.append(current_data[1:], current)
    power_data = np.append(power_data[1:], power)
    voltage_curve.setData(voltage_data)
    current_curve.setData(current_data)
    power_curve.setData(power_data)

# Start the real-time plot timer
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(100)
app.exec()
