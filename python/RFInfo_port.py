from MSDD_base import *
#import Queue, threading

    
class PortFRONTENDRFInfoIn_implemented(PortFRONTENDRFInfoIn_i): 
    def _get_rf_flow_id(self):
        return str(self.parent.device_rf_flow)

    def _set_rf_flow_id(self, data):
        self.parent.update_rf_flow_id(data)
        return

    def _get_rfinfo_pkt(self):
        return self.parent.device_rf_info_pkt

    def _set_rfinfo_pkt(self, data):
        self.parent.device_rf_info_pkt = data
        self.parent.update_rf_flow_id(data.rf_flow_id)
