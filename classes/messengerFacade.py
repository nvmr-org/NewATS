'''
Created on Nov 18, 2016

@author: ttb
'''
import time
import sys
import logging
import traceback
from trolleyRoster import TrolleyRoster

logger = logging.getLogger("ATS."+__name__)
logger.setLevel(logging.INFO)
thisFuncName = lambda n=0: sys._getframe(n + 1).f_code.co_name

trolleyRoster = TrolleyRoster()

try:
    __jmriFlag = True
    import jmri
    logger.info('Successfully Imported jmri', exc_info=True)
    #jmri.jmrix.loconet.LocoNetListener
except ImportError:
    __jmriFlag = False
    logger.info('Failed to import jmri - bypassing', exc_info=True)

# **************************************************
#class to handle a listener event loconet messages *
#                                                  *
# OpCode values: 131 = 0x83 = OPC_GPON             *
#                229 = 0xE5 = OPC_PEER_XFER        *
#                                                  *
#                176 = 0xB0 = OPC_SW_REQ           *
#                177 = 0xB1 = OPC_SW_REP           *
#                178 = 0xB2 = OPC_INPUT_REP        *
#                231 = 0xE7 = OPC_SL_RD_DATA       *
#                237 = 0xED = OPC_IMM_PACKET       *
#                                                  *
# **************************************************
#class MsgListener(jmri.jmrix.loconet.LocoNetListener):
#
#    def message(self, msg):
#        return
class Messenger(jmri.jmrix.loconet.LocoNetListener):

    __instance = None
    __lnListen = None

    def __init__(self):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        self.debounce = False #turn track contact loss debounce off/on
        self.eventQueue = None
        self.accumByteCnt = 0
        logger.info("Initializing Messenger Listener")


    def __new__(cls): # __new__ always a class method
        if Messenger.__instance is None:
            logger.info("Creating NEW Messenger Listener")
            Messenger.__instance = object.__new__(cls)
        return Messenger.__instance


    # **********************
    # Set Event Queue for Simulations
    # **********************
    def createEventQueue(self, eventQueue = None):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        self.eventQueue = eventQueue
        logger.trace("Exiting %s.%s", __name__, thisFuncName())
        return


    def setDebugLevel(self,state):
        logger.setLevel(logging.DEBUG if state else logging.INFO)
        for handler in logging.getLogger("ATS").handlers:
            handler.setLevel(logging.DEBUG)
        logger.debug("%s.%s - Logger:%s - Set Debug Flag:%s", __name__, thisFuncName(),str(logger),str(state))


    def getDebugLevel(self):
        return logger.level


    def delayForMsec(self, delayInMsec=1000):
        if __jmriFlag: jmri.jmrit.automat.AbstractAutomaton.waitMsec(delayInMsec,delayInMsec)


    def createPacket(self,msgLength,opcode,ARGS):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        logger.debug("MsgLen: %s  OpCode: %s  ARGS: %s" ,msgLength, hex(opcode), ARGS)
        try:
            if __jmriFlag: packet = jmri.jmrix.loconet.LocoNetMessage(msgLength)
            packet.setElement(0, opcode)
            packet.setElement(1, ARGS[1])
            packet.setElement(2, ARGS[2])
            if msgLength > 4:
                for i in range(3,13):
                    packet.setElement(i, ARGS[i])
        except:
            logger.warn("Message Send Failed")
            traceback.print_exc()
            raise
        logger.trace("Exiting %s.%s", __name__, thisFuncName())
        return packet


    # **********************
    # Send LocoNet Message
    # **********************
    def sendLnMsg(self,msgLength,opcode,ARGS) :
        # format and send the specific LocoNet message
        # send up to 16 bytes in the message - includes checksum
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        packet = self.createPacket(msgLength,opcode,ARGS)
        logger.trace("Just prior to send message - jmriFlag = %s", __jmriFlag)
        logger.trace("Packet ==>> %s", packet)           # print packet to Script Output window
        if __jmriFlag: 
            try:
                jmri.InstanceManager.getList(jmri.jmrix.loconet.LocoNetSystemConnectionMemo).get(0).getLnTrafficController().sendLocoNetMessage(packet)
            except:
                logger.warn("Skipping JRMI.sendLoconetMessage")
                pass
        return


    # ***********************************
    # * Create and send a sensor report *
    # ***********************************
    def sendSenorReportMsg(self,sensorId):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        ARGS = [0]*14 # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        snrAddr = sensorId -1
        in1 = (snrAddr & 0xFF) >> 1 # lower 7 address bits left shifted once
        b2I = (snrAddr % 2) << 5 # remainder odd/even
        b2XL = 0x50 # X = 1 and L = 1
        b2XIL = b2I | b2XL
        in2 = b2XIL + (snrAddr >> 8) # XIL plus upper 4 address bits
        msgLength = 4
        opcode = jmri.jmrix.loconet.LnConstants.OPC_INPUT_REP #0xB2 OPC_INPUT_REP
        ARGS[1] = in1
        ARGS[2] = in2
        self.sendLnMsg(msgLength,opcode,ARGS)
        logger.debug("Sent Sensor Message for SensorId:" + str(sensorId))
        logger.trace("Exiting %s.%s", __name__, thisFuncName())
        return


    # ************************
    # Send Emergency stop 
    # ************************
    def eStop(self, slotId) :
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        msgLength = 4
        opcode = jmri.jmrix.loconet.LnConstants.OPC_LOCO_SPD #0xA0 OPC_LOCO_SPD
        ARGS = [0]*14 # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = slotId
        ARGS[2] = 0x01
        self.sendLnMsg(msgLength,opcode,ARGS)
        logger.debug("sent Estop %s" ,str(hex(opcode)))
        logger.trace("Exiting %s.%s", __name__, thisFuncName())
        return
    
    
    # *********************************************
    # Ring the trolley bell before start and stop *
    # *********************************************
    def ringBell(self, slotId) :
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        #print "Ring Bell for Trolley:", self.address, "Throttle:", self.throttle
        #if self.throttle == None: return
        #ringBell 1st time by setting F1 = ON
        msgLength = 4
        opcode = jmri.jmrix.loconet.LnConstants.OPC_LOCO_DIRF #0xA1 OPC_LOCO_DIRF
        ARGS = [0]*14 # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = slotId
        ARGS[2] = 0x11 #ON with direction forward and light ON
        self.sendLnMsg(msgLength,opcode,ARGS)
        time.sleep(1) #wait 1 sec before toggling other way
        #ringBell 2nd time by setting F1 = OFF
        msgLength = 4
        opcode = jmri.jmrix.loconet.LnConstants.OPC_LOCO_DIRF #0xA1 OPC_LOCO_DIRF
        ARGS = [0]*14 # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = slotId
        ARGS[2] = 0x10 #OFF with direction forward and light ON
        self.sendLnMsg(msgLength,opcode,ARGS)
        logger.debug("sent ring bell %s", str(hex(opcode)))
        #time.sleep(3) #wait 3 sec before returning
        #self.throttle.setF1(True)     # turn on bell
        #self.waitMsec(1000)           # wait for 1 seconds
        #self.throttle.setF1(False)    # turn off bell
        #self.waitMsec(1000)           # wait for 1 second
        logger.trace("Exiting %s.%s", __name__, thisFuncName())
        return


    # **************************
    # Turn light OFF *
    # **************************
    def lightOff(self,slotId) :
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        msgLength = 4
        opcode = jmri.jmrix.loconet.LnConstants.OPC_LOCO_DIRF #0xA1 OPC_LOCO_DIRF
        ARGS = [0]*14 # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = slotId
        ARGS[2] = 0x00 #light OFF, direction forward
        self.sendLnMsg(msgLength,opcode,ARGS)
        logger.debug("sent light OFF: %s ",str(hex(opcode)))
        logger.trace("Exiting %s.%s", __name__, thisFuncName())
        return


    # **************************
    # Turn light ON *
    # **************************
    def lightOn(self,slotId) :
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        msgLength = 4
        opcode = jmri.jmrix.loconet.LnConstants.OPC_LOCO_DIRF #0xA1 OPC_LOCO_DIRF
        ARGS = [0]*14 # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = slotId
        ARGS[2] = 0x00 #light OFF, direction forward
        self.sendLnMsg(msgLength,opcode,ARGS)
        logger.debug("sent light OFF: %s",str(hex(opcode)))
        logger.trace("Exiting %s.%s", __name__, thisFuncName())
        return


    def setSpeed(self, slotId, speed):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        msgLength = 4
        opcode = jmri.jmrix.loconet.LnConstants.OPC_LOCO_SPD #0xA0 OPC_LOCO_SPD
        ARGS = [0]*14 # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = slotId
        ARGS[2] = speed
        self.sendLnMsg(msgLength,opcode,ARGS)
        logger.debug("sent Set Speed %s",str(hex(opcode)))
        #self.throttle.setSpeedSetting(speed)
        #self.speed = speed
        logger.trace("Exiting %s.%s", __name__, thisFuncName())
        return


    # ***************************************
    # Free Trolley Slot (Dispatch Trolleys) *
    # ***************************************
    def freeSlot(self,slotId) :
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        global ARGS
        msgLength = 4
        opcode = jmri.jmrix.loconet.LnConstants.OPC_SLOT_STAT1 #0xB5 OPC_SLOT_STAT1
        ARGS = [0]*14 # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = slotId
        ARGS[2] = 0x13 #update status to Not Consisted, Common slot
        self.sendLnMsg(msgLength,opcode,ARGS)
        logger.debug("sent Slot Not Consisted & Common %s", str(hex(opcode)))
        msgLength = 4
        opcode = jmri.jmrix.loconet.LnConstants.OPC_MOVE_SLOTS #0xBA OPC_MOVE_SLOTS
        ARGS = [0]*14 # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = slotId
        ARGS[2] = 0x00 #mark slot as DISPATCHED
        self.sendLnMsg(msgLength,opcode,ARGS)
        logger.debug("sent Slot Dispatch %s",str(hex(opcode)))
        time.sleep(1)           # wait for 1 seconds
        logger.trace("Exiting %s.%s", __name__, thisFuncName())
        return


    # *******************
    # Update Slot STAT1 *
    # *******************
    def updateSlot(self, slotId) :
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        msgLength = 4
        opcode = jmri.jmrix.loconet.LnConstants.OPC_SLOT_STAT1 #0xB5 OPC_SLOT_STAT1
        ARGS = [0]*14 # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = slotId
        ARGS[2] = 0x03
        self.sendLnMsg(msgLength,opcode,ARGS)
        logger.debug("sent Slot Stat1 Update ", str(hex(opcode)))
        logger.trace("Exiting %s.%s", __name__, thisFuncName())
        return


    # *******************************************************
    # Request Trolley Slot (acquire Trolleys)
    # *******************************************************
    def requestThrottle(self,address, isLong, throttleWaitTime) : #sends 0xBF with loco address
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        logger.debug("requested address = %s",str(address))
        try:
            throttle = jmri.jmrit.automat.AbstractAutomaton().getThrottle(address, isLong, throttleWaitTime)  # address, long address = true
        except Exception as e:
            throttle = None
            logger.warn("throttle exception: %s", e)
            logger.warn("Unable to get throttle")
        logger.debug("sent throttle request: "+str(throttle))
        logger.trace("Exiting %s.%s", __name__, thisFuncName())
        return throttle


    # *******************************************************
    # Request Trolley Slot (acquire Trolleys)
    # *******************************************************
    def requestSlot(self,slotId) : #sends 0xBF with loco address
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        logger.debug("requested slot = %s",str(slotId))
        #self.noSlotID = True
        self.lastDeviceID = slotId
        self.dtxAddress = int(slotId)    # get address from entry field for LocoNet
        self.hiAddrByte = self.dtxAddress - ((self.dtxAddress / 128) * 128) #most significant address byte
        self.loAddrByte = self.dtxAddress / 128 #least significant address byte
        logger.debug("dtxAddress: %s  hiAddrByte: %s  loAddrByte: %s", self.dtxAddress, self.hiAddrByte, self.loAddrByte)
        #msg.prepLnAddr(deviceID)
        logger.debug("prep return = %s %s",hex(self.hiAddrByte),hex(self.loAddrByte))
        #request Loco data slot
        msgLength = 4
        opcode = jmri.jmrix.loconet.LnConstants.OPC_LOCO_ADR #0xBF OPC_LOCO_ADR request current slot assigned, if not create slot
        ARGS = [0]*14 # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = self.loAddrByte
        ARGS[2] = self.hiAddrByte
        self.sendLnMsg(msgLength,opcode,ARGS)
        #self.bfSent = True #turn on to allow E7 response to be read for slotID (flag set must be after send!)
        logger.debug("sent Slot Request %s",str(hex(opcode)))
        logger.trace("Exiting %s.%s", __name__, thisFuncName())
        return True


    def setSlotInUse(self, slotId):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        """Set the Trolley's DCC SlotId."""
        # ****************
        # Set Slot INUSE *
        # ****************
        msgLength = 4
        opcode = jmri.jmrix.loconet.LnConstants.OPC_MOVE_SLOTS #0xBA OPC_MOVE_SLOTS
        ARGS = [0]*14 # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = slotId
        ARGS[2] = slotId
        self.sendLnMsg(msgLength,opcode,ARGS)
        logger.debug("sent Slot INUSE %s", str(hex(opcode)))
        logger.trace("Exiting %s.%s", __name__, thisFuncName())


    # ****************
    # Write Slot Data *
    # ****************
    def writeSlotData(self, ARGS=[0]*14) :
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        msgLength = 14
        opcode = jmri.jmrix.loconet.LnConstants.OPC_WR_SL_DATA #0xEF OPC_WR_SL_DATA
        #ARGS = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        #### ARGS[1] =0x0E #part of OPC
        #### ARGS[2] = slotID taken from last 0xE7 response
        ARGS[3] = 0x33 #change from 0x03 to refresh INUSE
        #use rest of ARGS from last 0xE7 response
        self.sendLnMsg(msgLength,opcode,ARGS)
        logger.debug("sent Slot Data Update %s", str(hex(opcode)))
        logger.trace("Exiting %s.%s", __name__, thisFuncName())
        return


    def getArgsFromMessage(self,msg):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        i = 1
        ARGS=[0]*14
        logger.debug("Getting ARGS from message - msgLen:%s",str(msg.getNumDataElements()))
        while i < msg.getNumDataElements():
            ARGS[i] = msg.getElement(i)
            #logger.info("Arg[%s]:%s ", str(i),str(hex(msg.getElement(i))))
            i+=1
        logger.debug("ARGS from message - ARGS:%s",str(ARGS))
        logger.trace("Exiting %s.%s", __name__, thisFuncName())
        return ARGS


