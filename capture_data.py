import sqlite3
import Adafruit_DHT
import datetime

def _verify_value(val: float, min: float, max: float) -> bool:
    return (val is not None) and (val >= min) and (val <= max)

def log_DHT(sensor_id: int, temp: float, hum: float) -> bool:
    success = False
    if sensor_id is None:
        return success
    conn = sqlite3.connect('/var/www/temp_log/temp_db.db')
    try:
        curs = conn.cursor()
        
        # since the fckn Wemos board keeps restarting, and sending data too fckin frequently
        # I need to limit the frequency of updates here, to a bit less than 5 minutes
        
        # get latest entry
        curs.execute("SELECT read_time FROM temperature WHERE sensorID == (?) ORDER BY read_time DESC LIMIT 1",
                     (sensor_id, ))
        records = curs.fetchall()
        if len(records) >= 1:
            read_str = records[0][0]
        else:
            read_str = "2000-01-01 12:00:00"  # some value in the past
        
        read_time = datetime.datetime.strptime(read_str, '%Y-%m-%d %H:%M:%S')
        next_read_time = read_time + datetime.timedelta(minutes=4)
        
        if datetime.datetime.now() >= next_read_time:
            if _verify_value(temp, -10, 50):
                curs.execute(
                    """INSERT INTO temperature VALUES(datetime(CURRENT_TIMESTAMP, 'localtime'), (?), (?))""",
                    (temp, sensor_id))
            if _verify_value(hum, 0, 100):
                curs.execute(
                    """INSERT INTO humidity VALUES(datetime(CURRENT_TIMESTAMP, 'localtime'), (?), (?))""",
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