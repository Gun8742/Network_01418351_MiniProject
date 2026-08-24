import socket
import time
import threading

HOST = "127.0.0.1"
PORT = 8080

socketClient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
socketClient.settimeout(0.5)

seq = 1
message = "TCASP/1.0 PING 1 CC202 -3.0 32000.0 0.0"
running = True;
worst = "";

def receive_loop():
        global running, worst
        while running:
            try:
                data, addr = socketClient.recvfrom(1024)
                response = data.decode("utf-8")
                print(f"[RECV] {response}")

                if "DISCONNECT" in response:
                    worst = "DISCONNECT"
                    running = False
                elif "RA_CLIMB" in response:
                    worst = "RA_CLIMB"
                elif "RA_DESCEND" in response:
                    worst = "RA_DESCEND"
            except socket.timeout:
                continue
            
def send_loop():
    global seq, message, worst
    while running:
        arr = message.split()

        flightID = arr[3]
        posX = float(arr[4])
        posY = float(arr[5])
        posZ = float(arr[6])

        socketClient.sendto(message.encode("utf-8"), (HOST, PORT))
        time.sleep(2);

        if "DISCONNECT" in worst:
            break;
        # no RA handling on purpose: flies straight into the other aircraft
        worst = "";
        seq += 1;
        message = "TCASP/1.0 PING" + " " + str(seq) + " " + flightID + " " + str(posX + 1) + " " + str(posY) + " " + str(posZ);

t = threading.Thread(target=receive_loop);
t.daemon = True;
t.start();
send_loop();

socketClient.close()
