from . import grapher
from Pyro5.api import Proxy
import json
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash
from humidifier.db import get_db
from datetime import (datetime, timedelta)

bp = Blueprint('panel', __name__)

def build_new_values(form):
    values = {}
    for i in range(3):
        num = str(i)
        values['sensor'+num] = {}
        values['sensor'+num]['zero_humidity'] = form['sensor'+num+'_zero_humidity']
        values['sensor'+num]['full_humidity'] = form['sensor'+num+'_full_humidity']
        values['sensor'+num]['relay_start'] = form['sensor'+num+'_relay_start']
        values['sensor'+num]['relay_duration'] = form['sensor'+num+'_relay_duration']
    values['log_delay'] = form['log_delay']
    return values

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/panel', methods=['GET', 'POST'])
def show_panel():

    ### handle GET method ###
    if request.method =='GET':

        ### generate graph SVG ###
        timeDelta = timedelta(days=7)
        time = request.args.get('timespan')
        if time == 'h4':
            timeDelta = timedelta(hours=4)
        elif time == 'd1':
            timeDelta = timedelta(days=1)
        elif time == 'd3':
            timeDelta = timedelta(days=3)
        elif time == 'd7':
            timeDelta = timedelta(days=7)
        elif time == 'd30':
            timeDelta = timedelta(days=30)
        endTimePoint = datetime.now()
        startTimePoint = endTimePoint - timeDelta
        timeframe = [startTimePoint, endTimePoint]
        logsList = grapher.get_logs_in_timeframe(timeframe)
        dataPoints = grapher.combine_logs(logsList, timeframe)
        html_str = grapher.plot_data_mlp_to_html(dataPoints)

        ### get sensor values ###
        sensor_values = ''
        with Proxy('PYRONAME:serial_server.serial_connection') as controller:
            sensor_values = controller.get_settings()

        return render_template('panel/panel.html', panel=html_str, stored=sensor_values)

    ### handle POST method ###
    if request.method == 'POST':
        new = build_new_values(request.form)

        with Proxy('PYRONAME:serial_server.serial_connection') as controller:
            controller.set_settings(new)
        return redirect(url_for('reload'))


@bp.route('/reloading', methods=['GET'])
def show_reloading():
    return render_template('panel/reloading.html', root_url=url_for('index'))