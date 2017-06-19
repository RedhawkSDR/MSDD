#!/usr/bin/env python
import unittest
import ossie.utils.testing
import os, sys, time
from omniORB import any
from ossie.utils import sb
from omniORB import CORBA
from ossie.cf import CF 
from ossie import properties
from ossie import utils

import subprocess
import signal
import inspect 
import math

from ossie.cf import CF, CF__POA
from ossie.utils import uuid
from ossie.resource import usesport, providesport
from ossie.cf import ExtendedCF
from omniORB import CORBA
import pprint
import sys

IP_ADDRESS="127.0.0.1"
PORT="23"

class DeviceTests(ossie.utils.testing.ScaComponentTestCase):
    FE_TYPE_RECEIVER="RX"
    FE_TYPE_RXDIG="RX_DIGITIZER"
    FE_TYPE_RXDIGCHAN="RX_DIGITIZER_CHANNELIZER"
    FE_TYPE_DDC="DDC"
    
    def make_allocation_struct(self,tuner_type, allocation_id, center_frequency, bandwidth, sample_rate, bandwidth_tolerance=10.0, sample_rate_tolerance=10.0, rf_flow_id="", group_id="", device_control=True):
        return ossie.cf.CF.DataType(id='FRONTEND::tuner_allocation', value=CORBA.Any(CORBA.TypeCode("IDL:CF/Properties:1.0"), [
                ossie.cf.CF.DataType(id='FRONTEND::tuner_allocation::device_control', value=CORBA.Any(CORBA.TC_boolean, device_control)), 
                ossie.cf.CF.DataType(id='FRONTEND::tuner_allocation::bandwidth', value=CORBA.Any(CORBA.TC_double, bandwidth)), 
                ossie.cf.CF.DataType(id='FRONTEND::tuner_allocation::bandwidth_tolerance', value=CORBA.Any(CORBA.TC_double, bandwidth_tolerance)), 
                ossie.cf.CF.DataType(id='FRONTEND::tuner_allocation::sample_rate_tolerance', value=CORBA.Any(CORBA.TC_double, sample_rate_tolerance)), 
                ossie.cf.CF.DataType(id='FRONTEND::tuner_allocation::allocation_id', value=CORBA.Any(CORBA.TC_string, allocation_id)), 
                ossie.cf.CF.DataType(id='FRONTEND::tuner_allocation::tuner_type', value=CORBA.Any(CORBA.TC_string, tuner_type)), 
                ossie.cf.CF.DataType(id='FRONTEND::tuner_allocation::rf_flow_id', value=CORBA.Any(CORBA.TC_string,rf_flow_id)), 
                ossie.cf.CF.DataType(id='FRONTEND::tuner_allocation::sample_rate', value=CORBA.Any(CORBA.TC_double,sample_rate)), 
                ossie.cf.CF.DataType(id='FRONTEND::tuner_allocation::group_id', value=CORBA.Any(CORBA.TC_string, group_id)), 
                ossie.cf.CF.DataType(id='FRONTEND::tuner_allocation::center_frequency', value=CORBA.Any(CORBA.TC_double, center_frequency))]))
    
    def make_listener_allocation_struct(self,listener_allocation_id, existing_allocation_id):
        return ossie.cf.CF.DataType(id='FRONTEND::listener_allocation', value=CORBA.Any(CORBA.TypeCode("IDL:CF/Properties:1.0"), [
                ossie.cf.CF.DataType(id='FRONTEND::listener_allocation::listener_allocation_id', value=CORBA.Any(CORBA.TC_string, listener_allocation_id)), 
                ossie.cf.CF.DataType(id='FRONTEND::listener_allocation::existing_allocation_id', value=CORBA.Any(CORBA.TC_string, existing_allocation_id))]))
    def print_allocated_tuners(self,device):
        print "TUNER STATUS:"
        for tuner_num in range(0,len(device.frontend_tuner_status)):
            
            if (device.frontend_tuner_status[tuner_num].allocated) == False:
                continue
            print "Tuner: " + str(tuner_num)
            print str(device.frontend_tuner_status[tuner_num])
            print ""
    
    def attempt_allocation(self,device_ref,allocation_struct,success_list):
        try:
            alloc_success = device_ref.allocateCapacity([allocation_struct])
            if alloc_success:
                success_list.append(allocation_struct)
                return True
        except:
            None
        return False
        
    
    def fail_and_cleanup(self,error_message,additional_debug, device_ref, allocation_list):
        print "** TEST FAILED !!! DEALLOCATING AND CLEANING UP**"
        print "ADDITIONAL DEBUG: " + str(additional_debug)
        for s_alloc in allocation_list:
            try:
                device_ref.deallocateCapacity([s_alloc])
            except:
                None
        self.fail(error_message)
    def custom_fail(self,error_message,additional_debug):
        print "** TEST FAILED !!! **"
        print "ADDITIONAL DEBUG: " + str(additional_debug)
        self.fail(error_message)
    """Test for all device implementations in MSDD"""
    def make_prop_msdd_configuration(self,ip,port):
        return {'msdd_configuration::msdd_ip_address' : ip ,'msdd_configuration::msdd_port' : str(port)}
    def make_prop_msdd_configuration(self):
        global IP_ADDRESS
        global PORT
        return {'msdd_configuration::msdd_ip_address' : IP_ADDRESS ,'msdd_configuration::msdd_port' : str(PORT)}
    


    def testScaBasicBehavior(self):
        print "\n*--- RUNNING TEST " + str(inspect.stack()[0][3]) + " ---*"
        device = sb.Component("../MSDD.spd.xml",execparams={"DEBUG_LEVEL":0})
        device.releaseObject()
        return
        print "\n*--- RUNNING TEST " + str(inspect.stack()[0][3]) + " ---*"
        #######################################################################
        # Launch the device with the default execparams
        execparams = self.getPropertySet(kinds=("execparam",), modes=("readwrite", "writeonly"), includeNil=False)
        execparams = dict([(x.id, any.from_any(x.value)) for x in execparams])
        self.launch(execparams)
        #######################################################################
        # Verify the basic state of the device
        self.assertNotEqual(self.comp, None)
        self.assertEqual(self.comp.ref._non_existent(), False)
	
        self.assertEqual(self.comp.ref._is_a("IDL:CF/Device:1.0"), True)
	
        self.assertEqual(self.spd.get_id(), self.comp.ref._get_identifier())
        
        #######################################################################
        # Simulate regular device startup
        # Verify that initialize nor configure throw errors
        self.comp.initialize()
        configureProps = self.getPropertySet(kinds=("configure",), modes=("readwrite", "writeonly"), includeNil=False)
        self.comp.configure(configureProps)
        
        #######################################################################
        # Validate that query returns all expected parameters
        # Query of '[]' should return the following set of properties
        expectedProps = []
        expectedProps.extend(self.getPropertySet(kinds=("configure", "execparam"), modes=("readwrite", "readonly"), includeNil=True))
        expectedProps.extend(self.getPropertySet(kinds=("allocate",), action="external", includeNil=True))
        props = self.comp.query([])
        props = dict((x.id, any.from_any(x.value)) for x in props)
        # Query may return more than expected, but not less
        for expectedProp in expectedProps:
            self.assertEquals(props.has_key(expectedProp.id), True)
        
        #######################################################################
        # Verify that all expected ports are available
        for port in self.scd.get_componentfeatures().get_ports().get_uses():
            port_obj = self.comp.getPort(str(port.get_usesname()))
            self.assertNotEqual(port_obj, None)
            self.assertEqual(port_obj._non_existent(), False)
            self.assertEqual(port_obj._is_a("IDL:CF/Port:1.0"),  True)
            
        for port in self.scd.get_componentfeatures().get_ports().get_provides():
            port_obj = self.comp.getPort(str(port.get_providesname()))
            self.assertNotEqual(port_obj, None)
            self.assertEqual(port_obj._non_existent(), False)
            self.assertEqual(port_obj._is_a(port.get_repid()),  True)
            
        #######################################################################
        # Make sure start and stop can be called without throwing exceptions
        self.comp.start()
        self.comp.stop()
        
        #######################################################################
        # Simulate regular device shutdown
        self.comp.releaseObject()
        
    def test_ConnToMSDD(self):
