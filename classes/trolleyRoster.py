'''
Created on Nov 18, 2016

@author: ttb
'''
import sys
import logging
import datetime
from blockMap import BlockMap
#from classes.messengerFacade import Messenger

logger = logging.getLogger(__name__)
layoutMap = BlockMap()

class TrolleyRoster(object):
    """A TrolleyRoster object is essentially a linked list of trolley objects that 
       consists of the following additional properties:
         deviceCount: Total number of objects in the list
         first: a reference to the first trolley object in the list
         last: a reference to the last trolley object in the list
         
       Ideally trolleys are added to the list in positional order with their starting
       position.  There currently is no check on the positional ordering other than
       detection of multiple trolleys in a black at initialization.

    Attributes:
        address: The DCC address of the trolley object.
        speed: The speed of the trolley, non-zero indicates it is moving.
        currentPosition:  This indicates the block that the trolley is currently in.
        nextPosition: This should always be currentPosition + 1.
    """


    deviceCount = 0
    multipleDetectedInBlock = False
    #msg = Messenger()
    __instance = None  # Make sure there is only one version of the trolleyroster
    __allowRun = False
    
    def __init__(self, trolleyObjects=None):
        """Initialize the class"""
        super(TrolleyRoster, self).__init__()
        self.deviceCount += 1
        if trolleyObjects is not None:
            self._list = list(trolleyObjects)
            self.first = None
            self.last = None
            #self.next = trolleyObjects
        else:
            self._list = list()
            self.first = None
            self.last = None
            #self.next = None
        

    def __new__(cls, trolleyObjects=None): # __new__ always a class method
        if TrolleyRoster.__instance is None:
            TrolleyRoster.__instance = object.__new__(cls,trolleyObjects)
        return TrolleyRoster.__instance


    def __repr__(self):
        return "<{0} {1}>".format(self.__class__.__name__, self._list)
    

    def __len__(self):
        """List length"""
        return(len(self._list))
    

    def size(self):
        return(len(self._list))
    

    def __getitem__(self, ii):
        """Get a list item"""
        return self._list[ii]
    

    def __delitem__(self, ii):
        """Delete an item"""
        del self._list[ii]
        

    def __setitem__(self, ii, val):
        # optional: self._acl_check(val)
        self._list[ii] = val


    def __str__(self):
        return str(self._list)
    

    def insert(self, ii, val):
        # optional: self._acl_check(val)
        self._list.insert(len(self._list), val)
        if self.first is None:
            self.first = val
            self._list[ii].next = self._list[ii]
        else:
            self._list[ii-1].next=self._list[ii]
            self._list[ii].next=self.first
            self.last = val
            #self.next = self.first
            #self.next = self.first
        self.last = val
        

    def append(self, trolley):
        # if the block is currently occupied by another trolley set a flag before inserting
        #print 'TrolleyRoster.append'
        if self.findByAddress(trolley.address) != None:
            logger.error("Error: Attempt to register multiple trolleys to the same address: %s", trolley.address)
            sys.exit("Error: Attempt to register multiple trolleys to the same address:" + trolley.address)
        self.checkForMultipleTrolleysInOneBlock()
#         if self.findByCurrentBlock(trolley.currentPosition.address):
#             logger.warning('Warning: Multiple trolleys registered to the same block: %s', trolley.currentPosition.address)
#             logger.warning('Warning: Trolleys will depart in the order they were registered.')
#             self.multipleDetectedInBlock = True
        #print "Requesting Slot for Trolley:", trolley.address
        #trolley.requestSlot(trolley.address)
        self.insert(len(self._list), trolley)


    def checkForMultipleTrolleysInOneBlock(self):
        self.multipleDetectedInBlock = False
        for trolley in self._list:
            logger.debug("Trolley: %s   Find: %s", str(trolley.address), str(self.findByCurrentBlock(trolley.currentPosition.address).address))
            if self.findByCurrentBlock(trolley.currentPosition.address).address <> trolley.address:
                logger.warning('Warning: Multiple trolleys registered to the same block: %s', trolley.currentPosition.address)
                logger.warning('Warning: Trolleys will depart in the order they were registered.')
                self.multipleDetectedInBlock = True
                break


    def destroy(self):
        for trolley in self._list:
            trolley.freeSlot()
            logger.info('Trolley %s Stopped and Removed', trolley.address)


    def dump(self):
        print "**************"
        print "TrolleyRoster"
        print "**************"
        self.checkForMultipleTrolleysInOneBlock()
