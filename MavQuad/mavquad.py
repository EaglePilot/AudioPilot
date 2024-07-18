from pymavlink import mavutil
from enum import Enum, auto
from datetime import datetime, timedelta
import sys
import time

COLORED_RESULT = (
    lambda result: "\033[92mSuccess\033[0m" if result else "\033[91mFailed\033[0m"
)


class APMTakeoffState(Enum):
    kLand = auto()
    kArmed = auto()
    kTakeoff1 = auto()
    kTakeoff2 = auto()


class BaseDrone:
    def __init__(self, device, baud: int = 115200) -> None:
        self._last_request = datetime.now()
        self._connected = False
        self.mav_connection = mavutil.mavlink_connection(device=device, baud=baud)

    @property
    def connected(self):
        if self.mav_connection.wait_heartbeat(blocking=False) is not None:
            self._connected = True
        return self._connected

    def arm(self):
        pass

    def takeoff(self, altitude):
        pass

    def land(self):
        pass

    def isTimeElapsed(self, delay) -> bool:
        return datetime.now() - self._last_request > timedelta(seconds=delay)

    def updateLastRequestTime(self) -> None:
        self._last_request = datetime.now()


class DroneAPM(BaseDrone):
    def __init__(self, device, baud=115200) -> None:
        BaseDrone.__init__(self, device, baud)

    def takeoff(self, takeoff_altitude: float):
        self.wait_until_position_aiding()

        # mode_id = self.mav_connection.mode_mapping()["GUIDED"]
        takeoff_params = [0, 0, 0, 0, 0, 0, takeoff_altitude]

        # # Change mode to guided (Ardupilot) or takeoff (PX4)
        # self.mav_connection.mav.command_long_send(self.mav_connection.target_system, self.mav_connection.target_component, mavutil.mavlink.MAV_CMD_DO_SET_MODE,
        #                             0, mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, mode_id, 0, 0, 0, 0, 0)
        # ack_msg = self.mav_connection.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
        # print(f"Change Mode ACK:  {ack_msg}")

        # # Arm the UAS
        # self.mav_connection.mav.command_long_send(self.mav_connection.target_system, self.mav_connection.target_component,
        #                                     mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 1, 0, 0, 0, 0, 0, 0)

        # arm_msg = self.mav_connection.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
        # print(f"Arm ACK:  {arm_msg}")

        # Command Takeoff
        self.mav_connection.mav.command_long_send(
            self.mav_connection.target_system,
            self.mav_connection.target_component,
            mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
            0,
            takeoff_params[0],
            takeoff_params[1],
            takeoff_params[2],
            takeoff_params[3],
            takeoff_params[4],
            takeoff_params[5],
            takeoff_params[6],
        )

        takeoff_msg = self.mav_connection.recv_match(
            type="COMMAND_ACK", blocking=True, timeout=3
        )
        # print(f"Takeoff ACK:  {takeoff_msg}")
        return takeoff_msg.result == 0

    def arm(self):
        self.mav_connection.mav.command_long_send(
            self.mav_connection.target_system,
            self.mav_connection.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0,
            1,
            0,
            0,
            0,
            0,
            0,
            0,
        )

        msg = self.mav_connection.recv_match(type="COMMAND_ACK", blocking=True)
        if not msg:
            return False
        if msg.get_type() == "BAD_DATA":
            if mavutil.all_printable(msg.data):
                sys.stdout.write(msg.data)
                sys.stdout.flush()
            return False
        else:
            # Message is valid
            # Use the attribute
            return msg.result == 0  # MAV_RESULT_ACCEPTED

    def land(self, timeout=10):
        """
        Sends a command for the drone to land.

        Args:
            the_connection (mavutil.mavlink_connection): The MAVLink connection to use.
            timeout (int): Time in seconds to wait for an acknowledgment.

        Returns:
            int: mavutil.mavlink.MAV_RESULT enum value.
        """

        # Send a command to land
        self.mav_connection.mav.command_long_send(
            self.mav_connection.target_system,
            self.mav_connection.target_component,
            mavutil.mavlink.MAV_CMD_NAV_LAND,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        )

        # Wait for the acknowledgment
        ack = self.mav_connection.recv_match(
            type="COMMAND_ACK", blocking=True, timeout=timeout
        )
        if ack is None:
            print("No acknowledgment received within the timeout period.")
            return False

        return ack.result == 0

    def sendGpOrigin(
        self, latitude=32.108693377508494, longitude=118.92943049870283, altitude=0
    ):
        self.mav_connection.mav.set_gps_global_origin_send(
            self.mav_connection.target_system,
            int(latitude * 1e7),
            int(longitude * 1e7),
            int(altitude * 1000),
        )
        # ack_msg = self.mav_connection.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
        # # print(ack_msg)
        # return ack_msg.result == 0 # MAV_RESULT_ACCEPTED

    def setMoveSpeed(self, speed):
        pass

    def setSpeedBody(self, x, y, z, yaw_rate=0):
        pass

    def setAngularRate(self, yaw_rate=0):
        pass

    def setPosBody(self, PX: float, PY: float, PZ: float, yaw: float = 0):
        type_mask = int(
            TypeMask.IGNORE_VX.value
            | TypeMask.IGNORE_VY.value
            | TypeMask.IGNORE_VZ.value
            | TypeMask.IGNORE_AFX.value
            | TypeMask.IGNORE_AFY.value
            | TypeMask.IGNORE_AFZ.value
            | TypeMask.IGNORE_YAW_RATE.value
        )
        self.mav_connection.mav.send(
            mavutil.mavlink.MAVLink_set_position_target_local_ned_message(
                10,
                self.mav_connection.target_system,
                self.mav_connection.target_component,
                mavutil.mavlink.MAV_FRAME_BODY_OFFSET_NED,
                type_mask,
                PX,
                PY,
                PZ,
                0,
                0,
                0,
                0,
                0,
                0,
                yaw,
                0,
            )
        )
        ack_msg = self.mav_connection.recv_match(
            type="LOCAL_POSITION_NED", blocking=True, timeout=3
        )
        # print(ack_msg)
        return ack_msg is not None

    def setPoseWorld(self, x, y, z, yaw):
        pass

    def setBreak(self):
        pass

    def setModeGuided(self):
        return self.change_mode("GUIDED")

    def change_mode(self, mode="GUIDED"):
        # Check if mode is available
        if mode not in self.mav_connection.mode_mapping():
            print(f"Unknown mode : {mode}")
            print(f"available modes: {list(self.mav_connection.mode_mapping().keys())}")
            raise Exception("Unknown mode")

        # Get mode ID
        mode_id = self.mav_connection.mode_mapping()[mode]
        sub_mode = 0

        self.mav_connection.mav.command_long_send(
            self.mav_connection.target_system,
            self.mav_connection.target_component,
            mavutil.mavlink.MAV_CMD_DO_SET_MODE,
            0,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            mode_id,
            sub_mode,
            0,
            0,
            0,
            0,
        )
        ack_msg = self.mav_connection.recv_match(
            type="COMMAND_ACK", blocking=True, timeout=3
        )
        # print(ack_msg)
        return ack_msg.result == 0  # MAV_RESULT_ACCEPTED

    def wait_until_position_aiding(self, timeout=120):
        """
        Wait until the MAVLink connection has EKF position aiding.

        Args:
            mav_connection (mavutil.mavlink_connection): The MAVLink connection to check.
            timeout (int, optional): The maximum time to wait for EKF position aiding in seconds. Defaults to 120.

        Raises:
            TimeoutError: If EKF position aiding is not achieved within the specified timeout.

        Returns:
            None
        """
        estimator_status_msg = "EKF_STATUS_REPORT"

        flags = ["EKF_PRED_POS_HORIZ_REL", "EKF_PRED_POS_HORIZ_REL"]
        time_start = time.time()
        while True:
            if (
                self.ekf_pos_aiding(flags, estimator_status_msg)
                or time.time() - time_start > timeout
            ):
                break
            print(
                f"Waiting for position aiding: {time.time() - time_start} seconds elapsed"
            )

        if time.time() - time_start > timeout:
            raise TimeoutError(
                f"Position aiding did not become available within {timeout} seconds"
            )

    def ekf_pos_aiding(self, flags, estimator_status_msg="EKF_STATUS_REPORT"):
        """
        Check the EKF position aiding status of a MAVLink connection.

        Args:
            mav_connection (mavutil.mavlink_connection): The MAVLink connection to check.
            flags (List[str]): The flags to check in the EKF status.
            estimator_status_msg (str, optional): The name of the estimator status message. Defaults to "ESTIMATOR_STATUS".

        Returns:
            bool: True if all flags are present in the EKF status, False otherwise.
        """
        msg = self.mav_connection.recv_match(
            type=estimator_status_msg, blocking=True, timeout=5
        )
        if not msg:
            raise ValueError(
                f"No message of type {estimator_status_msg} received within the timeout"
            )

        # print(f"from sysid {msg.get_srcSystem()} {msg}")
        ekf_flags = msg.flags

        for flag in flags:
            flag_val = get_enum_value_by_name(
                mavutil.mavlink.enums["EKF_STATUS_FLAGS"], flag
            )
            if not ekf_flags & flag_val:
                return False

        return True


def get_enum_value_by_name(enum_dict, name):
    """
    Get the value of an enum entry by its name.

    Args:
        enum_dict (Dict[str, int]): The enum dictionary to search.
        name (str): The name of the enum entry.

    Returns:
        int: The value of the enum entry.

    Raises:
        ValueError: If no enum entry with the given name is found.
    """
    for key, enum_entry in enum_dict.items():
        if enum_entry.name == name:
            return key
    raise ValueError("No enum entry with name: " + name)


class TypeMask(Enum):
    IGNORE_PX: int = 1
    IGNORE_PY: int = 2
    IGNORE_PZ: int = 4
    IGNORE_VX: int = 8
    IGNORE_VY: int = 16
    IGNORE_VZ: int = 32
    IGNORE_AFX: int = 64
    IGNORE_AFY: int = 128
    IGNORE_AFZ: int = 256
    FORCE: int = 512
    IGNORE_YAW: int = 1024
    IGNORE_YAW_RATE: int = 2048
