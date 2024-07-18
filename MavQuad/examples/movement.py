from MavQuad.mavquad import DroneAPM, COLORED_RESULT
import time

if __name__ == "__main__":

    apm = DroneAPM("udpin:localhost:14551")

    print(f'Waiting heartbeat...')

    while True:
        if apm.connected:
            print("Drone connected!")
            break

    result = apm.setModeGuided()
    print(f'Result of setModeGuided command: {COLORED_RESULT(result)}')
    apm.sendGpOrigin()

    time.sleep(1)

    result = apm.arm()
    print(f'Result of arm command: {COLORED_RESULT(result)}')

    time.sleep(1)

    result = apm.takeoff(10)
    print(f'Result of takeoff command: {COLORED_RESULT(result)}')

    time.sleep(20)

    result = apm.setPosBody(10, 10, 0)
    print(f'Result of setPosBody command: {COLORED_RESULT(result)}')

    time.sleep(20)

    result = apm.land(20)
    print(f'Result of land command: {COLORED_RESULT(result)}')
    

