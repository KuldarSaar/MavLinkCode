import time
import sys
import csv
import datetime
from pymavlink import mavutil

connected = False
gps_input = False
location_input = False
time_input = False

date = ""
time_str = ""
lat = 0.0
lon = 0.0
alt = 0.0
lat_target = 0.0
lon_target = 0.0
alt_target = 0.0
ground_distance = 0.0

csv_file = 'autopilot_data.csv'

DEG_TO_MM = 111319.9 * 1000  # Convert degrees to millimeters
        
def send_data_to_csv(csv_writer, csv_data):
    try:
        print(csv_data)
        csv_writer.writerow(csv_data)
    except KeyboardInterrupt:
        print("Interrupted...")

# Try connecting until a heartbeat is received.
while not connected:
    try:
        master = mavutil.mavlink_connection('udp:127.0.0.1:14560')
        print("Attempting connection")
        master.wait_heartbeat()  # Wait for heartbeat to confirm connection.
        connected = True
        print("Connected")
        break
    except Exception as e:
        time.sleep(1)
        print("Waiting for connection")

try:
    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Date', 'Time', 'Latitude Difference (mm)', "Longitude Difference (mm)"])
        
        while True:
            msg = master.recv_match()
            if not msg:
                continue

            # Process GPS_RAW_INT message
            if msg.get_type() == 'GPS_RAW_INT':
                gps_message = msg.to_dict()
                lat = gps_message["lat"] / 1e7
                lon = gps_message["lon"] / 1e7
                alt = gps_message["alt"]
                gps_input = True

            # Process POSITION_TARGET_GLOBAL_INT message
            if msg.get_type() == 'POSITION_TARGET_GLOBAL_INT':
                position_target = msg.to_dict()
                lat_target = position_target["lat_int"] / 1e7
                lon_target = position_target["lon_int"] / 1e7
                alt_target = position_target["alt"] * 1000
                location_input = True

            if msg.get_type() == 'OPTICAL_FLOW':
                height_message = msg.to_dict()
                ground_distance = height_message["ground_distance"] * 1000

            # Process SYSTEM_TIME message
            if msg.get_type() == 'SYSTEM_TIME':
                time_message = msg.to_dict()
                time_usec = time_message["time_unix_usec"]
                time_sec = time_usec / 1e6
                date_time = datetime.datetime.fromtimestamp(time_sec)
                date = date_time.strftime('%d.%m.%Y')
                time_str = date_time.strftime('%H:%M:%S')
                time_input = True

            # Only log data if valid location and time information have been received.
            if location_input and time_input and gps_input:
                lat_diff = (lat - lat_target) * DEG_TO_MM
                lon_diff = (lon - lon_target) * DEG_TO_MM
                alt_diff = round(alt_target - alt, 2)

                lat_diff = round(lat_diff, 2)
                lon_diff = round(lon_diff, 2)

                data = [date, time_str, lat_diff, lon_diff]
                send_data_to_csv(writer, data)
            
except Exception as e:
    print(e)
finally:
    print("Script interrupted. Closing file...")
