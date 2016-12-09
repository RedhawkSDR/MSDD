#!/usr/bin/env python


import sys, os
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.abspath(os.path.join(script_dir, '..'))
lib_dir = os.path.join(script_dir, 'fei_base')
sys.path.append(lib_dir)
import frontend_tuner_unit_test_base as fe

''' TODO:
  1)  set the desired DEBUG_LEVEL (typical values include 0, 1, 2, 3, 4 and 5)
  2)  set DUT correctly to specify the USRP under test
  3)  set IMPL_ID to the implementation that should be tested.
  4)  Optional: set dut_execparams if it is necessary to specify a particular
      USRP. Default behavior is to target the first device of the type specified.
  5)  Optional: set dut_capabilities to reflect the hardware capabilities of
      the dut if different from what is provided below.
'''

DEBUG_LEVEL = 4
dut_name = 'MSDD'
IMPL_ID = 'python'
dut_execparams = {}
dut_configure = {
                 "msdd_configuration" : {
                     "msdd_configuration::msdd_ip_address":"192.168.103.250",
                     "msdd_configuration::msdd_port":"23"
                      }
                 ,
                "msdd_output_configuration": [{
                     "msdd_output_configuration::tuner_number":0,
                     "msdd_output_configuration::protocol":"UDP_SDDS",
                     "msdd_output_configuration::ip_address":"234.168.103.100",
                     "msdd_output_configuration::port":0,
                     "msdd_output_configuration::vlan":0,
                     "msdd_output_configuration::enabled":True,
                     "msdd_output_configuration::timestamp_offset":0,
                     "msdd_output_configuration::endianess":1,
                     "msdd_output_configuration::mfp_flush":63,
                     "msdd_output_configuration::vlan_enable": False                        
                    }]
                                    
                 }
dut_capabilities = {'RX_DIGITIZER':{'COMPLEX': True,
                                    'CF_MAX':   6000e6,
                                    'CF_MIN':   30e6,
                                    'BW_MAX':   20000000.0,
                                    'BW_MIN':   20000000.0,
                                    'SR_MAX':   25000000.0,
                                    'SR_MIN':   25000000.0,
                                    'GAIN_MIN' :-60,
                                    'GAIN_MAX' :0}}



DEVICE_INFO = {}
DEVICE_INFO[dut_name] = dut_capabilities
DEVICE_INFO[dut_name]['SPD'] = os.path.join(project_dir, 'MSDD.spd.xml')
DEVICE_INFO[dut_name]['execparams'] = dut_execparams
DEVICE_INFO[dut_name]['configure'] = dut_configure
#******* DO NOT MODIFY ABOVE **********#



class FrontendTunerTests(fe.FrontendTunerTests):
    
    def __init__(self,*args,**kwargs):
        import ossie.utils.testing
        super(FrontendTunerTests,self).__init__(*args,**kwargs)
        fe.set_debug_level(DEBUG_LEVEL)
        fe.set_device_info(DEVICE_INFO[dut_name])
        fe.set_impl_id(IMPL_ID)
    
    # Use functions below to add pre-/post-launch commands if your device has special startup requirements
    @classmethod
    def devicePreLaunch(self):
        pass
    @classmethod
    def devicePostLaunch(self):
        pass
    
    # Use functions below to add pre-/post-release commands if your device has special shutdown requirements
    @classmethod
    def devicePreRelease(self):
        pass
    @classmethod
    def devicePostRelease(self):
        pass
    
    
if __name__ == '__main__':
    fe.set_debug_level(DEBUG_LEVEL)
    fe.set_device_info(DEVICE_INFO[dut_name])
    fe.set_impl_id(IMPL_ID)
    
    # run using nose
    import nose
    nose.main(defaultTest=__name__)
