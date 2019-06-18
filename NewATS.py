'''
ATS (Automatic Trolley Sequencer)
@author: ttb

This script has been modified to read in trolley block 
occupancy messages and control the speed of the related
trolleys as they move around the same track loop.

This is built on a set of code which can display
each sensor event and/or speak it for debugging purposes.

Based on ATS.py written by 
    Gerry Wolfson, 
    October 9, 1942 - April 8, 2018
    Member: Northern Virginia Model Railroad
    URL: http://nvmr.org
'''
import time
import logging
import os.path
from classes.trolley import Trolley
from classes.trolleyRoster import TrolleyRoster
from classes.blockMap import BlockMap
from classes.block import Block
from classes.announcer import MessageAnnouncer
from classes.messengerFacade import Messenger
from classes.atsTrolleyAutomation import TrolleyAutomation
from classes.atsUI import AtsUI

print "ATS Start"

try:
    jmriFlag = True
    import jmri
    print('Successfully Imported jmri')
except ImportError:
    jmriFlag = False
    print('Failed to import jmir - bypassing')

TROLLEY_ROSTER_ADDRESS_FILE = "trolleyRosterAddresses.cfg"
ATS_MESSAGE_FONT_SIZE = 12
ATS_MESSAGE_WINDOW_PANE_WIDTH = 1500
ATS_ROSTER_WINDOW_PANE_WIDTH = 1200
ATS_MESSAGE_WINDOW_WIDTH = 100
ATS_ROSTER_ROW_HEIGHT = 30
__apNameVersion = "Automatic Trolley Sequencer"
enableSimulator = False
__fus = jmri.util.FileUtilSupport()

#logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger("ATS")
if not len(logger.handlers):
    fileHandler = logging.FileHandler("{0}/{1}.log".format(__fus.getUserFilesPath(),'NewATS'))
    fileHandler.setLevel(logging.INFO)
    fileHandler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(logging.INFO)
    consoleHandler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
    logger.addHandler(fileHandler)
    logger.addHandler(consoleHandler)
    logger.setLevel(logging.INFO)

print("Log File Path:"+__fus.getUserFilesPath())

msg = Messenger()
msg.createListener()
# create a TrolleyAutomation object
trolleyAutomationObject = TrolleyAutomation()


#Trolley.setMessageManager(msgManager = msg)        
logger.info("Initialize Empty Layout Map")
layoutMap = BlockMap() # Initialize and empty block map to define the layout
logger.info("Initialize Empty Trolley Roster")
trolleyRoster = TrolleyRoster(layoutMap=layoutMap)  # Initialize an empty roster of trolley devices


def buildLayoutMap(layout):
    # Create a layoutMap map that consists of consecutive blocks representing a complete 
    # circuit. The map also identifies the segment associated with each block. This is
    # done because so a multiple block area can be identified as occupied.
    #    
    #        --100/1--                                                                                      ----103/6---*
    #      /          \                                                                                    /             \
    #     /            *                                                                                  /               \
    #     *             \                                                                                *                |
    #      \             --106/10---*----121/9-----*---123/8---*-----120/7----*-\                       /                /
    #       \                                                                    >--102/6--*---107/6---<-*----104/6----/ 
    #         -----101/2-----*------118/3------*-----116/4-----*-----117/5----*-/
    #
    # Trolley Sequencing
    # Block 100 - Thomas Loop
    # Block 101 - Spencer Station Isle Side
    # Block 118 - Spencer Boulevard Isle Side
    # Block 116 - Traffic Intersection Isle Side
    # Block 117 - Single Track Signal Block Isle Side
    # Block 102 - Single Track Spencer Side
    # Block 107 - Single Track Majolica Side
    # Block 104 - Majolica Outbound Loop
    # Block 103 - Majolica Return Loop
    # Block 107 - Single Track Majolica End
    # Block 102 - Single Track Spencer End
    # Block 120 - Spencer Boulevard Interchange Yard Side 
    # Block 123 - Spencer Boulevard Shelter Yard Side
    # Block 121 - Spencer Boulevard Buckholtz Yard Side
    # Block 106 - Spencer Station Yard Side
    #
    layout.append(Block(blockAddress=100, newSegment=True,  stopRequired=True,  length=24,  description='Thomas Loop'))
    layout.append(Block(blockAddress=101, newSegment=True,  stopRequired=False, length=130, description='Spencer Station Isle Side'))
    layout.append(Block(blockAddress=118, newSegment=True,  stopRequired=False, length=30,  description='Spencer Boulevard Isle Side'))
    layout.append(Block(blockAddress=116, newSegment=True,  stopRequired=True,  length=135, description='Traffic Intersection Isle Side'))
    layout.append(Block(blockAddress=117, newSegment=True,  stopRequired=False, length=20,  description='Single Track Signal Block Isle Side'))
    layout.append(Block(blockAddress=102, newSegment=True,  stopRequired=False, length=48,  description='Single Track Spencer Side'))
    layout.append(Block(blockAddress=107, newSegment=False, stopRequired=False, length=40,  description='Single Track Majolica Side'))
    layout.append(Block(blockAddress=104, newSegment=False, stopRequired=False, length=40,  description='Majolica Outbound Loop'))
    layout.append(Block(blockAddress=103, newSegment=False, stopRequired=False, length=30,  description='Majolica Return Loop'))
    layout.append(Block(blockAddress=107, newSegment=False, stopRequired=False, length=40,  description='Single Track Majolica End'))
    layout.append(Block(blockAddress=102, newSegment=False, stopRequired=False, length=48,  description='Single Track Spencer End'))
    layout.append(Block(blockAddress=120, newSegment=True,  stopRequired=False, length=114, description='Spencer Boulevard Interchange Yard Side'))
    layout.append(Block(blockAddress=123, newSegment=True,  stopRequired=True,  length=72,  description='Spencer Boulevard Shelter Yard Side'))
    layout.append(Block(blockAddress=121, newSegment=True,  stopRequired=False, length=84,  description='Spencer Boulevard Buckholtz Yard Side'))
    layout.append(Block(blockAddress=106, newSegment=True,  stopRequired=True,  length=28,  description='Spencer Station Yard Side'))


