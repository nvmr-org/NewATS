import time
import logging

logger= logging.getLogger("NewATS."+__name__)

class Messenger(object):
    
    def __init__(self, trolleyRoster=None, layoutMap=None):
        self.iTrace = False #turn enter (In) trace print off/on
        self.bTrace = False #turn all (Between) enter and exit traces print off/on 
        self.oTrace = False #turn exit (Out) trace print off/on
        self.dTrace = False #turn limited section Debug trace print off/on
        self.lTrace = False #turn msgListener incoming opcode print off/on
        self.tTrace = False #turn trolley array status print off/on
        self.sTrace = False #turn sequence view of LocoNet messages off/on
        self.debounce = False #turn track contact loss debounce off/on
        self.eventQueue = None
        self.trolleyRoster=trolleyRoster
        self.layoutMap = layoutMap


    # **********************
    # Set Event Queue for Simulations
    # **********************
    def createEventQueue(self, eventQueue = None):
        self.eventQueue = eventQueue
        return

    
    # **********************
    # Send LocoNet Message *
    # **********************
    def sendLnMsg(self,msgLength,opcode,ARGS) :
        # format and send the specific LocoNet message
        # send up to 16 bytes in the message - includes checksum
        if self.iTrace : print "==>>entering sendLnMsg -->"
        if self.bTrace : print "MsgLen:",msgLength, " OpCode:", opcode, "ARGS:",ARGS
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
        if self.sTrace : print "sent Estop " + str(hex(opcode))
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
        if self.sTrace : print "sent ring bell " + str(hex(opcode))
        time.sleep(3) #wait 3 sec before returning
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
        time.sleep(1.0) #wait 1 second before sending in case decoder is processing a previous command
        self.sendLnMsg(msgLength,opcode,ARGS)
        if self.sTrace : print "sent light OFF " + str(hex(opcode))
        time.sleep(1.0) #wait 1 second before returning to let decoder finish processing this command
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
        time.sleep(1.0) #wait 1 second before sending in case decoder is processing a previous command
        self.sendLnMsg(msgLength,opcode,ARGS)
        if self.sTrace : print "sent light OFF " + str(hex(opcode))
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
        ARGS[2] = hex(speed)
        self.sendLnMsg(msgLength,opcode,ARGS)
        if self.sTrace : print "sent Set Speed " + str(hex(opcode))
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
        if self.sTrace : print "sent Slot Not Consisted & Common " + str(hex(opcode))
        msgLength = 4
        opcode = 0xBA #OPC_MOVE_SLOTS
        ARGS = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = slotId
        ARGS[2] = 0x00 #mark slot as DISPATCHED
        self.sendLnMsg(msgLength,opcode,ARGS)
        if self.sTrace : print "sent Slot Dispatch " + str(hex(opcode))
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
        if self.sTrace : print "sent Slot Stat1 Update " + str(hex(opcode))
        return
    

    # *******************************************************
    # Request Trolley Slot (acquire Trolleys)
    # *******************************************************
    def requestSlot(self,deviceID) : #sends 0xBF with loco address
        if self.iTrace : print "==>>entering requestSlot"
        if self.bTrace : print "requested slot = " + str(deviceID)
        self.noSlotID = True
        self.lastDeviceID = deviceID
        self.dtxAddress = int(deviceID)    # get address from entry field for LocoNet
        self.hiAddrByte = self.dtxAddress - ((self.dtxAddress / 128) * 128) #most significant address byte
        self.loAddrByte = self.dtxAddress / 128 #least significant address byte
        if self.bTrace : print "dtxAddress:", self.dtxAddress, " hiAddrByte:", self.hiAddrByte, "loAddrByte:", self.loAddrByte
        #msg.prepLnAddr(deviceID)
        if self.bTrace : print "prep return = " +hex(self.hiAddrByte) + " " + hex(self.loAddrByte)
        #request Loco data slot
        msgLength = 4
        opcode = 0xBF #OPC_LOCO_ADR request current slot assigned, if not create slot
        ARGS = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = self.loAddrByte
        ARGS[2] = self.hiAddrByte
        self.sendLnMsg(msgLength,opcode,ARGS)
        self.bfSent = True #turn on to allow E7 response to be read for slotID (flag set must be after send!)
        if self.sTrace : print "sent Slot Request " + str(hex(opcode))
        if self.oTrace : print "<<==exiting requestSlot"
        return
        

    def setSlotId(self, slotId):
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
        if self.sTrace : print "sent Slot INUSE " + str(hex(opcode))

        
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
        if self.sTrace : print "sent Slot Data Update " + str(hex(opcode))
        return
            

