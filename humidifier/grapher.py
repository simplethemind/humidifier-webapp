import os
import matplotlib
from mpld3.plugins import MousePosition
from numpy.core.fromnumeric import swapaxes
from numpy.core.function_base import logspace
from math import floor, ceil
import pandas
import glob
import numpy
import datetime
import re
import matplotlib.pyplot as plt
import matplotlib.dates as dates
from mpld3 import fig_to_html, plugins
from Pyro5.api import Proxy

def get_logs_in_timeframe(timeframe):
    start = timeframe[0]
    end = timeframe[1]
    logs_folder = ''
    with Proxy('PYRONAME:serial_server.serial_connection') as controller:
        logs_folder = os.path.join(controller.working_directory,'logs','*.csv')

    all_logs = glob.glob(logs_folder)
    all_logs.sort(reverse=True)
    valid_logs = []
    for log in all_logs:
        log_date_string = re.search('(\d{4}\.\d{2}\.\d{2}_\d{2}\.\d{2}\.\d{2})', log)
        log_date = datetime.datetime.strptime(log_date_string[0], '%Y.%m.%d_%H.%M.%S')
        if log_date < end and log_date > start:
            if os.path.getsize(log) > 0:
                valid_logs.append(log)
                continue
        if log_date < start:
            if os.path.getsize(log) > 0:
                valid_logs.append(log)
                break
    valid_logs.sort()
    return valid_logs

def validate_logs(log_entry_array):
    validated_array = []
    for entry in log_entry_array:
        if type(entry[0]) is str and type(entry[1]) is float and type(entry[2]) is float and type(entry[3]) is float and len(entry) == 4:
            validated_array.append(entry)
    return validated_array

def combine_logs(logs, timeframe):
    np_array_list = []
    for file in logs:
        log_data_frame = pandas.read_csv(
            file, sep=',', 
            header=0, 
            index_col=None,
            warn_bad_lines=True,
            error_bad_lines=False
        )
        np_array_list.append(log_data_frame)
    combined_array = numpy.vstack(np_array_list)
    combined_array = validate_logs(combined_array)
    # filter out extraneous values
    start = 0
    test_date = datetime.datetime.strptime(combined_array[start][0], '%m/%d/%y %H:%M:%S')
    while test_date < timeframe[0]:
        start += 1
        if start>len(combined_array)-1:
            return []
        test_date = datetime.datetime.strptime(combined_array[start][0], '%m/%d/%y %H:%M:%S')
    end = len(combined_array) - 1
    test_date = datetime.datetime.strptime(combined_array[end][0], '%m/%d/%y %H:%M:%S')
    while test_date > timeframe[1]:
        end -= 1
        test_date = datetime.datetime.strptime(combined_array[end][0], '%m/%d/%y %H:%M:%S')
    valid_array = combined_array[start:end + 1]
    return valid_array

# def customLegend(fig, nameSwap):
#     for i, dat in enumerate(fig.data):
#         for elem in dat:
#             if elem == 'name':
#                 fig.data[i].name = nameSwap[fig.data[i].name]
#     return(fig)
    
# def PlotData(dataPoints):
#     if len(dataPoints) == 0:
#         return None
#     fig = px.line(
#         dataPoints, x=0, y=[1,2,3],
#         title='Umiditatea solului',
#         width=900, height=600,
#         labels={'value':'Procent','variable':'Plante'})
#     fig.update_layout(
#         yaxis_range=[0,100],
#         xaxis_title='',
#         yaxis_title='')
#     return customLegend(fig, {'1':'Menta','2':'Yucca','3':'Gol'})

def extract_point_position(dates, values):
        # ydata = [i for i in values]
        # xdata = [i for i in dates]
    fdata = [(dates[i], values[i]) for i in range(len(dates))]
    # print(fdata)
    # stringData = ['humidity: {0}\ntime: {1}'.format(dataInfo[0], datetime.datetime.strftime(dates.num2date(dataInfo[1]), '%Y/%m/%d %H:%M:%S')) for dataInfo in fdata]
    string_data = ['humidity: {:.2%}\ntime: {}'.format(dataInfo[1]/100,dataInfo[0]) for dataInfo in fdata]
    return string_data

