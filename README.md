# plot-using-LSL
Explore the power of real-time data visualization with Lab Streaming Layer (LSL).

This repository provides a Python-based solution for real-time data visualization using Lab Streaming Layer (LSL). The code allows you to easily connect to an LSL stream and plot the streamed data in real-time.

**Features**:
* Connect to an LSL stream and visualize the data in real-time.
* Adjustable parameters:
    * plot_duration: Set the duration of the plot window.
    * update_interval: Define the interval for updating the plot.
    * pull_interval: Specify the interval for pulling data from the LSL stream.
* Customizable stream inlet type:
    * Declare the type of the stream inlet as an argument of the LSLManagement class.
* Flexible filtering options:
    * Modify the filtering parameters in the design_filters method to suit your requirements.
