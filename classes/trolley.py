'''
Created on Nov 18, 2016
@author: ttb
'''
import sys
import time
import datetime
import logging
from classes.messengerFacade import Messenger

logger = logging.getLogger(__name__)



class Trolley(object):
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
    #eventQueue = Queue()
    msg = Messenger()
    #interruptableSleep = Event()
    
    def __init__(self, blockMap, address=9999, maxSpeed=0, currentPosition=0):
        """Return a Trolley object whose id is *id* and starting position and next 
        position are the 0th and 1st blocks if not provided.  Priority should reflect the 
        order of the trolley's on the Layout."""
        self.priority = self.deviceCount
        Trolley.deviceCount += 1
        
        self.address = address
        isLong = True if self.address > 100 else False
        self.speed = 0
        self.maxSpeed = maxSpeed
        # Check that the position requested is defined otherwise throw an exception
        currentBlock = blockMap.findBlockByAddress(currentPosition)
        if currentBlock == None:
            logger.error( "Exception: Unable to initialize trolley at unregistered block: %s", str(currentPosition) )
            sys.exit( "Exception: Unable to initialize trolley at unregistered block: " + str(currentPosition) )
        # Set the requested block position to occupied
        currentBlock.set_blockOccupied()
        # Go ahead and set the current and next blocks for this trolley
        self.currentPosition = currentBlock
        self.nextPosition = self.currentPosition.next
        self.next = None
        self.stopTime = datetime.datetime.now()
        self.startTime = None
        self.slotId = None
        self.slotRequestSent = None
        #print "Going to add throttle for address: ", self.address, "isLong:", isLong
        #self.throttle = Trolley.msg.requestThrottle(self.address, isLong, self.throttleWaitTime)  # address, long address = true
        #print "Return from getThrottle"
        #self.slotId = self.throttle.getLocoNetSlot()\
        #self.slotRequestSent = Trolley.msg.requestSlot(address)
        #logger.info("Trolley SlotRequestSent=%s", self.slotRequestSent)
        self.lastStatusTime=datetime.datetime.now()
        #while self.slotId is None:
        #    logger.info("Waiting for SlotId assignment on Trolley: %s", self.address)
            #Trolley.interruptableSleep.wait(10)
        #   time.sleep(0.01)
        #self.slotId = None
        #Trolley.msg.setSlotInUse(self.slotId)
        #print "Returned from getThrottle"
        #if (self.throttle == None) :
        #    print "Couldn't assign throttle!"
        logger.info("Trolley Added: %s  in Block: %s at Slot: %s", self.address, self.currentPosition.address,self.slotId)
        

    @staticmethod
    def getMessageManager():
        return Trolley.msg


    @staticmethod
    def getEventQueue():
        return Trolley.eventQueue


    def setAddress(self, address=9999):
        """Set the Trolley's ID."""
        self.address = address


    # ****************
    # Set Slot INUSE *
    # ****************
    def setSlotId(self, slotId=None):
        """Set the Trolley's DCC SlotId."""
        logger.info("Set SlotId - Trolley: "+str(self.address)+" SlotId:"+str(slotId))
        self.slotId = slotId
        #Trolley.msg.setSlotInUse(slotId)
        

    def requestSlot(self,slotId):
        """Request the Trolley's DCC SlotId."""
        logger.info("Set SlotId - Trolley: "+str(self.address)+" SlotId:"+str(slotId))
        #self.slotId = deviceID
        Trolley.msg.requestSlot(slotId)
        self.setSpeed(0)


    # ***************************************
    # Free Trolley Slot (Dispatch Trolleys) *
    # ***************************************
    def freeSlot(self) :
        self.setSpeed(0) #stop trolley
        Trolley.msg.freeSlot(self.slotId)
        self.slotId = None
        return


    # ************************
    # Emergency stop trolley *
    # ************************
    def eStop(self) :
        Trolley.msg.eStop(self.slotId)
        self.setSpeed(0)
        self.stopTime = datetime.datetime.now()
        return


    # *******************************************************
    def slowStop(self):
        self.setSpeed(int(self.maxSpeed * 0.5)) #set speed to 50% of max
        time.sleep(0.5) #wait 500 milliseconds
        self.setSpeed(int(self.maxSpeed * 0.25)) #set speed to 25% of max
        time.sleep(0.5) #wait 500 milliseconds
        self.eStop() #hard stop now
        time.sleep(0.5) #wait half a second after after stop, then ring bell
        self.ringBell()
        self.stopTime = datetime.datetime.now()
        #if self.tTrace: scrollArea.setText(scrollArea.getText() + "slot " + str(self.slotId) + " trolley stopped\n")
        return
    

    # *******************************************************
    def fullSpeed(self):
        self.ringBell()    
        self.setSpeed(self.maxSpeed)
        return
    

    # *********************************************
    # Ring the trolley bell before start and stop *
    # *********************************************
    def ringBell(self) :
        Trolley.msg.ringBell(self.slotId)
        return


    # **************************
    # Turn light OFF *
    # **************************
    def lightOff(self) :
        Trolley.msg.lightOff(self.slotId)
        return
    
    
    # **************************
    # Turn light ON *
    # **************************
    def lightOn(self) :
        Trolley.msg.lightOn(self.slotId)
        return
    
    
    # **************************
    # Blink light and leave ON *
    # **************************
    def blinkOn(self) :
        logger.debug("Blink Lights for Trolley: %s", self.address)
        count = 3
        while (count > 0) :
            count -= 1
            time.sleep(0.5) #wait half sec before toggling
            self.lightOff()
            time.sleep(0.5) #wait half sec before toggling
            self.lightOn()
            return
    

    def setCurrentPosition(self, currentPosition=-1):
        """Set the Trolley's current position. Note that by setting the current position
        we are implicitly setting the next position"""
        self.currentPosition = currentPosition
#         if self.currentPosition > max(self.blockMap):
#             self.currentPosition = -1
        

    def setSpeed(self, speed=0):
        Trolley.msg.setSpeed(self.slotId, speed)
        if self.speed == 0 and speed > 0: self.startTime = datetime.datetime.now()
        if speed == 0: self.stopTime = datetime.datetime.now()
        self.speed = speed
        return


    def advance(self, trolleyRoster, blockMap):
        logger.debug("Advancing Trolley: %s", self.address)
        lastBlock = self.currentPosition
        self.currentPosition = self.nextPosition
        self.nextPosition = self.currentPosition.next
        self.currentPosition.set_blockOccupied()
        self.stopTime = datetime.datetime.now()
        self.startTime = datetime.datetime.now()
        if trolleyRoster.findByCurrentBlock(lastBlock.address) == None:
            lastBlock.set_blockClear()
        return                
        

#     def move(self, layoutLength):
#         print ""
#         print "MOVE:",self.address,self.currentPosition,self.nextPosition
#         self.currentPosition += 1
#         if self.currentPosition >= layoutLength:
#             self.currentPosition = 0
#         self.nextPosition = self.currentPosition + 1
#         if self.nextPosition >= layoutLength:
#             self.nextPosition = 0
#         print "MOVE:",self.address,self.currentPosition,self.nextPosition
    

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
            
