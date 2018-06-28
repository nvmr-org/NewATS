#from argparse import _StoreFalseAction
#from classes.layoutMap import LayoutMap
from datetime import timedelta
#from classes import layoutMap
print "ATS Start"
from classes.trolley import Trolley
from classes.trolleyRoster import TrolleyRoster
from classes.blockMap import BlockMap
from classes.block import Block
from classes.messengerFacade import Messenger
import datetime
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger("NewATS")
msg = Messenger()
#Trolley.setMessageManager(msgManager = msg)        


def main():
    logger.info("Initialize Empty Layout Map")
    layoutMap = BlockMap([]) # Initialize and empty block map to define the layout
    logger.info("Initialize Empty Trolley Roster")
    trolleyRoster = TrolleyRoster([])  # Initialize an empty roster of trolley devices
    
    logger.info("Build Layout Map")
    buildLayoutMap(layoutMap)  # Build the layout
    logger.info("Build Trolley Roster")
    buildTrolleyRoster(trolleyRoster, layoutMap)  # Build the roster of trolleys
    
    logger.info("Dumping Trolley Roster")
    trolleyRoster.dump()
    logger.info("Dumping Layout Map")
    layoutMap.dump()
    
    layoutMap.printBlocks(trolleyRoster)
    layoutMap.printSegments(trolleyRoster)
       
    
    #startAllTrolleysMoving(trolleyRoster, layoutMap)
    msg = Trolley.getMessageManager()
    
    try:
        while True:
            #logger.info("looping for events")
            checkAllTrolleyMovement(trolleyRoster, layoutMap)
            event = simulateAllMovement(trolleyRoster,layoutMap)
            if event: processBlockEvent(trolleyRoster, layoutMap, event)
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
 
    layoutMap.printBlocks(trolleyRoster)
    layoutMap.printSegments(trolleyRoster)
    trolleyRoster.dump()


def checkAllTrolleyMovement(trolleyRoster, layoutMap):
    for trolley in trolleyRoster:
        if trolley.getSpeed() == 0:
            if checkIfTrolleyCanMove(trolley, trolleyRoster, layoutMap):
                logger.info("Trolley: %s   Status: Not Moving (%s seconds) in block: %s",
                        trolley.address, (datetime.datetime.now() - trolley.stopTime).seconds, trolley.currentPosition.address)
                logger.info("Trolley: %s   Action: Starting",trolley.address)
                trolley.fullSpeed()
                trolleyRoster.dump()
        else:
            if checkIfTrolleyShouldStop(trolley, trolleyRoster, layoutMap):
                logger.info("Trolley: %s   Status: Is Running (%s seconds) in block: %s",
                        trolley.address, (datetime.datetime.now() - trolley.startTime).seconds, trolley.currentPosition.address)
                logger.info("Trolley: %s   Status: Stopping",trolley.address)
                trolley.slowStop()
                trolleyRoster.dump()
    

def checkIfTrolleyCanMove(trolley, trolleyRoster, layoutMap):
    # If the next segment is occupied return false
    if layoutMap.isSegmentOccupied(trolley.nextPosition.segment): 
        logger.debug("Trolley: %s   Alert: Next segment occupied", trolley.address)
        return False
    # If this trolley is not the next one scheduled for the next block return false
    if not trolley.address == trolleyRoster.findByNextBlock(trolley.nextPosition.address).address:
        logger.debug("Trolley: %s   Alert: Not the first trolley scheduled for Block %s", trolley.address, trolley.getNextPosition().address)
        return False
    # If this trolley is in a block that requires a stop and has not been stopped long enough return false
    if trolley.currentPosition.stopRequired:
        if not checkRequiredStopTimeMet(trolley.stopTime, trolley.currentPosition.waitTime): 
            logger.debug("Trolley: %s   Alert: Required stop time has not been met", trolley.address)
            return False
    #print "Reason: is allowed to move"
    return True


def checkRequiredStopTimeMet(stopTime, waitTime):
    timeSinceStop = (datetime.datetime.now() - stopTime).seconds
    #logger.info("Required Stop Time Met = %s (TimeStopped: %s   waitTime: %s)", timeSinceStop > waitTime, timeSinceStop, waitTime)
    if timeSinceStop > waitTime: return True
    return False


