'''
Created on Nov 18, 2016
@author: ttb
'''
import sys
import time
import datetime
import logging

logger = logging.getLogger("ATS."+__name__)
logger.setLevel(logging.INFO)
thisFuncName = lambda n=0: sys._getframe(n + 1).f_code.co_name

class Trolley(object):
    """A trolley object that consists of the following properties:

    Attributes:
        address: The DCC address of the trolley object.
        speed: The speed of the trolley, non-zero indicates it is moving.
        currentPosition:  This indicates the block that the trolley is currently in.
        nextPosition: This should always be currentPosition + 1.
    """
    #global layoutLength
    automationManager = None
    THROTTLE_REFRESH_TIME = 2 # Seconds between status updates for throttles on a slot
    THROTTLE_WAIT_TIME = 5
    MOMENTUM_DELAY_SEC = 2 # Seconds to allows for momentum to be considered still moving


    msg = None

    def __init__(self, blockMap, address=9999, maxSpeed=0, soundEnabled=True, currentPosition=0):
        """Return a Trolley object whose id is *id* and starting position and next 
        position are the 0th and 1st blocks if not provided.  Priority should reflect the 
        order of the trolley's on the Layout."""

        logger.trace("Entering %s.%s", __name__, thisFuncName())
        self.address = address
        self.speed = 0              # Current Speed
        self.maxSpeed = maxSpeed    # Speed when running
        self.soundEnabled = soundEnabled
        # Check that the position requested is defined otherwise throw an exception
        currentBlock = blockMap.findBlockByAddress(currentPosition)
        if currentBlock == None:
            logger.error( "Exception: Unable to initialize trolley at unregistered block: %s", str(currentPosition) )
            raise ValueError
            #sys.exit( "Exception: Unable to initialize trolley at unregistered block: " + str(currentPosition) )
        # Set the requested block position to occupied
        currentBlock.set_blockOccupied()
        # Go ahead and set the current and next blocks for this trolley
        self.currentPosition = currentBlock
        self.nextPosition = self.currentPosition.next
        self.next = None
        self.stopTime = datetime.datetime.now()     # Time when unit last stopped
        self.startTime = None                       # Time when unit last started
        self.lastAlertTime = datetime.datetime.now()        # Time when console alert was generated
        self.lastAudibleAlertTime = datetime.datetime.now() # Time when audible alert was generated
        self.slotId = None
        self.slotRequestSent = True
        self.speedFactor = 1.0  # Default to one inch per second for calculating overdue
        #self.slotId = self.throttle.getLocoNetSlot()\
        #self.slotRequestSent = Trolley.msg.requestSlot(address)
        #logger.info("Trolley SlotRequestSent=%s", self.slotRequestSent)
        # Keep track of when the last throttle message occurred so we can refresh the throttle
        self.throttleLastMsgTime=datetime.datetime.now()

        #logger.info("Going to add throttle for address: %s", self.address)
        self.throttle = None
        self.slotId = None
        self.slotRequestSent = None
        logger.info("Trolley Added: %s  in Block: %s at Slot: %s", self.address, self.currentPosition.address,self.slotId)


    @staticmethod
    def getMessageManager():
        return Trolley.msg


    @staticmethod
    def setMessageManager(messageManager):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        Trolley.msg = messageManager


    @staticmethod
    def setAutomationManager(automationObject):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        Trolley.automationManager = automationObject
        logger.debug("%s.%s - Automation Object: %s",__name__, thisFuncName(),str(Trolley.automationManager))
        logger.debug("Exiting %s.%s", __name__, thisFuncName())
        return


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
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        """Set the Trolley's DCC SlotId."""
        logger.info("Set SlotId - Trolley: "+str(self.address)+" SlotId:"+str(slotId))
        self.slotId = slotId
        if self.slotId:
            if self.soundEnabled: 
                self.ringBell()
            else:
                self.blinkOn()


    # ****************
    # Request Slot   *
    # ****************
    def requestSlot(self,slotId):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        """Request the Trolley's DCC SlotId."""
        logger.info("Set SlotId - Trolley: "+str(self.address)+" SlotId:"+str(slotId))
        #Trolley.msg.requestSlot(slotId)
        self.setThrottleLastMsgTime()
        self.setSpeed(0)


    # ***************************************
    # Free Trolley Slot (Dispatch Trolleys) *
    # ***************************************
    def freeSlot(self) :
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        self.setSpeed(0) #stop trolley
        #self.slotRequestSent=False
        time.sleep(0.5) #wait 500 milliseconds
        self.slotRequestSent = None
        #Trolley.msg.freeSlot(self.slotId)
        self.setThrottleLastMsgTime()
        self.slotId = None
        return


    # ************************
    # Emergency stop trolley *
    # ************************
    def eStop(self) :
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        #Trolley.msg.eStop(self.slotId)
        self.setSpeed(0)
        self.stopTime = datetime.datetime.now()
        self.speedFactor = 1.0
        return


    # *******************************************************
    def slowStop(self):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        #self.setSpeed(int(self.maxSpeed * 0.75)) #set speed to 50% of max
        #time.sleep(0.25) #wait 500 milliseconds
        #self.setSpeed(int(self.maxSpeed * 0.5)) #set speed to 50% of max
        #time.sleep(0.25) #wait 500 milliseconds
        #self.setSpeed(int(self.maxSpeed * 0.25)) #set speed to 25% of max
        #time.sleep(0.25) #wait 500 milliseconds
        #self.setSpeed(int(self.maxSpeed * 0.0)) #set speed to 25% of max
        #time.sleep(0.25) #wait half a second after after stop, then ring bell
        self.setSpeed(0)
        self.ringBell()
        self.stopTime = datetime.datetime.now()
        #if self.tTrace: scrollArea.setText(scrollArea.getText() + "slot " + str(self.slotId) + " trolley stopped\n")
        return


    # *******************************************************
    def fullSpeed(self):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        self.ringBell()
        self.setSpeed(self.maxSpeed)
        return


    # *********************************************
    # Ring the trolley bell before start and stop *
    # *********************************************
    def ringBell(self):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        #if self.soundEnabled: Trolley.msg.ringBell(self.slotId)
        if self.soundEnabled and self.throttle: self.throttle.setF2Momentary(True)
        return


    # **************************
    # Turn light OFF *
    # **************************
    def lightOff(self):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        #Trolley.msg.lightOff(self.slotId)
        if self.throttle: self.throttle.setF0(False)
        return


    # **************************
    # Turn light ON *
    # **************************
    def lightOn(self):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        #Trolley.msg.lightOn(self.slotId)
        if self.throttle: self.throttle.setF0(True)
        return


    # **************************
    # Blink light and leave ON *
    # **************************
    def blinkOn(self) :
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        logger.debug("Blink Lights for Trolley: %s", self.address)
        count = 3
        while (count > 0) :
            count -= 1
            time.sleep(0.5) #wait half sec before toggling
            self.lightOff()
            time.sleep(0.5) #wait half sec before toggling
            self.lightOn()
            return


    def setDebugLevel(self,state):
        logger.setLevel(logging.DEBUG if state else logging.INFO)
        logger.info("Logger:%s Now at Level: %s", __name__, str(logger.level))
        for handler in logging.getLogger("ATS").handlers:
            handler.setLevel(logging.DEBUG)
            logger.info("Handler %s Logger:%s Now at Level: %s", handler, __name__, str(handler.level))
        logger.debug("%s.%s - Logger:%s - Set Debug Flag:%s", __name__, thisFuncName(),str(logger),str(state))


    def getDebugLevel(self):
        return logger.level


    def setCurrentPosition(self, currentPosition=-1):
        logger.trace("Entering %s.%s %s ", __name__, thisFuncName(), currentPosition)
        """Set the Trolley's current position. Note that by setting the current position
        we are implicitly setting the next position"""
        self.currentPosition = currentPosition
