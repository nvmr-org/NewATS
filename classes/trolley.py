'''
Created on Nov 18, 2016
@author: ttb
'''
import sys
import time
import datetime
from classes.messenger import Messenger

import jmri
import java


msg = Messenger()

class Trolley(jmri.jmrit.automat.AbstractAutomaton):
    """A trolley object that consists of the following properties:

    Attributes:
        address: The DCC address of the trolley object.
        speed: The speed of the trolley, non-zero indicates it is moving.
        currentPosition:  This indicates the block that the trolley is currently in.
        nextPosition: This should always be currentPosition + 1.
    """
    #global layoutLength
    
    deviceCount = 0
    throttleWaitTime = 10    
    
    def __init__(self, blockMap, address=9999, maxSpeed=0, currentPosition=0):
        """Return a Trolley object whose id is *id* and starting position and next 
        position are the 0th and 1st blocks if not provided.  Priority should reflect the 
        order of the trolley's on the Layout."""
        self.priority = self.deviceCount
        Trolley.deviceCount += 1
        
        self.address = address
        isLong = True if self.address > 100 else False
        self.speed = 0
        self.bfSent = False
        self.maxSpeed = maxSpeed
        # Check that the position requested is defined otherwise throw an exception
        currentBlock = blockMap.findBlockByAddress(currentPosition)
        if currentBlock == None:
            sys.exit( "Exception: Unable to initialize trolley at unregistered block: " + str(currentPosition) )
        # Set the requested block position to occupied
        currentBlock.set_blockOccupied()
        # Go ahead and set the current and next blocks for this trolley
        self.currentPosition = currentBlock
        self.nextPosition = self.currentPosition.next
        self.next = None
        self.stopTime = datetime.datetime.now()
        print "Going to add throttle for address: ", self.address, "type:", isLong
        self.throttle = self.getThrottle(self.address, isLong, self.throttleWaitTime)  # address, long address = true
        print "Return from getThrottle"
        #self.slotId = self.throttle.getLocoNetSlot()
        print "Returned from getThrottle"
        if (self.throttle == None) :
            print "Couldn't assign throttle!"
        print "Trolley Added: ", self.address, " in Block:", self.currentPosition.address
        

    def setAddress(self, address=9999):
        """Set the Trolley's ID."""
        self.address = address
        
        
    def setSlotId(self, slotId=-1):
        """Set the Trolley's DCC SlotId."""
        self.slotId = slotId
        # ****************
        # Set Slot INUSE *
        # ****************
        msgLength = 4
        opcode = 0xBA #OPC_MOVE_SLOTS
        ARGS = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = slotId
        ARGS[2] = slotId
        msg.sendLnMsg(msgLength,opcode,ARGS)
        
        
    # ***************************************
    # Free Trolley Slot (Dispatch Trolleys) *
    # ***************************************
    def freeSlot(self) :
        global ARGS
        self.setSpeed(0) #stop trolley
        msgLength = 4
        opcode = 0xB5 #OPC_SLOT_STAT1
        ARGS = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = self.slotId
        ARGS[2] = 0x13 #update status to Not Consisted, Common slot
        msg.sendLnMsg(msgLength,opcode,ARGS)
        if msg.sTrace : print "sent Slot Not Consisted & Common " + str(hex(opcode))
        msgLength = 4
        opcode = 0xBA #OPC_MOVE_SLOTS
        ARGS = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = self.slotId
        ARGS[2] = 0x00 #mark slot as DISPATCHED
        msg.sendLnMsg(msgLength,opcode,ARGS)
        if msg.sTrace : print "sent Slot Dispatch " + str(hex(opcode))
        self.updateSlot() #sets slot to being FREE
        self.slotId = -1
        return

