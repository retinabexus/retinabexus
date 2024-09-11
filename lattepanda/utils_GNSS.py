import numpy as np
from numpy.linalg import inv
import time

def send_serial_command(ser, command):
    import time
    time.sleep(2)
    ser.write(command.encode('utf-8') + b'\r\n')

def hex_to_bin(hex_str):
    """Convert hexadecimal string to binary string."""
    bin_str = bin(int(hex_str, 16))[2:]  # Convert hex to int, then int to binary string
    return bin_str.zfill(32)  # Pad with leading zeros to ensure the binary string is 32 bits long

def bin_to_dec(bin_str):
    """Convert binary string to decimal integer."""
    return int(bin_str, 2)

def extract_bits(value, start, length):
    """Extract specific bits from a binary string."""
    return value[start:start + length]

def hex_to_bin(hex_str):
    """Convert hexadecimal string to binary string."""
    bin_str = bin(int(hex_str, 16))[2:]  # Convert hex to int, then int to binary string
    return bin_str.zfill(32)  # Pad with leading zeros to ensure the binary string is 32 bits long

def bin_to_dec(bin_str):
    """Convert binary string to decimal integer."""
    return int(bin_str, 2)

def decode_ch_tr_status(ch_tr_status_hex):
    """Decode the channel tracking status from a hexadecimal string."""
    ch_tr_status_bin = hex_to_bin(ch_tr_status_hex)

    # Extract and convert satellite system (bits 16-18)
    bit_16 = (int(ch_tr_status_hex, 16) & 0x00010000) >> 16
    bit_17 = (int(ch_tr_status_hex, 16) & 0x00020000) >> 17
    bit_18 = (int(ch_tr_status_hex, 16) & 0x00040000) >> 18

    # Combine the bits to form the satellite system value
    satellite_system = (bit_18 << 2) | (bit_17 << 1) | bit_16

    # Satellite systems mapping
    satellite_systems = {
        0: "GPS",
        1: "GLONASS",
        2: "SBAS",
        3: "GALILEO",
        4: "BEIDOU",
        5: "QZSS",
        6: "Reserved",
        7: "Reserved"
    }

    system_name = satellite_systems.get(satellite_system, "Unknown")

    # Extract and convert signal type (bits 20-27)
    bit_20 = (int(ch_tr_status_hex, 16) & 0x00100000) >> 20
    bit_21 = (int(ch_tr_status_hex, 16) & 0x00200000) >> 21
    bit_22 = (int(ch_tr_status_hex, 16) & 0x00400000) >> 22
    bit_23 = (int(ch_tr_status_hex, 16) & 0x00800000) >> 23
    bit_24 = (int(ch_tr_status_hex, 16) & 0x01000000) >> 24
    bit_25 = (int(ch_tr_status_hex, 16) & 0x02000000) >> 25
    bit_26 = (int(ch_tr_status_hex, 16) & 0x04000000) >> 26
    bit_27 = (int(ch_tr_status_hex, 16) & 0x08000000) >> 27

    # Combine the bits to form the signal type value
    signal_type = (bit_25 << 4) | (bit_24 << 3) | (bit_23 << 2) | (bit_22 << 1) | (bit_21 << 0)

    # Signal types and their frequencies for different satellite systems
    signal_types = {
        "GPS": {
            0: {"type": "L1 C/A", "frequency": 1575.42},
            9: {"type": "L2P (Y)", "frequency": 1227.60},
            6: {"type": "L5 data", "frequency": 1176.45},
            14: {"type": "L5 pilot", "frequency": 1176.45},
            17: {"type": "L2C (L)", "frequency": 1227.60}
        },
        "GLONASS": {
            0: {"type": "L1 C/A", "frequency": 1602.00},
            5: {"type": "L2 C/A", "frequency": 1246.00}
        },
        "SBAS": {
            0: {"type": "L1 C/A", "frequency": 1575.42},
            6: {"type": "L5 (I)", "frequency": 1176.45}
        },
        "GALILEO": {
            1: {"type": "E1B", "frequency": 1575.42},
            2: {"type": "E1C", "frequency": 1575.42},
            12: {"type": "E5A pilot", "frequency": 1176.45},
            17: {"type": "E5B pilot", "frequency": 1207.14}
        },
        "BEIDOU": {
            0: {"type": "B1I", "frequency": 1561.098},
            4: {"type": "B1Q", "frequency": 1561.098},
            8: {"type": "B1C (Pilot)", "frequency": 1575.42},
            23: {"type": "B1C (Data)", "frequency": 1575.42},
            5: {"type": "B2Q", "frequency": 1207.14},
            17: {"type": "B2I", "frequency": 1207.14},
            12: {"type": "B2a (Pilot)", "frequency": 1176.45},
            28: {"type": "B2a (Data)", "frequency": 1176.45},
            6: {"type": "B3Q", "frequency": 1268.52},
            21: {"type": "B3I", "frequency": 1268.52},
            13: {"type": "B2b (I)", "frequency": 1207.14}
        },
        "QZSS": {
            0: {"type": "L1 C/A", "frequency": 1575.42},
            6: {"type": "L5 data", "frequency": 1176.45},
            14: {"type": "L5 pilot", "frequency": 1176.45},
            17: {"type": "L2C (L)", "frequency": 1227.60},
            27: {"type": "L2C (L)", "frequency": 1227.60}
        }
    }

    signal_info = signal_types.get(system_name, {}).get(signal_type, {"type": "Unknown", "frequency": "Unknown"})
    f = float(signal_info["frequency"])

    return f,{
        "satellite_system": system_name,
        "signal_type": signal_info["type"],
        "frequency": signal_info["frequency"]
    }