def buildTrolleyRoster(trolleyRoster, blockMap):
    # When building a roster you need to provide the layout map so that the starting 
    # potisions of the trolleys can be validated. The roster is built prior to sending any
    # requests to JMRI for slots. Slot registration should occur in the handler on a one by one
    # basis to avoid conflicts.
    trolleyRosterFile = __fus.getUserFilesPath() + TROLLEY_ROSTER_ADDRESS_FILE
    if os.path.isfile(trolleyRosterFile):
        logger.info("Trolley Roster Address File: %s",trolleyRosterFile)
    else:
        logger.info("Creating default trolley Roster")
    trolleyRoster.append(Trolley(blockMap, address=501, maxSpeed=50, soundEnabled=True, currentPosition=100))
    trolleyRoster.append(Trolley(blockMap, address=502, maxSpeed=40, soundEnabled=False, currentPosition=100))
    trolleyRoster.append(Trolley(blockMap, address=503, maxSpeed=80, soundEnabled=True, currentPosition=106)) 
    trolleyRoster.append(Trolley(blockMap, address=504, maxSpeed=50, soundEnabled=False, currentPosition=106)) 


# *************************************
# start to initialize the display GUI *
# *************************************
atsUi = AtsUI(automationObject=trolleyAutomationObject, appName=__apNameVersion)


# set the name - This will show in the thread monitor
trolleyAutomationObject.setName(__apNameVersion)
trolleyRoster.setAutomationObject(trolleyAutomationObject)
audible = MessageAnnouncer(atsUi.msgSpkCheckBox)
trolleyRoster.setMessageAnnouncer(audible)
audible.announceMessage("Welcome to the "+__apNameVersion)

# Set output locations for 
#layoutMap.setBlockDumpOutput(output=messageInfoPanel)
layoutMap.setBlockInfoOutput(output=atsUi.blockInfoPane)
layoutMap.setSegmentInfoOutput(output=atsUi.segmentInfoPane)
trolleyRoster.setRosterInfoOutput(output=atsUi.rosterInfoPane)
trolleyRoster.setMessageInfoOutput(output=atsUi.messageInfoPanel)

logger.info("Building Layout Map")
buildLayoutMap(layoutMap)  # Build the layout
layoutMap.dump()

logger.info("Building Trolley Roster")
buildTrolleyRoster(trolleyRoster, layoutMap)  # Build the roster of trolleys
trolleyRoster.dump()
#frameRoster = createEditRosterDataFrame(trolleyRoster)

logger.info("Setup Complete  - ")
layoutMap.printBlocks(trolleyRoster)
layoutMap.printSegments(trolleyRoster)