# *******************************************************
    def requestSlot(self,deviceID) : #sends 0xBF with loco address
        #global ARGS
        #global hiAddrByte
        #global loAddrByte
        #global BFsent
        #global noSlotID
        #global lastDeviceID
    
        if msg.iTrace : print "==>>entering requestSlot"
        if msg.bTrace : print "requested slot = " + str(deviceID)
        msg.noSlotID = True
        msg.lastDeviceID = deviceID
        msg.dtxAddress = int(deviceID)    # get address from entry field for LocoNet
        msg.hiAddrByte = msg.dtxAddress - ((msg.dtxAddress / 128) * 128) #most significant address byte
        msg.loAddrByte = msg.dtxAddress / 128 #least significant address byte
        print "dtxAddress:", msg.dtxAddress, " hiAddrByte:", msg.hiAddrByte, "loAddrByte:", msg.loAddrByte
        #msg.prepLnAddr(deviceID)
        if msg.bTrace : print "prep return = " +hex(msg.hiAddrByte) + " " + hex(msg.loAddrByte)
        #request Loco data slot
        msgLength = 4
        opcode = 0xBF #OPC_LOCO_ADR request current slot assigned, if not create slot
        ARGS = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = msg.loAddrByte
        ARGS[2] = msg.hiAddrByte
        msg.sendLnMsg(msgLength,opcode,ARGS)
        self.bfSent = True #turn on to allow E7 response to be read for slotID (flag set must be after send!)
        if msg.sTrace : print "sent Slot Request " + str(hex(opcode))
        if msg.oTrace : print "<<==exiting requestSlot"
        return
        

    # *******************
    # Update Slot STAT1 *
    # *******************
    def updateSlot(self) :
        msgLength = 4
        opcode = 0xB5 #OPC_SLOT_STAT1
        ARGS = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = self.slotId
        ARGS[2] = 0x03
        msg.sendLnMsg(msgLength,opcode,ARGS)
        if msg.sTrace : print "sent Slot Stat1 Update " + str(hex(opcode))
        return
    

    # ************************
    # Emergency stop trolley *
    # ************************
    def eStop(self) :
        msgLength = 4
        opcode = 0xA0 #OPC_LOCO_SPD
        ARGS = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = self.slotId
        ARGS[2] = 0x01
        msg.sendLnMsg(msgLength,opcode,ARGS)
        if msg.sTrace : print "sent Estop " + str(hex(opcode))
        #self.setSpeed(0)
        #self.stopTime = datetime.datetime.now()
        return

    # *******************************************************
    def slowStop(self):
        self.setSpeed(int(self.maxSpeed * 0.5)) #set speed to 50% of max
        time.sleep(0.5) #wait 500 milliseconds
        self.setSpeed(int(self.maxSpeed * 0.25)) #set speed to 25% of max
        time.sleep(0.5) #wait 500 milliseconds
        self.self.eStop() #hard stop now
        time.sleep(0.5) #wait half a second after after stop, then ring bell
        self.ringBell()
        self.stopTime = datetime.datetime.now()
        #if self.tTrace: scrollArea.setText(scrollArea.getText() + "slot " + str(self.slotId) + " trolley stopped\n")
        return
    
    # *******************************************************
    def fullSpeed(self):
        #global slotID
        self.ringBell()    
        #self.setSpeed(self.maxSpeed) #set speed to 50
        ####time.sleep(3.0) #wait 3 secs after ringing bell and then go
        #if self.tTrace: scrollArea.setText(scrollArea.getText() + "slot " + str(slotID) + " trolley running\n")
        # turn on whistle, set direction to forward, set speed
        self.setSpeed(self.maxSpeed)
        return
    
    # *********************************************
    # Ring the trolley bell before start and stop *
    # *********************************************
    def ringBell(self) :
        #print "Ring Bell for Trolley:", self.address, "Throttle:", self.throttle
        #if self.throttle == None: return
        ringBell 1st time by setting F1 = ON
        msgLength = 4
        opcode = 0xA1 #OPC_LOCO_DIRF
        ARGS = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = self.slotId
        ARGS[2] = 0x11 #ON with direction forward and light ON
        msg.sendLnMsg(msgLength,opcode,ARGS)
        time.sleep(1) #wait 1 sec before toggling other way
        ringBell 2nd time by setting F1 = OFF
        msgLength = 4
        opcode = 0xA1 #OPC_LOCO_DIRF
        ARGS = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = self.slotId
        ARGS[2] = 0x10 #OFF with direction forward and light ON
        msg.sendLnMsg(msgLength,opcode,ARGS)
        if msg.sTrace : print "sent ring bell " + str(hex(opcode))
        time.sleep(3) #wait 3 sec before returning
        #self.throttle.setF1(True)     # turn on bell
        #self.waitMsec(1000)           # wait for 1 seconds
        #self.throttle.setF1(False)    # turn off bell
        #self.waitMsec(1000)           # wait for 1 second
        return

    # **************************
    # Turn light OFF *
    # **************************
    def lightOff(self) :
        #print "Lights Off for Trolley:", self.address, "Throttle:", self.throttle
        #if self.throttle == None: return
        msgLength = 4
        opcode = 0xA1 #OPC_LOCO_DIRF
        ARGS = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = self.slotId
        ARGS[2] = 0x00 #light OFF, direction forward
        time.sleep(1.0) #wait 1 second before sending in case decoder is processing a previous command
        msg.sendLnMsg(msgLength,opcode,ARGS)
        if msg.sTrace : print "sent light OFF " + str(hex(opcode))
        time.sleep(1.0) #wait 1 second before returning to let decoder finish processing this command
        #self.throttle.setF0(False)    # turn off light
        #self.waitMsec(1000)           # wait for 1 second
        return
    
    
    # **************************
    # Turn light ON *
    # **************************
    def lightOn(self) :
        #print "Lights On for Trolley:", self.address, "Throttle:", self.throttle
        #if self.throttle == None: return
        msgLength = 4
        opcode = 0xA1 #OPC_LOCO_DIRF
        ARGS = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = self.slotId
        ARGS[2] = 0x00 #light OFF, direction forward
        time.sleep(1.0) #wait 1 second before sending in case decoder is processing a previous command
        msg.sendLnMsg(msgLength,opcode,ARGS)
        if msg.sTrace : print "sent light OFF " + str(hex(opcode))
        #time.sleep(1.0) #wait 1 second before returning to let decoder finish processing this command
        #self.throttle.setF0(True)    # turn on light
        #self.waitMsec(1000)           # wait for 1 second
        return
    
    
    # **************************
    # Blink light and leave ON *
    # **************************
    def blinkOn(self) :
        print "Blink Lights for Trolley:", self.address, "Throttle:", self.throttle
        if self.throttle == None: return
        count = 5
        while (count > 0) :
            count -= 1
            time.sleep(0.5) #wait half sec before toggling
            #msgLength = 4
            #opcode = 0xA1 #OPC_LOCO_DIRF
            #ARGS[1] = self.slotId
            #ARGS[2] = 0x00 #light OFF, direction forward
            #msg.sendLnMsg(msgLength,opcode,ARGS)
            self.lightOff()
            time.sleep(0.5) #wait half sec before toggling
            #msgLength = 4
            #opcode = 0xA1 #OPC_LOCO_DIRF
            #ARGS[1] = self.slotId
            #ARGS[2] = 0x10 #light ON, direction forward
            #msg.sendLnMsg(msgLength,opcode,ARGS)
            self.lightOn()
            #if msg.sTrace : print "sent light ON/OFF " + str(hex(opcode))
            return
    

    def setCurrentPosition(self, currentPosition=-1):
        """Set the Trolley's current position. Note that by setting the current position
        we are implicitly setting the next position"""
        self.currentPosition = currentPosition
