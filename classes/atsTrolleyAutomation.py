import datetime
import logging
import sys
import jmri
from random import randint
from classes.trolleyRoster import TrolleyRoster
#from classes.messengerFacade import Messenger

logger = logging.getLogger("ATS."+__name__)
logger.setLevel(logging.INFO)
thisFuncName = lambda n=0: sys._getframe(n + 1).f_code.co_name
trolleyRoster = TrolleyRoster()
#msg = Messenger()

class TrolleyAutomation(jmri.jmrit.automat.AbstractAutomaton):
    #from classes.messengerFacade import Messenger
    #msg = Messenger()
    #msg.createListener()

    simulatorEnabled = False
    SIMULATOR_TIME_MULTIPLIER = 4.0
    HANDLER_TIME_SLICE_MILLISEC = 250
    REQUEST_THROTTLE = False
    THROTTLE_WAIT_TIME = 5
    THROTTLE_REQUEST_ADDRESS = None

    def init(self):
        logger.info("Initialize Trolley Automation")
        pass


    def handle(self):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        # handle() is called repeatedly until it returns false.
        #
        # We wait until handle gets called to check if trolleys
        # in the roster have been assigned slots.  If at least 
        # one trolley is not assigned we register it.  We wait
        # for all trolleys to be registered before starting the
        # movement checks.
        #
        # This is where we should also check that all the trolleys
        # in the roster are current.
        if (TrolleyAutomation.REQUEST_THROTTLE) :
            self.getNewThrottle()
            TrolleyAutomation.REQUEST_THROTTLE = False
            TrolleyAutomation.THROTTLE_REQUEST_ADDRESS = None

        if self.isRunning():
            logger.trace("Automation is running")
            if trolleyRoster.checkIfAllTrolleysAreRegistered():
                trolleyRoster.processAllTrolleyMovement()
                if self.simulatorEnabled : self.simulateAllMovement()
                #trolleyRoster.refreshTrolleysSlots()
            else:
                trolleyRoster.registerOneTrolley()
        #else:
            #logger.trace("Automation is NOT running")
        self.waitMsec(self.HANDLER_TIME_SLICE_MILLISEC)
        return True


    def simulateAllMovement(self):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        event = None
        for trolley in trolleyRoster:
            if trolley.getSpeed() > 0:
                now = datetime.datetime.now()
                travelTime = (now - trolley.startTime).total_seconds()
                travelLength = travelTime * self.SIMULATOR_TIME_MULTIPLIER
                logger.debug("Simulator - Trolley: %s - travelTime: %s TravelLength:%s",trolley.address, travelTime, travelLength)
                if travelLength > (trolley.currentPosition.length):
                    realSpeed = trolley.currentPosition.length / travelTime
                    logger.info("Simulating event for SensorID: %s by Trolley: %s - Time:%s Length:%s RealSpeed:%s", trolley.nextPosition.address, 
                                trolley.address, travelTime, trolley.currentPosition.length, str("{:.2f}".format(realSpeed)) )
                    event =  trolley.nextPosition.address
                # Simulate random noise on used block
                if randint(0, 999) > 990:
                    event =  trolley.currentPosition.address
        if event: self.msg.sendSenorReportMsg(event)
        return event


    def isSimulatorEnabled(self):
        return self.simulatorEnabled


    def setDebugLevel(self,state):
        logger.setLevel(logging.DEBUG if state else logging.INFO)
        for handler in logging.getLogger("ATS").handlers:
            handler.setLevel(logging.DEBUG)
        logger.debug("%s.%s - Logger:%s - Set Debug Flag:%s", __name__, thisFuncName(),str(logger),str(state))


    def getDebugLevel(self):
        return logger.level


    def setSimulatorState(self, state):
        self.simulatorEnabled = state
        logger.info("AUTOMATION - Set Simulator State: %s, %s",state, self.simulatorEnabled)


    def setSimulatorEnabled(self):
        self.simulatorEnabled = True


    def setSimulatorDisabled(self):
        self.simulatorEnabled = False


    def getAutomationName(self):
        return self.getName()

    def prepareThrottleRequest(self, address):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        TrolleyAutomation.THROTTLE_REQUEST_ADDRESS = address
        TrolleyAutomation.REQUEST_THROTTLE = True
        logger.debug("%s.%s - Requesting Address:%s - %s", __name__, thisFuncName(),TrolleyAutomation.THROTTLE_REQUEST_ADDRESS,TrolleyAutomation.REQUEST_THROTTLE)


    def getNewThrottle(self):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        isLong = True if TrolleyAutomation.THROTTLE_REQUEST_ADDRESS > 100 else False
        trolley = trolleyRoster.findByAddress(TrolleyAutomation.THROTTLE_REQUEST_ADDRESS)
        logger.debug("getNewThrottle -  address: %s isLong: %s", TrolleyAutomation.THROTTLE_REQUEST_ADDRESS, isLong)
        logger.debug("getNewThrottle -  trolley address: %s", trolley.address)
        try:
            logger.debug("getNewThrottle -  Calling getThrottle")
            trolley.slotRequestSent = True
            trolley.throttle = self.getThrottle(TrolleyAutomation.THROTTLE_REQUEST_ADDRESS, isLong, TrolleyAutomation.THROTTLE_WAIT_TIME)  # address, long address = true
            trolley.slotId = str(trolley.throttle)
            logger.debug("getNewThrottle -  ThrottleId: %s ReqSent:%s", str(trolley.throttle),trolley.slotRequestSent)
            logger.info("Trolley %s -  Throttle Assigned: %s", trolley.address, str(trolley.throttle))
            trolleyRoster.dump()
        except Exception as e:
            trolley.throttle = None
            logger.warn("getNewThrottle -  Throttle Exception: %s", e)
            logger.warn("getNewThrottle -  Unable to get throttle")
        logger.debug("getNewThrottle -  Sent Throttle Request: %s",str(trolley.throttle))
        logger.trace("Exiting %s.%s", __name__, thisFuncName())
        return 
