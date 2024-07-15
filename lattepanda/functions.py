from datetime import datetime 
import serial
import time

def send_serial_command(ser, command):
    #try:
        # Aspetta un attimo per assicurarti che la connessione sia stabilita
        time.sleep(2)

        # Invia il comando sulla seriale
        ser.write(command.encode('utf-8') + b'\r\n')  # Aggiungi '\r\n' per inviare CR LF
        print('c')

        # Leggi la risposta (opzionale)
        response = ser.read(500).decode('utf-8')  # Leggi fino a 100 byte di risposta
        print(f"Risposta ricevuta: {response}")
        
    #except serial.SerialException as e:
    #    print(f"Errore nella comunicazione seriale: {e}")

def extract_phi_M(message):
    IDs = []
    phi_Ms = []
    observations = []
    observations_0 = []
    pseudors = []
    obs_nums = []
    psr_stds = []
    adr_stds = []
    dopps = []
    c_n0s = []
    time_ref = ""
    wn = ""
    LS = ""
    odt = ""
    SOW = ""


    message_str = message.decode('utf-8').strip()
    if message_str.startswith("#OBSVMA"):
        parts = message_str.split(';')
        if len(parts) > 1:
            observations_0 = parts[0].split(',')
            time_ref = observations_0[2]
            wn = observations_0[4]
            SOW = observations_0[5]
            LS = observations_0[8]
            odt = observations_0[9]

            observations = parts[1].split(',')
        for i in range(len(observations) // 9):
                if (2 +11*i) < len(observations):
                    try:
                        obs_num = observations[0+11*i]
                        ID = observations[2+11*i]
                        pseudor = observations[3+11*i]
                        phi_M = observations[4+11*i]
                        psr_std = observations[5+11*i]
                        adr_std = observations[6+11*i]
                        dopp = observations[7+11*i]
                        c_n0 = observations[8+11*i]

                        IDs.append(ID)
                        phi_Ms.append(phi_M)
                        pseudors.append(pseudor)
                        obs_nums.append(obs_num)
                        psr_stds.append(psr_std)
                        adr_stds.append(adr_std)
                        dopps.append(dopp)
                        c_n0s.append(c_n0)
                    
                    except IndexError:
                        print("FASE Errore di indice durante l'estrazione dei dati")
    return IDs, phi_Ms, pseudors, time_ref, wn, SOW, LS, odt, obs_nums, psr_stds, adr_stds, dopps, c_n0s



def extract_phi_S(message):
    IDs = []
    phi_Ms = []
    observations = []
    observations_0 = []
    pseudors = []
    obs_nums = []
    psr_stds = []
    adr_stds = []
    dopps = []
    c_n0s = []
    time_ref = ""
    wn = ""
    LS = ""
    odt = ""
    SOW = ""


    message_str = message.decode('utf-8').strip()
    if message_str.startswith("#OBSVHA"):
        parts = message_str.split(';')
        if len(parts) > 1:
            observations_0 = parts[0].split(',')
            time_ref = observations_0[2]
            wn = observations_0[4]
            SOW = observations_0[5]
            LS = observations_0[8]
            odt = observations_0[9]

            observations = parts[1].split(',')
        for i in range(len(observations) // 9):
                if (2 +11*i) < len(observations):
                    try:
                        obs_num = observations[0+11*i]
                        ID = observations[2+11*i]
                        pseudor = observations[3+11*i]
                        phi_M = observations[4+11*i]
                        psr_std = observations[5+11*i]
                        adr_std = observations[6+11*i]
                        dopp = observations[7+11*i]
                        c_n0 = observations[8+11*i]

                        IDs.append(ID)
                        phi_Ms.append(phi_M)
                        pseudors.append(pseudor)
                        obs_nums.append(obs_num)
                        psr_stds.append(psr_std)
                        adr_stds.append(adr_std)
                        dopps.append(dopp)
                        c_n0s.append(c_n0)
                    
                    except IndexError:
                        print("FASE Errore di indice durante l'estrazione dei dati")
    return IDs, phi_Ms, pseudors, time_ref, wn, SOW, LS, odt, obs_nums, psr_stds, adr_stds, dopps, c_n0s

def extract_position_GLO_M(message):
    observations = []
    observations_0 = []
    rss = []
    vss = []
    fos = []
    ews = []
    ets = []
    tos = []
    Nts = []
    current_time = ""
    rw = ""
    SOW = ""
    

    message_str = message.decode('utf-8').strip()
    if message_str.startswith("#GLOEPHA"):
        parts = message_str.split(';')
        if len(parts) > 1:
            observations_0 = parts[0].split(',')
            observations = parts[1].split(',')
            rw = observations_0[5]
            SOW = observations_0[6]
            #if len(observations) >16:
            for i in range(len(observations) // 28):
                    if (1 +30*i) < len(observations):
                        try:
                            fo = observations[1+30*i]
                            ew = observations[3+30*i]
                            et = observations[4+30*i]
                            to = observations[5+30*i]
                            Nt = observations[6+30*i]
                            rs = [observations[12+30*i], observations[13+30*i], observations[14+30*i]]
                            vs = [observations[15+30*i], observations[16+30*i], observations[17+30*i]]
                            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S") #sync con oscillatore

                            fos.append(fo)
                            ews.append(ew)
                            ets.append(et)
                            tos.append(to)
                            Nts.append(Nt)
                            rss.append(rs)
                            vss.append(vs)

                        except IndexError:
                            print("GLONASS Errore di indice durante l'estrazione dei dati")            
    return rss, vss, fos, ews, ets, tos, Nts, current_time, rw, SOW


def extract_position_GPS_M(message):
    observations = []
    observations_0 = []
    PRNs = []
    iodes= []
    weeks = []
    rtephs = [] #reference time of ephemeris
    ass = []
    mms = []
    mas = []
    es = []
    ws = []
    cucs = []
    cuss = []
    crcs = []
    crss = []
    cics = []
    ciss = []
    iss = []
    idots = []
    RAANs =[]
    RAANdots = []
    iodcs = []
    tocs = []
    tgds = [] #total group delay
    af0s = []
    af1s = []
    af2s = []
    Ns = []
    current_time = ""
    rw = ""
    SOW = ""


    message_str = message.decode('utf-8').strip()
    if message_str.startswith("#GPSEPHA"):
        parts = message_str.split(';')

        if len(parts) > 1:
            observations_0 = parts[0].split(',')
            observations = parts[1].split(',')
            rw = observations_0[5]
            SOW = observations_0[8]
            #if len(observations) > 25:
            for i in range(len(observations) // 31):
                    if (1 +33*i) < len(observations):
                        try:
                            PRN = observations[0+33*i]
                            iode1 = observations[3+33*i]
                            week = observations[5+33*i]
                            rteph = observations[7+33*i] #reference time of ephemeris
                            a = observations[8+33*i]
                            mm = observations[9+33*i]
                            ma = observations[10+33*i]
                            e = observations[11+33*i]
                            w = observations[12+33*i]
                            cuc = observations[13+33*i]
                            cus = observations[14+33*i]
                            crc = observations[15+33*i]
                            crs = observations[16+33*i]
                            cic = observations[17+33*i]
                            cis = observations[18+33*i]
                            inc = observations[19+33*i]
                            idot = observations[20+33*i]
                            raan = observations[21+33*i]
                            raandot = observations[22+33*i]
                            iodc = observations[23+33*i]
                            toc = observations[24+33*i]
                            tgd = observations[25+33*i]
                            af0 = observations[26+33*i]
                            af1 = observations[27+33*i]
                            af2 = observations[28+33*i]
                            N = observations[29+33*i]
                            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                            ass.append(a)
                            PRNs.append(PRN)
                            iodes.append(iode1)
                            weeks.append(week)
                            rtephs.append(rteph)
                            mms.append(mm)
                            mas.append(ma)
                            es.append(e)
                            ws.append(w)
                            cucs.append(cuc)
                            cuss.append(cus)
                            crcs.append(crc)
                            crss.append(crs)
                            cics.append(cic)
                            ciss.append(cis)
                            iss.append(inc)
                            idots.append(idot)
                            RAANs.append(raan)
                            RAANdots.append(raandot)
                            iodcs.append(iodc)
                            tocs.append(toc)
                            tgds.append(tgd)
                            af0s.append(af0)
                            af1s.append(af1)
                            af2s.append(af2)
                            Ns.append(N)


                        except IndexError:
                            print("GPS Errore di indice durante l'estrazione dei dati")  
            
    return PRNs, rtephs, ass, mms, mas, es, ws, iss, RAANs, tgds, current_time, rw, SOW, iodes, weeks, cucs, cuss, crcs, crss, cics, ciss, idots, RAANdots, iodcs, tocs, af0s, af1s, af2s, Ns 


def extract_position_BDS_M(message):
    observations = []
    observations_0 = []
    PRNs = []
    rtephs = [] #reference time of ephemeris
    ass = []
    mms = []
    mas = []
    es = []
    ws = []
    iss = []
    RAANs =[]
    tgds = [] #total group delay
    current_time = ""
    rw = ""
    SOW = ""


    message_str = message.decode('utf-8').strip()
    if message_str.startswith("#BDSEPHA"):
        parts = message_str.split(';')

        if len(parts) > 1:
            observations_0 = parts[0].split(',')
            observations = parts[1].split(',')
            rw = observations_0[5]
            SOW = observations_0[6]
            #if len(observations) > 25:
            for i in range(len(observations) // 32):
                    if (1 +34*i) < len(observations):
                        try:
                            PRN = observations[0+34*i]
                            rteph = observations[7+34*i] #reference time of ephemeris
                            a = observations[8+34*i]
                            mm = observations[9+34*i]
                            ma = observations[10+34*i]
                            e = observations[11+34*i]
                            w = observations[12+34*i]
                            inc = observations[19+34*i]
                            RAAN = observations[21+34*i]
                            tgd = observations[25+34*i]
                            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                            ass.append(a)
                            PRNs.append(PRN)
                            rtephs.append(rteph)
                            mms.append(mm)
                            mas.append(ma)
                            es.append(e)
                            ws.append(w)
                            iss.append(inc)
                            RAANs.append(RAAN)
                            tgds.append(tgd)

                        except IndexError:
                            print("BEIDOU Errore di indice durante l'estrazione dei dati")  
            
    return PRNs, rtephs, ass, mms, mas, es, ws, iss, RAANs, tgds, current_time, rw, SOW

def extract_position_GAL_M(message):
    observations = []
    observations_0 = []
    PRNs = []
    rtephs = [] #reference time of ephemeris
    rootas = []
    mms = []
    mas = []
    es = []
    ws = []
    iss = []
    RAANs =[]
    current_time = ""
    rw = ""
    SOW = ""


    message_str = message.decode('utf-8').strip()
    if message_str.startswith("#GALEPHA"):
       parts = message_str.split(';')

       if len(parts) > 1:
            observations_0 = parts[0].split(',')
            observations = parts[1].split(',')
            rw = observations_0[5]
            SOW = observations_0[6]
            #if len(observations) > 26:
            for i in range(len(observations) // 37):
                    if (1 +34*i) < len(observations):
                        try:
                            PRN = observations[0+34*i]
                            rteph = observations[12+34*i] #reference time of ephemeris
                            roota = observations[13+34*i]
                            mm = observations[14+34*i]
                            ma = observations[15+34*i]
                            e = observations[16+34*i]
                            w = observations[17+34*i]
                            inc = observations[24+34*i]
                            RAAN = observations[26+34*i]
                            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                            rootas.append(roota)
                            PRNs.append(PRN)
                            rtephs.append(rteph)
                            mms.append(mm)
                            mas.append(ma)
                            es.append(e)
                            ws.append(w)
                            iss.append(inc)
                            RAANs.append(RAAN)
                            

                        except IndexError:
                                print("GALILEO Errore di indice durante l'estrazione dei dati")
                            
          
    return PRNs, rtephs, rootas, mms, mas, es, ws, iss, RAANs, current_time, rw, SOW