def checkIfTrolleyShouldStop(trolley, trolleyRoster, layoutMap):
    # If the next segment is occupied return false
    if layoutMap.isSegmentOccupied(trolley.nextPosition.segment) and trolley.currentPosition.segment <> trolley.nextPosition.segment: 
        logger.info("Trolley: %s   Alert: Next segment occupied", trolley.address)
        return True
    # If this trolley is not the next one scheduled for the next block return true
    if trolley.address != trolleyRoster.findByNextBlock(trolley.nextPosition.address).address: 
        logger.info("Trolley: %s   Alert: Not the first trolley scheduled for Block %s", trolley.address, trolley.getNextPosition.address)
        return True
    # If this trolley is in a block that requires a stop and has not been stopped long enough return true
    if trolley.currentPosition.stopRequired:
        if not checkRequiredStopTimeMet(trolley.stopTime, trolley.currentPosition.waitTime): 
            logger.info("Trolley: %s   Alert: Required stop time has not been met", trolley.address)
            return True
    #print "Reason: is allowed to move"
    return False
    
    
    
# def startAllTrolleysMoving(trolleyRoster, layoutMap):
#     for trolley in trolleyRoster:
#         if trolley.getSpeed() == 0:
#             # A trolley can start moving if the next block is empty, and the trolley is the 
#             # next one (by priority order) to be scheduled for the next block
#             logger.info("Trolley: %s  is not moving" ,trolley.address)
# #             print "  CurrentPosition:",trolley.getCurrentPosition().address
# #             print "  NextPosition:",trolley.getNextPosition().address
# #             print "  NextSegmentOccupied? ",layout.isSegmentOccupied(trolley.getNextPosition().segment)
# #             print "  Next trolley to move into that block: ", trolleyRoster.findByNextBlock(trolley.getNextPosition().address).address
#             if (not layoutMap.isSegmentOccupied(trolley.getNextPosition().segment) and 
#                 trolley.address == trolleyRoster.findByNextBlock(trolley.getNextPosition().address).address):
#                 logger.info("Starting Trolley: %s", trolley.address)
#                 trolley.fullSpeed()
def simulateAllMovement(trolleyRoster, layoutMap):
    for trolley in trolleyRoster:
        if trolley.getSpeed() > 0:
            travelTime = (datetime.datetime.now() - trolley.startTime).seconds
            if travelTime > (trolley.currentPosition.length / 4):
                logger.info("Simulating event for SensorID: %s by Trolley: %s", trolley.nextPosition.address, trolley.address)
                return trolley.nextPosition.address
    return None
    
    
def processBlockEvent(trolleyRoster, layoutMap, sensorId):
    # We should only process sensors going HIGH or OCCUPIED
    # A sensor going high indicates that a trolley has moved into that block
    logger.info('Processing event for SensorID = %s', sensorId)
    # check if the event should be associated with a trolley
    trolley = trolleyRoster.findByNextBlock(sensorId)
    if trolley and trolley.getSpeed() > 0 :
        # If we get here, this trolley was associated with this event
        logger.info('Trolley %s found for block: %s',trolley.address , sensorId)
        # Move the trolley into the next block
        trolley.advance(trolleyRoster, layoutMap)
        # Check if the trolley should stop at thsi location
        #if trolley.currentPosition.isStopRequired():
        #    print "Trolley Stop Required for Trolley:", trolley.address, 'at Block:', trolley.currentPosition.address
        #    trolley.slowStop()
        if layoutMap.isSegmentOccupied(trolley.nextPosition):
            trolley.slowStop()
    layoutMap.printBlocks(trolleyRoster)
    layoutMap.printSegments(trolleyRoster)
    trolleyRoster.dump()


# def moveAllTrolleys(trolleyRoster, layout):
#     layoutLength = len(layout)
#     nextList = []
#     for trolley in trolleyRoster:
#         if layout[trolley.nextPosition].get_isBlockOccupied() == False:
#             print "Next Block Free:",
#             if trolley.nextPosition in nextList:
#                 print "Next Block Already Scheduled"
#                 continue
#             else:
#                 print "Nothing Scheduled for Next Block:",
#                 nextList.append(trolley.nextPosition)
#                 trolley.move(layoutLength)
#                 print 'new nextposition = ', trolley.nextPosition
                