#        return
        print "\n*--- RUNNING TEST " + str(inspect.stack()[0][3]) + " ---*"
        device = sb.Component("../MSDD.spd.xml",execparams={"DEBUG_LEVEL":0})
        device.msdd_configuration = self.make_prop_msdd_configuration()
        
        print "MSDD STATUS:"
        print str(device.msdd_status)
        
        device.releaseObject()
    
    def test_SimpleRXDAllocationDeallocation(self):
#        return
        print "\n*--- RUNNING TEST " + str(inspect.stack()[0][3]) + " ---*"
        device = sb.Component("../MSDD.spd.xml",execparams={"DEBUG_LEVEL":0})
        device.msdd_configuration = self.make_prop_msdd_configuration()
        device_ref = device.ref._narrow(CF.Device)
        alloc_struct = self.make_allocation_struct(tuner_type=self.FE_TYPE_RXDIG, 
                                                   allocation_id = "ALLOC_1", 
                                                   center_frequency = 160000000.0, 
                                                   bandwidth=20000000.0, 
                                                   sample_rate=25000000.0)
      
        known_bad_alloc_struct = self.make_allocation_struct(tuner_type=self.FE_TYPE_RXDIG, 
                                                   allocation_id = "ALLOC_2", 
                                                   center_frequency = 160000000.0, 
                                                   bandwidth=25.0, 
                                                   sample_rate=25.0)
                
        
        print "Attempting Allocation.."
        successful_allocations = []
        if not self.attempt_allocation(device_ref,alloc_struct,successful_allocations):
            self.fail_and_cleanup("Allocation Failed Unexpectedly!", str(alloc_struct), device_ref, successful_allocations)
        if self.attempt_allocation(device_ref,known_bad_alloc_struct,successful_allocations):
            self.fail_and_cleanup("Allocation Should Not Work For Known Bad Value!", str(known_bad_alloc_struct), device_ref, successful_allocations)
    
    
        self.print_allocated_tuners(device)
        device.releaseObject()    
        
        
    def test_RXDC_with_AutoAlloc_AllocationDeallocation(self):
