import time
import datetime


def log_message(message):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{current_time}] {message}"
    return log_message

def write_log(log, filepath):
    with open(filepath, 'a') as file:  # 'a' mode opens the file for appending
        file.write(log + '\n')

def csvstring(input_data, output_data, ii, exp):

    if exp == 'AI':

        # Get measurements
        gx = input_data[0]
        gy = input_data[1]
        gz = input_data[2]
        ax = input_data[3]
        ay = input_data[4]
        az = input_data[5]
        mx = input_data[6]
        my = input_data[7]
        mz = input_data[8]
        timeutc = input_data[9]
        q0 = input_data[10]
        q1 = input_data[11]
        q2 = input_data[12]
        q3 = input_data[13]

        # Get quaternions
        qe0 = output_data[0]
        qe1 = output_data[1]
        qe2 = output_data[2]
        qe3 = output_data[3]
        
        data = [
            {'ID': 'RET', 'Type': 'ATT', 'Number': ii, 'Datetime [UTC]': timeutc,
            'GyroX [rad/s]': gx , 'GyroY [rad/s]': gy, 'GyroZ [rad/s]': gz,
            'AccX [m/s^2]': ax, 'AccY [m/s^2]': ay, 'AccZ [m/s^2]': az, 
            'MagX': mx, 'MagY': my, 'MagZ': mz, 'q0': q0, 'q1': q1, 'q2': q2, 'q3': q3,
            'qe0': qe0, 'qe1': qe1, 'qe2': qe2, 'qe3': qe3,
            }
        ]

    elif exp == 'GNSS':

        # Get measurements
        carrier1 = input_data[0]
        pseudo1  = input_data[1]
        doppler1 = input_data[2]
        carrier2 = input_data[3]
        pseudo2  = input_data[4]
        doppler2 = input_data[5]

        # Get output
        lat     = output_data[0]
        lon     = output_data[1]
        alt     = output_data[2]
        timeutc = output_data[2]

        data = [
            {'ID': 'RET', 'Type': 'GNSS', 'Number': ii, 'Datetime [UTC]': timeutc,
            'Carrier phase 1': carrier1 , 'Pseudorange 1': pseudo1, 'Doppler 1': doppler1,
            'Carrier phase 2': carrier2, 'Pseudorange 2': pseudo2, 'Doppler 2': doppler2, 
            'Latitude': lat, 'Longitude': lon, 'Altitude': alt}
        ]

    return data

def packetstring(input_data, output_data, ii, exp):

    if exp == 'AI':

        # Get measurements
        gx = input_data[0]
        gy = input_data[1]
        gz = input_data[2]
        ax = input_data[3]
        ay = input_data[4]
        az = input_data[5]
        mx = input_data[6]
        my = input_data[7]
        mz = input_data[8]
        timeutc = input_data[9]
        q0 = input_data[10]
        q1 = input_data[11]
        q2 = input_data[12]
        q3 = input_data[13]

        # Get quaternions
        qe0 = output_data[0]
        qe1 = output_data[1]
        qe2 = output_data[2]
        qe3 = output_data[3]

        merge = ['RET',exp,ii,timeutc,gx,gy,gz,ax,ay,az,mx,my,mz,q0,q1,q2,q3,qe0,qe1,qe2,qe3]
        
        data = ','.join(map(str, merge)) 
        data = data + '\n'
    elif exp == 'GNSS':

        # Get measurements
        carrier1 = input_data[0]
        pseudo1  = input_data[1]
        doppler1 = input_data[2]
        carrier2 = input_data[3]
        pseudo2  = input_data[4]
        doppler2 = input_data[5]

        # Get output
        lat     = output_data[0]
        lon     = output_data[1]
        alt     = output_data[2]
        timeutc = output_data[2]

        merge = ['RET',exp,ii,timeutc,carrier1,pseudo1,doppler1,carrier2,pseudo2,doppler2,lat,lon,alt]

    return data
