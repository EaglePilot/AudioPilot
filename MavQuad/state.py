# For system_status values
# see https://mavlink.io/en/messages/common.html#MAV_STATE

class State:
    def __init__(self, header, connected=False, armed=False, guided=False, manual_input=False, mode="", system_status=0):
        self.header = header
        self.connected = connected
        self.armed = armed
        self.guided = guided
        self.manual_input = manual_input
        self.mode = mode
        self.system_status = system_status

    def __str__(self):
        return f"Header: {self.header}, Connected: {self.connected}, Armed: {self.armed}, Guided: {self.guided}, " \
               f"Manual Input: {self.manual_input}, Mode: {self.mode}, System Status: {self.system_status}"

