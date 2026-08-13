# Idea Summarized TCAS Protocol

1. ***Protocol Name***: TCASP (Traffic Control Avoidance System Protocol)

2. ***Transport Layer***: UDP (Because we need an information about coordinate and altitude which real time and highspeed rather than repeating)

3. ***Coordinate System***: 3D position, the ground plane is ```posX``` / ```posZ``` and ```posY``` is the altitude
- ```posX``` : horizontal axis (unit: nautical mile)
- ```posY``` : vertical axis, replaces the old altitude field (unit: foot)
- ```posZ``` : horizontal axis (unit: nautical mile)

4. ***Request Format*** (Client -> Server): ```PING <flight_ID> <posX_nm> <posY_ft> <posZ_nm>```
- ***EX.*** ```PING TG611 -4.0 32000.0 0.0```

5. ***Respond Format*** (Server -> Client) : ```[<flight_ID>] <Status_Code> <Status_Phrase> <Message>```
***EX.***
    - ```[TG611] 200 CLEAR MAINTAIN_HEADING```
    - ```[TG611] 300 TA_TRAFFIC MONITOR_CLOSELY (FOUND FD3020)```
    - ```400 BAD_REQUEST INVALID_FORMAT```
    - ```[TG611] 401 RA_CLIMB CLIMB_IMMEDIATELY (FOUND FD3020)```
    - ```[TG611] 402 RA_DESCEND DESCEND_IMMEDIATELY (FOUND FD3020)```
    - ```[TG611] 500 DISCONNECT CRASHED```

6. ***Separation Rule***: two aircraft are only in conflict when they are close on BOTH axes
- horizontal distance = ```sqrt((posX1 - posX2)^2 + (posZ1 - posZ2)^2)```
- vertical gap = ```abs(posY1 - posY2)```
- vertical gap >= 1000 ft -> ```200 CLEAR``` no matter how close the horizontal distance is
- distance > 5.0 nm -> ```200 CLEAR```
- distance > 2.0 nm -> ```300 TA_TRAFFIC```
- distance > 0.0 nm -> ```401 RA_CLIMB``` and ```402 RA_DESCEND```
- distance = 0.0 nm and vertical gap < 1000 ft -> ```500 DISCONNECT```

7. ***Client Behaviour***: the client obeys the RA by changing its own ```posY```
- ```401 RA_CLIMB``` -> ```posY += 1000```
- ```402 RA_DESCEND``` -> ```posY -= 1000```
- ```500 DISCONNECT``` -> stop the loop and close the socket