def average_lists(list):
    swap = swapaxes(list, 0, 1)
    averages = []
    for entry in swap[1:]:
        averages.append(sum(entry) / len(entry))
    return averages

def cull_to_number(data_points, max_length):
    if len(data_points) <= max_length:
        return data_points
    step_size =  floor(len(data_points) / max_length)
    culled_data_points = []
    i = step_size
    while i < len(data_points):
        averages = average_lists(data_points[i-step_size:i])
        current_data_point = [data_points[i][0]]
        current_data_point.extend(averages)
        culled_data_points.append(numpy.array(current_data_point, dtype=object))
        i += step_size

    averages = average_lists(data_points[i-step_size:])
    last_data_point = [data_points[len(data_points)-1][0]]
    last_data_point.extend(averages)
    culled_data_points.append(numpy.array(last_data_point, dtype=object))
    return culled_data_points



def plot_data_mlp_to_html(data_points, labels=[]):
    # print(len(dataPoints))
    data_points = cull_to_number(data_points, 250)
    # print(len(dataPoints))
    # print(dataPoints)
    swap = swapaxes(data_points, 0, 1)
    # print(swap)
    timescale = []
    for i, date in enumerate(swap[0]):
        parsedDate = datetime.datetime.strptime(date, '%m/%d/%y %H:%M:%S')
        timescale.append(parsedDate)
    # timescale = [datetime.datetime.strptime(date, '%m/%d/%y %H:%M:%S') for date in swap[0]]
    dates = matplotlib.dates.date2num(timescale)
    fig, ax = plt.subplots(figsize=[9.28, 4.8])
    plt.rcParams.update({'figure.autolayout': True})
    ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(10))
    ax.grid(which='major', axis='both', linestyle="-", alpha=0.25, linewidth=1)
    ax.tick_params(labelsize='medium', width=1)
    # Read labels from list
    p1 = ax.plot_date(dates, swap[1], color='red', linestyle='solid', marker=None, label=labels[0])
    p2 = ax.plot_date(dates, swap[2], color='green', linestyle='solid', marker=None, label=labels[1])
    p3 = ax.plot_date(dates, swap[3], color='blue', linestyle='solid', marker=None, label=labels[2])
    s1 = ax.scatter(dates, swap[1], color='#00000000', s=50)
    s2 = ax.scatter(dates, swap[2], color='#00000000', s=50)
    s3 = ax.scatter(dates, swap[3], color='#00000000', s=50)
    ax.legend()
    # xlabels = ax.get_xticklabels()
    # plt.setp(xlabels, rotation=30, horizontalalignment='right')
    ax.set(ylim=[0, 100], xlabel='Dată', ylabel='Procent (%)', title='Grafic umiditate plante')

    # Create HTML
    plugins.clear(fig)
    tooltip_plugin1 = plugins.PointLabelTooltip(s1, extract_point_position(swap[0], swap[1]))
    tooltip_plugin2 = plugins.PointLabelTooltip(s2, extract_point_position(swap[0], swap[2]))
    tooltip_plugin3 = plugins.PointLabelTooltip(s3, extract_point_position(swap[0], swap[3]))
    plugins.connect(fig, tooltip_plugin1, tooltip_plugin2, tooltip_plugin3, plugins.Zoom(), plugins.Reset())
    html_str = fig_to_html(fig)
    return html_str

if __name__ == '__main__':
    end_time_point = datetime.datetime.now() - datetime.timedelta(days=0)
    start_time_point = end_time_point - datetime.timedelta(days=5)
    timeframe = [start_time_point, end_time_point]
    logs_list = get_logs_in_timeframe(timeframe)
    data_points = combine_logs(logs_list, timeframe)
    # figure = PlotData(dataPoints)
    # figure.show()
    html_str = plot_data_mlp_to_html(data_points)
    with open('index.html', 'w') as f:
        f.write(html_str)