# **************************************************
#class to handle a listener event loconet messages *
#                                                  *
# OpCode values: 131 = 0x83 = OPC_GPON             *
#                229 = 0xE5 = OPC_PEER_XFER        *
#                                                  *
#                176 = 0xB0 = OPC_SW_REQ           *
#                177 = 0xB1 = OPC_SW_REP           *
#                178 = 0xB2 = OPC_INPUT_REP        *
#                231 = 0xE7 = OPC_SL_RD_DATA       *
#                237 = 0xED = OPC_IMM_PACKET       *
#                                                  *
# **************************************************
    def message(self, msg):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        newMsgOpCodeHex = msg.getOpCodeHex()
        newMsgLength = msg.getNumDataElements()
        self.accumByteCnt += newMsgLength
        # Note: accumByteCnt background task will read and be reset to zero and plotted every 1 second
        
        logger.trace("rcvd " + str(newMsgOpCodeHex))
        logger.trace("len = "+str(newMsgLength) + " msg = " + str(msg))

        ######################################################################################
        ## only listen for OPC_INPUT_REP message from trolley BODs (0xB2) going active (hi) ##
        ######################################################################################
        if (msg.getOpCode() == jmri.jmrix.loconet.LnConstants.OPC_INPUT_REP) and ((msg.getElement(2) & 0x10) == 0x10) :
            eventAddr = msg.sensorAddr() + 1
            logger.trace("== eventAddr = " + str(eventAddr))
            trolleyRoster.processBlockEvent(eventAddr)

        #####################################################################
        ## only listen for slot data response message (opcode 231 or 0xE7) ##
        ## triggered by throttle requests 0xBF #OPC_LOCO_ADR               ##
        #####################################################################
        if (msg.getOpCode() == jmri.jmrix.loconet.LnConstants.OPC_SL_RD_DATA):
            slotId = msg.getElement(2)
            if slotId > 120: return # Larger slots are Digitrax Internal Use Only
            status = msg.getElement(3)
            loAddrByte =  msg.getElement(4)
            hiAddrByte = msg.getElement(9)
            address = hiAddrByte*128+loAddrByte
            #trolley = trolleyRoster.findByAddress(address)
            logger.trace("E7 Opcode Received - Hi:"+str(hex(hiAddrByte))+" Lo:"+ str(hex(loAddrByte))
                        +" address:"+str(address)+" slot:"+str(slotId)
                        +" Status:"+str(hex(status)))
            # See if this 0xE7 message is for a device in the trolleyRoster that sent a slot request
            trolley = trolleyRoster.findByAddress(address)
            if trolley and trolley.slotRequestSent:
                logger.trace("Trolley: "+str(address)+" SlotId:"+str(slotId)+" Status:"+str(status))
                # Per the LocoNet specs, check the D5 & D4 bits of the STATUS1 byte to determine the state of the slot
                # 11=IN_USE, 10=IDLE, 01=COMMON, 00=FREE SLOT and respond
                if ((status >> 4) & 0x03) < 3: # if status is IDLE, COMMON, or FREE
                    if trolley.slotId is None: 
                        logger.trace("Trolley: "+str(address)+" Slot was IDLE, COMMON, or FREE")
                        self.setSlotInUse(slotId) # Set the slot to IN-USE
                        trolley.setSlotId(slotId=slotId)
                        logger.info("Trolley %s SlotId = %s",str(address), str(slotId))
                        ARGS = self.getArgsFromMessage(msg)
                        ARGS[3]=0 # Set Speed to Zero
                        self.writeSlotData(ARGS)  # Write back the slot data with speed = 0
                        #trolley.ringBell()
                        #trolley.blinkOn()
                    else:
                        # We really should never get here because that means a slot was already assigned to the 
                        # trollet but we somehow received a slot request anyway.  So just write the slot data back
                        # out to refresh the slot.
                        logger.debug("Trolley: "+str(address)+" Slot was IDLE, COMMON, or FREE")
                        logger.warn("Trolley %s SlotId = %s - STRANGE CONDITION",str(address), str(slotId))
                        self.writeSlotData(self.getArgsFromMessage(msg))
                        #trolley.ringBell()
                        #trolley.blinkOn()
                else:
                    # If we get here LocoNet already has the slot assigned and marked as IN-USE.  Per the LocoNet specs
                    # we should effectively Steal this throttle by unlinking and re-linking.  For now though we will just 
                    # assume the slot is ours and set the speed to zero.
                    trolley.slotId = slotId
                    ARGS = self.getArgsFromMessage(msg)
                    ARGS[3]=0 # Set Speed to Zero
                    logger.warn("Trolley %s SlotId = %s - SLOT WAS ALREADY ASSIGNED",str(address), str(slotId))
                    self.writeSlotData(ARGS)  # Write back the slot data with speed = 0
                    #trolley.ringBell()
                    #trolley.blinkOn()
            else:
                logger.warn("E7 Opcode Received for address:%s - But no trolley defined",str(address))
        logger.trace("Exiting %s.%s", __name__, thisFuncName())


    def destroyListener(self):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        Messenger.__instance = None
        if __jmriFlag: 
            try:
                jmri.InstanceManager.getList(jmri.jmrix.loconet.LocoNetSystemConnectionMemo).get(0).getLnTrafficController().removeLocoNetListener(0xFF, Messenger.__lnListen)
                Messenger.__lnListen = None
                logger.warn("JMRI.removeLocoNetListener Removed")
            except:
                logger.warn("Unable to remove JMRI.removeLocoNetListener")
                pass
        logger.trace("Exiting %s.%s", __name__, thisFuncName())
        return 


    def createListener(self):
        if Messenger.__lnListen is None:
            Messenger.__lnListen = Messenger() #create and start LocoNet listener
            ##jmri.jmrix.loconet.LnTrafficController.instance().addLocoNetListener(0xFF, lnListen)
            if __jmriFlag: 
                try:
                        jmri.InstanceManager.getList(jmri.jmrix.loconet.LocoNetSystemConnectionMemo).get(0).getLnTrafficController().addLocoNetListener(0xFF, Messenger.__lnListen)
                        logger.warn("Created JMRI.addLocoNetListener")
                except:
                        logger.warn("Unable to add JMRI.addLocoNetListener")
                        pass


    def getListener(self):
        return Messenger.__lnListen
