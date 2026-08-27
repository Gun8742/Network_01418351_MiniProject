import socket;
import time;
import threading;
import argparse;

# Setup argument parser
parser = argparse.ArgumentParser(description="TCASP Client");
parser.add_argument("--flight", type=str, required=True, help="Flight ID (e.g. TG611)");
parser.add_argument("--x", type=float, required=True, help="Initial X position");
parser.add_argument("--y", type=float, required=True, help="Initial Y position");
parser.add_argument("--z", type=float, required=True, help="Initial Z position");
parser.add_argument("--dx", type=float, required=True, help="X position change per step");
parser.add_argument("--crash", action="store_true", help="Enable crash mode (ignore RA commands)");

args = parser.parse_args();

HOST = "127.0.0.1";
PORT = 8080;

socketClient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM);
socketClient.settimeout(0.5);

seq = 1;
flightID = args.flight;
posX = args.x;
posY = args.y;
posZ = args.z;
dx = args.dx;
is_crash = args.crash;

message = f"TCASP/1.0 PING {seq} {flightID} {posX} {posY} {posZ}";
running = True;
worst = "";
lock = threading.Lock();

print(f"""
 __________________________________________________
|                                                  |
|  ✈️  Flight: {flightID:<32}    |
|  [+] System: TCASP Module Active                 |
|  [+] Status: Welcome aboard, Captain.            |
|__________________________________________________|
""");

print("""
░░░░░░░░░░░░░░░░██████░░░░ 
░███░░░░░░░░░░██▒▒▒▒▒▒███░ 
█▒▒▒█░░░░░░░██▒▒▒▒▒▒▒▒▒▒▒█ 
░█▒▒▒█░░░░██▒▒▒▒▒▒▒▒▒▒▒▒▒█ 
░░█▒▒▒█░░██▒▒██▒▒▒▒██▒▒▒▒▒ 
░░░█▒▒▒█░█▒▒▒████▒▒████▒▒▒ 
░█████████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ 
█▒▒▒▒▒▒▒▒▒█▒▒▒▒█▒▒▒▒▒▒▒▒▒▒ 
░█▒▒▒█████▒▒█▒▒▒▒▒▒▒▒▒██▒▒ 
█▒▒▒▒▒▒▒▒▒█▒███████████▒▒▒ 
░█▒▒▒█████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ 
░░█▒▒▒▒▒▒▒██▒▒▒▒▒▒▒▒▒▒▒▒██ 
░░░███████░░█▒▒▒▒▒▒▒▒▒███░
""")

def receive_loop():
        global running, worst;
        while running:
            try:
                data, _ = socketClient.recvfrom(1024);
                response = data.decode("utf-8");
                print(f"[RECV] {response}");
                with lock:
                    if "DISCONNECT" in response:
                        worst = "DISCONNECT";
                        running = False;
                    elif "RA_CLIMB" in response:
                        worst = "RA_CLIMB";
                    elif "RA_DESCEND" in response:
                        worst = "RA_DESCEND";
            except socket.timeout:
                continue;
            
def send_loop():
    global seq, message, worst, posX, posY, posZ;
    while running:
        # Send current position
        socketClient.sendto(message.encode("utf-8"), (HOST, PORT));
        time.sleep(2);
        with lock:
            current = worst;
            worst = "";

        if "DISCONNECT" in current:
            break;
            
        if not is_crash:
            # Normal RA handling
            if "RA_CLIMB" in current:
                posY += 1000;
            elif "RA_DESCEND" in current:
                posY -= 1000;
        
        # Update position for next step
        posX += dx;
        seq += 1;
        message = f"TCASP/1.0 PING {seq} {flightID} {posX} {posY} {posZ}";

t = threading.Thread(target=receive_loop);
t.daemon = True;
t.start();
send_loop();

socketClient.close();
