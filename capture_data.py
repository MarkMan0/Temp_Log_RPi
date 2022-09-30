import sqlite3
import Adafruit_DHT

def _verify_value(val: float, min: float, max: float) -> bool:
    return (val is not None) and (val >= min) and (val <= max)

def log_DHT(sensor_id: int, temp: float, hum: float) -> bool:
    success = False
    if sensor_id is None:
        return success
    conn = sqlite3.connect('/var/www/temp_log/temp_db.db')
    try:
        curs = conn.cursor()
        
        if _verify_value(temp, -10, 50):
            curs.execute(
                """INSERT INTO temperature VALUES(datetime(CURRENT_TIMESTAMP, 'utc'), (?), (?))""",
                (temp, sensor_id))
        if _verify_value(hum, 0, 100):
            curs.execute(
                """INSERT INTO humidity VALUES(datetime(CURRENT_TIMESTAMP, 'utc'), (?), (?))""",
                (hum, sensor_id))
            
        conn.commit()
        success = True
    except:
        success = False
    finally:
        conn.close()
    
    return success
        

def main():
    hum, temp = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, 17)
    log_DHT(0, temp, hum)
    

if __name__ == '__main__':
    main()