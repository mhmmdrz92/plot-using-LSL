import time
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets
from pylsl import StreamInlet, resolve_byprop, proc_clocksync, proc_dejitter
from scipy import signal


class LSLManagement:
    def __init__(self, type_):
        self.type = type_
        self.channel_count = None
        self.pull_timer = None
        self.update_timer = None
        self.curves = None
        self.inlet = None
        self.sample_rate = None
        self.ch_names = []
        self.eeg_data = None
        self.window_live = None
        self.plot_duration = 10  # the duration would be displayed in seconds
        self.update_interval = 60  # rate of screen updates in ms
        self.pull_interval = 200  # rate of pull operation in ms
        self.plot_samples = None  # number of samples that would be displayed
        self.filters = {}
        self.device_search_attempts = 3
        self.device_search_timeout = 1

    def plot_setter(self):
        self.curves = []
        ticks = [list(zip(range(self.channel_count), reversed(self.ch_names[:self.channel_count])))]
        plot = pg.plot()
        yay = plot.getAxis('left')
        yay.setTicks(ticks)
        self.plot_samples = int(self.plot_duration * self.sample_rate)

        for j in range(len(self.ch_names)):
            self.window_live[j] = [0] * self.plot_samples

            curve = pg.PlotCurveItem(pen=pg.mkPen(color='#1c1c1c', width=1))
            plot.addItem(curve)
            curve.setPos(0, j * 1)
            self.curves.append(curve)

        font = QtGui.QFont()
        font.setPixelSize(16)
        plot.getAxis("left").setStyle(tickFont=font)
        plot.setBackground(None)
        plot.setMouseEnabled(x=False, y=False)
        plot.showGrid(x=True, y=False, alpha=1.0)
        plot.setMenuEnabled(False)
        plot.setYRange(0, self.channel_count * 1)

    def search_device(self):
        time.sleep(0.1)
        streams = []
        for _ in range(self.device_search_attempts):
            streams = resolve_byprop('type', self.type, timeout=self.device_search_timeout)

            if streams:
                self.inlet = StreamInlet(streams[0], max_buflen=self.plot_duration,
                                         processing_flags=proc_clocksync | proc_dejitter)
                print(f'Device {self.inlet.info().name()} found.')
                self.sample_rate = int(self.inlet.info().nominal_srate())
                self.channel_count = self.inlet.info().channel_count()
                self.extract_channel_names()
                self.design_filters(self.sample_rate * 0.5)
                break

        if not streams:
            print('No devices found.')

    def extract_channel_names(self):
        channel = self.inlet.info().desc().child("channels").child("channel")
        for _ in range(self.channel_count):
            channel_name = channel.child_value("label")
            self.ch_names.append(channel_name)
            channel = channel.next_sibling()

    def connect_to_LSL(self):
        self.eeg_data = [[] for _ in range(self.channel_count)]
        self.window_live = [[] for _ in range(self.channel_count)]
        self.plot_setter()
        self.set_pull_timer()
        self.set_plot_update_timer()

    def stop_LSL(self):
        if self.pull_timer:
            self.pull_timer.stop()
        if self.update_timer:
            self.update_timer.stop()

    def set_pull_timer(self):
        self.pull_timer = QtCore.QTimer()
        self.pull_timer.timeout.connect(self.pull_data)
        self.pull_timer.start(self.pull_interval)

    def set_plot_update_timer(self):
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.update_plot)
        self.update_timer.start(self.update_interval)

    def pull_data(self):
        eeg_data_chunk, _ = self.inlet.pull_chunk()

        if eeg_data_chunk:
            eeg_data_chunk = np.array(eeg_data_chunk).T
            for i, channel_data in enumerate(eeg_data_chunk):
                self.eeg_data[i].extend(channel_data)
                self.window_live[i].extend(channel_data)
                if len(self.window_live[i]) > self.plot_samples:
                    self.window_live[i] = self.window_live[i][-self.plot_samples:]

    def update_plot(self):
        try:
            plot_data = np.array(self.window_live)
            if np.sum(plot_data) != 0:
                plot_data = signal.detrend(plot_data, axis=1)
                plot_data = self.filter_data(plot_data)
                for i, curve in enumerate(self.curves):
                    curve.setData(y=plot_data[i, :])

        except Exception as e:
            print(f"Error in update_plot: {str(e)}")

    def design_filters(self, nyquist_freq, low_cut=0.5, high_cut=40):
        output = signal.butter(N=5, Wn=[low_cut / nyquist_freq, high_cut / nyquist_freq], btype='bandpass', analog=False,
                               output='ba')
        self.filters['bandpass'] = [output[0], output[1]]  # b, a

    def filter_data(self, data):
        filtered_data = signal.filtfilt(self.filters['bandpass'][0], self.filters['bandpass'][1], data, axis=1)
        return filtered_data


def main():
    obj = LSLManagement('EEG')  # specify the type of the stream
    obj.search_device()
    obj.connect_to_LSL()

    import sys

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtWidgets.QApplication.instance().exec_()


if __name__ == '__main__':
    main()
