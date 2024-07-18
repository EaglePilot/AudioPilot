from MavQuad.mavquad import DroneAPM, COLORED_RESULT
import time
import socket

if __name__ == "__main__":

    apm = DroneAPM("/dev/ttyUSB0")

    print(f'Waiting heartbeat...')

    while True:
        if apm.connected:
            print("Drone connected!")
            break

    result = apm.setModeGuided()
    print(f'Result of setModeGuided command: {COLORED_RESULT(result)}')
    apm.sendGpOrigin()

    time.sleep(1)
    
    is_takeoff = False
    
    # 创建socket对象
    socket_server = socket.socket()
    # 绑定ip和端口，表明是服务端
    socket_server.bind(("0.0.0.0", 12003))
    socket_server.listen(1)
    
    while True:
        
        print("Port Opened!")
        
        conn, address = socket_server.accept()
        data = conn.recv(2100).decode("UTF-8")
        
        print(f'received command: {data}')
        

        if data == "L" and is_takeoff:
            result = apm.setPosBody(1, -1, 0)
            print(f'Result of setPosBody command: {COLORED_RESULT(result)}')
            time.sleep(8)
            pass
            
        elif data == "R" and is_takeoff:
            result = apm.setPosBody(1, 1, 0)
            print(f'Result of setPosBody command: {COLORED_RESULT(result)}')
            time.sleep(8)
            pass
        
        elif data == "F" and is_takeoff:
            result = apm.setPosBody(1, 0, 0)
            print(f'Result of setPosBody command: {COLORED_RESULT(result)}')
            time.sleep(8)
            pass
        
        elif data == "B" and is_takeoff:
            result = apm.setPosBody(-1, 0, 0)
            print(f'Result of setPosBody command: {COLORED_RESULT(result)}')
            time.sleep(8)
            pass
        
        elif data == "U" and not is_takeoff: # takeoff
            result = apm.arm()
            print(f'Result of arm command: {COLORED_RESULT(result)}')
            time.sleep(1)
            result = apm.takeoff(1)
            print(f'Result of takeoff command: {COLORED_RESULT(result)}')
            time.sleep(8)
            is_takeoff = True
            pass
        
        elif data == "D" and is_takeoff: # land
            result = apm.land(20)
            print(f'Result of land command: {COLORED_RESULT(result)}')
            is_takeoff = False
            pass
        
        # elif data is "H":
            # pass
        
        else:
            # socket_server.close()
            pass