#        return
        # This test should:  (1) Allocate wideband as RX_DIGITIZER_CHANNELIZER
        #                    (2) Allocate software DDC. In doing so, it should require a automatic allocation of a hw nb ddc
        #                    (3) Allocate a second software DDC. It should require a automatic allocation of a hw nb ddc that is different than the previous allocation
        print "\n*--- RUNNING TEST " + str(inspect.stack()[0][3]) + " ---*"
        device = sb.Component("../MSDD.spd.xml",execparams={"DEBUG_LEVEL":0})
        device.msdd_configuration = self.make_prop_msdd_configuration()
        device_ref = device.ref._narrow(CF.Device)
        alloc_struct = self.make_allocation_struct(tuner_type=self.FE_TYPE_RXDIGCHAN, 
                                                   allocation_id = "ALLOC_1", 
                                                   center_frequency = 160000000.0, 
                                                   bandwidth=20000000.0, 
                                                   sample_rate=25000000.0)
      
        alloc_struct_sw_ddc =  self.make_allocation_struct(tuner_type=self.FE_TYPE_DDC, 
                                                   allocation_id = "SW_ALLOC_1", 
                                                   center_frequency = 160000000.0, 
                                                   bandwidth=390625.0, 
                                                   sample_rate=390625.0)
        
        alloc_struct_sw_ddc2 =  self.make_allocation_struct(tuner_type=self.FE_TYPE_DDC, 
                                                   allocation_id = "SW_ALLOC_2", 
                                                   center_frequency = 170000000.0, 
                                                   bandwidth=390625.0, 
                                                   sample_rate=390625.0)
        
        successful_allocations = []
        
         
        
        print "Attempting Allocation.."
        if not self.attempt_allocation(device_ref,alloc_struct,successful_allocations):
            self.fail_and_cleanup("Allocation Failed Unexpectedly!", str(alloc_struct), device_ref, successful_allocations)
        if not self.attempt_allocation(device_ref,alloc_struct_sw_ddc,successful_allocations):
            self.fail_and_cleanup("Allocation Failed Unexpectedly!", str(alloc_struct_sw_ddc), device_ref, successful_allocations)
        if not self.attempt_allocation(device_ref,alloc_struct_sw_ddc2,successful_allocations):
            self.fail_and_cleanup("Allocation Failed Unexpectedly!", str(alloc_struct_sw_ddc2), device_ref, successful_allocations)

        
        self.print_allocated_tuners(device)
        device.releaseObject()   
        
    def test_RXDC_with_AutoAlloc_MultList_AllocationDeallocation(self):
