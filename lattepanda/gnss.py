import serial
import function as fn

ser = serial.Serial('COM16', 115200, timeout=0)

# i primi 4 messaggi servono per il codice mentre gli ultimi 4 vanno solo salvati raw
commands = ['obsvma 1', 'obsvha 1', 'bestnava 2', 'bestnavha 2', 'galepha 1', 'gloepha 1', 'gpsepha 1', 'bdsepha 1']

for command in commands:
    fn.send_serial_command(ser, command)

master_packets = []
slave_packets = []
sow_old = ""
f_old = ""
i = 0
ii = 0
iii = 0
while True:

    line = ser.readline().strip()
    if line:
        packet_M, packet_S = fn.extract_phi_M(line)
        master, slave = fn.extract_data(line)

        if packet_M:
            master_packets.append(packet_M)
        if packet_S:
            slave_packets.append(packet_S)

        if master != []:
            ii = ii + 1
            vect_m = master
            vect_m.insert(2,ii)
            stringa_M = ",".join([str(vect_m)])
            print("M", stringa_M)
        if slave != []:
            iii = iii + 1 
            vect_s = slave
            vect_s.insert(2, iii)
            stringa_S = ",".join([str(vect_s)])
            print("S", stringa_S)


        matched_pairs, freq = fn.match_master_slave_packets(master_packets, slave_packets)
        for master, slave in matched_pairs:
            double_diff_results, s_freq = fn.compare_and_extract_phase(master, slave)
            
            if s_freq:
                dd_packet, sow_now, f_now = fn.inizializzazione(double_diff_results, s_freq, sow_old, f_old)
                sow_old = sow_now
                f_old = f_now
                if dd_packet != None:
                    i = i + 1
                    counter = i
                    dd_packet.insert(2, counter)
                    packet2send = ",".join([str(dd_packet)])
                    print(packet2send)
