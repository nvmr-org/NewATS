'''
Created on Nov 18, 2016

@author: ttb
'''
import sys

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
    multipleDetected = False
    
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
            
        """Return a Trolley object whose id is *id* and starting position and next 
        position are the 0th and 1st blocks if not provided.  Priority should reflect the 
        order of the trolley's on the Layout."""
        #self.trolleys = list(trolleyObjects)
        #TrolleyRoster.deviceCount += 1
        
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
        print 'TrolleyRoster.append'
        if self.findByAddress(trolley.address) != None:
            sys.exit("Error: Attempt to register multiple trolleys to the same address:" + trolley.address)
        if self.findByCurrentBlock(trolley.currentPosition.address):
            print 'Warning: Multiple trolleys registered to the same block: ', trolley.currentPosition.address
            print 'Warning: Trolleys will depart in the order they were registered.'
            self.multipleDetected = True
        print "Requesting Slot for Trolley:", trolley.address
        trolley.requestSlot(trolley.address)
        self.insert(len(self._list), trolley)
        
    def dump(self):
        print "**************"
        print "TrolleyRoster"
        print "**************"
        if self.multipleDetected:
            print 'Warning: Multiple trolleys registered to the same block. '

        print "Roster Size: ", self.size()
        print "MultipleState: ",self.multipleDetected
        for trolley in self._list:
            print "Id:", trolley.priority, 
            print " Address:", trolley.address, 
            print " Speed:", trolley.speed,
            print " Current Position:", trolley.currentPosition.address, 
            print " Next Position:", trolley.nextPosition.address,
            print " Next Trolley:", self.getNextTrolley(trolley).address,
            print " Throttle:", trolley.throttle

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