#        return

        # This test should:  (1) Allocate wideband as RX_DIGITIZER_CHANNELIZER
        #                    (2) Allocate software DDC. In doing so, it should require a automatic allocation of a hw nb ddc
        #                    (3) Allocate a second software DDC. It should use the same hw nb ddc as the previous allocation
        print "\n*--- RUNNING TEST " + str(inspect.stack()[0][3]) + " ---*"
        device = sb.Component("../MSDD.spd.xml",execparams={"DEBUG_LEVEL":0})
        device.msdd_configuration = self.make_prop_msdd_configuration()
        device_ref = device.ref._narrow(CF.Device)
        alloc_struct = self.make_allocation_struct(tuner_type=self.FE_TYPE_RXDIGCHAN, 
                                                   allocation_id = "ALLOC_1", 
                                                   center_frequency = 160000000.0, 
                                                   bandwidth=20000000.0, 
                                                   sample_rate=25000000.0)
      
        alloc_struct_sw_ddc =  self.make_allocation_struct(tuner_type=self.FE_TYPE_DDC, 
                                                   allocation_id = "SW_ALLOC_1", 
                                                   center_frequency = 160000000.0, 
                                                   bandwidth=390625.0, 
                                                   sample_rate=390625.0)
        
        alloc_struct_sw_ddc2 =  self.make_allocation_struct(tuner_type=self.FE_TYPE_DDC, 
                                                   allocation_id = "SW_ALLOC_2", 
                                                   center_frequency = 160001000.0, 
                                                   bandwidth=390625.0, 
                                                   sample_rate=390625.0)
        
        successful_allocations = []
        
         
        
        print "Attempting Allocation.."
        if not self.attempt_allocation(device_ref,alloc_struct,successful_allocations):
            self.fail_and_cleanup("Allocation Failed Unexpectedly!", str(alloc_struct), device_ref, successful_allocations)
        if not self.attempt_allocation(device_ref,alloc_struct_sw_ddc,successful_allocations):
            self.fail_and_cleanup("Allocation Failed Unexpectedly!", str(alloc_struct_sw_ddc), device_ref, successful_allocations)
        if not self.attempt_allocation(device_ref,alloc_struct_sw_ddc2,successful_allocations):
            self.fail_and_cleanup("Allocation Failed Unexpectedly!", str(alloc_struct_sw_ddc2), device_ref, successful_allocations)
    
        self.print_allocated_tuners(device)
        device.releaseObject()   
        
    def test_RXD_with_AutoAlloc_MultList_AllocationDeallocation(self):
#        return

        # This test should:  (1) Allocate wideband as RX_DIGITIZER
        #                    (2) All other allocations should fail because RX_DIGITIZER does not allow for children
        print "\n*--- RUNNING TEST " + str(inspect.stack()[0][3]) + " ---*"
        device = sb.Component("../MSDD.spd.xml",execparams={"DEBUG_LEVEL":0})
        device.msdd_configuration = self.make_prop_msdd_configuration()
        device_ref = device.ref._narrow(CF.Device)
        alloc_struct = self.make_allocation_struct(tuner_type=self.FE_TYPE_RXDIG, 
                                                   allocation_id = "ALLOC_1", 
                                                   center_frequency = 160000000.0, 
                                                   bandwidth=20000000.0, 
                                                   sample_rate=25000000.0)
      
        alloc_struct_sw_ddc =  self.make_allocation_struct(tuner_type=self.FE_TYPE_DDC, 
                                                   allocation_id = "SW_ALLOC_1", 
                                                   center_frequency = 160000000.0, 
                                                   bandwidth=390625.0, 
                                                   sample_rate=390625.0)
        
        
        successful_allocations = []
        
         
        
        print "Attempting Allocation.."
        if not self.attempt_allocation(device_ref,alloc_struct,successful_allocations):
            self.fail_and_cleanup("Allocation Failed Unexpectedly!", str(alloc_struct), device_ref, successful_allocations)
        if self.attempt_allocation(device_ref,alloc_struct_sw_ddc,successful_allocations):
            self.fail_and_cleanup("Allocation Should Fail!", str(alloc_struct_sw_ddc), device_ref, successful_allocations)
        
        self.print_allocated_tuners(device)
        device.releaseObject()   

    def test_SimpleRX_WithFFT_AllocationDeallocation(self):
#        return
        print "\n*--- RUNNING TEST " + str(inspect.stack()[0][3]) + " ---*"
        device = sb.Component("../MSDD.spd.xml",execparams={"DEBUG_LEVEL":0})
        device.msdd_configuration = self.make_prop_msdd_configuration()
        device_ref = device.ref._narrow(CF.Device)
        
        alloc_struct = self.make_allocation_struct(tuner_type=self.FE_TYPE_RXDIG, 
                                                   allocation_id = "ALLOC_1", 
                                                   center_frequency = 160000000.0, 
                                                   bandwidth=20000000.0, 
                                                   sample_rate=25000000.0)

        print "Attempting Allocation.."
        successful_allocations = []
        if not self.attempt_allocation(device_ref,alloc_struct,successful_allocations):
            self.fail_and_cleanup("Allocation Failed Unexpectedly!", str(alloc_struct), device_ref, successful_allocations)
       
    
        self.print_allocated_tuners(device)
        device.releaseObject() 

    
if __name__ == "__main__":
    ossie.utils.testing.main("../MSDD.spd.xml") # By default tests all implementations
