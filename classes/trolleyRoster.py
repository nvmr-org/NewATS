'''
Created on Nov 18, 2016

@author: ttb
'''
import sys
import logging
import datetime
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
from classes.trolley import Trolley

logger = logging.getLogger("ATS."+__name__)
logger.setLevel(logging.INFO)
thisFuncName = lambda n=0: sys._getframe(n + 1).f_code.co_name


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
    automationManager = None
    __outputRosterInfo = None
    __outputMessageInfo = None
    __layoutMap = None
    SECONDS_BETWEEN_CONSOLE_ALERTS = 2
    SECONDS_BETWEEN_AUDIBLE_ALERTS = 15
    SECONDS_BETWEEN_SLOT_REQUESTS = 10
    SECONDS_BEFORE_OVERDUE = 5

    def __init__(self, trolleyObjects=None, layoutMap=None, title=None, automationManager=None):
        """Initialize the class"""
        super(TrolleyRoster, self).__init__()
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        self.title = title
        self.comment = []
        self.SlotIdRequestTimer = datetime.datetime.now()
        #self.msg = messageManager
        #Trolley.setMessageManager(messageManager)
        TrolleyRoster.automationManager = automationManager
        Trolley.setAutomationManager(automationManager)
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


    def __new__(cls, trolleyObjects=None, layoutMap=None, automationManager=None): # __new__ always a class method
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
        logger.trace("%s.%s - delete index=%s", __name__, thisFuncName(),str(ii))
        del self._list[ii]


    def __setitem__(self, ii, val):
        # optional: self._acl_check(val)
        self._list[ii] = val


    def __str__(self):
        return str(self._list)


    def getIndex(self,trolley):
        return self._list.index(trolley)


    def reset(self):
        self.title = None
        self.comment = []
        for trolley in self._list:
            trolley.currentPosition.set_blockClear()
            #try:
            #    trolley.freeSlot()
            #except:
            #    pass
        self._list = list()
        self.first = None
        self.last = None
        self.multipleDetectedInBlock = False
        return


    def count(self, iterable):
        return sum(1 for _ in iterable)


    def delete(self,ii):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        #currentPosition = self._list[ii].currentPosition
        logger.trace("%s.%s - Roster Length=%s", __name__, thisFuncName(),len(self._list))
        self._list[ii-1].next = self._list[ii].next
        self.__delitem__(ii)
        logger.trace("%s.%s - Roster Length=%s", __name__, thisFuncName(),len(self._list))


    def insert(self, ii, val):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
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
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        # if the block is currently occupied by another trolley set a flag before inserting
        if self.findByAddress(trolley.address) != None:
            logger.error("Error: Attempt to register multiple trolleys to the same address: %s", str(trolley.address))
        else:
            self.checkForMultipleTrolleysInOneBlock()
            self.insert(len(self._list), trolley)
        return


    def setDebugFlag(self,state):
        logger.setLevel(logging.DEBUG if state else logging.INFO)
        for handler in logging.getLogger("ATS").handlers:
            handler.setLevel(logging.DEBUG)
        logger.debug("%s.%s - Logger:%s - Set Debug Flag:%s", __name__, thisFuncName(),str(logger),str(state))


    def getDebugLevel(self):
        return logger.level


    def getMessageManager(self):
        return self.msg


    def setMessageManager(self, messageManager):
        self.msg = messageManager


    def setAutomationManager(self,automationObject):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        self.automationManager = automationObject
        Trolley.setAutomationManager(automationObject)
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
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        for trolley in self._list:
            if self.findByCurrentBlock(trolley.currentPosition.address).address <> trolley.address:
                logger.warning('Warning: Multiple trolleys registered to the same block: %s', trolley.currentPosition.address)
                logger.warning('Warning: Trolleys will depart in the order they were registered.')
                self.multipleDetectedInBlock = True
            else:
                self.multipleDetectedInBlock = False
        return self.multipleDetectedInBlock


    def destroy(self):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        for trolley in self._list:
            if TrolleyRoster.__dTrace : logger.info('Trolley: %s Free Slot #%s',str(trolley.address),str(trolley.slotId))
            if trolley.slotId:
                trolley.freeSlot()
                logger.info('Trolley %s Stopped and Removed', trolley.address)
            else:
                logger.debug("Trolley %s - No slot assigned",str(trolley.address))


    def dump(self):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        logger.trace("Enter trolleyRoster.dump")
        if self.__outputRosterInfo is None:
            print self.getRosterStatus()
        else:
            self.__outputRosterInfo.setText("")
            __doc = self.__outputRosterInfo.getDocument()
            __style = self.__outputRosterInfo.getStyle("Color Style")
            __doc.insertString(__doc.getLength(), self.getRosterStatus(), __style)


    def getRosterAsXml(self):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        trolleyXml = ET.Element('trolleyRoster')
        trolleyXml.set('version', '1.0')
        for individualComment in self.comment:
            trolleyXml.append(ET.Comment(individualComment))
        self.setXmlElementKeyValuePair(trolleyXml, 'title', self.title)
        self.setXmlElementKeyValuePair(trolleyXml, 'dateCreated', datetime.datetime.now())
        self.setXmlElementKeyValuePair(trolleyXml, 'dateModified', datetime.datetime.now())
        self.setXmlElementKeyValuePair(trolleyXml, 'rosterCount', self.size())
        roster = ET.SubElement(trolleyXml, 'roster')
        for trolley in self._list:
            roster.append(self.getTrolleyAsXml(trolley))
        xmlstr = minidom.parseString(ET.tostring(trolleyXml)).toprettyxml(indent="   ")
        text_re = re.compile('>\n\s+([^<>\s].*?)\n\s+</', re.DOTALL)
        prettyXml = text_re.sub('>\g<1></', xmlstr)
        logger.info("%s", prettyXml)
        return trolleyXml


    def getTrolleyAsXml(self, trolley):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        trolleyXml = ET.Element('trolley')
        self.setXmlElementKeyValuePair(trolleyXml, 'address', trolley.address)
        self.setXmlElementKeyValuePair(trolleyXml, 'maxSpeed', trolley.maxSpeed)
        self.setXmlElementKeyValuePair(trolleyXml, 'soundEnabled', trolley.soundEnabled)
        self.setXmlElementKeyValuePair(trolleyXml, 'currentPosition', trolley.currentPosition.address)
        self.setXmlElementKeyValuePair(trolleyXml, 'currentPositionDescription', trolley.currentPosition.description)
        return trolleyXml


    def addXmlTrolleyToRoster(self, trolley):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        address = int(trolley.find('address').text)
        maxSpeed = int(trolley.find('maxSpeed').text)
        soundEnabled = (trolley.find('soundEnabled').text == 'True')
        currentPosition = int(trolley.find('currentPosition').text)
        positionDescription  = trolley.find('currentPositionDescription').text
        logger.info('Address:%s MxSp:%s Sound:%s Pos:%s Description:%s', address, maxSpeed, soundEnabled, currentPosition, positionDescription)
        self.append(Trolley(self.__layoutMap,address=address, maxSpeed=maxSpeed,
                               soundEnabled=soundEnabled, currentPosition=currentPosition))
        logger.trace("Exiting %s.%s", __name__, thisFuncName())


    def setXmlElementKeyValuePair(self, xmlParent, tagName, tagValue):
        newElement = ET.SubElement(xmlParent, tagName)
        newElement.text = str(tagValue)


    def getRosterStatus(self):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        __rosterStatusInfo = []
        __rosterStatusInfo.append("*********************************************\n")
        __rosterStatusInfo.append(str(datetime.datetime.now())+" - TrolleyRoster\n")
        __rosterStatusInfo.append("*********************************************\n")
        self.checkForMultipleTrolleysInOneBlock()
        if self.checkForMultipleTrolleysInOneBlock():
            __rosterStatusInfo.append('Warning: Multiple trolleys registered to the same block.\n')
        __rosterStatusInfo.append("Roster Size: "+str(self.size()))
        #print "MultipleState: ",self.multipleDetectedInBlock
        for trolley in self._list:
            __rosterStatusInfo.append("\nAddress:"+str(trolley.address)+
                          " SlotID:"+str(trolley.slotId)+
                          " Speed:"+str(trolley.speed)+
                          " CurrentPosition:"+str(trolley.currentPosition.address)+
                          " NextPosition:"+str(trolley.nextPosition.address)+
                          " NextTrolley:"+str(self.getNextTrolley(trolley).address)+
                          " SpeedFactor:"+str("{:.2f}".format(trolley.speedFactor)))
            logger.debug("Addr:"+str(trolley.address)+
                         " SlotId:"+str(trolley.slotId)+
                         " Spd:"+str(trolley.speed)+
                         " Cur Pos:"+str(trolley.currentPosition.address)+
                         " Nxt Pos:"+str(trolley.nextPosition.address)+
                         " SltReqSnt:"+str(trolley.slotRequestSent)+
                         " StpTime:"+str(trolley.stopTime)+
                         " StrtTime:"+str(trolley.startTime)+
                         " ThrtleTime:"+str(trolley.throttleLastMsgTime)+
                         " SpFctr:"+str("{:.2f}".format(trolley.speedFactor)))
        #__rosterStatusInfo.append("\n")
        return ''.join(__rosterStatusInfo)


    def getNextTrolleyAddress(self, val):
        return val.next.address


    def getNextTrolley(self, val):
        return val.next
        

    def findByCurrentBlock(self, currentPosition):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        for trolley in self._list:
            if trolley.currentPosition.address == currentPosition:
                logger.trace("%s.%s - %s found in block %s", __name__, thisFuncName(),str(trolley.address),str(currentPosition))
                return trolley
        #return find(lambda trolley: trolley.currentPosition == currentPosition, self._list)
        logger.trace("%s.%s - No trollies found in block %s", __name__, thisFuncName(),str(currentPosition))
        return None
        

    def findByAddress(self, address):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        logger.trace("%s.%s - List Length %s", __name__, thisFuncName(),len(self._list))
        for trolley in self._list:
            if trolley.address == address:
                logger.trace("%s.%s - Found %s", __name__, thisFuncName(),address)
                return trolley
        return None
        #return find(lambda trolley: trolley.currentPosition == currentPosition, self._list)


    def findByNextBlock(self, nextPosition):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        numScheduledForBlock = self.count(t for t in self._list if t.nextPosition.address == nextPosition)
        segmentForNextPosition = TrolleyRoster.__layoutMap.findSegmentByAddress(nextPosition)
        logger.debug("Number of Trolleys Scheduled for Block  %s: %s", str(nextPosition), str(numScheduledForBlock) )
        trolleysScheduledForBlock = []
        for trolley in self._list:
            if trolley.nextPosition.address == nextPosition:
                logger.debug("Trolley: %s is scheduled for Block: %s", trolley.address, nextPosition)
                if numScheduledForBlock == 1: return trolley
                trolleysScheduledForBlock.append(trolley)
                if trolley.currentPosition.segment == segmentForNextPosition:
                    logger.debug("Trolley: %s is currently in Segment: %s and will get priority", trolley.address, segmentForNextPosition)
                    return trolley
        if trolleysScheduledForBlock:
            logger.debug("Multiple Trolleys scheduled for Block:%s - Priority given to Trolley: %s", nextPosition, trolleysScheduledForBlock[0].address)
            return trolleysScheduledForBlock[0]
        return None


    def findByCurrentSegment(self, segment):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        for trolley in self._list:
            if trolley.currentPosition.segment == segment:
                logger.debug("Trolley %s found in Segment:%s",str(trolley.address),str(segment))
                return trolley


    def checkIfAllTrolleysAreRegistered(self):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        for trolley in self._list:
            if trolley.throttle is None:
                logger.trace("Not all trolleys are registered")
                return False
        logger.trace("All trolleys are registered")
        return True


    def requestThrottles(self):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        for trolley in self._list:
            if trolley.throttle is None:
                logger.info("Trolley %s Requesting Throttle", trolley.address)
                trolley.automationManager.prepareThrottleRequest(trolley.address)
                trolley.automationManager.handle()
        logger.trace("Exiting %s.%s", __name__, thisFuncName())
        return 


    def refreshTrolleysSlots(self):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        for trolley in self._list:
            if (datetime.datetime.now() - trolley.getThrottleLastMsgTime()).total_seconds() > trolley.THROTTLE_REFRESH_TIME:
                logger.debug("Refreshing trolley:%s Slot:%s", str(trolley.address), str(trolley.slotId))
                trolley.setSpeed(trolley.speed) # send a speed update message to keep throttle fresh


    def registerOneTrolley(self):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        if (datetime.datetime.now() - self.SlotIdRequestTimer).total_seconds() < TrolleyRoster.SECONDS_BETWEEN_SLOT_REQUESTS:
            logger.trace("%s.%s - SlotTimer:%s", __name__, thisFuncName(),(datetime.datetime.now() - self.SlotIdRequestTimer).total_seconds())
            return
        for trolley in self._list:
            logger.trace("Trolley %s - Checking Registration", trolley.address)
            if trolley.throttle:
                logger.trace("Trolley %s - Throttle Assigned: %s", trolley.address,str(trolley.throttle))
                self.dump()
                continue
            if trolley.slotRequestSent: 
                logger.info("Trolley %s - Slot Id not yet assigned", trolley.address)
                break
            self.SlotIdRequestTimer = datetime.datetime.now()
            trolley.automationManager.prepareThrottleRequest(trolley.address)
            #trolley.automationManager.handle()
            #trolley.slotRequestSent = trolley.msg.requestSlot(trolley.address)
            #self.SlotIdRequestTimer = datetime.datetime.now()
            logger.info("Trolley %s  SlotRequestSent=%s", trolley.address, trolley.slotRequestSent)
            break
        logger.trace("Exiting %s.%s", __name__, thisFuncName())


    def processAllTrolleyMovement(self):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        for trolley in self._list:
            if trolley.getSpeed() == 0:
                if self.checkIfTrolleyCanMove(trolley):
                    logger.info("Trolley %s Not Moving (%s seconds) Action: Starting  Block: %s - %s",
                            trolley.address, (datetime.datetime.now() - trolley.stopTime).total_seconds(),
                            trolley.currentPosition.address, trolley.currentPosition.description)
                    trolley.fullSpeed()
                    self.dump()
            else:
                if self.checkIfTrolleyShouldStop(trolley):
                    logger.info("Trolley %s Is Running (%s seconds) Action: Stopping  Block: %s - %s",
                            trolley.address, (datetime.datetime.now() - trolley.startTime).total_seconds(),
                            trolley.currentPosition.address, trolley.currentPosition.description)
                    trolley.slowStop()
                    self.dump()
                elif self.checkIfTrolleyIsOverdue(trolley):
                    if (datetime.datetime.now() - trolley.lastAlertTime).total_seconds() > TrolleyRoster.SECONDS_BETWEEN_CONSOLE_ALERTS:
                        logger.warn("Trolley %s Alert: Trolley is Overdue in block: %s - %s",
                            trolley.address, trolley.currentPosition.address, trolley.currentPosition.description)
                        trolley.lastAlertTime = datetime.datetime.now()
                    if (datetime.datetime.now() - trolley.lastAudibleAlertTime).total_seconds() > TrolleyRoster.SECONDS_BETWEEN_AUDIBLE_ALERTS:
                        audible.announceMessage("Trolley: "+str(trolley.address)+" Alert: Trolley is Overdue. "+
                                                "Last seen in "+trolley.currentPosition.description)
                        trolley.lastAudibleAlertTime = datetime.datetime.now()


    def checkIfTrolleyIsOverdue(self, trolley):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        travelTime = (datetime.datetime.now() - trolley.startTime).total_seconds() - self.SECONDS_BEFORE_OVERDUE
        logger.debug("Trolley %s TravelTime:%s SpeedFactor:%s Mult:%s, Length:%s",
                     trolley.address, travelTime, trolley.speedFactor, travelTime * trolley.speedFactor,
                     trolley.currentPosition.length)
        if (travelTime * trolley.speedFactor) > (trolley.currentPosition.length):
            return True
        return False


    def checkIfTrolleyShouldStop(self,trolley):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        # If the next segment is occupied return false
        if TrolleyRoster.__layoutMap.isSegmentOccupied(trolley.nextPosition.segment) and trolley.currentPosition.segment <> trolley.nextPosition.segment: 
            logger.info("Trolley %s Must stop next segment occupied", trolley.address)
            return True
        # If this trolley is in a block that requires a stop and has not been stopped long enough return true
        if trolley.currentPosition.stopRequired:
            if not self.__checkRequiredStopTimeMet(trolley.stopTime, trolley.currentPosition.waitTime): 
                logger.info("Trolley %s Required stop time has not been met", trolley.address)
                return True
        # If this trolley is not the next one scheduled for the next block return true
        if trolley.address != self.findByNextBlock(trolley.nextPosition.address).address: 
            # The exception to this is if the next block is part of the current segment the trolley is already in
            if trolley.currentPosition.segment != trolley.nextPosition.segment:
                logger.info("Trolley %s Not the first trolley scheduled for Block %s", trolley.address, trolley.nextPosition.address)
                return True
            else:
                logger.info("Trolley %s Not the first trolley scheduled for Block %s - ******* CONTINUE IN SEGMENT CLEARANCE GRANTED", trolley.address, trolley.nextPosition.address)
            #return True
        #print "Reason: is allowed to move"
        return False


    def checkIfTrolleyCanMove(self, trolley):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        # If the slotId has not been set return false
        if trolley.slotId is None:
            logger.info("Trolley %s Alert: Slot Not Yet Set", trolley.address)
            return False
        # If the next segment is occupied return false
        if TrolleyRoster.__layoutMap.isSegmentOccupied(trolley.nextPosition.segment) and (trolley.currentPosition.segment != trolley.nextPosition.segment) : 
            logger.debug("Trolley %s Next segment occupied", trolley.address)
            return False
        # If this trolley is in a block that requires a stop and has not been stopped long enough return false
        if trolley.currentPosition.stopRequired:
            if not self.__checkRequiredStopTimeMet(trolley.stopTime, trolley.currentPosition.waitTime): 
                logger.debug("Trolley %s Required stop time has not been met", trolley.address)
                return False
        # If this trolley is not the next one scheduled for the next block return false
        if trolley.address != self.findByNextBlock(trolley.nextPosition.address).address:
            # The exception to this is if the next block is part of the current segment the trolley is already in
            if trolley.currentPosition.segment != trolley.nextPosition.segment:
                logger.debug("Trolley %s Not the first trolley scheduled for Block %s", trolley.address, trolley.getNextPosition().address)
                return False
            else:
                logger.info("Trolley %s Not the first trolley scheduled for Block %s - ******* START CLEARANCE GRANTED", trolley.address, trolley.nextPosition.address)
        #print "Reason: is allowed to move"
        return True


    def __checkRequiredStopTimeMet(self,stopTime, waitTime):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        timeSinceStop = (datetime.datetime.now() - stopTime).total_seconds()
        #logger.info("Required Stop Time Met = %s (TimeStopped: %s   waitTime: %s)", timeSinceStop > waitTime, timeSinceStop, waitTime)
        if timeSinceStop > waitTime: return True
        return False


    def processBlockEvent(self, sensorId):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        if not self.automationManager.isRunning(): return
        # We should only process sensors going HIGH or OCCUPIED
        # A sensor going high indicates that a trolley has moved into that block
        if TrolleyRoster.__layoutMap.findBlockByAddress(sensorId) :
            logger.debug('Processing event for SensorID = %s', sensorId)
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
            if trolley and (trolley.isMoving() or trolley.wasMoving()):
                # If we get here, this trolley was associated with this event
                logger.info('Trolley %s found in Segment: %s  for Block: %s',trolley.address , eventSegmentId, sensorId)
                # Move the trolley into the next block
                trolley.advance(self, TrolleyRoster.__layoutMap)
                # Check if the trolley should stop at this location
                if trolley.currentPosition.segment <> trolley.nextPosition.segment: 
                    if TrolleyRoster.__layoutMap.isSegmentOccupied(trolley.nextPosition.segment):
                        logger.info('Trolley %s Stopping in: %s - Reason: Next Segment Occupied',trolley.address , sensorId)
                        trolley.slowStop()
            else:
                trolley = self.findByNextBlock(sensorId)
                if trolley and (trolley.isMoving() or trolley.wasMoving()):
                    # If we get here, this trolley was associated with this event
                    logger.info('Trolley %s found for block: %s',trolley.address , sensorId)
                    # Move the trolley into the next block
                    trolley.advance(self, TrolleyRoster.__layoutMap)
                    # Check if the trolley should stop at this location
                    if trolley.currentPosition.segment <> trolley.nextPosition.segment:
                        if TrolleyRoster.__layoutMap.isSegmentOccupied(trolley.nextPosition.segment):
                            logger.info('Trolley %s Stopping in: %s - Reason: Next Segment Occupied',trolley.address , sensorId)
                            trolley.slowStop()
            TrolleyRoster.__layoutMap.printBlocks(self)
            TrolleyRoster.__layoutMap.printSegments(self)
            self.dump()
        return


    def stopAllTrolleys(self):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        for trolley in self._list:
            if trolley.slotId:
                trolley.eStop()


    def buildDefaultRoster(self,layoutMap):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        # When building a roster you need to provide the layout map so that the starting
        # potisions of the trolleys can be validated. The roster is built prior to sending any
        # requests to JMRI for slots. Slot registration should occur in the handler on a one by one
        # basis to avoid conflicts.
        self.title="NVMR Automated Trolley Roster"
        self.comment.append(r'Generated by NVMR Automated Trolley Sequencer')
        self.comment.append(r'Create a trolley roster that consists of consecutive trolleys on a layout')
        self.append(Trolley(layoutMap, address=501, maxSpeed=50, soundEnabled=True, currentPosition=100))
        self.append(Trolley(layoutMap, address=502, maxSpeed=40, soundEnabled=False, currentPosition=100))
        self.append(Trolley(layoutMap, address=503, maxSpeed=80, soundEnabled=True, currentPosition=106))
        self.append(Trolley(layoutMap, address=504, maxSpeed=50, soundEnabled=False, currentPosition=106))


    def loadRosterFromXmlFile(self, trolleyRosterFile):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        logger.info("Loading Roster File: %s", trolleyRosterFile)
        try:
            tree = ET.parse(str(trolleyRosterFile))
            self.title =  tree.find('title').text
            roster = tree.find('roster')
            if roster is None:
                raise Exception('File does not contain a roster.')
            logger.info("Number of Trolleys: %s", len(roster))
            self.reset()
            for trolley in roster.iter(tag = 'trolley'):
                self.addXmlTrolleyToRoster(trolley)
        except Exception, e:
            logger.warning(e)
            logger.warning('Unable to open roster file: %s - Building Default Roster', trolleyRosterFile)
            #TrolleyRoster.buildDefaultRoster()


    def validatePositions(self, blockMap):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        for trolley in self._list:
            logger.debug("Checking trolley:%s", trolley.address)
            if blockMap.findBlockByAddress(trolley.currentPosition.address) is None:
                logger.warning('Warning: Trolleys %s assigned to invalid block: %s', trolley.address, trolley.currentPosition.address)
                logger.warning('Warning: Trolleys %s will be removed', trolley.address)
                self.delete(self.getIndex(trolley))
                break
            trolley.currentPosition.set_blockOccupied()
        logger.trace("Exiting %s.%s", __name__, thisFuncName())
        return
