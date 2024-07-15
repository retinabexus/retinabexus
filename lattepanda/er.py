import serial
import csv
import time
from datetime import datetime, timedelta 
import functions as fn
#import send_serial_command


ser = serial.Serial('COM16', 115200, timeout=0)

commands = ['obsvma 1', 'obsvha 1','galepha 2', 'gloepha 2', 'gpsepha 2', 'bdsepha 2']

for command in commands:
    fn.send_serial_command(ser, command)


def generate_raw_data_csv_filename():
    timestamp = datetime.now().strftime("%H_%M_%S")
    return f"C:/Users/carol/OneDrive/Desktop/università/REXUS/software_RETINA/results/raw_data_{timestamp}.csv"

raw_data_csv_file = generate_raw_data_csv_filename()
next_file_change = datetime.now() + timedelta(minutes=30)


output_csv_phase_M = "C:/Users/carol/OneDrive/Desktop/università/REXUS/software_RETINA/results/phase_M.csv"
output_csv_phase_S = "C:/Users/carol/OneDrive/Desktop/università/REXUS/software_RETINA/results/phase_S.csv"
output_csv_ephem_GLO_M = "C:/Users/carol/OneDrive/Desktop/università/REXUS/software_RETINA/results/ephem_GLO_M.csv"
output_csv_ephem_GPS_M = "C:/Users/carol/OneDrive/Desktop/università/REXUS/software_RETINA/results/ephem_GPS_M.csv"
output_csv_ephem_BDS_M = "C:/Users/carol/OneDrive/Desktop/università/REXUS/software_RETINA/results/ephem_BDS_M.csv"
output_csv_ephem_GAL_M = "C:/Users/carol/OneDrive/Desktop/università/REXUS/software_RETINA/results/ephem_GAL_M.csv"


with open(output_csv_phase_M, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["PRN", "time reference", "week number", "SOW", "LS", "output delay time", "phi_M [cycles]", "pseudorange [m]", "Observation number", "psr std", "adr std", "dopp", "C/N0"])

with open(output_csv_phase_S, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["PRN", "time reference", "week number", "SOW", "LS", "output delay time", "phi_M [cycles]", "pseudorange [m]", "Observation number", "psr std", "adr std", "dopp", "C/N0"])