#         if self.multipleDetectedInBlock:
#             print 'Warning: Multiple trolleys registered to the same block. '
        print "Roster Size: ", self.size()
        print "MultipleState: ",self.multipleDetectedInBlock
        for trolley in self._list:
            print "Id:", trolley.priority, 
            print " Address:", trolley.address, 
            print " SlotID:", trolley.slotId,
            print " Speed:", trolley.speed,
            print " Current Position:", trolley.currentPosition.address, 
            print " Next Position:", trolley.nextPosition.address,
            print " Next Trolley:", self.getNextTrolley(trolley).address
            #print " Throttle:", trolley.throttle


    def getNextTrolleyAddress(self, val):
        return val.next.address


    def getNextTrolley(self, val):
        return val.next
        

    def findByCurrentBlock(self, currentPosition):
        for trolley in self._list:
            if trolley.currentPosition.address == currentPosition:
                return trolley
        #return find(lambda trolley: trolley.currentPosition == currentPosition, self._list)
        

    def findByAddress(self, address):
        for trolley in self._list:
            if trolley.address == address:
                return trolley
        return None
        #return find(lambda trolley: trolley.currentPosition == currentPosition, self._list)

            
    def findByNextBlock(self, nextPosition):
        for trolley in self._list:
            if trolley.nextPosition.address == nextPosition:
                return trolley
            

    def findByCurrentSegment(self, segment, blockMap):
        for trolley in self._list:
            for block in blockMap:
                if trolley.currentPosition.address == block.address and block.segment == segment:
                        return trolley


    def checkIfAllTrolleysAreRegistered(self):
        for trolley in self._list:
            if trolley.slotId is None:
                return False
        return True


    def registerOneTrolley(self):
        for trolley in self._list:
            if trolley.slotId: continue
            trolley.slotRequestSent = trolley.msg.requestSlot(trolley.address)
            logger.info("Trolley %s  SlotRequestSent=%s", trolley.address, trolley.slotRequestSent)
            break


    def checkAllTrolleyMovement(self, layoutMap):
        for trolley in self._list:
            if trolley.getSpeed() == 0:
                if self.checkIfTrolleyCanMove(trolley,layoutMap):
                    logger.info("Trolley: %s   Status: Not Moving (%s seconds) in block: %s",
                            trolley.address, (datetime.datetime.now() - trolley.stopTime).seconds, trolley.currentPosition.address)
                    logger.info("Trolley: %s   Action: Starting",trolley.address)
                    trolley.fullSpeed()
                    self.dump()
            else:
                if self.checkIfTrolleyShouldStop(trolley,layoutMap):
                    logger.info("Trolley: %s   Status: Is Running (%s seconds) in block: %s",
                            trolley.address, (datetime.datetime.now() - trolley.startTime).seconds, trolley.currentPosition.address)
                    logger.info("Trolley: %s   Action: Stopping",trolley.address)
                    trolley.slowStop()
                    self.dump()
    

    def checkIfTrolleyShouldStop(self,trolley,layoutMap):
        # If the next segment is occupied return false
        if layoutMap.isSegmentOccupied(trolley.nextPosition.segment) and trolley.currentPosition.segment <> trolley.nextPosition.segment: 
            logger.info("Trolley: %s   Alert: Next segment occupied", trolley.address)
            return True
        # If this trolley is in a block that requires a stop and has not been stopped long enough return true
        if trolley.currentPosition.stopRequired:
            if not self.__checkRequiredStopTimeMet(trolley.stopTime, trolley.currentPosition.waitTime): 
                logger.info("Trolley: %s   Alert: Required stop time has not been met", trolley.address)
                return True
        # If this trolley is not the next one scheduled for the next block return true
        if trolley.address != self.findByNextBlock(trolley.nextPosition.address).address: 
            # The exception to this is if the next block is part of the current segment the trolley is already in
            if trolley.currentPosition.segment != trolley.nextPosition.segment:
                logger.info("Trolley: %s   Alert: Not the first trolley scheduled for Block %s", trolley.address, trolley.nextPosition.address)
                return True
            else:
                logger.info("Trolley: %s   Alert: Not the first trolley scheduled for Block %s - ******* CONTINUE CLEARANCE GRANTED", trolley.address, trolley.nextPosition.address)
            #return True
        #print "Reason: is allowed to move"
        return False
    

    def checkIfTrolleyCanMove(self, trolley, layoutMap):
        # If the slotId has not been set return false
        if trolley.slotId is None:
            logger.info("Trolley: %s   Alert: Slot Not Yet Set", trolley.address)
            return False
        # If the next segment is occupied return false
        if layoutMap.isSegmentOccupied(trolley.nextPosition.segment): 
            logger.debug("Trolley: %s   Alert: Next segment occupied", trolley.address)
            return False
        # If this trolley is in a block that requires a stop and has not been stopped long enough return false
        if trolley.currentPosition.stopRequired:
            if not self.__checkRequiredStopTimeMet(trolley.stopTime, trolley.currentPosition.waitTime): 
                logger.debug("Trolley: %s   Alert: Required stop time has not been met", trolley.address)
                return False
        # If this trolley is not the next one scheduled for the next block return false
        if trolley.address != self.findByNextBlock(trolley.nextPosition.address).address:
            # The exception to this is if the next block is part of the current segment the trolley is already in
            if trolley.currentPosition.segment != trolley.nextPosition.segment:
                logger.debug("Trolley: %s   Alert: Not the first trolley scheduled for Block %s", trolley.address, trolley.getNextPosition().address)
                return False
            else:
                logger.info("Trolley: %s   Alert: Not the first trolley scheduled for Block %s - ******* START CLEARANCE GRANTED", trolley.address, trolley.nextPosition.address)
        #print "Reason: is allowed to move"
        return True


    def __checkRequiredStopTimeMet(self,stopTime, waitTime):
        timeSinceStop = (datetime.datetime.now() - stopTime).seconds
        #logger.info("Required Stop Time Met = %s (TimeStopped: %s   waitTime: %s)", timeSinceStop > waitTime, timeSinceStop, waitTime)
        if timeSinceStop > waitTime: return True
        return False


    def processBlockEvent(self, sensorId):
        # We should only process sensors going HIGH or OCCUPIED
        # A sensor going high indicates that a trolley has moved into that block
        logger.info('Processing event for SensorID = %s', sensorId)
        # check if this event is associated with a trolley that is already in this block
        # if it is, then treat the event as a bouncy sensor reading
        if self.findByCurrentBlock(sensorId):
            logger.info('Bouncy sensor event for block: %s', sensorId)
            return
        # check if this event is associated with a trolley that is already in this segment
        # if it is, then us this trolley.  This give priority to a trolley that is 
        # already in a segment vs a new one entering the segment.
        eventSegmentId = layoutMap.findSegmentByAddress(sensorId)
        trolley = self.findByCurrentSegment(eventSegmentId, layoutMap)
        if trolley and trolley.getSpeed() > 0:
            # If we get here, this trolley was associated with this event
            logger.info('Trolley %s found in Segment: %s  for Block: %s',trolley.address , eventSegmentId, sensorId)
            # Move the trolley into the next block
            trolley.advance(self, layoutMap)
            # Check if the trolley should stop at this location
            if layoutMap.isSegmentOccupied(trolley.nextPosition):
                trolley.slowStop()
        else:
            trolley = self.findByNextBlock(sensorId)
            if trolley and trolley.getSpeed() > 0 :
                # If we get here, this trolley was associated with this event
                logger.info('Trolley %s found for block: %s',trolley.address , sensorId)
                # Move the trolley into the next block
                trolley.advance(self, layoutMap)
                # Check if the trolley should stop at this location
                if layoutMap.isSegmentOccupied(trolley.nextPosition):
                    trolley.slowStop()
        layoutMap.printBlocks(self)
        layoutMap.printSegments(self)
        self.dump()