#         if self.currentPosition > max(self.blockMap):
#             self.currentPosition = -1
        
    def setSpeed(self, speed=0):
        #print "Setting Trolley:", self.address, "Speed:", speed, "Throttle:", self.throttle
        #if self.throttle == None: return
        msgLength = 4
        opcode = 0xA0 #OPC_LOCO_SPD
        ARGS = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        ARGS[1] = self.slotId
        ARGS[2] = hex(speed)
        msg.sendLnMsg(msgLength,opcode,ARGS)
        if msg.sTrace : print "sent Set Speed " + str(hex(opcode))
        #self.throttle.setSpeedSetting(speed)
        #self.speed = speed
        if self.speed == 0: self.currentPosition.stopTime = datetime.datetime.now()
        return


    def advance(self, trolleyRoster, blockMap):
        lastBlock = self.currentPosition
        self.currentPosition = self.nextPosition
        self.nextPosition = blockMap.findNextBlockByAddress(self.currentPosition.address)
        self.currentPosition.set_blockOccupied()
        if trolleyRoster.findByCurrentBlock(lastBlock.address) == None:
            lastBlock.set_blockClear()
        return                
        
    def move(self, layoutLength):
        print ""
        print "MOVE:",self.address,self.currentPosition,self.nextPosition
        self.currentPosition += 1
        if self.currentPosition >= layoutLength:
            self.currentPosition = 0
        self.nextPosition = self.currentPosition + 1
        if self.nextPosition >= layoutLength:
            self.nextPosition = 0
        print "MOVE:",self.address,self.currentPosition,self.nextPosition
    
    def getAddress(self):
        return self.address

    def getSpeed(self):
        return self.speed
        
    def getRosterPosition(self):
        return self.rosterPosition
    
    def getCurrentPosition(self):
        return self.currentPosition
    
    def getNextPosition(self):
        return self.nextPosition
    
    def updatePosition(self):
        if self.speed > 0:
            self.set_currentPosition(self.currentPosition+1)
            

 
