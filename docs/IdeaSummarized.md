# Idea Summarized TCAS Protocol

1. ***Protocol Name***: TCASP (Traffic Control Avoidance System Protocol)

2. ***Transport Layer***: UDP
- TCASP requires real-time and high-speed data transmission rather than connection reliability.
- **Low latency**: Positioning data must arrive as fast as possible. TCP handshake and retransmissions would cause unacceptable delays.
- **Tolerance to packet loss**: If a position packet is lost, it is better to send a new, updated coordinate rather than waiting for the old packet to retransmit.

3. ***Coordinate System***: 3D position, the ground plane is ```posX``` / ```posZ``` and ```posY``` is the altitude
- ```posX``` : horizontal axis (unit: nautical mile)
- ```posY``` : vertical axis, replaces the old altitude field (unit: foot)
- ```posZ``` : horizontal axis (unit: nautical mile)

4. ***Request Format*** (Client -> Server): ```TCASP/<version> PING <seq_no> <flight_ID> <posX_nm> <posY_ft> <posZ_nm>```
- ***EX.*** ```TCASP/1.0 PING 1 TG611 -4.0 32000.0 0.0```
- Added **Version** to allow future protocol upgrades.
- Added **Sequence Number** to handle UDP packet out-of-order or loss detection.

5. ***Respond Format*** (Server -> Client) : ```TCASP/<version> <seq_no> [<flight_ID>] <Status_Code> <Status_Phrase> <Message>```
- ***EX.***
    - ```TCASP/1.0 1 [TG611] 200 CLEAR MAINTAIN_HEADING```
    - ```TCASP/1.0 2 [TG611] 300 TA_TRAFFIC MONITOR_CLOSELY (FOUND FD3020)```
    - ```TCASP/1.0 0 400 BAD_REQUEST INVALID_FORMAT```
    - ```TCASP/1.0 3 [TG611] 401 RA_CLIMB CLIMB_IMMEDIATELY (FOUND FD3020)```
    - ```TCASP/1.0 4 [TG611] 402 RA_DESCEND DESCEND_IMMEDIATELY (FOUND FD3020)```
    - ```TCASP/1.0 5 [TG611] 500 DISCONNECT CRASHED```

6. ***Separation Rule***: Two aircraft are only in conflict when they are close on BOTH axes
- horizontal distance = ```sqrt((posX1 - posX2)^2 + (posZ1 - posZ2)^2)```
- vertical gap = ```abs(posY1 - posY2)```
- vertical gap >= 1000 ft -> ```200 CLEAR``` no matter how close the horizontal distance is
- distance > 5.0 nm -> ```200 CLEAR```
- distance > 2.0 nm -> ```300 TA_TRAFFIC```
- distance > 0.0 nm -> ```401 RA_CLIMB``` and ```402 RA_DESCEND```
- distance = 0.0 nm and vertical gap < 1000 ft -> ```500 DISCONNECT```

7. ***Client Behaviour (Threading Implementation)***:
- Client application is built with **Multi-threading** to operate in real-time.
- **Receive Thread**: Constantly listens for Server responses without blocking, tracking the "Worst-case scenario" (e.g., prioritizing RA over CLEAR).
- **Send Thread**: Sends PING requests every 2 seconds, and then obeys the RA by changing its own ```posY``` based on the worst status received.
- ```401 RA_CLIMB``` -> ```posY += 1000```
- ```402 RA_DESCEND``` -> ```posY -= 1000```
- ```500 DISCONNECT``` -> stop the loop and close the socket

8. ***Server Outstanding Features***:
- **Multi-Aircraft Support (N Connections)**: The server does pairwise calculations for ALL connected aircraft, completely scalable for heavy traffic.
- **Safety-Aware Notification**: For TA/RA/CRASH alerts, the server immediately pushes notifications to BOTH involved aircraft to ensure symmetric observation, but for CLEAR status, it only responds to the sender to save bandwidth.
- **Error Handling**: Graceful degradation against malformed UDP packets (e.g. invalid string instead of floats) returns a `400 BAD_REQUEST` without crashing the main server loop.
