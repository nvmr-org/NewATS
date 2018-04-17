print "ATS Start"
from classes.trolley import Trolley
from classes.trolleyRoster import TrolleyRoster
from classes.blockMap import BlockMap
from classes.block import Block


def main():
    print "Initialize Empty Layout Map"
    blockMap = BlockMap([]) # Initialize and empty block map to define the layout
    print "Initialize Empty Trolley Roster"
    trolleyRoster = TrolleyRoster([])  # Initialize an empty roster of trolley devices
    
    print "Build Layout Map"
    buildLayoutMap(blockMap)  # Build the layout
    print "Build Trolley Roster"
    buildTrolleyRoster(trolleyRoster, blockMap)  # Build the roster of trolleys
    
    trolleyRoster.dump()
    blockMap.dump()

    blockMap.printBlocks(trolleyRoster)
    blockMap.printSegments(trolleyRoster)
    
    startAllTrolleysMoving(trolleyRoster, blockMap)
    trolleyRoster.dump()
    
    print "Creating Fake Event: 101"
    processBlockEvent(trolleyRoster, blockMap, 101)

    print "Creating Another Fake Event: 118"
    processBlockEvent(trolleyRoster, blockMap, 118)

    blockMap.printBlocks(trolleyRoster)
    blockMap.printSegments(trolleyRoster)
    trolleyRoster.dump()

def startAllTrolleysMoving(trolleyRoster, layout):
    for trolley in trolleyRoster:
        if trolley.getSpeed() == 0:
            # A trolley can start moving if the next block is empty, and the trolley is the 
            # next one (by priority order) to be scheduled for the next block
            print "Trolley:",trolley.address, " is not moving"
#             print "  CurrentPosition:",trolley.getCurrentPosition().address
#             print "  NextPosition:",trolley.getNextPosition().address
#             print "  NextSegmentOccupied? ",layout.isSegmentOccupied(trolley.getNextPosition().segment)
#             print "  Next trolley to move into that block: ", trolleyRoster.findByNextBlock(trolley.getNextPosition().address).address
            if (not layout.isSegmentOccupied(trolley.getNextPosition().segment) and 
                trolley.address == trolleyRoster.findByNextBlock(trolley.getNextPosition().address).address):
                print "Starting Trolley:", trolley.address
                trolley.fullSpeed()
    
        
def processBlockEvent(trolleyRoster, layout, sensorId):
    # We should only process sensors going HIGH or OCCUPIED
    # A sensor going high indicates that a trolley has moved into that block
    print 'Processing event for SensorID = ', sensorId
    # check if the event should be associated with a trolley
    trolley = trolleyRoster.findByNextBlock(sensorId)
    if trolley and trolley.getSpeed() > 0 :
        # If we get here, this trolley was associated with this event
        print 'Trolley ', trolley.address, ' found for block:', sensorId
        # Move the trolley into the next block
        trolley.advance(trolleyRoster, layout)
        # Check if the trolley should stop at thsi location
        if trolley.currentPosition.isStopRequired():
            print "Trolley Stop Required for Trolley:", trolley.address, 'at Block:', trolley.currentPosition.address
            trolley.slowStop()
        if layout.isSegmentOccupied(trolley.nextPosition):
            trolley.slowStop()  

def moveAllTrolleys(trolleyRoster, layout):
    layoutLength = len(layout)
    nextList = []
    for trolley in trolleyRoster:
        if layout[trolley.nextPosition].get_isBlockOccupied() == False:
            print "Next Block Free:",
            if trolley.nextPosition in nextList:
                print "Next Block Already Scheduled"
                continue
            else:
                print "Nothing Scheduled for Next Block:",
                nextList.append(trolley.nextPosition)
                trolley.move(layoutLength)
                print 'new nextposition = ', trolley.nextPosition
                

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
    #      \             --106/0---*-----121/9-----*---123/8---*-----120/7----*-\                       /                /
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
    layout.append(Block(blockAddress=100, newSegment=True,  stopRequired=True,  length=20, description='Thomas Loop'))
    layout.append(Block(blockAddress=101, newSegment=True,  stopRequired=False, length=40, description='Spencer Station Isle'))
    layout.append(Block(blockAddress=118, newSegment=True,  stopRequired=False, length=40, description='Spencer Blvd Isle'))
    layout.append(Block(blockAddress=116, newSegment=True,  stopRequired=True,  length=40, description='Traffic Intersection Isle'))
    layout.append(Block(blockAddress=119, newSegment=True,  stopRequired=False, length=20, description='Single Track Signal Block Isle'))
    layout.append(Block(blockAddress=102, newSegment=True,  stopRequired=False, length=30, description='Single Track Spencer Side'))
    layout.append(Block(blockAddress=107, newSegment=False, stopRequired=False, length=30, description='Single Track Majolica Side'))
    layout.append(Block(blockAddress=104, newSegment=False, stopRequired=False, length=20, description='Majolica Outbound Loop'))
    layout.append(Block(blockAddress=103, newSegment=False, stopRequired=False, length=15, description='Majolica Return Loop'))
    layout.append(Block(blockAddress=107, newSegment=False, stopRequired=False, length=30, description='Single Track Majolica Side'))
    layout.append(Block(blockAddress=102, newSegment=False, stopRequired=False, length=30, description='Single Track Spencer Side'))
    layout.append(Block(blockAddress=120, newSegment=True,  stopRequired=False, length=30, description='Spencer Blvd Interchange Yard Side'))
    layout.append(Block(blockAddress=123, newSegment=True,  stopRequired=True,  length=30, description='Spencer Blvd Shelter Yard Side'))
    layout.append(Block(blockAddress=121, newSegment=True,  stopRequired=False, length=30, description='Spencer Blvd Buckholtz Yard Side'))
    layout.append(Block(blockAddress=106, newSegment=True,  stopRequired=True,  length=30, description='Spencer Station Yard Side'))

def buildTrolleyRoster(trolleyRoster, blockMap):
    # When building a roster you need to provide the layout map so that the starting 
    # potisions of the trolleys can be validated.
    print "Add Trolley 501"
    trolleyRoster.append(Trolley(blockMap, address=501, maxSpeed=50, currentPosition=100))
    print "Add Trolley 502"
    trolleyRoster.append(Trolley(blockMap, address=502, maxSpeed=40, currentPosition=100))
    print "Add Trolley 503"
    trolleyRoster.append(Trolley(blockMap, address=503, maxSpeed=80, currentPosition=106)) 


main()