with open(output_csv_ephem_GLO_M, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Oscill Time", "Ref week", "SOW", "Positions", "Velocities", "f channel offset", "Week of eph", "Time of eph [ms]", "Time offset", "Number of day"])

with open(output_csv_ephem_GPS_M, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Oscill Time", "PRN", "Ref time", "SOW", "ref t eph", "a", "mm", "ma", "e", "w", "i", "RAAN", "tgd", "iode1", "weeks", "cuc", "cus", "crcs", "crs", "cic", "cis", "idot", "RAANdot", "iodc", "toc", "af0", "af1", "af2", "N"])

with open(output_csv_ephem_BDS_M, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["PRN", "Oscill Time", "Ref week", "SOW", "ref t eph", "a", "mm", "ma", "e", "w", "i", "RAAN", "tgd"])

with open(output_csv_ephem_GAL_M, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["PRN", "Oscill Time", "Ref week", "SOW", "ref t eph", "roota", "mm", "ma", "e", "w", "i", "RAAN"])

with open(raw_data_csv_file, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Raw Data"])



while True:
    
    if datetime.now() >= next_file_change:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        raw_data_csv_file = f"C:/Users/carol/OneDrive/Desktop/università/REXUS/software_RETINA/results/raw_data_{timestamp}.csv"
        next_file_change = datetime.now() + timedelta(minutes=30)

        with open(raw_data_csv_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
        writer.writerow(["Raw Data"])

    line = ser.readline().strip()

    if line:

        with open(raw_data_csv_file, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([line.decode('utf-8')])

        IDs_M, phi_Ms, pseudors_M, time_ref_M, wn_M, SOW_M, LS_M, odt_M, obs_nums_M, psr_stds_M, adr_stds_M, dopps_M, c_n0s_M = fn.extract_phi_M(line)
        IDs_S, phi_Ss, pseudors_S, time_ref_S, wn_S, SOW_S, LS_S, odt_S, obs_nums_S, psr_stds_S, adr_stds_S, dopps_S, c_n0s_S = fn.extract_phi_S(line)
        rss, vss, fos, ews, ets, tos, Nts, current_time_GLO, rw_GLO, SOW_GLO = fn.extract_position_GLO_M(line)
        PRN_GPS, rteph_GPS, a_GPS, mm_GPS, ma_GPS, e_GPS, w_GPS, i_GPS, RAAN_GPS, tgd_GPS, current_time_GPS, rw_GPS, SOW_GPS, iodes, weeks, cucs, cuss, crcs, crss, cics, ciss, idots, RAANdots, iodcs, tocs, af0s, af1s, af2s, Ns = fn.extract_position_GPS_M(line) 
        PRN_BDS, rteph_BDS, a_BDS, mm_BDS, ma_BDS, e_BDS, w_BDS, i_BDS, RAAN_BDS, tgd_BDS, current_time_BDS, rw_BDS, SOW_BDS = fn.extract_position_BDS_M(line)
        PRN_GAL, rteph_GAL, roota_GAL, mm_GAL, ma_GAL, e_GAL, w_GAL, i_GAL, RAAN_GAL, current_time_GAL, rw_GAL, SOW_GAL = fn.extract_position_GAL_M(line)


        if IDs_M and phi_Ms and pseudors_M and time_ref_M and wn_M and SOW_M and LS_M and odt_M:
            with open(output_csv_phase_M, 'a', newline='') as csvfile:
         
                    for i in range(len(IDs_M)):
                        writer = csv.writer(csvfile)
                        writer.writerow([IDs_M[i], time_ref_M, wn_M, SOW_M, LS_M, odt_M, phi_Ms[i], pseudors_M[i], obs_nums_M[i], psr_stds_M[i], adr_stds_M[i], dopps_M[i], c_n0s_M[i]])

        if IDs_S and phi_Ss and pseudors_S and time_ref_S and wn_S and SOW_S and LS_S and odt_S:
            with open(output_csv_phase_S, 'a', newline='') as csvfile:
         
                    for i in range(len(IDs_S)):
                        writer = csv.writer(csvfile)
                        writer.writerow([IDs_S[i], time_ref_S, wn_S, SOW_S, LS_S, odt_S, phi_Ss[i], pseudors_S[i], obs_nums_S[i], psr_stds_S[i], adr_stds_S[i], dopps_S[i], c_n0s_S[i]])                


        if rss and vss:
            with open(output_csv_ephem_GLO_M, 'a', newline='') as csvfile:
                    for i in range(len(fos)):
                        writer = csv.writer(csvfile)
                        writer.writerow([current_time_GLO, rw_GLO, SOW_GLO, rss[i], vss[i], fos[i], ews[i], ets[i], tos[i], Nts[i]])


        if PRN_GPS and rteph_GPS and a_GPS and mm_GPS and ma_GPS and e_GPS and w_GPS and i_GPS and RAAN_GPS and tgd_GPS:
            with open(output_csv_ephem_GPS_M, 'a', newline='') as csvfile:
                    for i in range(len(PRN_GPS)):
                        writer = csv.writer(csvfile)
                        writer.writerow([current_time_GPS, PRN_GPS[i], rw_GPS, SOW_GPS, rteph_GPS[i], a_GPS[i], mm_GPS[i], ma_GPS[i], e_GPS[i], w_GPS[i], i_GPS[i], RAAN_GPS[i], tgd_GPS[i], iodes[i], weeks[i], cucs[i], cuss[i], crcs[i], crss[i], cics[i], ciss[i], idots[i], RAANdots[i], iodcs[i], tocs[i], af0s[i], af1s[i], af2s[i], Ns[i]])


        if PRN_BDS and rteph_BDS and a_BDS and mm_BDS and ma_BDS and e_BDS and w_BDS and i_BDS and RAAN_BDS and tgd_BDS:
            with open(output_csv_ephem_BDS_M, 'a', newline='') as csvfile:
                    for i in range(len(PRN_BDS)):
                        writer = csv.writer(csvfile)
                        writer.writerow([PRN_BDS[i], current_time_BDS, rw_BDS, SOW_BDS, rteph_BDS[i], a_BDS[i], mm_BDS[i], ma_BDS[i], e_BDS[i], w_BDS[i], i_BDS[i], RAAN_BDS[i], tgd_BDS[i]])


        if PRN_GAL and rteph_GAL and roota_GAL and mm_GAL and ma_GAL and e_GAL and w_GAL and i_GAL and RAAN_GAL:
            with open(output_csv_ephem_GAL_M, 'a', newline='') as csvfile:
                    for i in range(len(PRN_GAL)):
                        writer = csv.writer(csvfile)
                        writer.writerow([PRN_GAL[i], current_time_GAL, rw_GAL, SOW_GAL, rteph_GAL[i], roota_GAL[i], mm_GAL[i], ma_GAL[i], e_GAL[i], w_GAL[i], i_GAL[i], RAAN_GAL[i]])

    time.sleep(1)

ser.close()
