import socket
import math

HOST = "127.0.0.1"
PORT = 8080

print("Creating Server...")
socketServer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
socketServer.bind((HOST, PORT))

aircrafts = {}

while True:
    data, addr = socketServer.recvfrom(1024)
    message = data.decode("utf-8")
    parts = message.split()

    if len(parts) != 5 or parts[0] != "PING":
        response = "400 BAD_REQUEST INVALID_FORMAT"
        socketServer.sendto(response.encode("utf-8"), addr)
        continue

    flightID = parts[1]
    posX = float(parts[2])
    posY = float(parts[3])
    posZ = float(parts[4])
    aircrafts[flightID] = {
        "posX": posX,
        "posY": posY,
        "posZ": posZ,
        "addr": addr
    }

    print(f"\n[RECV] {flightID:<8} X={posX:>6.1f}  Y={posY:>6.0f} ft  Z={posZ:>6.1f}")

    if len(aircrafts) < 2:
        status = "200 CLEAR MAINTAIN_HEADING"
        response = f"[{flightID}] {status}"
        socketServer.sendto(response.encode("utf-8"), addr)
        print(f"[SEND] {flightID:<8} {status}")
    else:
        ids = list(aircrafts.keys())
        plane1 = aircrafts[ids[0]]
        plane2 = aircrafts[ids[1]]
        total_distance = math.sqrt((plane1["posX"] - plane2["posX"]) ** 2 + (plane1["posZ"] - plane2["posZ"]) ** 2)
        vertical_gap = abs(plane1["posY"] - plane2["posY"])

        print(f"[CALC] {ids[0]} <-> {ids[1]}   distance={total_distance:>5.2f} nm   gap={vertical_gap:>5.0f} ft")

        if total_distance > 5.0 or vertical_gap >= 1000:
            status1 = "200 CLEAR MAINTAIN_HEADING"
            status2 = "200 CLEAR MAINTAIN_HEADING"
        elif total_distance > 2.0:
            status1 = f"300 TA_TRAFFIC MONITOR_CLOSELY (FOUND {ids[1]})"
            status2 = f"300 TA_TRAFFIC MONITOR_CLOSELY (FOUND {ids[0]})"
        elif total_distance > 0.0:
            status1 = f"401 RA_CLIMB CLIMB_IMMEDIATELY (FOUND {ids[1]})"
            status2 = f"402 RA_DESCEND DESCEND_IMMEDIATELY (FOUND {ids[0]})"
        else:
            status1 = "500 DISCONNECT CRASHED"
            status2 = "500 DISCONNECT CRASHED"

        response1 = f"[{ids[0]}] {status1}"
        response2 = f"[{ids[1]}] {status2}"

        if total_distance <= 2.0 and vertical_gap < 1000:
            socketServer.sendto(response1.encode("utf-8"), plane1["addr"])
            socketServer.sendto(response2.encode("utf-8"), plane2["addr"])
            print(f"[SEND] {ids[0]:<8} {status1}")
            print(f"[SEND] {ids[1]:<8} {status2}")
        elif flightID == ids[0]:
            socketServer.sendto(response1.encode("utf-8"), addr)
            print(f"[SEND] {ids[0]:<8} {status1}")
        else:
            socketServer.sendto(response2.encode("utf-8"), addr)
            print(f"[SEND] {ids[1]:<8} {status2}")

        if total_distance == 0.0 and vertical_gap < 1000:
            print(f"[INFO] {ids[0]} and {ids[1]} crashed, removed from radar")
            del aircrafts[ids[0]]
            del aircrafts[ids[1]]
