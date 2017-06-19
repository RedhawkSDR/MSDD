from MSDD_base import *
import Queue, threading
import inspect 
from omniORB import CORBA, any
#import redhawk.frontendInterfaces.Frontend_idl
from redhawk.frontendInterfaces.Frontend_idl import *
from redhawk.frontendInterfaces.FRONTEND import FrontendException
from ossie.properties import props_from_dict, props_to_dict
#NB - This port needs to do reasonableness checking on all inputs
#     the underlying self.parent.configureTuner() call does not perform adequate checking for invalid inputs

class PortFRONTENDDigitalTunerIn_implemented(PortFRONTENDDigitalTunerIn_i):
    def __init__(self, parent, name):
        self.parent = parent
        self.name = name
        self.sri = None
        self.queue = Queue.Queue()
        self.port_lock = threading.Lock()
      
   
    def getTunerType(self, id):
        tuner_num = self.parent.findTunerByAllocationID(alloc_id=id, include_control=True, include_listeners=True)
        if tuner_num == None:
            error_string = "Can not determine tuner for allocation id "+ str(id) + " when running function " + str(inspect.stack()[0][3]) + ". Either invalid id or permissions"
            raise FrontendException(error_string)
        return self.parent.frontend_tuner_status[tuner_num].tuner_type

    def getTunerDeviceControl(self, id):
        tuner_num_control = self.parent.findTunerByAllocationID(alloc_id=id, include_control=True, include_listeners=False)
        tuner_num_listener = self.parent.findTunerByAllocationID(alloc_id=id, include_control=False, include_listeners=True)
        if tuner_num_control == None and tuner_num_listener == None:
            error_string = "Can not determine tuner for allocation id "+ str(id) + " when running function " + str(inspect.stack()[0][3]) + ". Either invalid id or permissions"
            raise FrontendException(error_string)
        return (tuner_num_control != None)

    def getTunerGroupId(self, id):
        tuner_num = self.parent.findTunerByAllocationID(alloc_id=id, include_control=True, include_listeners=True)
        if tuner_num == None:
            error_string = "Can not determine tuner for allocation id "+ str(id) + " when running function " + str(inspect.stack()[0][3]) + ". Either invalid id or permissions"
            raise FrontendException(error_string)
        return self.parent.frontend_tuner_status[tuner_num].group_id
   

    def getTunerRfFlowId(self, id):
        tuner_num = self.parent.findTunerByAllocationID(alloc_id=id, include_control=True, include_listeners=True)
        if tuner_num == None:
            error_string = "Can not determine tuner for allocation id "+ str(id) + " when running function " + str(inspect.stack()[0][3]) + ". Either invalid id or permissions"
            raise FrontendException(error_string)
        return self.parent.frontend_tuner_status[tuner_num].rf_flow_id

    def getTunerStatus(self, id):
        status = []
        tuner_num = self.parent.findTunerByAllocationID(alloc_id=id, include_control=True, include_listeners=True)
        if tuner_num == None:
            error_string = "Can not determine tuner for allocation id "+ str(id) + " when running function " + str(inspect.stack()[0][3]) + ". Either invalid id or permissions"
            raise FrontendException(error_string)
        prop = self.parent._props.query("FRONTEND::tuner_status")
        for p in prop.value():
            for pp in p.value():
                if str(pp.id) == "FRONTEND::tuner_status::tuner_number" and int(any.from_any(pp.value)) == tuner_num:
                    status = p.value()
                    break
        return status
        

    def setTunerCenterFrequency(self, id, freq):
        tuner_num = self.parent.findTunerByAllocationID(alloc_id=id, include_control=True, include_listeners=False)
        if tuner_num == None:
            error_string = "Can not determine tuner for allocation id "+ str(id) + " when running function " + str(inspect.stack()[0][3]) + ". Either invalid id or permissions"
            raise FrontendException(error_string)
    
        valid_cf = None
        changed_child_numbers = []
        try:
            if self.parent.frontend_tuner_status[tuner_num].rx_object.is_digital_only():
                org_cf_offset = self.parent.frontend_tuner_status[tuner_num].rx_object.digital_rx_object.object.rf_offset_hz
                parent_tnr = self.parent.MSDD.get_parent_tuner_num(self.parent.frontend_tuner_status[tuner_num].rx_object)
                if parent_tnr is not None:
                    #if the parent DDC is no longer tuned in a valid range then retune it
                    if not self.parent.frontend_tuner_status[parent_tnr].enabled or \
                        len(self.parent.MSDD.get_child_tuner_num_list(self.parent.frontend_tuner_status[tuner_num].rx_object)) <2: 
                        self.setTunerCenterFrequency(self.parent.frontend_tuner_status[parent_tnr].allocation_id_control, freq)
                    parent_cf = self.parent.frontend_tuner_status[parent_tnr].center_frequency
                    self.parent.frontend_tuner_status[tuner_num].rx_object.digital_rx_object.object.updateRfFrequencyOffset(parent_cf)
                    valid_cf = self.parent.frontend_tuner_status[tuner_num].rx_object.digital_rx_object.object.get_valid_frequency(freq)
                    if valid_cf is not None:
                        self.parent.frontend_tuner_status[tuner_num].rx_object.digital_rx_object.object.setFrequency_Hz(valid_cf)
                        self.parent.frontend_tuner_status[tuner_num].rx_object.digital_rx_object.object.enable = True
                    else:
                        self.parent.frontend_tuner_status[tuner_num].rx_object.digital_rx_object.object.updateRfFrequencyOffset(org_cf_offset)
            if self.parent.frontend_tuner_status[tuner_num].rx_object.is_analog():
                valid_cf = self.parent.frontend_tuner_status[tuner_num].rx_object.analog_rx_object.object.get_valid_frequency(freq)
                self.parent.frontend_tuner_status[tuner_num].rx_object.analog_rx_object.object.setFrequency_Hz(valid_cf)
            if self.parent.frontend_tuner_status[tuner_num].rx_object.is_spectral_scan():
                startFreq = freq - self.parent.frontend_tuner_status[tuner_num].bandwidth / 2.0
                stopFreq = freq + self.parent.frontend_tuner_status[tuner_num].bandwidth / 2.0
                spcconfig = props_to_dict(self.parent.query(props_from_dict({"msdd_spc_configuration": {}})))
                spcconfig["msdd_spc_configuration"]["msdd_spc_configuration::start_frequency"] = startFreq
                spcconfig["msdd_spc_configuration"]["msdd_spc_configuration::stop_frequency"] = stopFreq
                self.parent.configure(props_from_dict(spcconfig))
                valid_cf = True
            if valid_cf == None:
                raise Exception("")
            try:
                
                for child_num in self.parent.MSDD.get_child_tuner_num_list(self.parent.frontend_tuner_status[tuner_num].rx_object):
                    child = self.parent.frontend_tuner_status[child_num]
                    if child.rx_object.digital_rx_object != None and self.parent.frontend_tuner_status[child_num].allocated:
                        org_cf_offset = child.rx_object.digital_rx_object.object.rf_offset_hz
                        child.rx_object.digital_rx_object.object.updateRfFrequencyOffset(valid_cf)
                        self.parent._log.debug("Updating offset with: %s"%valid_cf)
                        try:
                            current_cf = child.rx_object.digital_rx_object.object.get_valid_frequency(child.center_frequency)
                            self.parent._log.debug("Current valid CF %s"%current_cf)
                            child.rx_object.digital_rx_object.object.setFrequency_Hz(current_cf)
                            if child.allocated:
                                child.rx_object.digital_rx_object.object.enable = True
                        except:
                            child.rx_object.digital_rx_object.object.enable = False
                            child.rx_object.digital_rx_object.object.updateRfFrequencyOffset(org_cf_offset)
                        changed_child_numbers.append(child_num)
            except Exception, e:
                self.parent._log.warn("PROBLEM: %s"%e)
        except:
            error_string = "Error setting center frequency to " + str(freq) + " for tuner " + str(tuner_num)
            raise FrontendException(error_string)
        finally:
            self.parent.update_tuner_status([tuner_num]+changed_child_numbers)
        

    def getTunerCenterFrequency(self, id):
        tuner_num = self.parent.findTunerByAllocationID(alloc_id=id, include_control=True, include_listeners=True)
        if tuner_num == None:
            error_string = "Can not determine tuner for allocation id "+ str(id) + " when running function " + str(inspect.stack()[0][3]) + ". Either invalid id or permissions"
            raise FrontendException(error_string)
        return self.parent.frontend_tuner_status[tuner_num].center_frequency


    def setTunerBandwidth(self, id, bw):
        #self.parent._log.info("Setting BW to: "+str(bw))
        tuner_num = self.parent.findTunerByAllocationID(alloc_id=id, include_control=True, include_listeners=False)
        if tuner_num == None:
            error_string = "Can not determine tuner for allocation id "+ str(id) + " when running function " + str(inspect.stack()[0][3]) + ". Either invalid id or permissions"
            self.parent._log.error(error_string)
            raise FrontendException(error_string)

        valid_bw = None
        try:
            if self.parent.frontend_tuner_status[tuner_num].rx_object.is_digital():
                try:
                    valid_bw = self.parent.frontend_tuner_status[tuner_num].rx_object.digital_rx_object.object.get_valid_bandwidth(bw,100)
                    self.parent.frontend_tuner_status[tuner_num].rx_object.digital_rx_object.object.setBandwidth_Hz(valid_bw)
                except NotImplementedError:
                    None
                valid_bw = 0
        
            if self.parent.frontend_tuner_status[tuner_num].rx_object.is_analog():
                valid_bw = self.parent.frontend_tuner_status[tuner_num].rx_object.analog_rx_object.object.get_valid_bandwidth(bw,100)
                self.parent.frontend_tuner_status[tuner_num].rx_object.analog_rx_object.object.setBandwidth_Hz(valid_bw)
            if self.parent.frontend_tuner_status[tuner_num].rx_object.is_spectral_scan():
                startFreq = self.parent.frontend_tuner_status[tuner_num].center_frequency - bw /2.0
                stopFreq = self.parent.frontend_tuner_status[tuner_num].center_frequency + bw /2.0
                spcconfig = props_to_dict(self.parent.query(props_from_dict({"msdd_spc_configuration": {}})))
                spcconfig["msdd_spc_configuration"]["msdd_spc_configuration::start_frequency"] = startFreq
                spcconfig["msdd_spc_configuration"]["msdd_spc_configuration::stop_frequency"] = stopFreq
                self.parent.configure(props_from_dict(spcconfig))
                valid_bw = True
            if valid_bw == None:
                raise Exception("")
        except Exception, e:
            self.parent._log.warning(str(e))
            error_string = "Error setting bandwidth to " + str(bw) + " for tuner " + str(tuner_num)
            self.parent._log.warning(error_string)
            raise FrontendException(error_string)
        self.parent.update_tuner_status([tuner_num])

    def getTunerBandwidth(self, id):
        tuner_num = self.parent.findTunerByAllocationID(alloc_id=id, include_control=True, include_listeners=True)
        if tuner_num == None:
            error_string = "Can not determine tuner for allocation id "+ str(id) + " when running function " + str(inspect.stack()[0][3]) + ". Either invalid id or permissions"
            raise FrontendException(error_string)
        return self.parent.frontend_tuner_status[tuner_num].bandwidth

    def setTunerAgcEnable(self, id, enable):
        raise NotSupportedException("AGC is NOT supported in the MSDD device")

    def getTunerAgcEnable(self, id):
        return False

    def setTunerGain(self, id, gain):
        tuner_num = self.parent.findTunerByAllocationID(alloc_id=id, include_control=True, include_listeners=False)
        if tuner_num == None:
            error_string = "Can not determine tuner for allocation id "+ str(id) + " when running function " + str(inspect.stack()[0][3]) + ". Either invalid id or permissions"
            raise FrontendException(error_string)
    
        valid_gain = None
        try:
        
            if self.parent.frontend_tuner_status[tuner_num].rx_object.is_analog():
                valid_gain = self.parent.frontend_tuner_status[tuner_num].rx_object.analog_rx_object.object.get_valid_gain(gain)
                self.parent.frontend_tuner_status[tuner_num].rx_object.analog_rx_object.object.setGain(valid_gain)
            elif self.parent.frontend_tuner_status[tuner_num].rx_object.is_digital():
                valid_gain = self.parent.frontend_tuner_status[tuner_num].rx_object.digital_rx_object.object.get_valid_gain(gain)
                self.parent.frontend_tuner_status[tuner_num].rx_object.digital_rx_object.object.setGain(valid_gain)
            if valid_gain == None:
                raise Exception("")
        except:
            error_string = "Error setting gain to " + str(gain) + " for tuner " + str(tuner_num)
            raise FrontendException(error_string)
        self.parent.update_tuner_status([tuner_num])

    def getTunerGain(self, id):
        tuner_num = self.parent.findTunerByAllocationID(alloc_id=id, include_control=True, include_listeners=True)
        if tuner_num == None:
            error_string = "Can not determine tuner for allocation id "+ str(id) + " when running function " + str(inspect.stack()[0][3]) + ". Either invalid id or permissions"
            raise FrontendException(error_string)
        return self.parent.frontend_tuner_status[tuner_num].gain


    def setTunerReferenceSource(self, id, source):
        tuner_num = self.parent.findTunerByAllocationID(alloc_id=id, include_control=True, include_listeners=True)
        if tuner_num == None:
            error_string = "Can not determine tuner for allocation id "+ str(id) + " when running function " + str(inspect.stack()[0][3]) + ". Either invalid id or permissions"
            raise FrontendException(error_string)
        raise NotSupportedException("Can not change 10MHz reference")

    def getTunerReferenceSource(self, id):
        tuner_num = self.parent.findTunerByAllocationID(alloc_id=id, include_control=True, include_listeners=True)
        if tuner_num == None:
            error_string = "Can not determine tuner for allocation id "+ str(id) + " when running function " + str(inspect.stack()[0][3]) + ". Either invalid id or permissions"
            raise FrontendException(error_string)
        return int(self.parent.clock_ref == 10)

    def setTunerEnable(self, id, enable):
        tuner_num = self.parent.findTunerByAllocationID(alloc_id=id, include_control=True, include_listeners=True)
        if tuner_num == None:
            error_string = "Can not determine tuner for allocation id "+ str(id) + " when running function " + str(inspect.stack()[0][3]) + ". Either invalid id or permissions"
            raise FrontendException(error_string)
        try:
            if self.frontend_tuner_status[tuner_num].rx_object.is_digital():
                self.frontend_tuner_status[tuner_num].rx_object.digital_rx_object.object.setEnable(enable)
        except:
            pass
        self.parent.update_tuner_status([tuner_num])

    def getTunerEnable(self, id):
        tuner_num = self.parent.findTunerByAllocationID(alloc_id=id, include_control=True, include_listeners=True)
        if tuner_num == None:
            error_string = "Can not determine tuner for allocation id "+ str(id) + " when running function " + str(inspect.stack()[0][3]) + ". Either invalid id or permissions"
            raise FrontendException(error_string)
        return self.parent.frontend_tuner_status[tuner_num].enabled


    def setTunerOutputSampleRate(self, id, sr):
        tuner_num = self.parent.findTunerByAllocationID(alloc_id=id, include_control=True, include_listeners=False)
        if tuner_num == None:
            error_string = "Can not determine tuner for allocation id "+ str(id) + " when running function " + str(inspect.stack()[0][3]) + ". Either invalid id or permissions"
            raise FrontendException(error_string)
    
        valid_sr = None
        try:
            if self.parent.frontend_tuner_status[tuner_num].rx_object.is_digital():
                valid_sr = self.parent.frontend_tuner_status[tuner_num].rx_object.digital_rx_object.object.get_valid_sample_rate(sr, self.parent.frontend_tuner_status[tuner_num].sample_rate_tolerance)
                self.parent.frontend_tuner_status[tuner_num].rx_object.digital_rx_object.object.setSampleRate(valid_sr)
            if self.parent.frontend_tuner_status[tuner_num].rx_object.is_spectral_scan():
                startFreq = self.parent.frontend_tuner_status[tuner_num].center_frequency - sr /2.0
                stopFreq = self.parent.frontend_tuner_status[tuner_num].center_frequency + sr /2.0
                spcconfig = props_to_dict(self.parent.query(props_from_dict({"msdd_spc_configuration": {}})))
                spcconfig["msdd_spc_configuration"]["msdd_spc_configuration::start_frequency"] = startFreq
                spcconfig["msdd_spc_configuration"]["msdd_spc_configuration::stop_frequency"] = stopFreq
                self.parent.configure(props_from_dict(spcconfig))
                valid_sr = True
            else:
                valid_sr = 0
            if valid_sr == None:
                raise Exception("")
        except Exception, e:
            error_string = "Error setting sr to " + str(sr) + " for tuner " + str(tuner_num)
            self.parent._log.error(error_string)
            self.parent._log.error(str(e))
            raise FrontendException(error_string)
        self.parent.update_tuner_status([tuner_num])

    def getTunerOutputSampleRate(self, id):
        tuner_num = self.parent.findTunerByAllocationID(alloc_id=id, include_control=True, include_listeners=True)
        if tuner_num == None:
            error_string = "Can not determine tuner for allocation id "+ str(id) + " when running function " + str(inspect.stack()[0][3]) + ". Either invalid id or permissions"
            raise FrontendException(error_string)
        return self.parent.frontend_tuner_status[tuner_num].sample_rate
