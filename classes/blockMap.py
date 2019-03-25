'''
Created on Nov 18, 2016

@author: ttb
'''
import logging
import datetime

logger = logging.getLogger("ATS."+__name__)

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

    def __init__(self, blockObjects=None):
        """Initialize the class"""
        super(BlockMap, self).__init__()
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
        logger.debug("Entering blockMap.dump - output=%s", str(self.__outputBlockDump))
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
            self.__outputBlockDump.append("Id:"+str(block.index))
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


    def getNextBlock(self, val):
        return val.next


    def getBlockAddressList(self):
        blockList = ""
        for block in self._blockmap:
            blockList.append(block.address)
        return list


    def isSegmentOccupied(self, segment):
        logger.debug("Entering blockMap.isSegmentOccupied %s",segment)
        for block in self._blockmap:
            if block.segment == segment:
                if block.occupied == True:
                    logger.debug("Segment %s is OCCUPIED - Block %s",segment, str(block.address))
                    return True
        logger.debug("Segment %s is NOT OCCUPIED", segment)
        return False


    def findBlockByAddress(self,address):
        logger.debug("Entering blockMap.findBlockByAddress")
        for block in self._blockmap:
            if block.address == address:
                logger.debug("Block found for address %s",str(block.address))
                return block
        return None


    def findBlockByDescription(self,description):
        logger.debug("Entering blockMap.findBlockByDescription")
        for block in self._blockmap:
            if block.description == description:
                return block
        return None


    def findSegmentByAddress(self,address):
        logger.debug("Entering blockMap.findSegmentByAddress")
        for block in self._blockmap:
            if block.address == address:
                logger.debug("Segment found for address %s",str(block.address))
                return block.segment
        return None


    def findNextBlockByAddress(self,address):
        logger.debug("Entering blockMap.findNextBlockByAddress")
        for block in self._blockmap:
            if block.address == address:
                return block.next
        return None


    def printBlocks(self,trolleyRoster):
        logger.debug("Entering blockMap.printBlocks - output=%s", str(self.__outputBlockInfo))
        if self.__outputBlockInfo is None:
            print self.getBlockStatus(trolleyRoster)
        else:
            self.__outputBlockInfo.setText("")
            __doc = self.__outputBlockInfo.getDocument()
            __style = self.__outputBlockInfo.getStyle("Color Style")
            __doc.insertString(__doc.getLength(), self.getBlockStatus(trolleyRoster), __style)

  
    def getBlockStatus(self,trolleyRoster):
        logger.debug("Entering blockMap.getBlockStatus")
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
        logger.debug("Entering blockMap.printSegments - output=%s", str(self.__outputSegmentInfo))
        if self.__outputSegmentInfo is None:
            print self.getSegmentStatus(trolleyRoster)
        else:
            self.__outputSegmentInfo.setText("")
            __doc = self.__outputSegmentInfo.getDocument()
            __style = self.__outputSegmentInfo.getStyle("Color Style")
            __doc.insertString(__doc.getLength(), self.getSegmentStatus(trolleyRoster), __style)

  
    def getSegmentStatus(self,trolleyRoster):   
        logger.debug("Entering blockMap.getSegmentStatus")
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