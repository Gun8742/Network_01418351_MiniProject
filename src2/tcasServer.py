import socket;
import math;
import time;

HOST = "127.0.0.1";
PORT = 8080;
CRASH_DIST = 0.2;
TIMEOUT = 6;

print("""
  _______   _____           _____   _____
 |__   __| / ____|   /\\    / ____| |  __ \\
    | |   | |       /  \\  | (___   | |__) |
    | |   | |      / /\\ \\  \\___ \\  |  ___/
    | |   | |____ / ____ \\ ____) | | |
    |_|    \\_____/_/    \\_\\_____/  |_|
                                         
 [+] TCASP Server Initialized...
 [+] Listening on UDP Port 8080...
""");
socketServer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM);
socketServer.bind((HOST, PORT));

aircrafts = {};

while True:
    data, addr = socketServer.recvfrom(1024);
    message = data.decode("utf-8");
    parts = message.split();

    if len(parts) != 7 or parts[0] != "TCASP/1.0" or parts[1] != "PING":
        response = "TCASP/1.0 0 400 BAD_REQUEST INVALID_FORMAT";
        socketServer.sendto(response.encode("utf-8"), addr);
        continue;

    seq = parts[2];
    flightID = parts[3];
    try:
        posX = float(parts[4]);
        posY = float(parts[5]);
        posZ = float(parts[6]);
    except ValueError:
        print(f"[ERROR] Invalid coordinate from {flightID}: {parts[4]} {parts[5]} {parts[6]}");
        response = f"TCASP/1.0 {seq} 400 BAD_REQUEST INVALID_COORDINATE";
        socketServer.sendto(response.encode("utf-8"), addr);
        continue;

    
    aircrafts[flightID] = {
        "posX": posX,
        "posY": posY,
        "posZ": posZ,
        "addr": addr,
        "last_seen": time.time(),
        "seq": seq
    };

    print(f"\n[RECV] {flightID:<8} X ={posX:>6.1f}  Y ={posY:>6.0f} ft  Z ={posZ:>6.1f}");

    now = time.time();
    ids = list(aircrafts.keys());
    for fid in ids:
        if (now - aircrafts[fid]["last_seen"] > TIMEOUT):
            print(f"[INFO] {fid} timed out, removed from radar");
            del aircrafts[fid];

    if len(aircrafts) < 2:
        status = "200 CLEAR MAINTAIN_HEADING";
        response = f"TCASP/1.0 {seq} [{flightID}] {status}";
        socketServer.sendto(response.encode("utf-8"), addr);
        print(f"[SEND] {flightID:<8} {status}");
    else:
        ids = list(aircrafts.keys());
        crashed = set();
        for i in range(len(ids) - 1):
            if (ids[i] in crashed):
                continue;
            plane1 = aircrafts[ids[i]];
            for j in range(i + 1, len(ids)):
                if (ids[j] in crashed):
                    continue;
                plane2 = aircrafts[ids[j]];
                total_distance = math.sqrt((plane1["posX"] - plane2["posX"]) ** 2 + (plane1["posZ"] - plane2["posZ"]) ** 2);
                vertical_gap = abs(plane1["posY"] - plane2["posY"]);

                print(f"[CALC] {ids[i]} <-> {ids[j]}   distance ={total_distance:>5.2f} nm   gap ={vertical_gap:>5.0f} ft");

                if total_distance > 5.0 or vertical_gap >= 1000:
                    status1 = f"200 CLEAR MAINTAIN_HEADING (FOUND {ids[j]})";
                    status2 = f"200 CLEAR MAINTAIN_HEADING (FOUND {ids[i]})";
                elif total_distance > 2.0:
                    status1 = f"300 TA_TRAFFIC MONITOR_CLOSELY (FOUND {ids[j]})";
                    status2 = f"300 TA_TRAFFIC MONITOR_CLOSELY (FOUND {ids[i]})";
                elif total_distance > CRASH_DIST:
                    status1 = f"401 RA_CLIMB CLIMB_IMMEDIATELY (FOUND {ids[j]})";
                    status2 = f"402 RA_DESCEND DESCEND_IMMEDIATELY (FOUND {ids[i]})";
                else:
                    status1 = "500 DISCONNECT CRASHED";
                    status2 = "500 DISCONNECT CRASHED";

                response1 = f"TCASP/1.0 {plane1['seq']} [{ids[i]}] {status1}";
                response2 = f"TCASP/1.0 {plane2['seq']} [{ids[j]}] {status2}";

                if "CLEAR" in status1:
                    if flightID == ids[i]:
                        socketServer.sendto(response1.encode("utf-8"), plane1["addr"]);
                        print(f"[SEND] {ids[i]:<8} {status1}");
                    elif flightID == ids[j]:
                        socketServer.sendto(response2.encode("utf-8"), plane2["addr"]);
                        print(f"[SEND] {ids[j]:<8} {status2}");
                else:
                    socketServer.sendto(response1.encode("utf-8"), plane1["addr"]);
                    socketServer.sendto(response2.encode("utf-8"), plane2["addr"]);
                    print(f"[SEND] {ids[i]:<8} {status1}");
                    print(f"[SEND] {ids[j]:<8} {status2}");

                if total_distance <= CRASH_DIST and vertical_gap < 1000:
                    print(f"[INFO] {ids[i]} and {ids[j]} crashed, removed from radar");
                    crashed.add(ids[i]);
                    crashed.add(ids[j]);
                    break;
        for fid in crashed:
            del aircrafts[fid];