def buildLayoutMap(layout):
    # Create a layoutMap map that consists of consecutive blocks representing a complete 
    # circuit. The map also identifies the segment associated with each block. This is
    # done because so a multiple block area can be identified as occupied.
    #        -100/1--                                                     ---103/3---
    #      /          \                                                  /            \
    #     |            -----106/4--------------\                       /              /
    #      \                                    >--102/3--|---107/3---<_____104/3____/
    #        ------------101/2-----------------/
    #
    #    
    #        --100/1--                                                                                      ----103/6---*
    #      /          \                                                                                    /             \
    #     /            *                                                                                  /               \
    #     *             \                                                                                *                |
    #      \             --106/10---*----121/9-----*---123/8---*-----120/7----*-\                       /                /
    #       \                                                                    >--102/6--*---107/6---<-*----104/6----/ 
    #         -----101/2-----*------118/3------*-----116/4-----*-----119/5----*-/
    #
    # Trolley Sequencing
    # Block 100 - Thomas Loop
    # Block 101 - Spencer Station Isle
    # Block 118 - Spencer Blvd Isle
    # Block 116 - Traffic Intersection Isle
    # Block 119 - Single Track Signal Block Isle
    # Block 102 - Single Track Spencer Side
    # Block 107 - Single Track Majolica Side
    # Block 104 - Majolica Outbound Loop
    # Block 103 - Majolica Return Loop
    # Block 107 - Single Track Majolica Side
    # Block 102 - Single Track Spencer Side
    # Block 120 - Spencer Blvd Interchange Yard Side 
    # Block 123 - Spencer Blvd Shelter Yard Side
    # Block 121 - Spencer Blvd Buckholtz Yard Side
    # Block 106 - Spencer Station Yard Side
    #
    layout.append(Block(blockAddress=100, newSegment=True,  stopRequired=True,  length=24,  description='Thomas Loop'))
    layout.append(Block(blockAddress=101, newSegment=True,  stopRequired=False, length=130, description='Spencer Station Isle'))
    layout.append(Block(blockAddress=118, newSegment=True,  stopRequired=False, length=30,  description='Spencer Blvd Isle'))
    layout.append(Block(blockAddress=116, newSegment=True,  stopRequired=True,  length=135, description='Traffic Intersection Isle'))
    layout.append(Block(blockAddress=119, newSegment=True,  stopRequired=False, length=20,  description='Single Track Signal Block Isle'))
    layout.append(Block(blockAddress=102, newSegment=True,  stopRequired=False, length=48,  description='Single Track Spencer Side'))
    layout.append(Block(blockAddress=107, newSegment=False, stopRequired=False, length=40,  description='Single Track Majolica Side'))
    layout.append(Block(blockAddress=104, newSegment=False, stopRequired=False, length=40,  description='Majolica Outbound Loop'))
    layout.append(Block(blockAddress=103, newSegment=False, stopRequired=False, length=30,  description='Majolica Return Loop'))
    layout.append(Block(blockAddress=107, newSegment=False, stopRequired=False, length=40,  description='Single Track Majolica Side'))
    layout.append(Block(blockAddress=102, newSegment=False, stopRequired=False, length=48,  description='Single Track Spencer Side'))
    layout.append(Block(blockAddress=120, newSegment=True,  stopRequired=False, length=114, description='Spencer Blvd Interchange Yard Side'))
    layout.append(Block(blockAddress=123, newSegment=True,  stopRequired=True,  length=72,  description='Spencer Blvd Shelter Yard Side'))
    layout.append(Block(blockAddress=121, newSegment=True,  stopRequired=False, length=84,  description='Spencer Blvd Buckholtz Yard Side'))
    layout.append(Block(blockAddress=106, newSegment=True,  stopRequired=True,  length=28,  description='Spencer Station Yard Side'))

def buildTrolleyRoster(trolleyRoster, blockMap):
    # When building a roster you need to provide the layout map so that the starting 
    # potisions of the trolleys can be validated.
    trolleyRoster.append(Trolley(blockMap, address=501, maxSpeed=50, currentPosition=100))
    trolleyRoster.append(Trolley(blockMap, address=502, maxSpeed=40, currentPosition=100))
    trolleyRoster.append(Trolley(blockMap, address=503, maxSpeed=80, currentPosition=106)) 


main()
