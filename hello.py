from flask import Flask, request, render_template
from capture_data import log_DHT
import sqlite3
import datetime
import time
import arrow


app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello UWSGI!'


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

# Add date limits in the URL #Arguments: from=2015-03-04&to=2015-03-05
@app.route("/lab_env_db", methods=['GET'])
def lab_env_db():
    temperatures, humidities, timezone, from_date_str, to_date_str = get_records()

    # Create new record tables so that datetimes are adjusted back to the user browser's time zone.
    time_adjusted_temperatures = []
    time_adjusted_humidities = []
    for record in temperatures:
        local_timedate = arrow.get(record[0], "YYYY-MM-DD HH:mm:ss").to(timezone)
        time_adjusted_temperatures.append(
            [local_timedate.format('YYYY-MM-DD HH:mm:ss'), round(record[1], 2)])

    for record in humidities:
        local_timedate = arrow.get(record[0], "YYYY-MM-DD HH:mm:ss").to(timezone)
        time_adjusted_humidities.append(
            [local_timedate.format('YYYY-MM-DD HH:mm:ss'), round(record[1], 2)])

    return render_template("temp_table.html",   timezone=timezone,
                           temp=time_adjusted_temperatures,
                           hum=time_adjusted_humidities,
                           from_date=from_date_str,
                           to_date=to_date_str,
                           query_string=request.query_string)


def get_records():
    from_date_str = request.args.get('from', time.strftime(
        "%Y-%m-%d 00:00"))  # Get the from date value from the URL
    to_date_str = request.args.get('to', time.strftime(
        "%Y-%m-%d %H:%M"))  # Get the to date value from the URL
    timezone = request.args.get('timezone', 'Etc/UTC')
    # This will return a string, if field range_h exists in the request
    range_h_form = request.args.get('range_h', '')
    range_h_int = "nan"  # initialise this variable with not a number

    try:
        range_h_int = int(range_h_form)
    except:
        pass


    # Validate date before sending it to the DB
    if not validate_date(from_date_str):
        from_date_str = time.strftime("%Y-%m-%d 00:00")
    if not validate_date(to_date_str):
        # Validate date before sending it to the DB
        to_date_str = time.strftime("%Y-%m-%d %H:%M")
    # Create datetime object so that we can convert to UTC from the browser's local time
    from_date_obj = datetime.datetime.strptime(from_date_str, '%Y-%m-%d %H:%M')
    to_date_obj = datetime.datetime.strptime(to_date_str, '%Y-%m-%d %H:%M')

    # If range_h is defined, we don't need the from and to times
    if isinstance(range_h_int, int):
        arrow_time_from = arrow.utcnow().shift(hours=-range_h_int)
        arrow_time_to = arrow.utcnow()
        from_date_utc = arrow_time_from.strftime("%Y-%m-%d %H:%M")
        to_date_utc = arrow_time_to.strftime("%Y-%m-%d %H:%M")
        from_date_str = arrow_time_from.to(timezone).strftime("%Y-%m-%d %H:%M")
        to_date_str = arrow_time_to.to(timezone).strftime("%Y-%m-%d %H:%M")
    else:
        # Convert datetimes to UTC so we can retrieve the appropriate records from the database
        from_date_utc = arrow.get(from_date_obj, timezone).to(
            'Etc/UTC').strftime("%Y-%m-%d %H:%M")
        to_date_utc = arrow.get(to_date_obj, timezone).to(
            'Etc/UTC').strftime("%Y-%m-%d %H:%M")

    conn = sqlite3.connect('/var/www/temp_log/temp_db.db')
    curs = conn.cursor()
    curs.execute("SELECT * FROM temperature WHERE read_time BETWEEN ? AND ?",
                 (from_date_utc.format('YYYY-MM-DD HH:mm:ss'), to_date_utc.format('YYYY-MM-DD HH:mm:ss')))
    temperatures = curs.fetchall()
    curs.execute("SELECT * FROM humidity WHERE read_time BETWEEN ? AND ?",
                 (from_date_utc.format('YYYY-MM-DD HH:mm:ss'), to_date_utc.format('YYYY-MM-DD HH:mm:ss')))
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
    app.run(host='0.0.0.0', port=3600)
