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
import datetime
import re
import xml.etree.ElementTree as ET
from classes.trolley import Trolley
from classes.trolleyRoster import TrolleyRoster
from classes.blockMap import BlockMap
from classes.block import Block
from classes.announcer import MessageAnnouncer
from classes.messengerFacade import Messenger
from classes.atsTrolleyAutomation import TrolleyAutomation
from classes.atsUI import AtsUI
from javafx.scene import layout
from xml.dom import minidom

print "ATS Start"

try:
    jmriFlag = True
    from jmri.jmrit import XmlFile
    import jmri
    print('Successfully Imported jmri')
    class myXmlFile(XmlFile) :   # XmlFile is abstract
        def nullMethod(self) :
            return
except ImportError:
    jmriFlag = False
    print('Failed to import jmir - bypassing')

TROLLEY_ROSTER_ADDRESS_FILE = "trolleyRosterAddresses.cfg"
LAYOUT_MAP_FILE_NAME ='ATS_Layout_Map.xml'
ATS_MESSAGE_FONT_SIZE = 12
ATS_MESSAGE_WINDOW_PANE_WIDTH = 1500
ATS_ROSTER_WINDOW_PANE_WIDTH = 1200
ATS_MESSAGE_WINDOW_WIDTH = 100
ATS_ROSTER_ROW_HEIGHT = 30
__apNameVersion = "Automatic Trolley Sequencer"
enableSimulator = False
jmriFileUtilSupport = jmri.util.FileUtilSupport()

#logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger("ATS")
if not len(logger.handlers):
    fileHandler = logging.FileHandler("{0}/{1}.log".format(jmriFileUtilSupport.getUserFilesPath(),'NewATS'))
    fileHandler.setLevel(logging.INFO)
    fileHandler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(logging.INFO)
    consoleHandler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
    logger.addHandler(fileHandler)
    logger.addHandler(consoleHandler)
    logger.setLevel(logging.INFO)

msg = Messenger()
msg.createListener()
# create a TrolleyAutomation object
trolleyAutomationObject = TrolleyAutomation()

#Trolley.setMessageManager(msgManager = msg)        
logger.info("Initialize Empty Layout Map")
layoutMap = BlockMap() # Initialize and empty block map to define the layout
logger.info("Initialize Empty Trolley Roster")
trolleyRoster = TrolleyRoster(layoutMap=layoutMap)  # Initialize an empty roster of trolley devices


def loadLayoutMap():
    logger.debug("Entering loadLayoutMap")
    layoutMapFilePath = jmriFileUtilSupport.getUserFilesPath()
    layoutMapFile = layoutMapFilePath + LAYOUT_MAP_FILE_NAME
    logger.info("User Files Path: %s" + layoutMapFilePath)
    logger.info('Layout Map File: %s', layoutMapFile)
    try:
        tree = ET.parse(layoutMapFile)
        layoutMap.title =  tree.find('title')
        blocks = tree.find('blocks')
        logger.info("Number of BLocks: %s", len(blocks))
        for block in blocks.iter(tag = 'block'):
            addXmlBlockToLayoutMap(block)
    except Exception, e:
        logger.error(e)
        logger.error('Unable to open Layout Map: %s - Building Default Layout', layoutMapFile)
        buildDefaultLayoutMap()
        layoutXml = layoutMap.getMapAsXml()
        xmlstr = minidom.parseString(ET.tostring(layoutXml)).toprettyxml(indent="   ")
        text_re = re.compile('>\n\s+([^<>\s].*?)\n\s+</', re.DOTALL)
        prettyXml = text_re.sub('>\g<1></', xmlstr)
        logger.info("%s",prettyXml)
        xmlDocument = myXmlFile.newDocument(layoutXml)
        jmriFileUtilSupport.writeFile(layoutMapFile, xmlDocument)




def addXmlBlockToLayoutMap(block):
    logger.debug("Entering addXmlBlockToLayoutMap")
    address = block.find('address').text
    newSegment = (block.find('newSegment').text == 'True')
    stopRequired = (block.find('stopRequired').text == 'True')
    waitTime = block.find('waitTime').text
    length = block.find('length').text
    description = block.find('description').text
    logger.info('address:%s Seg:%s Stop:%s Time:%s Len:%s Description:%s',address,newSegment,stopRequired,waitTime,length,description)
    for element in block.iter():
        logger.info("   %s: '%s'" % (element.tag, element.text))
    layoutMap.append(Block(blockAddress=int(address), newSegment=newSegment,
                           stopRequired=stopRequired, waitTime=int(waitTime),
                           length=int(length),  description=description))
    

