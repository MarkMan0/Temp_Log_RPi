from flask import Flask, request, render_template
from capture_data import log_DHT
import sqlite3
import datetime
import time
import arrow


app = Flask(__name__)


@app.route('/log_values', methods=['POST', ])
def log_sensor():
    sensor_id = request.form.get('sensor_id', type=int)
    temp = request.form.get('temperature', type=float)
    humidity = request.form.get('humidity', type=float)
    success = log_DHT(sensor_id, temp, humidity)
    retval = f'ID: {sensor_id}, temp: {temp}, hum: {humidity}'
    if success:
        return retval, 200
    else:
        return retval, 400


def _shift_to_timezone(records: list, timezone: str) -> list:
    ret = []
    for record in records:
        t = arrow.get(record[0], "YYYY-MM-DD HH:mm:ss").to(timezone).format('YYYY-MM-DD HH:mm:ss')
        ret.append((t, record[1], ))
    return ret
        
def _records_to_dict(records: list) -> list:
    ret = []
    for record in records:
        date = datetime.datetime.strptime(record[0], "%Y-%m-%d %H:%M:%S")
        ret.append({
            'year': date.year,
            'month': date.month,
            'day': date.day,
            'hour': date.hour,
            'minute': date.minute,
            'value': record[1],
            'date_str': record[0],
        })
    return ret

@app.route("/", methods=['GET'])
def render_records():
    temperatures, humidities, timezone, from_date_str, to_date_str = get_records()

    temperatures = _shift_to_timezone(temperatures, timezone)
    humidities = _shift_to_timezone(humidities, timezone)

    temp_data = {
        'column_name': 'Temperature',
        'unit': 'Celsius',
        'title': 'Temperature',
        'data': _records_to_dict(temperatures),
        'div_id': 'chart_temps',
    }
    hum_data = {
        'column_name': 'Humidity',
        'unit': 'Percent',
        'title': 'Humidity',
        'data': _records_to_dict(humidities),
        'div_id': 'chart_humid',    
    }
    

    table_entries = 5
    table_idxs = list(range(0, len(temperatures), int(
        1 + len(temperatures) / float(table_entries))))
    table_idxs[-1] = len(temperatures) - 1

    return render_template("temp_table.html",   timezone=timezone,
                           temp=temp_data,
                           hum=hum_data,
                           from_date=from_date_str,
                           to_date=to_date_str,
                           table_entries=table_idxs)
    


def get_records():
    ####
    #### STEP 1: retrieve date from request, or choose current as default
    #### Get other values
    ####
    from_date_str = request.args.get('from', time.strftime(
        "%Y-%m-%d 00:00"))  # Get the from date or current time
    to_date_str = request.args.get('to', time.strftime(
        "%Y-%m-%d %H:%M"))  # Get the to date or current time
    if not validate_date(from_date_str):
        from_date_str = time.strftime("%Y-%m-%d 00:00")
    if not validate_date(to_date_str):
        to_date_str = time.strftime("%Y-%m-%d %H:%M")
    
    # Create datetime object so that we can convert to UTC from the browser's local time
    from_date_obj = datetime.datetime.strptime(from_date_str, '%Y-%m-%d %H:%M')
    to_date_obj = datetime.datetime.strptime(to_date_str, '%Y-%m-%d %H:%M')
    
    timezone = request.args.get('timezone', 'Etc/UTC') # get the timezone or UTC default
    
    range_h_form = request.args.get('range_h', '')
    range_h_int = None

    try:
        range_h_int = int(range_h_form)
    except:
        pass


    ###
    ### STEP 2: convert to UTC
    ###

    if range_h_int is not None:
        # If range_h is defined, we don't need the from and to times
        arrow_time_from = arrow.utcnow().shift(hours=-range_h_int)  # from is "before"
        arrow_time_to = arrow.utcnow()                              # to is "now"
        from_date_utc = arrow_time_from.strftime("%Y-%m-%d %H:%M")  # from as string
        to_date_utc = arrow_time_to.strftime("%Y-%m-%d %H:%M")      # to as string
        from_date_str = arrow_time_from.to(timezone).strftime("%Y-%m-%d %H:%M")     # to update form
        to_date_str = arrow_time_to.to(timezone).strftime("%Y-%m-%d %H:%M")         # to update form
    else:
        # get the range from date time picker
        # change time zone and convert to string
        from_date_utc = arrow.get(from_date_obj, timezone).to(
            'Etc/UTC').strftime("%Y-%m-%d %H:%M") 
        to_date_utc = arrow.get(to_date_obj, timezone).to(
            'Etc/UTC').strftime("%Y-%m-%d %H:%M")


    ###
    ### STEP 3: retrieve from database
    ###
    conn = sqlite3.connect('/var/www/temp_log/temp_db.db')
    curs = conn.cursor()
    curs.execute("SELECT * FROM temperature WHERE read_time BETWEEN ? AND ?",
                 (from_date_utc, to_date_utc))
    temperatures = curs.fetchall()
    curs.execute("SELECT * FROM humidity WHERE read_time BETWEEN ? AND ?",
                 (from_date_utc, to_date_utc))
    humidities = curs.fetchall()
    conn.close()
    
    return [temperatures, humidities, timezone, from_date_str, to_date_str]


def validate_date(d):
    try:
        datetime.datetime.strptime(d, '%Y-%m-%d %H:%M')
        return True
    except ValueError:
        return False


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3601)
