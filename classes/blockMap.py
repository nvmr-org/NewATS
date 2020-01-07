'''
Created on Nov 18, 2016

@author: ttb
'''
import logging
import datetime
import sys
import xml.etree.ElementTree as ET
from classes.block import Block

logger = logging.getLogger("ATS."+__name__)
logger.setLevel(logging.INFO)
thisFuncName = lambda n=0: sys._getframe(n + 1).f_code.co_name

class BlockMap(object):
    """A trolley object that consists of the following properties:

    Attributes:
        address: The DCC address of the trolley object.
        speed: The speed of the trolley, non-zero indicates it is moving.
        currentPosition:  This indicates the block that the trolley is currently in.
        nextPosition: This should always be currentPosition + 1.
    """

    __instance = None  # Make sure there is only one version of the blockmap
    __outputBlockDump=None
    __outputBlockInfo=None
    __outputSegmentInfo=None
    __blockMapXml=None

    def __init__(self, blockObjects=None, title=None):
        """Initialize the class"""
        super(BlockMap, self).__init__()
        logger.debug("Entering %s.%s", __name__, thisFuncName())
        self.title = title
        self.comment = []
        if blockObjects is not None:
            self._blockmap = list(blockObjects)
            self.first = None
            self.last = None
            #self.next = blockObjects
        else:
            self._blockmap = list()
            self.first = None
            self.last = None
            #self.next = blockObjects


    def __new__(cls, blockObjects=None): # __new__ always a class method
        if BlockMap.__instance is None:
            BlockMap.__instance = object.__new__(cls,blockObjects)
        return BlockMap.__instance


    def __repr__(self):
        return "<{0} {1}>".format(self.__class__.__name__, self._blockmap)


    def __len__(self):
        """List length"""
        return(len(self._blockmap))


    def size(self):
        return(len(self._blockmap))


    def __getitem__(self, ii):
        """Get a list item"""
        return self._blockmap[ii]


    def __delitem__(self, ii):
        """Delete an item"""
        del self._blockmap[ii]


    def __setitem__(self, ii, val):
        # optional: self._acl_check(val)
        self._blockmap[ii] = val


    def __str__(self):
        return str(self._blockmap)


    def reset(self):
        self.title = None
        self.comment = []
        self._blockmap = list()
        self.first = None
        self.last = None
        Block.segmentCount = 0
        return


    def insert(self, ii, val):
        # optional: self._acl_check(val)
        self._blockmap.insert(len(self._blockmap), val)
        if self.first is None:
            self.first = val
            self._blockmap[ii].next = self._blockmap[ii]
        else:
            self.last.next = val
            self._blockmap[ii].next=self.first
            self.last = val
        self.last = val


    def append(self, val):
        self.insert(len(self._blockmap), val)


    def setOutput(self,output=None):
        self.__output=output


    def setBlockInfoOutput(self,output=None):
        self.__outputBlockInfo=output


    def setBlockDumpOutput(self,output=None):
        self.__outputBlockDump=output


    def setSegmentInfoOutput(self,output=None):
        self.__outputSegmentInfo=output


    def dump(self):
        logger.debug("Entering %s.%s - output=%s", __name__, thisFuncName(), str(self.__outputBlockDump))
        printFlag = False
        if self.__outputBlockDump is None:
            printFlag = True
            self.__outputBlockDump = []
        self.__outputBlockDump.append("******************************************\n")
        self.__outputBlockDump.append(str(datetime.datetime.now())+" - Layout Map\n")
        self.__outputBlockDump.append("******************************************\n")
        self.__outputBlockDump.append("Number of Blocks: "+ str(self.size())+"\n")
        m = max(self, key=lambda x: x.segment)
        self.__outputBlockDump.append("Number of Segments: "+str(m.segment)+"\n")
        for block in self._blockmap:
            self.__outputBlockDump.append(" Address:"+str(block.address))
            self.__outputBlockDump.append(" Segment:"+str(block.segment))
            self.__outputBlockDump.append(" Occupied:"+str(block.occupied))
            self.__outputBlockDump.append(" StopReqd:"+str(block.stopRequired))
            self.__outputBlockDump.append(" WaitTime:"+str(block.waitTime))
            self.__outputBlockDump.append(" Length:"+str(block.length))
            self.__outputBlockDump.append(" Next Block:"+str(block.next.address))
            self.__outputBlockDump.append(" Description:"+str(block.description))
            self.__outputBlockDump.append("\n")
        self.__outputBlockDump.append("\n")
        if printFlag:
            print ''.join(self.__outputBlockDump)
            self.__outputBlockDump = None
        else:
            pass
            #output.scrollArea.setCaretPosition(output.scrollArea.getDocument().getLength())


    def getMapAsXml(self):
        logger.debug("Entering %s.%s", __name__, thisFuncName())
        layoutXml = ET.Element('layoutMap')
        layoutXml.set('version', '1.0')
        for individualComment in self.comment:
            layoutXml.append(ET.Comment(individualComment))
        self.setXmlElementKeyValuePair(layoutXml, 'title', self.title)
        self.setXmlElementKeyValuePair(layoutXml, 'dateCreated', datetime.datetime.now())
        self.setXmlElementKeyValuePair(layoutXml, 'dateModified', datetime.datetime.now())
        self.setXmlElementKeyValuePair(layoutXml, 'blockCount', self.size())
        m = max(self, key=lambda x: x.segment)
        self.setXmlElementKeyValuePair(layoutXml, 'segmentCount', m.segment)
        blocks = ET.SubElement(layoutXml, 'blocks')
        segment = -1
        for blk in self._blockmap:
            blocks.append(self.getBlockAsXml(blk, segment))
            segment = blk.segment
        return layoutXml


    def getBlockAsXml(self, block, segment):
        logger.debug("Entering %s.%s", __name__, thisFuncName())
        blockXml = ET.Element('block')
        self.setXmlElementKeyValuePair(blockXml, 'address', block.address)
        self.setXmlElementKeyValuePair(blockXml, 'newSegment', segment!=block.segment)
        self.setXmlElementKeyValuePair(blockXml, 'stopRequired', block.stopRequired)
        self.setXmlElementKeyValuePair(blockXml, 'waitTime', block.waitTime)
        self.setXmlElementKeyValuePair(blockXml, 'length', block.length)
        self.setXmlElementKeyValuePair(blockXml, 'description', block.description)
        return blockXml


    def setXmlElementKeyValuePair(self, xmlParent, tagName, tagValue):
        newElement = ET.SubElement(xmlParent, tagName)
        newElement.text = str(tagValue)


    def addXmlBlockToLayoutMap(self, block):
        logger.debug("Entering %s.%s", __name__, thisFuncName())
        address = block.find('address').text
        newSegment = (block.find('newSegment').text == 'True')
        stopRequired = (block.find('stopRequired').text == 'True')
        waitTime = block.find('waitTime').text
        length = block.find('length').text
        description = block.find('description').text
        logger.info('Addr:%s Seg:%s Stop:%s Time:%s Len:%s Desc:%s',address,newSegment,stopRequired,waitTime,length,description)
        self.append(Block(blockAddress=int(address), newSegment=newSegment,
                               stopRequired=stopRequired, waitTime=int(waitTime),
                               length=int(length),  description=description))


    def getNextBlock(self, val):
        return val.next


    def getBlockAddressList(self):
        blockList = ""
        for block in self._blockmap:
            blockList.append(block.address)
        return list


    def isSegmentOccupied(self, segment):
        logger.debug("Entering %s %s", __name__, thisFuncName())
        for block in self._blockmap:
            if block.segment == segment:
                if block.occupied == True:
                    logger.debug("Segment %s is OCCUPIED - Block %s",segment, str(block.address))
                    return True
        logger.debug("Segment %s is NOT OCCUPIED", segment)
        return False


    def findBlockByAddress(self,address):
        logger.debug("Entering %s.%s", __name__, thisFuncName())
        for block in self._blockmap:
            if block.address == address:
                logger.debug("Block found for address %s",str(block.address))
                return block
        return None


    def findBlockByDescription(self,description):
        logger.debug("Entering %s.%s", __name__, thisFuncName())
        for block in self._blockmap:
            if block.description == description:
                return block
        return None


    def findSegmentByAddress(self,address):
        logger.debug("Entering %s.%s", __name__, thisFuncName())
        for block in self._blockmap:
            if block.address == address:
                logger.debug("Segment found for address %s",str(block.address))
                return block.segment
        return None


    def findNextBlockByAddress(self,address):
        logger.debug("Entering %s.%s", __name__, thisFuncName())
        for block in self._blockmap:
            if block.address == address:
                return block.next
        return None


    def printBlocks(self,trolleyRoster):
        logger.debug("Entering %s.%s - output=%s", __name__, thisFuncName(), str(self.__outputBlockInfo is None))
        if self.__outputBlockInfo is None:
            print self.getBlockStatus(trolleyRoster)
        else:
            self.__outputBlockInfo.setText("")
            __doc = self.__outputBlockInfo.getDocument()
            __style = self.__outputBlockInfo.getStyle("Color Style")
            __doc.insertString(__doc.getLength(), self.getBlockStatus(trolleyRoster), __style)

  
    def getBlockStatus(self,trolleyRoster):
        logger.debug("Entering %s.%s", __name__, thisFuncName())
        __blockStatusInfo = []
        __blockStatusInfo.append("*******************************************\n")
        __blockStatusInfo.append(str(datetime.datetime.now())+" - BlockStatus\n")
        __blockStatusInfo.append("*******************************************\n")
        for block in self._blockmap:
            __blockStatusInfo.append("{:<3}".format(block.address))
            if block.isStopRequired():
                __blockStatusInfo.append('s ')
            else:
                __blockStatusInfo.append('  ')
        __blockStatusInfo.append("\n")
        for block in self._blockmap:
            #print seg.blockAddress
            if block.isBlockOccupied()== True:
                __blockStatusInfo.append("{:<4}".format(trolleyRoster.findByCurrentBlock(block.address).address)+ " ")
                #print "ttt  ",
            else:
                __blockStatusInfo.append("**** ")
        #__blockStatusInfo.append("\n\n")
        return ''.join(__blockStatusInfo)


    def printSegments(self,trolleyRoster):
        logger.debug("Entering %s.%s - output=%s", __name__, thisFuncName(), str(self.__outputSegmentInfo is None))
        if self.__outputSegmentInfo is None:
            print self.getSegmentStatus(trolleyRoster)
        else:
            self.__outputSegmentInfo.setText("")
            __doc = self.__outputSegmentInfo.getDocument()
            __style = self.__outputSegmentInfo.getStyle("Color Style")
            __doc.insertString(__doc.getLength(), self.getSegmentStatus(trolleyRoster), __style)

  
    def getSegmentStatus(self,trolleyRoster):   
        logger.debug("Entering %s.%s", __name__, thisFuncName())
        __segmentStatusInfo = []
        __segmentStatusInfo.append("*********************************************\n")
        __segmentStatusInfo.append(str(datetime.datetime.now())+" - SegmentStatus\n")
        __segmentStatusInfo.append("*********************************************\n")
        #segments = {self.segment for segment in self._blockmap}
        segments = list(set([block.segment for block in self._blockmap]))
        segments.sort()
        for segment in segments:
            __segmentStatusInfo.append("{0:<4}".format(segment)+" ")
        __segmentStatusInfo.append("\n")
        for segment in segments:
            if self.isSegmentOccupied(segment)== True:
                __segmentStatusInfo.append("{0:<4}".format(trolleyRoster.findByCurrentSegment(segment).address)+" ")
            else:
                __segmentStatusInfo.append("**** ")
        #__segmentStatusInfo.append("\n")
        return ''.join(__segmentStatusInfo)


    def buildDefaultLayoutMap(self):
        logger.debug("Entering %s.%s", __name__, thisFuncName())
        self.title="NVMR Automated Trolley Layout"
        self.comment.append(r'# Generated by NVMR Automated Trolley Sequencer')
        self.comment.append(r'# Create a layoutMap map that consists of consecutive blocks representing a complete')
        self.comment.append(r'# circuit. The map also identifies the segment associated with each block. This is')
        self.comment.append(r'# done because so a multiple block area can be identified as occupied.')
        self.comment.append(r'#    ')
        self.comment.append(r'#        ==100/1==                                                                                      ====103/6===* ')
        self.comment.append(r'#      /          \                                                                                    /             \ ')
        self.comment.append(r'#     /            *                                                                                  /               \ ')
        self.comment.append(r'#     *             \                                                                                *                | ')
        self.comment.append(r'#      \             ==106/10===*====121/9=====*===123/8===*=====120/7====*=\                       /                / ')
        self.comment.append(r'#       \                                                                    >==102/6==*===107/6===<=*====104/6====/ ')
        self.comment.append(r'#         =====101/2=====*======118/3======*=====116/4=====*=====117/5====*=/')
        self.comment.append(r'#')
        self.comment.append(r'# Trolley Sequencing')
        self.comment.append(r'# Block 100 - Thomas Loop')
        self.comment.append(r'# Block 101 - Spencer Station Aisle Side')
        self.comment.append(r'# Block 118 - Spencer Boulevard Aisle Side')
        self.comment.append(r'# Block 116 - Traffic Intersection Aisle Side')
        self.comment.append(r'# Block 117 - Single Track Signal Block Aisle Side')
        self.comment.append(r'# Block 102 - Single Track Spencer Side')
        self.comment.append(r'# Block 107 - Single Track Majolica Side')
        self.comment.append(r'# Block 104 - Majolica Outbound Loop')
        self.comment.append(r'# Block 103 - Majolica Return Loop')
        self.comment.append(r'# Block 107 - Single Track Majolica End')
        self.comment.append(r'# Block 102 - Single Track Spencer End')
        self.comment.append(r'# Block 120 - Spencer Boulevard Interchange Yard Side')
        self.comment.append(r'# Block 123 - Spencer Boulevard Shelter Yard Side')
        self.comment.append(r'# Block 121 - Spencer Boulevard Buckholtz Yard Side')
        self.comment.append(r'# Block 106 - Spencer Station Yard Side')
        self.append(Block(blockAddress=100, newSegment=True,  stopRequired=True,  length=24,  description='Thomas Loop'))
        self.append(Block(blockAddress=101, newSegment=True,  stopRequired=False, length=130, description='Spencer Station Aisle Side'))
        self.append(Block(blockAddress=118, newSegment=True,  stopRequired=False, length=30,  description='Spencer Boulevard Buckholtz Aisle Side'))
        self.append(Block(blockAddress=116, newSegment=True,  stopRequired=True,  length=135, description='Spencer Boulevard Traffic Intersection Aisle Side'))
        self.append(Block(blockAddress=117, newSegment=True,  stopRequired=False, length=20,  description='Spencer Boulevard Aisle Track Signal'))
        self.append(Block(blockAddress=102, newSegment=True,  stopRequired=False, length=48,  description='Single Track Spencer Side Outbound'))
        self.append(Block(blockAddress=107, newSegment=False, stopRequired=False, length=40,  description='Single Track Majolica Side Outbound'))
        self.append(Block(blockAddress=104, newSegment=False, stopRequired=False, length=40,  description='Majolica Outbound Loop'))
        self.append(Block(blockAddress=103, newSegment=False, stopRequired=False, length=30,  description='Majolica Return Loop'))
        self.append(Block(blockAddress=107, newSegment=False, stopRequired=False, length=40,  description='Single Track Majolica End Returning'))
        self.append(Block(blockAddress=102, newSegment=False, stopRequired=False, length=48,  description='Single Track Spencer End Returning'))
        self.append(Block(blockAddress=120, newSegment=True,  stopRequired=False, length=114, description='Spencer Boulevard WNC Interchange Yard Side'))
        self.append(Block(blockAddress=123, newSegment=True,  stopRequired=True,  length=72,  description='Spencer Boulevard Bus Shelter Yard Side'))
        self.append(Block(blockAddress=121, newSegment=True,  stopRequired=False, length=84,  description='Spencer Boulevard Buckholtz Yard Side'))
        self.append(Block(blockAddress=106, newSegment=True,  stopRequired=True,  length=28,  description='Spencer Station Yard Side'))


    def loadLayoutMapFromXml(self, layoutMapFile):
        logger.debug("Entering %s.%s", __name__, thisFuncName())
        logger.info('Layout Map File: %s', layoutMapFile)
        try:
            logger.info("Loading Layout Tree")
            tree = ET.parse(str(layoutMapFile))
            blocks = tree.find('blocks')
            if blocks is None:
                raise Exception('File does not contain a layout map.')
            logger.info("Number of BLocks: %s", len(blocks))
            self.reset()
            self.title =  tree.find('title')
            for block in blocks.iter(tag = 'block'):
                self.addXmlBlockToLayoutMap(block)
        except Exception, e:
            logger.warning(e)
            logger.warning('Unable to open Layout Map: %s - Building Default Layout', layoutMapFile)