#         if self.currentPosition > max(self.blockMap):
#             self.currentPosition = -1


    # *******************************************************
    def setSpeed(self, speed=0):
        logger.trace("Entering %s.%s %s", __name__, thisFuncName(), speed)
        if not self.throttle: return
        if speed == 0 and self.speed > 0:
            logger.debug("Trolley %s - Updating Stop Time", self.address)
            self.stopTime = datetime.datetime.now() # Update the stop time if stopping
        #Trolley.msg.setSpeed(self.slotId, speed)
        #Trolley.msg.setSpeed(self.slotId, speed)  # Send a second time until we figure out why this is needed
        self.throttle.setSpeedSetting(float(speed)/128.0)
        self.setThrottleLastMsgTime()
        if self.speed == 0 and speed > 0:
            logger.debug("Trolley %s - Updating Start Time", self.address)
            self.startTime = datetime.datetime.now() # Update the start time if starting
        if self.speed != speed:
            logger.debug("Trolley %s - Speed Changed from %s to %s", self.address, self.speed, speed)
            self.speed = speed
        return


    def updateSpeedFactor(self, blockMap):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        travelTime = (datetime.datetime.now() - self.startTime).total_seconds()
        if travelTime > 1:
            realSpeedInBlock = self.currentPosition.length / travelTime
            historicalSpeed = self.speedFactor
            weightedSpeed = (historicalSpeed * (len(blockMap) - 1) + realSpeedInBlock ) / len(blockMap)
            self.speedFactor = weightedSpeed
            logger.debug("Trolley %s - TravelTime:%s RealSpeed:%s Historical:%s Weighted:%s blocks:%s",
                        self.address,travelTime, str("{:.2f}".format(realSpeedInBlock)),
                        str("{:.2f}".format(historicalSpeed)),str("{:.2f}".format(weightedSpeed)), len(blockMap))
        return


    def advance(self, trolleyRoster, blockMap):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        logger.debug("Trolley %s - Advancing to block %s", self.address, self.nextPosition.address)
        lastBlock = self.currentPosition
        self.updateSpeedFactor(blockMap)
        self.currentPosition = self.nextPosition
        self.nextPosition = self.currentPosition.next
        self.currentPosition.set_blockOccupied()
        self.stopTime = datetime.datetime.now()
        self.startTime = datetime.datetime.now()
        if trolleyRoster.findByCurrentBlock(lastBlock.address) == None:
            logger.debug("Trolley %s - Setting block %s to CLEAR", self.address, str(lastBlock.address))
            lastBlock.set_blockClear()
            if Trolley.automationManager.simulatorEnabled:
                Trolley.automationManager.simulateSingleBlockSensorUpdate(lastBlock)
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


    def isMoving(self):
        return self.speed > 0


    def wasMoving(self):
        speedIsZero = (self.speed == 0)
        timediff = (datetime.datetime.now() - self.stopTime).seconds
        stoppedLessThanMomentumTime = (timediff < Trolley.MOMENTUM_DELAY_SEC)
        return ( speedIsZero and stoppedLessThanMomentumTime )


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


    def getThrottleLastMsgTime(self):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        return self.throttleLastMsgTime


    def setThrottleLastMsgTime(self):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        self.throttleLastMsgTime=datetime.datetime.now()
