import socket
import time

HOST = "127.0.0.1"
PORT = 8080

socketClient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
socketClient.settimeout(0.5)

message = "PING CC201 3.0 32000.0 0.0"

while True:
    arr = message.split()

    flightID = arr[1]
    posX = float(arr[2])
    posY = float(arr[3])
    posZ = float(arr[4])

    socketClient.sendto(message.encode("utf-8"), (HOST, PORT))

    response = ""
    while True:
        try:
            data, addr = socketClient.recvfrom(1024)
            response = data.decode("utf-8")
            if "DISCONNECT" in response:
                break
        except socket.timeout:
            break

    print(f"X={posX:>6.1f}  Y={posY:>6.0f} ft  Z={posZ:>6.1f}  ->  {response}")

    if "DISCONNECT" in response:
        break

    # no RA handling on purpose: flies straight into the other aircraft
    message = "PING" + " " + flightID + " " + str(posX - 1) + " " + str(posY) + " " + str(posZ)
    time.sleep(2)

socketClient.close()
