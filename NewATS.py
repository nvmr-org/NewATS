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

import logging
import re
import xml.etree.ElementTree as ET
from classes.trolleyRoster import TrolleyRoster
from classes.blockMap import BlockMap
from classes.announcer import MessageAnnouncer
from classes.messengerFacade import Messenger
from classes.atsTrolleyAutomation import TrolleyAutomation
from classes.atsUI import AtsUI
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
TROLLEY_ROSTER_FILE_NAME = 'ATS_Roster_File.xml'
LAYOUT_MAP_FILE_NAME ='ATS_Layout_Map.xml'
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
trolleyRoster = TrolleyRoster(layoutMap=layoutMap, messageManager=msg)  # Initialize an empty roster of trolley devices


def loadAtsConfiguration():
    try:
        tree = ET.parse(configFile)
    except Exception, e:
        logger.warning(e)
        logger.warning('Unable to open ATS Config File: %s - Creating Default Configuration', configFile)


def saveFileAsXml(fileName, xmlString):
    logger.debug("Entering saveFileAsXml")
    try:
        text_file = open(fileName, "w")
        text_file.write(getFormattedXml(xmlString))
        text_file.close()
        logger.info("File Created: %s", fileName)
    except Exception, e:
        logger.error(e)
        logger.error('Unable to save file: %s', fileName)


def getFormattedXml(xmlParent):
    xmlstr = minidom.parseString(ET.tostring(xmlParent)).toprettyxml(indent="   ")
    text_re = re.compile('>\n\s+([^<>\s].*?)\n\s+</', re.DOTALL)
    prettyXml = text_re.sub('>\g<1></', xmlstr)
    return prettyXml


def buildDefaultConfig():


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
layoutMapFilePath = jmriFileUtilSupport.getUserFilesPath()
layoutMapFile = layoutMapFilePath + LAYOUT_MAP_FILE_NAME
logger.info("User Files Path: %s" + layoutMapFilePath)
logger.info('Layout Map File: %s', layoutMapFile)
layoutMap.loadLayoutMapFromXml(layoutMapFile)
layoutMap.dump()
#layoutMap.dumpXml()

logger.info("Building Trolley Roster")
trolleyRosterFilePath = jmriFileUtilSupport.getUserFilesPath()
trolleyRosterFile = trolleyRosterFilePath + TROLLEY_ROSTER_FILE_NAME
logger.info("User Files Path: %s", trolleyRosterFilePath)
logger.info("Roster File: %s", trolleyRosterFile)
trolleyRoster.loadRosterFromXmlFile(trolleyRosterFile)
trolleyRoster.dump()
#trolleyRoster.dumpXml()
#frameRoster = createEditRosterDataFrame(trolleyRoster)

logger.info("Setup Complete  - ")
layoutMap.printBlocks(trolleyRoster)
layoutMap.printSegments(trolleyRoster)