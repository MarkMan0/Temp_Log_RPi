from flask import Flask, request
from capture_data import log_DHT


app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello UWSGI!'

def _val_or_none(key: str, d: dict):
    if (key in d):
        return d[key]
    else:
        return None

@app.route('/log_values', methods = ['POST',])
def log_sensor():
    sensor_id = int(request.form.get('sensor_id'))
    temp = float(request.form.get('temperature'))
    humidity = float(request.form.get('humidity'))
    success = log_DHT(sensor_id, temp, humidity)
    retval = f'ID: {sensor_id}, temp: {temp}, hum: {humidity}, form: {request.form}'
    if success:
        return retval, 200
    else:
        return retval, 400
        

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3600)
