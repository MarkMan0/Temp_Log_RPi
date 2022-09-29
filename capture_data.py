import sqlite3
import Adafruit_DHT


def log_DHT(sensor_id: int, temp: float, hum: float):
    conn = sqlite3.connect('/var/www/temp_log/temp_db.db')
    try:
        curs = conn.cursor()
        curs.execute(
            """INSERT INTO temperature VALUES(datetime(CURRENT_TIMESTAMP, 'localtime'), (?), (?))""",
            (temp, sensor_id)
        )
        curs.execute(
            """INSERT INTO humidity VALUES(datetime(CURRENT_TIMESTAMP, 'localtime'), (?), (?))""",
            (hum, sensor_id)
        )
        conn.commit()
    except:
        pass
    finally:
        conn.close()
        

def main():
    hum, temp = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, 17)

    if (hum is None) or (temp is None):
        return
    
    if hum > 100 or hum < 0:
        return
    
    if temp > 50 or temp < -10:
        return
    
    log_DHT(0, temp, hum)
    

if __name__ == '__main__':
    main()