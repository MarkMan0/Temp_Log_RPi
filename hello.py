from flask import Flask, request
from capture_data import log_DHT


app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello UWSGI!'


@app.route('/log_values', methods = ['POST',])
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
        

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3600)
