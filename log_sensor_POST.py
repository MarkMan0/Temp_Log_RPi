import requests
import Adafruit_DHT

def main():
    hum, temp = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, 17)
    
    payload = {'sensor_id': 0,
               'temperature': temp,
               'humidity': hum }
    url = 'http://127.0.0.1:3600/log_values'
    
    x = requests.post(url, data=payload)
    #print(x)
    #print(x.text)
    

if __name__ == '__main__':
    main()