def buildDefaultLayoutMap():
    logger.debug("Entering buildDefaultLayoutMap")
    layoutMap.title="NVMR Automated Trolley Layout"
    layoutMap.comment.append(r'# Generated by NVMR Automated Trolley Sequencer')
    layoutMap.comment.append(r'# Create a layoutMap map that consists of consecutive blocks representing a complete') 
    layoutMap.comment.append(r'# circuit. The map also identifies the segment associated with each block. This is')
    layoutMap.comment.append(r'# done because so a multiple block area can be identified as occupied.')
    layoutMap.comment.append(r'#    ')
    layoutMap.comment.append(r'#        ==100/1==                                                                                      ====103/6===* ')
    layoutMap.comment.append(r'#      /          \                                                                                    /             \ ')
    layoutMap.comment.append(r'#     /            *                                                                                  /               \ ')
    layoutMap.comment.append(r'#     *             \                                                                                *                | ')
    layoutMap.comment.append(r'#      \             ==106/10===*====121/9=====*===123/8===*=====120/7====*=\                       /                / ')
    layoutMap.comment.append(r'#       \                                                                    >==102/6==*===107/6===<=*====104/6====/ ')
    layoutMap.comment.append(r'#         =====101/2=====*======118/3======*=====116/4=====*=====117/5====*=/')
    layoutMap.comment.append(r'#')
    layoutMap.comment.append(r'# Trolley Sequencing')
    layoutMap.comment.append(r'# Block 100 - Thomas Loop')
    layoutMap.comment.append(r'# Block 101 - Spencer Station Aisle Side')
    layoutMap.comment.append(r'# Block 118 - Spencer Boulevard Aisle Side')
    layoutMap.comment.append(r'# Block 116 - Traffic Intersection Aisle Side')
    layoutMap.comment.append(r'# Block 117 - Single Track Signal Block Aisle Side')
    layoutMap.comment.append(r'# Block 102 - Single Track Spencer Side')
    layoutMap.comment.append(r'# Block 107 - Single Track Majolica Side')
    layoutMap.comment.append(r'# Block 104 - Majolica Outbound Loop')
    layoutMap.comment.append(r'# Block 103 - Majolica Return Loop')
    layoutMap.comment.append(r'# Block 107 - Single Track Majolica End')
    layoutMap.comment.append(r'# Block 102 - Single Track Spencer End')
    layoutMap.comment.append(r'# Block 120 - Spencer Boulevard Interchange Yard Side')
    layoutMap.comment.append(r'# Block 123 - Spencer Boulevard Shelter Yard Side')
    layoutMap.comment.append(r'# Block 121 - Spencer Boulevard Buckholtz Yard Side')
    layoutMap.comment.append(r'# Block 106 - Spencer Station Yard Side')
    layoutMap.append(Block(blockAddress=100, newSegment=True,  stopRequired=True,  length=24,  description='Thomas Loop'))
    layoutMap.append(Block(blockAddress=101, newSegment=True,  stopRequired=False, length=130, description='Spencer Station Aisle Side'))
    layoutMap.append(Block(blockAddress=118, newSegment=True,  stopRequired=False, length=30,  description='Spencer Boulevard Buckholtz Aisle Side'))
    layoutMap.append(Block(blockAddress=116, newSegment=True,  stopRequired=True,  length=135, description='Spencer Boulevard Traffic Intersection Aisle Side'))
    layoutMap.append(Block(blockAddress=117, newSegment=True,  stopRequired=False, length=20,  description='Spencer Boulevard Aisle Track Signal'))
    layoutMap.append(Block(blockAddress=102, newSegment=True,  stopRequired=False, length=48,  description='Single Track Spencer Side Outbound'))
    layoutMap.append(Block(blockAddress=107, newSegment=False, stopRequired=False, length=40,  description='Single Track Majolica Side Outbound'))
    layoutMap.append(Block(blockAddress=104, newSegment=False, stopRequired=False, length=40,  description='Majolica Outbound Loop'))
    layoutMap.append(Block(blockAddress=103, newSegment=False, stopRequired=False, length=30,  description='Majolica Return Loop'))
    layoutMap.append(Block(blockAddress=107, newSegment=False, stopRequired=False, length=40,  description='Single Track Majolica End Returning'))
    layoutMap.append(Block(blockAddress=102, newSegment=False, stopRequired=False, length=48,  description='Single Track Spencer End Returning'))
    layoutMap.append(Block(blockAddress=120, newSegment=True,  stopRequired=False, length=114, description='Spencer Boulevard WNC Interchange Yard Side'))
    layoutMap.append(Block(blockAddress=123, newSegment=True,  stopRequired=True,  length=72,  description='Spencer Boulevard Bus Shelter Yard Side'))
    layoutMap.append(Block(blockAddress=121, newSegment=True,  stopRequired=False, length=84,  description='Spencer Boulevard Buckholtz Yard Side'))
    layoutMap.append(Block(blockAddress=106, newSegment=True,  stopRequired=True,  length=28,  description='Spencer Station Yard Side'))


