import time
import logging
import traceback
from trolleyRoster import TrolleyRoster
from blockMap import BlockMap

logger= logging.getLogger("NewATS."+__name__)
layoutMap = BlockMap()
trolleyRoster = TrolleyRoster()

try:
    jmriFlag = True
    import jmri
    logger.info('Successfully Imported jmri', exc_info=True)
    #jmri.jmrix.loconet.LocoNetListener
except ImportError:
    jmriFlag = False
    logger.info('Failed to import jmir - bypassing', exc_info=True)

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
    iTrace = False #turn enter (In) trace print off/on
    bTrace = True #turn all (Between) enter and exit traces print off/on 
    oTrace = False #turn exit (Out) trace print off/on
    dTrace = False #turn limited section Debug trace print off/on
    lTrace = False #turn msgListener incoming opcode print off/on
    tTrace = False #turn trolley array status print off/on
    sTrace = False #turn sequence view of LocoNet messages off/on
    
    __instance = None
    def __init__(self):
        self.debounce = False #turn track contact loss debounce off/on
        self.eventQueue = None
        self.accumByteCnt = 0
        #self.trolleyRoster=trolleyRoster
        #self.layoutMap = layoutMap
        logger.info("Initializing Messenger Listener")
        
    def __new__(cls): # __new__ always a class method
        if Messenger.__instance is None:
            Messenger.__instance = object.__new__(cls)
        return Messenger.__instance



    # **********************
    # Set Event Queue for Simulations
    # **********************
    def createEventQueue(self, eventQueue = None):
        self.eventQueue = eventQueue
        return

    # ******************************
    # Enable All Message Debugging 
    # ******************************
    def enableAllDebug(self):
        Messenger.iTrace = True #turn enter (In) trace print off/on
        Messenger.bTrace = True #turn all (Between) enter and exit traces print off/on 
        Messenger.oTrace = True #turn exit (Out) trace print off/on
        Messenger.dTrace = True #turn limited section Debug trace print off/on
        Messenger.lTrace = True #turn msgListener incoming opcode print off/on
        Messenger.tTrace = True #turn trolley array status print off/on
        Messenger.sTrace = True #turn sequence view of LocoNet messages off/on


    def delayForMsec(self, delayInMsec=1000):
        if jmriFlag: jmri.jmrit.automat.AbstractAutomaton.waitMsec(delayInMsec,delayInMsec)


    # **********************
    # Send LocoNet Message
    # **********************
    def sendLnMsg(self,msgLength,opcode,ARGS) :
        # format and send the specific LocoNet message
        # send up to 16 bytes in the message - includes checksum
        if Messenger.iTrace : logger.info("==>>entering sendLnMsg -->")
        if Messenger.bTrace : logger.info("MsgLen: %s  OpCode: %s  ARGS: %s" ,msgLength, hex(opcode), ARGS)
        try:
            if jmriFlag: packet = jmri.jmrix.loconet.LocoNetMessage(msgLength)
            if msgLength == 4 :
                packet.setElement(0, opcode)
                packet.setElement(1, ARGS[1])
                packet.setElement(2, ARGS[2])
            else :
                packet.setElement(0, opcode)
                packet.setElement(1, ARGS[1])
                packet.setElement(2, ARGS[2])
                packet.setElement(3, ARGS[3])
                packet.setElement(4, ARGS[4])
                packet.setElement(5, ARGS[5])
                packet.setElement(6, ARGS[6])
                packet.setElement(7, ARGS[7])
                packet.setElement(8, ARGS[8])
                packet.setElement(9, ARGS[9])
                packet.setElement(10, ARGS[10])
                packet.setElement(11, ARGS[11])
                packet.setElement(12, ARGS[12])
                packet.setElement(13, ARGS[13])
            if Messenger.bTrace : logger.info("Just prior to send message - jmriFlag = %s", jmriFlag)
            #tc = jmri.jmrix.loconet.LnTrafficController.status()
            #tc = jmri.jmrix.loconet.LnTrafficController()
            #print "TC="+str(jmri.jmrix.loconet.LnTrafficController().status())
            #if jmriFlag: jmri.jmrix.loconet.LnTrafficController.instance().sendLocoNetMessage(packet)
            if Messenger.bTrace : logger.info("Packet ==>> %s", packet)           # print packet to Script Output window
            #if jmriFlag: jmri.jmrix.loconet.LnTrafficController.instance().sendLocoNetMessage(packet)
            if jmriFlag: 
                try:
                    jmri.InstanceManager.getList(jmri.jmrix.loconet.LocoNetSystemConnectionMemo).get(0).getLnTrafficController().sendLocoNetMessage(packet)
                except:
                    logger.warn("Skipping JRMI.sendLoconetMessage")
                    pass
            ##prevMsg.setText(str(packet))     # put packet in hex in field
        except:
            logger.info("Message Send Failed")
            traceback.print_exc()
            raise
        if Messenger.oTrace : logger.info("<<==exiting sendLnMsg")
        return

    # ************************
    # * send a sensor report *
    # ************************
    def sendSenorReportMsg(self,sensorId):
        if Messenger.iTrace : logger.info("==>>entering sendSnrRptMsg -->")
        ARGS = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        snrAddr = sensorId -1
        in1 = (snrAddr & 0x7F) >> 1 # lower 7 address bits left shifted once
        b2I = (snrAddr % 2) << 5 # remainder odd/even
        b2XL = 0x50 # X = 1 and L = 1
        b2XIL = b2I | b2XL
        in2 = b2XIL + (snrAddr >> 7) # XIL plus upper 4 address bits
        msgLength = 4
        opcode = 0xB2
        ARGS[1] = in1
        ARGS[2] = in2
        self.sendLnMsg(msgLength,opcode,ARGS)
        logger.info("Sent Sensor Message for SensorId:" + str(sensorId))
        if Messenger.oTrace : logger.info("<<==exiting sendSnrRptMsg")
        return


    # ************************
    # Send Emergency stop 
    # ************************
    def eStop(self, slotId) :
        msgLength = 4
        opcode = 0xA0 #OPC_LOCO_SPD
        ARGS = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = slotId
        ARGS[2] = 0x01
        self.sendLnMsg(msgLength,opcode,ARGS)
        if Messenger.sTrace : logger.info("sent Estop %s" ,str(hex(opcode)))
        return
    
    
    # *********************************************
    # Ring the trolley bell before start and stop *
    # *********************************************
    def ringBell(self, slotId) :
        #print "Ring Bell for Trolley:", self.address, "Throttle:", self.throttle
        #if self.throttle == None: return
        #ringBell 1st time by setting F1 = ON
        msgLength = 4
        opcode = 0xA1 #OPC_LOCO_DIRF
        ARGS = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = slotId
        ARGS[2] = 0x11 #ON with direction forward and light ON
        self.sendLnMsg(msgLength,opcode,ARGS)
        time.sleep(1) #wait 1 sec before toggling other way
        #ringBell 2nd time by setting F1 = OFF
        msgLength = 4
        opcode = 0xA1 #OPC_LOCO_DIRF
        ARGS = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = slotId
        ARGS[2] = 0x10 #OFF with direction forward and light ON
        self.sendLnMsg(msgLength,opcode,ARGS)
        if Messenger.sTrace : logger.info("sent ring bell %s", str(hex(opcode)))
        #time.sleep(3) #wait 3 sec before returning
        #self.throttle.setF1(True)     # turn on bell
        #self.waitMsec(1000)           # wait for 1 seconds
        #self.throttle.setF1(False)    # turn off bell
        #self.waitMsec(1000)           # wait for 1 second
        return


    # **************************
    # Turn light OFF *
    # **************************
    def lightOff(self,slotId) :
        #print "Lights Off for Trolley:", self.address, "Throttle:", self.throttle
        #if self.throttle == None: return
        msgLength = 4
        opcode = 0xA1 #OPC_LOCO_DIRF
        ARGS = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = slotId
        ARGS[2] = 0x00 #light OFF, direction forward
        #time.sleep(1.0) #wait 1 second before sending in case decoder is processing a previous command
        self.sendLnMsg(msgLength,opcode,ARGS)
        if Messenger.sTrace : logger.info("sent light OFF ",str(hex(opcode)))
        #time.sleep(1.0) #wait 1 second before returning to let decoder finish processing this command
        #self.throttle.setF0(False)    # turn off light
        #self.waitMsec(1000)           # wait for 1 second
        return
    
    
    # **************************
    # Turn light ON *
    # **************************
    def lightOn(self,slotId) :
        #print "Lights On for Trolley:", self.address, "Throttle:", self.throttle
        #if self.throttle == None: return
        msgLength = 4
        opcode = 0xA1 #OPC_LOCO_DIRF
        ARGS = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = slotId
        ARGS[2] = 0x00 #light OFF, direction forward
        #time.sleep(1.0) #wait 1 second before sending in case decoder is processing a previous command
        self.sendLnMsg(msgLength,opcode,ARGS)
        if Messenger.sTrace : logger.info("sent light OFF ",str(hex(opcode)))
        #time.sleep(1.0) #wait 1 second before returning to let decoder finish processing this command
        #self.throttle.setF0(True)    # turn on light
        #self.waitMsec(1000)           # wait for 1 second
        return
    
    
    def setSpeed(self, slotId, speed):
        #print "Setting Trolley:", self.address, "Speed:", speed, "Throttle:", self.throttle
        #if self.throttle == None: return
        msgLength = 4
        opcode = 0xA0 #OPC_LOCO_SPD
        ARGS = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = slotId
        ARGS[2] = speed
        self.sendLnMsg(msgLength,opcode,ARGS)
        if Messenger.sTrace : logger.info("sent Set Speed %s",str(hex(opcode)))
        #self.throttle.setSpeedSetting(speed)
        #self.speed = speed
        return


    # ***************************************
    # Free Trolley Slot (Dispatch Trolleys) *
    # ***************************************
    def freeSlot(self,slotId) :
        global ARGS
        msgLength = 4
        opcode = 0xB5 #OPC_SLOT_STAT1
        ARGS = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = slotId
        ARGS[2] = 0x13 #update status to Not Consisted, Common slot
        self.sendLnMsg(msgLength,opcode,ARGS)
        if Messenger.sTrace : logger.info("sent Slot Not Consisted & Common ", str(hex(opcode)))
        msgLength = 4
        opcode = 0xBA #OPC_MOVE_SLOTS
        ARGS = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = slotId
        ARGS[2] = 0x00 #mark slot as DISPATCHED
        self.sendLnMsg(msgLength,opcode,ARGS)
        if Messenger.sTrace : logger.info("sent Slot Dispatch %s",str(hex(opcode)))
        self.updateSlot(slotId) #sets slot to being FREE
        return


    # *******************
    # Update Slot STAT1 *
    # *******************
    def updateSlot(self, slotId) :
        msgLength = 4
        opcode = 0xB5 #OPC_SLOT_STAT1
        ARGS = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = slotId
        ARGS[2] = 0x03
        self.sendLnMsg(msgLength,opcode,ARGS)
        if Messenger.sTrace : logger.info("sent Slot Stat1 Update ", str(hex(opcode)))
        return
    

    # *******************************************************
    # Request Trolley Slot (acquire Trolleys)
    # *******************************************************
