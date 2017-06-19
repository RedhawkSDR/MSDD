from msddcontroller import *

import os,sys,time

if __name__ == "__main__":

    ip = "192.168.1.250"
    port = 23

    radio = MSDDRadio(ip, port)

    
    radio.spectral_scan_modules[0].object.setEnable(False)
    radio.out_modules[19].object.setEnable(False)
    radio.wb_ddc_modules[0].object.setEnable(False)
    



