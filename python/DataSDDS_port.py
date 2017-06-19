from MSDD_base import *
import Queue, threading
    
class PortBULKIODataSDDSOut_implemented(PortBULKIODataSDDSOut_i):
    def __init__(self, parent, name, max_attachments=1):
        self.parent = parent
        self.name = name
        self.max_attachments = max_attachments
        self.outPorts = {} # key=connection_id,  value=port
        self.attachedGroup = {} # key=connection_id,  value=attach_id
        self.lastStreamData = {}
        self.lastName = {}
        self.defaultStreamSRI = BULKIO.StreamSRI(1, 0.0, 0.001, 1, 200, 0.0, 0.001, 1, 1, "sampleStream", False, [])
        self.defaultTime = BULKIO.PrecisionUTCTime(0, 0, 0, 0, 0)
        self.port_lock = threading.Lock()
        self.stats = self.linkStatistics(self)
        self.sriDict = {} # key=streamID  value=(StreamSRI, PrecisionUTCTime)
        self.H = {}
        self.T = {}


    def connectPort(self, connection, connectionId):
        self.parent._log.info("Got a connectPort called with connectionID:"+str(connectionId) + " with last stream: " + str(self.lastStreamData)) 
        self.port_lock.acquire()
        port = connection._narrow(BULKIO.dataSDDS)
        self.outPorts[str(connectionId)] = port
        
        self.parent._log.info("connectPort db 1!") 
        #TODO: need to figure out how to handle attach on connect, for multiple streams....
        try:
            if self.lastStreamData.has_key(connectionId):
                self.parent._log.info("calling attach " + str(self.lastStreamData[connectionId]) + " <---> " + str(self.lastName[connectionId]) + "!") 
                self.attachedGroup[str(connectionId)] = port.attach(self.lastStreamData[connectionId], self.lastName[connectionId])
                self.parent._log.trace("done calling attach " + str(self.lastStreamData[connectionId]) + " <---> " + str(self.lastName[connectionId]) + "!") 
                
                if self.H.has_key(connectionId) and self.T.has_key(connectionId):
                    self.pushSRIbyConnectionID(self.H[connectionId], self.T[connectionId], connectionId)
        except Exception, e:
            self.parent._log.error(str(e))
            self.port_lock.release()
            raise e
        self.parent._log.trace("connectPort done!") 
        
        self.port_lock.release()
    
        
    #overload attach to only send if the connection_id matches
    def attach(self, streamData, name):
        #print "Called attach() with name:"+str(name)
        ids = []
        self.port_lock.acquire()
        for entry in self.outPorts:
            try:
                #Added this check to only send to the connection with the connection_id == allocation_id
                if entry == streamData.id:
                    self.parent._log.trace("Found connection to to push attach() on")
                    if entry in self.attachedGroup:
                        self.outPorts[entry].detach(self.attachedGroup[entry])
                    self.attachedGroup[entry] = self.outPorts[entry].attach(streamData, name)
                    ids.append(self.attachedGroup[entry])
                    if self.H.has_key(entry) and self.T.has_key(entry):
                        self.pushSRIbyConnectionID(self.H[entry], self.T[entry], entry)
            except:
                self.parent._log.exception("Unable to deliver update to %s" + str(entry))
        #store old ones in here...
        self.parent._log.info("STREAM DATA ID: " + str(streamData.id))
        self.parent._log.info("STREAM DATA: " + str(streamData))
        self.parent._log.info("lastStreamData: " + str(self.lastStreamData))
        self.lastStreamData[streamData.id] = streamData
        self.lastName[streamData.id] = name
        self.port_lock.release()
        return ids    
    
    def detach(self, attachId=None, connectionId=None):
        self.port_lock.acquire()
        if attachId == None:
            for entry in self.outPorts:
                try:
                    if entry in self.attachedGroup:
                        if connectionId == None or entry == connectionId:
                            self.parent._log.info("START DETACH 1: " + str(self.attachedGroup[entry]))
                            self.outPorts[entry].detach(self.attachedGroup[entry])
                            self.attachedGroup.pop(entry)
                            self.parent._log.info("DONE DETACH 1 ")
                            
                except:
                    self.parent._log.exception("Unable to detach %s", str(entry))
            self.lastStreamData = {}
            self.lastName = {}
        else:
            for entry in self.attachedGroup:
                try:
                    if self.attachedGroup[entry] == attachId:
                        if entry in self.outPorts:
                            if connectionId == None or entry == connectionId:
                                self.parent._log.info("START DETACH 2: " + str(self.attachedGroup[entry]))
                                self.outPorts[entry].detach(self.attachedGroup[entry])
                                self.parent._log.info("DONE DETACH 2 ")
                        self.attachedGroup.pop(entry)
                        if len(self.attachedGroup) == 0:
                            self.lastStreamData = {}
                            self.lastName = {}
                        break
                except:
                    self.parent._log.exception("Unable to detach %s", str(entry))

        self.port_lock.release()
        
    #make a detachByConnectionID to allow for easier detaches
    def detachByConnectionID(self, connectionId=None):        
        self.parent._log.trace("Trying to do a detachByConnectionID, looking for id:"+str(connectionId))
        detachList = []
        
        try:
            for entry in self.attachedGroup:
                if entry == connectionId:
                    self.parent._log.info("Found connection to to push detach() on")
                    detachList.append(entry)
            for p in detachList:
                self.detach(self.attachedGroup[p])
            if self.lastStreamData != None:
                if self.lastStreamData.has_key(connectionId):
                    del self.lastStreamData[connectionId]
            if self.lastName != None:
                if self.lastName.has_key(connectionId):
                    del self.lastName[connectionId] 
        except:
            self.parent._log.exception("Unable to detach %s" + str(entry))

    #this will push SRI only on the correct connection ID
    def pushSRIbyConnectionID(self, H, T, connectionId):
        self.parent._log.info("pushSRIbyConnectionID start...") 
        try:
            for connId in self.outPorts.keys():
                self.parent._log.trace("in pushSRIbyConnectionID Checking connection:"+str(connId)+" for match with:"+str(connectionId))
                if self.outPorts[connId] != None:
                    if connId == connectionId:
                        self.parent._log.trace("Pushing SRI to matching port")
                        self.outPorts[connId].pushSRI(H, T)
                        

        except:
            self.parent._log.error("the call to pushSRI failed on connectionID" + str(connectionId))
        self.H[connectionId] = copy.deepcopy(H)
        self.T[connectionId] = copy.deepcopy(T)
        self.refreshSRI = False


class PortBULKIODataSDDSOutFFT_implemented(PortBULKIODataSDDSOut_implemented):
    def connectPort(self, connection, connectionId):
        self.parent.register_fft_connection(connectionId)
        PortBULKIODataSDDSOut_implemented.connectPort(self, connection, connectionId)
        
    def disconnectPort(self, connectionId):
        self.parent.deregister_fft_connection(connectionId)
        PortBULKIODataSDDSOut_implemented.disconnectPort(self, connectionId)
        
class PortBULKIODataSDDSOutSPC_implemented(PortBULKIODataSDDSOut_implemented):
    def connectPort(self, connection, connectionId):
        self.parent._log.debug("Called get port on SPC implementation")
        self.parent.register_spc_connection(connectionId, None)
        PortBULKIODataSDDSOut_implemented.connectPort(self, connection, connectionId)
        
    def disconnectPort(self, connectionId):
        self.parent.deregister_spc_connection(connectionId)
        PortBULKIODataSDDSOut_implemented.disconnectPort(self, connectionId)
    