#     def requestThrottle(self,address, isLong, throttleWaitTime) : #sends 0xBF with loco address
#         if Messenger.iTrace : logger.info("==>>entering requestThrottlet")
#         if Messenger.bTrace : logger.info("requested address = %s",str(address))
#         try:
#             throttle = jmri.jmrit.automat.AbstractAutomaton.getThrottle(address, isLong)  # address, long address = true
#         except:
#             throttle = None
#             logger.warn("Unable to get throttle")
#         if Messenger.sTrace : logger.info("sent throttle request: "+str(throttle))
#         if Messenger.oTrace : logger.info("<<==exiting requestThrottle")
#         return throttle
    
    # *******************************************************
    # Request Trolley Slot (acquire Trolleys)
    # *******************************************************
    def requestSlot(self,slotId) : #sends 0xBF with loco address
        if Messenger.iTrace : logger.info("==>>entering requestSlot")
        if Messenger.bTrace : logger.info("requested slot = %s",str(slotId))
        #self.noSlotID = True
        self.lastDeviceID = slotId
        self.dtxAddress = int(slotId)    # get address from entry field for LocoNet
        self.hiAddrByte = self.dtxAddress - ((self.dtxAddress / 128) * 128) #most significant address byte
        self.loAddrByte = self.dtxAddress / 128 #least significant address byte
        if Messenger.bTrace : logger.info("dtxAddress: %s  hiAddrByte: %s  loAddrByte: %s", self.dtxAddress, self.hiAddrByte, self.loAddrByte)
        #msg.prepLnAddr(deviceID)
        if Messenger.bTrace : logger.info("prep return = %s %s",hex(self.hiAddrByte),hex(self.loAddrByte))
        #request Loco data slot
        msgLength = 4
        opcode = 0xBF #OPC_LOCO_ADR request current slot assigned, if not create slot
        ARGS = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = self.loAddrByte
        ARGS[2] = self.hiAddrByte
        self.sendLnMsg(msgLength,opcode,ARGS)
        #self.bfSent = True #turn on to allow E7 response to be read for slotID (flag set must be after send!)
        if Messenger.sTrace : logger.info("sent Slot Request %s",str(hex(opcode)))
        if Messenger.oTrace : logger.info("<<==exiting requestSlot")
        return True
        

    def setSlotInUse(self, slotId):
        """Set the Trolley's DCC SlotId."""
        # ****************
        # Set Slot INUSE *
        # ****************
        msgLength = 4
        opcode = 0xBA #OPC_MOVE_SLOTS
        ARGS = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = slotId
        ARGS[2] = slotId
        self.sendLnMsg(msgLength,opcode,ARGS)
        if Messenger.sTrace : logger.info("sent Slot INUSE %s", str(hex(opcode)))

        
    # ****************
    # Write Slot Data *
    # ****************
    def writeSlotData(self, ARGS=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]) :
        msgLength = 14
        opcode = 0xEF #OPC_WR_SL_DATA
        #ARGS = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        #### ARGS[1] =0x0E #part of OPC
        #### ARGS[2] = slotID taken from last 0xE7 response
        ARGS[3] = 0x33 #change from 0x03 to refresh INUSE
        #use rest of ARGS from last 0xE7 response
        self.sendLnMsg(msgLength,opcode,ARGS)
        if Messenger.sTrace : logger.info("sent Slot Data Update %s", str(hex(opcode)))
        return
            

    def getArgsFromMessage(self,msg):
        i = 1
        ARGS=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        logger.info("Getting ARGS from message - msgLen:%s",str(msg.getNumDataElements()))
        while i < msg.getNumDataElements():
            ARGS[i] = msg.getElement(i)
            #logger.info("Arg[%s]:%s ", str(i),str(hex(msg.getElement(i))))
            i+=1
        logger.info("ARGS from message - ARGS:%s",str(ARGS))
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
        if Messenger.iTrace : logger.info("==>>entering MsgListener <--")
        newMsgOpCodeHex = msg.getOpCodeHex()
        newMsgLength = msg.getNumDataElements()
        self.accumByteCnt += newMsgLength
        # Note: accumByteCnt background task will read and be reset to zero and plotted every 1 second
        
        if Messenger.bTrace : logger.info("rcvd " + str(newMsgOpCodeHex))
        if Messenger.bTrace : logger.info("len = "+str(newMsgLength) + " msg = " + str(msg))

        ######################################################################################
        ## only listen for OPC_INPUT_REP message from trolley BODs (0xB2) going active (hi) ##
        ######################################################################################
        if (msg.getOpCode() == 178) and ((msg.getElement(2) & 0x10) == 0x10) :
            eventAddr = msg.sensorAddr() + 1
            if Messenger.bTrace : logger.info("== eventAddr = " + str(eventAddr))
            if layoutMap.findBlockByAddress(eventAddr) :
                if Messenger.bTrace : logger.info("Valid Sensor Event Rcvd = " + str(eventAddr) )#gaw-debug
                trolleyRoster.processBlockEvent(eventAddr)
                

        #####################################################################
        ## only listen for slot data response message (opcode 231 or 0xE7) ##
        ## triggered by throttle requests 0xBF #OPC_LOCO_ADR               ##
        #####################################################################
        if (msg.getOpCode() == 0xE7):
            slotId = msg.getElement(2)
            status = msg.getElement(3)
            loAddrByte =  msg.getElement(4)
            hiAddrByte = msg.getElement(9)
            address = hiAddrByte*128+loAddrByte
            #trolley = trolleyRoster.findByAddress(address)
            if Messenger.bTrace : logger.info("E7 Opcode Received - Hi:"+str(hex(hiAddrByte))+" Lo:"+ str(hex(loAddrByte))
                        +" address:"+str(address)+" slot:"+str(slotId)
                        +" Status:"+str(hex(status)))
            # See if this 0xE7 message is for a device in the trolleyRoster that sent a slot request
            trolley = trolleyRoster.findByAddress(address)
            if trolley and trolley.slotRequestSent:
                if Messenger.bTrace : logger.info("Trolley: "+str(address)+" SlotId:"+str(slotId)+" Status:"+str(status))
                # Per the LocoNet specs, check the D5 & D4 bits of the STATUS1 byte to determine the state of the slot
                # 11=IN_USE, 10=IDLE, 01=COMMON, 00=FREE SLOT and respond
                if ((status >> 4) & 0x03) < 3: # if status is IDLE, COMMON, or FREE
                    if trolley.slotId is None: 
                        if Messenger.bTrace : logger.info("Trolley: "+str(address)+" Slot was IDLE, COMMON, or FREE")
                        self.setSlotInUse(slotId) # Set the slot to IN-USE
                        trolley.slotId = slotId
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
                        if Messenger.bTrace : logger.info("Trolley: "+str(address)+" Slot was IDLE, COMMON, or FREE")
                        logger.info("Trolley %s SlotId = %s - STRANGE CONDITION",str(address), str(slotId))
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
                    logger.info("Trolley %s SlotId = %s - SLOT WAS ALREADY ASSIGNED",str(address), str(slotId))
                    self.writeSlotData(ARGS)  # Write back the slot data with speed = 0
                    #trolley.ringBell()
                    #trolley.blinkOn()
            else:
                logger.info("E7 Opcode Received - But no trolley defined")
            
                    
                
                    
        ######################################################################################
        ## only listen for OPC_INPUT_REP message from trolley BODs (0xB2) going active (hi) ##
        ######################################################################################
        #if (msg.getOpCode() == 178) and ((msg.getElement(2) & 0x10) == 0x10) :
        #    eventAddr = msg.sensorAddr() + 1
        #    if self.sTrace : print "== eventAddr = " + str(eventAddr)
        #checkAllTrolleyMovement(trolleyRoster, layoutMap)
        #event = simulateAllMovement(trolleyRoster,layoutMap)
        #if event: processBlockEvent(trolleyRoster, layoutMap, event)

lnListen = Messenger() #create and start LocoNet listener
##jmri.jmrix.loconet.LnTrafficController.instance().addLocoNetListener(0xFF, lnListen)
if jmriFlag: 
    try:
            jmri.InstanceManager.getList(jmri.jmrix.loconet.LocoNetSystemConnectionMemo).get(0).getLnTrafficController().addLocoNetListener(0xFF, lnListen)
            if Messenger.sTrace : logger.warn("Created JMRI.addLocoNetListener")
    except:
            if Messenger.sTrace : logger.warn("Skipping JMRI.addLocoNetListener")
            pass