def loadTrolleyRoster(trolleyRoster):
    logger.debug("Entering loadTrolleyRoster")
    print("User Files Path:"+jmriFileUtilSupport.getUserFilesPath())
    try:
        trolleyRosterFile = jmriFileUtilSupport.getFile(jmriFileUtilSupport.getUserFilesPath()+'ATS_Roster_File.xml')
        logger.info(trolleyRosterFile)
        trolleyRosterXml = jmriFileUtilSupport.readFile(trolleyRosterFile)
        logger.info(trolleyRosterXml)
        #rootElement = myXmlFile().rootFromName(str(layoutMapFile))
        layoutMap.dump()
        parseTrolleyRosterFile(trolleyRoster, trolleyRosterFile)
    except Exception, e:
        logger.error(e)
        logger.error('Unable to open Layout Map: %s - Building Default Layout', trolleyRosterFile)
        buildDefaultTrolleyRoster(trolleyRoster)  # Build the roster of trolleys


def parseTrolleyRosterFile(trolleyRoster, trolleyRosterFile):
    logger.debug("Entering parseTrolleyRosterFile")
    logger.info("Parsing Trolley Roster file: %s", trolleyRosterFile)
    tree = ET.parse(trolleyRosterFile)
    trolleyRoster.title =  tree.find('title')
    roster = tree.find('roster')
    logger.info("Number of Trolleys: %s", len(roster))
    for trolley in roster.iter(tag = 'trolley'):
        address = int(trolley.find('address').text)
        maxSpeed = int(trolley.find('maxSpeed').text)
        soundEnabled = (trolley.find('soundEnabled').text == 'True')
        currentPosition = int(trolley.find('currentPosition').text)
        positionDescription  = trolley.find('currentPositionDescription').text
        logger.info('Address:%s MxSp:%s Sound:%s Pos:%s Description:%s',address,maxSpeed,soundEnabled,currentPosition,positionDescription)
        trolleyRoster.append(Trolley(layoutMap,address=address, maxSpeed=maxSpeed,
                               soundEnabled=soundEnabled, currentPosition=currentPosition))
        #trolleyRoster.append(Trolley(blockMap, address=501, maxSpeed=50, soundEnabled=True, currentPosition=100))
    

def buildDefaultTrolleyRoster(trolleyRoster):
    logger.debug("Entering buildDefaultTrolleyRoster")
    # When building a roster you need to provide the layout map so that the starting 
    # potisions of the trolleys can be validated. The roster is built prior to sending any
    # requests to JMRI for slots. Slot registration should occur in the handler on a one by one
    # basis to avoid conflicts.
    trolleyRoster.title="NVMR Automated Trolley Roster"
    trolleyRosterFile = jmriFileUtilSupport.getUserFilesPath() + TROLLEY_ROSTER_ADDRESS_FILE
    logger.info("Creating default trolley Roster: %s", trolleyRosterFile)
    trolleyRoster.append(Trolley(layoutMap, address=501, maxSpeed=50, soundEnabled=True, currentPosition=100))
    trolleyRoster.append(Trolley(layoutMap, address=502, maxSpeed=40, soundEnabled=False, currentPosition=100))
    trolleyRoster.append(Trolley(layoutMap, address=503, maxSpeed=80, soundEnabled=True, currentPosition=106)) 
    trolleyRoster.append(Trolley(layoutMap, address=504, maxSpeed=50, soundEnabled=False, currentPosition=106)) 


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

logger.info("Loading Layout Map")
loadLayoutMap()  # Build the layout
layoutMap.dump()
#layoutMap.dumpXml()

logger.info("Building Trolley Roster")
loadTrolleyRoster(trolleyRoster)  # Build the roster of trolleys
trolleyRoster.dump()
#trolleyRoster.dumpXml()
#frameRoster = createEditRosterDataFrame(trolleyRoster)

logger.info("Setup Complete  - ")
layoutMap.printBlocks(trolleyRoster)
layoutMap.printSegments(trolleyRoster)