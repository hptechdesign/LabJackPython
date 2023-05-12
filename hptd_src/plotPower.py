import u6
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore

# Define the sampling rate and duration of the acquisition
sampling_rate = 1000  # Hz
duration = 1 # seconds

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
# Add the three plots to the grid layout
voltage_plot = win.addPlot(row=0, col=0, title="Voltage")
voltage_plot.setRange(xRange=[0, duration*sampling_rate])
voltage_plot.setAutoPan(x=True, y=True)
voltage_plot.setLabel('bottom', 'Sample #')
voltage_plot.setLabel('left', 'Voltage (V)')

current_plot = win.addPlot(row=1, col=0, title="Current")
current_plot.setRange(xRange=[0, duration*sampling_rate])
current_plot.setAutoPan(x=True, y=True)
current_plot.setXLink(voltage_plot)
current_plot.setLabel('bottom', 'Sample #')
current_plot.setLabel('left', 'Current (A)')

power_plot = win.addPlot(row=2, col=0, title="Power")
power_plot.setRange(xRange=[0, duration*sampling_rate])
power_plot.setAutoPan(x=True, y=True)
power_plot.setXLink(voltage_plot)
power_plot.setLabel('bottom', 'Sample #')
power_plot.setLabel('left', 'Power (W)')

# add minor gridlines
voltage_plot.showGrid(x=True, y=True, alpha=10)
current_plot.showGrid(x=True, y=True, alpha=50)
power_plot.showGrid(x=True, y=True, alpha=50)

# Initialize the plot curves
voltage_curve = voltage_plot.plot(pen='r')
current_curve = current_plot.plot(pen='g')
power_curve = power_plot.plot(pen='b')

voltage = d.getAIN(positiveChannel=0, resolutionIndex=1, gainIndex=0, differential=True)*1000
current = d.getAIN(positiveChannel=2, resolutionIndex=1, gainIndex=0, differential=True)*0.2*1000
power = voltage * current/1000

# add average value
# create text items showing the average values
voltage_avg=voltage
voltage_text = pg.TextItem(f"Average: {voltage_avg:.0f}")
voltage_text.setPos(sampling_rate*duration, voltage_avg) # set the position of the text box
voltage_plot.addItem(voltage_text) # add the text box to the plot

current_avg=current
current_text = pg.TextItem(f"Average: {current_avg:.0f}")
current_text.setPos(sampling_rate*duration, current_avg) # set the position of the text box
current_plot.addItem(current_text) # add the text box to the plot

power_avg=power
power_text = pg.TextItem(f"Average: {power_avg:.0f}")
power_text.setPos(sampling_rate*duration, power_avg) # set the position of the text box
power_plot.addItem(power_text) # add the text box to the plot

# Initialize the data arrays
voltage_data = np.ones(int(sampling_rate*duration))*voltage
current_data = np.ones(int(sampling_rate*duration))*current
power_data = np.ones(int(sampling_rate*duration))*power

# Define the update function for the real-time plot
def update():
    global voltage_data, current_data, power_data, voltage_avg, current_avg, power_avg
    voltage = d.getAIN(positiveChannel=0, resolutionIndex=1, gainIndex=0, differential=True)*1000
    current = d.getAIN(positiveChannel=2, resolutionIndex=1, gainIndex=0, differential=True)*0.2*1000
    power = voltage * current / 1000
    voltage_data = np.append(voltage_data[1:], voltage)
    current_data = np.append(current_data[1:], current)
    power_data = np.append(power_data[1:], power)
    voltage_curve.setData(voltage_data)
    current_curve.setData(current_data)
    power_curve.setData(power_data)

    voltage_avg = np.mean(voltage_data)
    voltage_1savg = np.mean(voltage_data[-100:])
    current_avg = np.mean(current_data)
    current_1savg = np.mean(current_data[-100:])
    power_avg = np.mean(power_data)
    power_1savg = np.mean(power_data[-100:])

    voltage_pos = np.mean(voltage_data)
    current_pos = np.mean(current_data)
    power_pos = np.mean(power_data)

    # get the current y limits
    ymaxV = np.max(voltage_data)
    ymaxI = np.max(current_data)
    ymaxP = np.max(power_data)

    yminV = np.min(voltage_data)
    yminI = np.min(current_data)
    yminP = np.min(power_data)

    voltage_plot.setRange(yRange=[yminV-(ymaxV-yminV)*0.1, ymaxV+(ymaxV-yminV)*0.1])
    current_plot.setRange(yRange=[yminI-(ymaxI-yminI)*0.1, ymaxI+(ymaxI-yminI)*0.1])
    power_plot.setRange(yRange=[yminP-(ymaxP-yminP)*0.1, ymaxP+(ymaxP-yminP)*0.1])

    ymin, yVtext= voltage_plot.viewRange()[1]
    voltage_text.setText(f"10s Average: {voltage_avg:.0f} mV\n1s Average: {voltage_1savg:.0f} mV")
    voltage_text.setPos(0, yVtext) # set the position of the text box

    ymin, yItext= current_plot.viewRange()[1]
    current_text.setText(f"10s Average: {current_avg:.0f} mA\n1s Average: {current_1savg:.0f} mA")
    current_text.setPos(0, yItext) # set the position of the text box

    ymin, yPtext= power_plot.viewRange()[1]
    power_text.setText(f"10s Average: {power_avg:.0f} mW\n1s Average: {power_1savg:.0f} mW")
    power_text.setPos(0, yPtext) # set the position of the text box
    

# Start the real-time plot timer
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(1)
app.exec()
