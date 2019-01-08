'''
Created on Nov 18, 2016

@author: ttb
'''
import sys
import logging
import datetime
#from classes.messengerFacade import Messenger

logger = logging.getLogger(__name__)

class TrolleyLogHandler(logging.StreamHandler):
    """ Not yet working - 
        Handler to redirect logging messages to the scroll text area in the application window
    """
    __outputMessageInfo = None
    def emit(self, record):
        if TrolleyLogHandler.__outputMessageInfo is not None:
            TrolleyLogHandler.__outputMessageInfo.append(str(record))


    def setMessageInfoOutput(self,output=None):
        self.__outputMessageInfo=output
        trolleyLogHandler = TrolleyLogHandler()
        logger.addHandler(trolleyLogHandler)


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
    __eTrace = False #turn ENTER (In) / EXIT (Out) trace print off/on
    __dTrace = False #turn limited section Debug trace print off/on
    __iTrace = False #turn msgListener INCOMING opcode print off/on
    __oTrace = False #turn sendLnMsg OUTGOING opcode messages off/on


    multipleDetectedInBlock = False
    #msg = Messenger()
    __instance = None  # Make sure there is only one version of the trolleyroster
    __allowRun = False
    __automationObject = None
    __outputRosterInfo = None
    __outputMessageInfo = None
    __layoutMap = None
    SECONDS_BETWEEN_AUDIBLE_ALERTS = 120

    def __init__(self, trolleyObjects=None, layoutMap=None):
        """Initialize the class"""
        super(TrolleyRoster, self).__init__()
        if trolleyObjects is not None:
            self._list = list(trolleyObjects)
            self.first = None
            self.last = None
            TrolleyRoster.__layoutMap = layoutMap
        else:
            self._list = list()
            self.first = None
            self.last = None
            TrolleyRoster.__layoutMap = layoutMap
        print("LayoutMap = "+str(TrolleyRoster.__layoutMap))

    def __new__(cls, trolleyObjects=None, layoutMap=None): # __new__ always a class method
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


    def delete(self,ii):
        if TrolleyRoster.__eTrace : logger.info("Enter TrolleyRoster.delete - "+str(ii))
        currentPosition = self._list[ii].currentPosition
        if ii > 0:
            self._list[ii-1].next = self._list[ii-1].next.next
            self.__delitem__(ii)
        else:
            self.__delitem__(ii)
        otherTrolleyInBlock = self.findByCurrentBlock(currentPosition.address)
        if otherTrolleyInBlock is None:
            if TrolleyRoster.__dTrace : logger.info("No other trolleys in block - setting clear")
            currentPosition.set_blockClear()


    def insert(self, ii, val):
        if TrolleyRoster.__eTrace : logger.info("Enter TrolleyRoster.insert")
        # optional: self._acl_check(val)
        self._list.insert(len(self._list), val)
        if self.first is None:
            self.first = val
            self._list[ii].next = self._list[ii]
        else:
            self._list[ii-1].next=self._list[ii]
            self._list[ii].next=self.first
            self.last = val
        self.last = val


    def append(self, trolley):
        if TrolleyRoster.__eTrace : logger.debug("Enter trolleyRoster.append")
        # if the block is currently occupied by another trolley set a flag before inserting
        if self.findByAddress(trolley.address) != None:
            logger.error("Error: Attempt to register multiple trolleys to the same address: %s", str(trolley.address))
            sys.exit("Error: Attempt to register multiple trolleys to the same address:" + str(trolley.address))
        self.checkForMultipleTrolleysInOneBlock()

        self.insert(len(self._list), trolley)


    def setDebugFlag(self,debugFlag,state):
        if debugFlag.lower() == 'etrace' : TrolleyRoster.__eTrace = state
        if debugFlag.lower() == 'dtrace' : TrolleyRoster.__dTrace = state
        return


    def setRosterInfoOutput(self,output=None):
        self.__outputRosterInfo=output


    def setMessageInfoOutput(self,output=None):
        self.__outputMessageInfo=output
        # Updating the Log Handler does not yet work
        #TrolleyLogHandler.__outputMessageInfo=output
        #trolleyLogHandler = TrolleyLogHandler()
        #print("Logger defined: %s", str(logger))
        #logger.addHandler(trolleyLogHandler)


    def setMessageAnnouncer(self,announcer=None):
        global audible
        audible=announcer


    def isTrolleyAddressValid(self,address):
        if address < 1 or address > 9999: return False
        return True


    def isTrolleyMaxSpeedValid(self,speed):
        if speed < 1 or speed > 99: return False
        return True


    def checkForMultipleTrolleysInOneBlock(self):
        if TrolleyRoster.__eTrace : logger.info("Enter trolleyRoster.checkForMultipleTrolleysInOneBlock")
        self.multipleDetectedInBlock = False
        for trolley in self._list:
            if self.findByCurrentBlock(trolley.currentPosition.address).address <> trolley.address:
                logger.warning('Warning: Multiple trolleys registered to the same block: %s', trolley.currentPosition.address)
                logger.warning('Warning: Trolleys will depart in the order they were registered.')
                self.multipleDetectedInBlock = True
        return self.multipleDetectedInBlock


    def destroy(self):
        if TrolleyRoster.__eTrace : logger.info("Enter trolleyRoster.destroy")
        for trolley in self._list:
            if TrolleyRoster.__dTrace : logger.info('Trolley: %s Free Slot #%s',str(trolley.address),str(trolley.slotId))
            if trolley.slotId:
                trolley.freeSlot()
                logger.info('Trolley %s Stopped and Removed', trolley.address)
            else:
                logger.debug("Trolley %s - No slot assigned",str(trolley.address))


    def dump(self):
        if TrolleyRoster.__eTrace : logger.info("Enter trolleyRoster.dump")
        if self.__outputRosterInfo is None:
            print self.getRosterStatus()
        else:
            self.__outputRosterInfo.setText("")
            __doc = self.__outputRosterInfo.getDocument()
            __style = self.__outputRosterInfo.getStyle("Color Style")
            __doc.insertString(__doc.getLength(), self.getRosterStatus(), __style)


    def getRosterStatus(self):   
        if TrolleyRoster.__eTrace : logger.info("Enter trolleyRoster.getRosterStatus")
        __rosterStatusInfo = []
        __rosterStatusInfo.append("*********************************************\n")
        __rosterStatusInfo.append(str(datetime.datetime.now())+" - TrolleyRoster\n")
        __rosterStatusInfo.append("*********************************************\n")
        self.checkForMultipleTrolleysInOneBlock()
        if self.checkForMultipleTrolleysInOneBlock():
            __rosterStatusInfo.append('Warning: Multiple trolleys registered to the same block.\n')
        __rosterStatusInfo.append("Roster Size: "+str(self.size())+"\n")
        #print "MultipleState: ",self.multipleDetectedInBlock
        for trolley in self._list:
            __rosterStatusInfo.append("Id:"+str(trolley.priority)+
                          " Address:"+str(trolley.address)+
                          " SlotID:"+str(trolley.slotId)+
                          " Speed:"+str(trolley.speed)+
                          " Current Position:"+str(trolley.currentPosition.address)+
                          " Next Position:"+str(trolley.nextPosition.address)+
                          " Next Trolley:"+str(self.getNextTrolley(trolley).address)+"\n")
            logger.debug("Id:"+str(trolley.priority)+
                         " Addr:"+str(trolley.address)+
                         " SlotId:"+str(trolley.slotId)+
                         " Spd:"+str(trolley.speed)+
                         " Cur Pos:"+str(trolley.currentPosition.address)+
                         " Nxt Pos:"+str(trolley.nextPosition.address)+
                         " SltReqSnt:"+str(trolley.slotRequestSent)+
                         " StpTime:"+str(trolley.stopTime)+
                         " StrtTime:"+str(trolley.startTime)+
                         " ThrtleTime:"+str(trolley.throttleLastMsgTime))
        #__rosterStatusInfo.append("\n")
        return ''.join(__rosterStatusInfo)


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


    def findByCurrentSegment(self, segment):
        if TrolleyRoster.__eTrace : logger.info("Enter trolleyRoster.findByCurrentSegment")
        for trolley in self._list:
            if trolley.currentPosition.segment == segment:
                if TrolleyRoster.__dTrace : logger.info("Trolley %s found in Segment:%s",str(trolley.address),str(segment))
                return trolley


    def checkIfAllTrolleysAreRegistered(self):
        if TrolleyRoster.__eTrace : logger.info("Enter trolleyRoster.checkIfAllTrolleysAreRegistered")
        for trolley in self._list:
            if trolley.slotId is None:
                logger.info("Not all trolleys are registered")
                return False
        logger.debug("All trolleys are registered")
        return True


    def refreshTrolleysSlots(self):
        if TrolleyRoster.__eTrace : logger.info("Enter trolleyRoster.refreshTrolleysSlots")
        for trolley in self._list:
            if (datetime.datetime.now() - trolley.getThrottleLastMsgTime()).seconds > trolley.THROTTLE_REFRESH_TIME:
                logger.info("Refreshing trolley:%s Slot:%s", str(trolley.address), str(trolley.slotId))
                trolley.setSpeed(trolley.speed) # send a speed update message to keep throttle fresh


    def registerOneTrolley(self):
        if TrolleyRoster.__eTrace : logger.info("Enter trolleyRoster.registerOneTrolley")
        for trolley in self._list:
            if trolley.slotId: continue
            if trolley.slotRequestSent: 
                logger.info("Trolley %s - Slot Id not yet assigned", trolley.address)
                break
            trolley.slotRequestSent = trolley.msg.requestSlot(trolley.address)
            logger.info("Trolley %s  SlotRequestSent=%s", trolley.address, trolley.slotRequestSent)
            break


    def processAllTrolleyMovement(self):
        if TrolleyRoster.__eTrace : logger.info("Enter trolleyRoster.processAllTrolleyMovement")
        for trolley in self._list:
            if trolley.getSpeed() == 0:
                if self.checkIfTrolleyCanMove(trolley):
                    logger.info("Trolley: %s   Status: Not Moving (%s seconds) in block: %s  Action: Starting",
                            trolley.address, (datetime.datetime.now() - trolley.stopTime).seconds, trolley.currentPosition.address)
                    trolley.fullSpeed()
                    self.dump()
            else:
                if self.checkIfTrolleyShouldStop(trolley):
                    logger.info("Trolley: %s   Status: Is Running (%s seconds) in block: %s  Action: Stopping",
                            trolley.address, (datetime.datetime.now() - trolley.startTime).seconds, trolley.currentPosition.address)
                    trolley.slowStop()
                    self.dump()
                elif self.checkIfTrolleyIsOverdue(trolley):
                    logger.warn("Trolley: %s   Alert:  Trolley is Overdue in block: %s",
                            trolley.address, trolley.currentPosition.description)
                    if (datetime.datetime.now() - trolley.lastAlertTime).seconds > TrolleyRoster.SECONDS_BETWEEN_AUDIBLE_ALERTS:
                        audible.announceMessage("Trolley: "+str(trolley.address)+" Alert: Trolley is Overdue. "+
                                                "Last seen in "+trolley.currentPosition.description)
                        trolley.lastAlertTime = datetime.datetime.now()


    def checkIfTrolleyIsOverdue(self, trolley):
        if TrolleyRoster.__eTrace : logger.info("Enter trolleyRoster.checkIfTrolleyIsOverdue")
        travelTime = (datetime.datetime.now() - trolley.startTime).seconds
        if travelTime > (trolley.currentPosition.length): # Assume a worst case of 1 inch per sec
            return True
        return False


    def checkIfTrolleyShouldStop(self,trolley):
        if TrolleyRoster.__eTrace : logger.info("Enter trolleyRoster.checkIfTrolleyShouldStop")
        # If the next segment is occupied return false
        if TrolleyRoster.__layoutMap.isSegmentOccupied(trolley.nextPosition.segment) and trolley.currentPosition.segment <> trolley.nextPosition.segment: 
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
                logger.info("Trolley: %s   Alert: Not the first trolley scheduled for Block %s - ******* CONTINUE IN SEGMENT CLEARANCE GRANTED", trolley.address, trolley.nextPosition.address)
            #return True
        #print "Reason: is allowed to move"
        return False


    def checkIfTrolleyCanMove(self, trolley):
        if TrolleyRoster.__eTrace : logger.info("Enter trolleyRoster.checkIfTrolleyCanMove")
        # If the slotId has not been set return false
        if trolley.slotId is None:
            logger.info("Trolley: %s   Alert: Slot Not Yet Set", trolley.address)
            return False
        # If the next segment is occupied return false
        if TrolleyRoster.__layoutMap.isSegmentOccupied(trolley.nextPosition.segment) and (trolley.currentPosition.segment != trolley.nextPosition.segment) : 
            if TrolleyRoster.__dTrace : logger.info("Trolley: %s   Alert: Next segment occupied", trolley.address)
            return False
        # If this trolley is in a block that requires a stop and has not been stopped long enough return false
        if trolley.currentPosition.stopRequired:
            if not self.__checkRequiredStopTimeMet(trolley.stopTime, trolley.currentPosition.waitTime): 
                if TrolleyRoster.__dTrace : logger.info("Trolley: %s   Alert: Required stop time has not been met", trolley.address)
                return False
        # If this trolley is not the next one scheduled for the next block return false
        if trolley.address != self.findByNextBlock(trolley.nextPosition.address).address:
            # The exception to this is if the next block is part of the current segment the trolley is already in
            if trolley.currentPosition.segment != trolley.nextPosition.segment:
                if TrolleyRoster.__dTrace : logger.info("Trolley: %s   Alert: Not the first trolley scheduled for Block %s", trolley.address, trolley.getNextPosition().address)
                return False
            else:
                logger.info("Trolley: %s   Alert: Not the first trolley scheduled for Block %s - ******* START CLEARANCE GRANTED", trolley.address, trolley.nextPosition.address)
        #print "Reason: is allowed to move"
        return True


    def __checkRequiredStopTimeMet(self,stopTime, waitTime):
        if TrolleyRoster.__eTrace : logger.info("Enter trolleyRoster.__checkRequiredStopTimeMet")
        timeSinceStop = (datetime.datetime.now() - stopTime).seconds
        #logger.info("Required Stop Time Met = %s (TimeStopped: %s   waitTime: %s)", timeSinceStop > waitTime, timeSinceStop, waitTime)
        if timeSinceStop > waitTime: return True
        return False


    def processBlockEvent(self, sensorId):
        if TrolleyRoster.__eTrace : logger.info("Enter trolleyRoster.processBlockEvent")
        if not self.__automationObject.isRunning(): return
        # We should only process sensors going HIGH or OCCUPIED
        # A sensor going high indicates that a trolley has moved into that block
        if TrolleyRoster.__layoutMap.findBlockByAddress(sensorId) :
            logger.info('Processing event for SensorID = %s', sensorId)
            # check if this event is associated with a trolley that is already in this block
            # if it is, then treat the event as a bouncy sensor reading
            if self.findByCurrentBlock(sensorId):
                logger.info('Bouncy sensor event for block: %s', sensorId)
                return
            # check if this event is associated with a trolley that is already in this segment
            # if it is, then use this trolley.  This gives priority to a trolley that is 
            # already in a segment vs a new one entering the segment.
            eventSegmentId = TrolleyRoster.__layoutMap.findSegmentByAddress(sensorId)
            trolley = self.findByCurrentSegment(eventSegmentId)
            if trolley and trolley.getSpeed() > 0:
                # If we get here, this trolley was associated with this event
                logger.info('Trolley %s found in Segment: %s  for Block: %s',trolley.address , eventSegmentId, sensorId)
                # Move the trolley into the next block
                trolley.advance(self, TrolleyRoster.__layoutMap)
                # Check if the trolley should stop at this location
                if trolley.currentPosition.segment <> trolley.nextPosition.segment: 
                    if TrolleyRoster.__layoutMap.isSegmentOccupied(trolley.nextPosition.segment):
                        trolley.slowStop()
            else:
                trolley = self.findByNextBlock(sensorId)
                if trolley and trolley.getSpeed() > 0 :
                    # If we get here, this trolley was associated with this event
                    logger.info('Trolley %s found for block: %s',trolley.address , sensorId)
                    # Move the trolley into the next block
                    trolley.advance(self, TrolleyRoster.__layoutMap)
                    # Check if the trolley should stop at this location
                    if trolley.currentPosition.segment <> trolley.nextPosition.segment:
                        if TrolleyRoster.__layoutMap.isSegmentOccupied(trolley.nextPosition.segment):
                            trolley.slowStop()
            TrolleyRoster.__layoutMap.printBlocks(self)
            TrolleyRoster.__layoutMap.printSegments(self)
            self.dump()
        return


    def setAutomationObject(self,automationObject):
        if TrolleyRoster.__eTrace : logger.info("Enter trolleyRoster.setAutomationObject")
        self.__automationObject = automationObject
        return


    def stopAllTrolleys(self):
        if TrolleyRoster.__eTrace : logger.info("Enter trolleyRoster.stopAllTrolleys")
        for trolley in self._list:
            if trolley.slotId:
                trolley.eStop()