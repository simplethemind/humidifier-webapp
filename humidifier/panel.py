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
        values['sensor'+num]['plant_label'] = form['sensor'+num+'_plant_label']
        values['sensor'+num]['zero_humidity'] = form['sensor'+num+'_zero_humidity']
        values['sensor'+num]['full_humidity'] = form['sensor'+num+'_full_humidity']
        values['sensor'+num]['relay_start'] = form['sensor'+num+'_relay_start']
        values['sensor'+num]['relay_duration'] = form['sensor'+num+'_relay_duration']
    values['log_delay'] = form['log_delay']
    values['relay_cooldown'] = str(int(float(form['relay_cooldown']) * 1000))
    return values

def activate_pump(index, duration):
    with Proxy('PYRONAME:serial_server.serial_connection') as controller:
        controller.post_message('r' + str(index) + 'd' + str(duration))


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/panel', methods=['GET', 'POST'])
def show_panel():

    ### handle GET method ###
    if request.method =='GET':

        ### get sensor values ###
        sensor_values = {}
        with Proxy('PYRONAME:serial_server.serial_connection') as controller:
            sensor_values = controller.get_settings()
        # change relay_cooldown value from miliseconds to seconds
        sensor_values['relay_cooldown'] /= 1000

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
        plant_labels = ['plant' + str(i) for i in range(3)]
        try:
            plant_labels = [
            sensor_values['sensor0']['plant_label'], 
            sensor_values['sensor1']['plant_label'],
            sensor_values['sensor2']['plant_label']]
        except:
            pass
        html_str = grapher.plot_data_mlp_to_html(dataPoints, labels=plant_labels)

        return render_template('panel/panel.html', panel=html_str, stored=sensor_values)

    ### handle POST method ###
    if request.method == 'POST':
        if g.user != None:
            if 'submit_settings_button' in request.form:
                new = build_new_values(request.form)

                with Proxy('PYRONAME:serial_server.serial_connection') as controller:
                    controller.set_settings(new)
                return redirect(url_for('reload'))
            else:
                for i in range(3):
                    str_i = str(i)
                    if 'submit_relay_' + str_i in request.form:
                        duration_i = request.form['relay' + str_i + '_activation_duration']
                        activate_pump(i, duration_i)
                        flash('S-a activat pompa ' + str_i + ' pentru ' + duration_i + ' milisecunde.')
                return redirect(url_for('reload'))


@bp.route('/reloading', methods=['GET'])
def show_reloading():
    return render_template('panel/reloading.html', root_url=url_for('index'))