def extract_phi_M(message):
    IDs_M, phi_Ms, pseudors_M, phi_std_Ms, constellations_M, fs_M, fs_S = [], [], [], [], [], [], []
    IDs_S, phi_Ss, pseudors_S, phi_std_Ss, constellations_S = [], [], [], [], []
    SOW_M, SOW_S = "", ""
    
    message_str = message.decode('utf-8').strip()
    if message_str.startswith("#OBSVMA"):
        parts = message_str.split(';')
        if len(parts) > 1:
            observations_0_M = parts[0].split(',')
            SOW_M = observations_0_M[5]

            observations_M = parts[1].split(',')
            for i in range(len(observations_M) //11):
                if (2 + 11 * i) < len(observations_M):
                    try:
                        ID = observations_M[2 + 11 * i]
                        pseudor_M = observations_M[3 + 11 * i]
                        phi_M = observations_M[4 + 11 * i]
                        phi_std_M = observations_M[6 + 11 * i]
                        ch_tr_status_hex_M = observations_M[11 + 11 * i]
                        ch_tr_status_hex_M = ch_tr_status_hex_M.split('*')[0].strip()
                        f_M,constellation_M = decode_ch_tr_status(ch_tr_status_hex_M)

                        if ID != "" and phi_M != "":
                                IDs_M.append(ID)
                                pseudors_M.append(pseudor_M)
                                phi_Ms.append(phi_M)
                                phi_std_Ms.append(phi_std_M)
                                fs_M.append(f_M)
                                constellations_M.append(tuple(sorted(constellation_M.items())))
                    except IndexError:
                        continue
                    except ValueError as e:
                        continue

    if message_str.startswith("#OBSVHA"):
        parts = message_str.split(';')
        if len(parts) > 1:
            observations_0_S = parts[0].split(',')
            SOW_S = observations_0_S[5]

            observations_S = parts[1].split(',')
            for i in range(len(observations_S) // 11):
                if (2 + 11 * i) < len(observations_S):
                    try:
                        ID_S = observations_S[2 + 11 * i]
                        pseudor_S = observations_S[3 + 11 * i]
                        phi_S = observations_S[4 + 11 * i]
                        phi_std_S = observations_S[6 + 11 * i]
                        ch_tr_status_hex_S = observations_S[11 + 11 * i]
                        ch_tr_status_hex_S = ch_tr_status_hex_S.split('*')[0].strip() 
                        f_S,constellation_S = decode_ch_tr_status(ch_tr_status_hex_S)

                        if ID_S != "" and phi_S != "":
                            IDs_S.append(ID_S)
                            pseudors_S.append(pseudor_S)
                            phi_Ss.append(phi_S)
                            phi_std_Ss.append(phi_std_S)
                            fs_S.append(f_S)
                            constellations_S.append(tuple(sorted(constellation_S.items())))
                    except IndexError:
                        continue
                    except ValueError as e:
                        continue

    packet_M = (IDs_M, pseudors_M, phi_Ms, phi_std_Ms, constellations_M, fs_M,SOW_M)
    packet_S = (IDs_S, pseudors_S, phi_Ss, phi_std_Ss, constellations_S, fs_S, SOW_S)
    return packet_M, packet_S


def match_master_slave_packets(master_packets, slave_packets):
    matched_pairs = []
    freq = []

 # controllo sul SOW   
    for master in master_packets:
        for slave in slave_packets:
            if master[6] == slave[6] != "":
                common_terms = set(master[5]) & set(slave[5])
                
                if common_terms:
                    matched_pairs.append((master, slave))
                    freq.extend(common_terms)  # Aggiungi i termini comuni alla lista delle frequenze

    return matched_pairs, freq


def compare_and_extract_phase(master, slave):
    master_IDs, master_pseudors, master_phis, master_phi_stds, master_consts, master_fs, master_SOW = master
    slave_IDs, slave_pseudors, slave_phis, slave_phi_stds, slave_consts, slave_fs, slave_SOW = slave

    if not master_IDs or not slave_IDs:
        return

    matched_phases = []
    std_devs_dict = {}
    pseudoranges_dict = {}

    for m_id, m_phi, m_pseudor, m_std, m_const, m_fs in zip(master_IDs, master_phis, master_pseudors, master_phi_stds, master_consts, master_fs):

        # controllo sulla frequenza
        if m_fs in slave_fs:
            s_freq = slave_fs[slave_fs.index(m_fs)]
            s_phi = slave_phis[slave_fs.index(m_fs)]
            s_pseudor = slave_pseudors[slave_fs.index(m_fs)]
            s_std = slave_phi_stds[slave_fs.index(m_fs)]
            s_const = slave_consts[slave_fs.index(m_fs)]
            

            try:
                # Prova a convertire le variabili e appendere
                matched_phases.append((
                    float(m_id), 
                    float(m_phi), 
                    float(s_phi), 
                    float(m_pseudor), 
                    float(s_pseudor), 
                    float(m_std) / 10000, 
                    float(s_std) / 10000, 
                    m_const, 
                    m_fs,
                    master_SOW
                ))
            except ValueError as e:
                continue 
            
            # Salva le deviazioni standard e pseudoranges per la frequenza corrente
            if m_const not in std_devs_dict:
                std_devs_dict[m_const] = []
                pseudoranges_dict[m_const] = []

            std_devs_dict[m_const].extend([float(m_std) / 10000, float(s_std) / 10000])
            pseudoranges_dict[m_const].extend([m_pseudor, s_pseudor])

    double_diff_results = {}
    for constellation in std_devs_dict.keys():
        if len(std_devs_dict[constellation]) >= 4:
            double_diff_results[constellation] = (None, matched_phases, pseudoranges_dict[constellation], std_devs_dict[constellation])

    return double_diff_results, s_freq


def inizializzazione(double_diff_results, freq, sow_old, f_old):
    c = 299792458  # Velocità della luce in m/s
    packet2send =  []
    sow_now = ""
    f_now = ""
    freq_index = 0  # Indice per tenere traccia della frequenza corrente

    for constellation, data in double_diff_results.items():
        double_diff, matched_phases, pseudoranges, deviations = data
        id = []
        cost = []
        #lambd = c / (freq * 1000000)
        
        for i in range(0, 4, 2):

            if len(matched_phases) <= i+1 or len(pseudoranges) <= i+1:  # Controllo che matched_phases abbia abbastanza elementi
                return None, None, None 

            else:
                m_pseudor_1 = float(matched_phases[i][3])
                m_pseudor_2 = float(matched_phases[i+1][3])
                s_pseudor_1 = float(matched_phases[i][4])
                s_pseudor_2 = float(matched_phases[i+1][4])
                m_std_1 = float(matched_phases[i][5])
                m_std_2 = float(matched_phases[i+1][5])
                s_std_1 = float(matched_phases[i][6])
                s_std_2 = float(matched_phases[i+1][6])
                m_phi_1 = matched_phases[i][1]
                m_phi_2 = matched_phases[i+1][1]
                s_phi_1 = matched_phases[i][2]
                s_phi_2 = matched_phases[i+1][2]
                id.append(matched_phases[i][0])
                sow = matched_phases[i][9] 
                satellite_system = next(value for key, value in matched_phases[i][7] if key == 'satellite_system')
                cost.append(satellite_system)
                #N_float.append((1 / lambd) * (lambd * m_phi - m_pseudor))
                #N_float.append((1 / lambd) * (lambd * s_phi - s_pseudor))
                #std_devs.extend([m_std, s_std])
#
        freq_index += 1  # Passa alla frequenza successiva
        if len(cost) < 2:
            return None, None, None

        # Estrai solo l'orario
        date = time.time()
        # creo il vettore da mandare on ground: [sow, id_m, id_s, cost_m, cost_s, f, pseudor_m, pseudor_s, std_m, std_s, phase_m, phase_s]
        vector = ["RET", "GNSS",date, sow, id[0], id[1], cost[0], cost[1], freq, m_pseudor_1, m_pseudor_2, s_pseudor_1, s_pseudor_2, m_std_1, m_std_2, s_std_1, s_std_2, m_phi_1, m_phi_2, s_phi_1, s_phi_2]

        if vector[0] != sow_old or freq != f_old:
            packet2send = vector
            sow_now = vector[0]
            f_now = freq
            break
        else:
            return None, None, None       

    return packet2send, sow_now, f_now



def extract_data(message):
    vect_M = []
    vect_S = []

    message_str = message.decode('utf-8').strip()
    if message_str.startswith("#BESTNAVA"):
        parts = message_str.split(';')
        if len(parts) > 1:

            observations_M = parts[1].split(',')

            if len(observations_M) > 27:
                    try:
                        lat_M = observations_M[2]           #latitudine master [°]
                        lon_M = observations_M[3]           #longitudine master [°]
                        alt_M = observations_M[4]           #altitudine master [m]
                        hor_speed_M = observations_M[25]    #horizontal speed master [m/s]   
                        trk_gnd_M = observations_M[26]      #actual direction of motion wrt True North master [°]
                        ver_speed_M = observations_M[27]    #vertical speed master [m/s]

                        if lat_M != "" and lon_M != "" and alt_M != "" and hor_speed_M != "" and trk_gnd_M != "" and ver_speed_M != "":
                            date = time.time()
                            vect_M = ["RET", "ANT",date, "ANT1", lat_M, lon_M, alt_M, hor_speed_M, trk_gnd_M, ver_speed_M]

                    except ValueError as e:
                        print(f"{e}")

    if message_str.startswith("#BESTNAVHA"):
            parts = message_str.split(';')
            if len(parts) > 1:

                observations_S = parts[1].split(',')

                if len(observations_S) > 27:
                        try:
                            lat_S = observations_S[2]           #latitudine slave [°]
                            lon_S = observations_S[3]           #longitudine slave [°]
                            alt_S = observations_S[4]           #altitudine slave [m]
                            hor_speed_S = observations_S[25]    #horizontal speed slave [m/s]   
                            trk_gnd_S = observations_S[26]      #actual direction of motion wrt True North slave [°]
                            ver_speed_S = observations_S[27]    #vertical speed slave [m/s]

                            if lat_S != "" and lon_S != "" and alt_S != "" and hor_speed_S != "" and trk_gnd_S != "" and ver_speed_S != "":
                                date = time.time()
                                vect_S = ["RET", "ANT", date, "ANT2", lat_S, lon_S, alt_S, hor_speed_S, trk_gnd_S, ver_speed_S]
                                
                        except ValueError as e:
                            print(f"{e}")

    return vect_M, vect_S

