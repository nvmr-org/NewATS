import datetime
import logging
import jmri
from random import randint
from classes.trolleyRoster import TrolleyRoster
from classes.messengerFacade import Messenger

logger = logging.getLogger("ATS."+__name__)
trolleyRoster = TrolleyRoster()
msg = Messenger()

class TrolleyAutomation(jmri.jmrit.automat.AbstractAutomaton):
    logger = logging.getLogger(__name__)
    simulatorEnabled = False
    def init(self):
        logger.info("Initialize Trolley Automation")
        pass


    def handle(self):
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
        if self.isRunning():
            logger.debug("Automation is running")
            if trolleyRoster.checkIfAllTrolleysAreRegistered():
                trolleyRoster.processAllTrolleyMovement()
                if TrolleyAutomation.simulatorEnabled : self.simulateAllMovement()
                trolleyRoster.refreshTrolleysSlots()
            else:
                trolleyRoster.registerOneTrolley()
        else:
            logger.info("Automation is NOT running")
        self.waitMsec(250)
        return True


    def simulateAllMovement(self):
        event = None
        for trolley in trolleyRoster:
            if trolley.getSpeed() > 0:
                now = datetime.datetime.now()
                travelTime = (now - trolley.startTime).total_seconds()
                if travelTime > (trolley.currentPosition.length / 4.0):
                    realSpeed = trolley.currentPosition.length / travelTime
                    logger.info("Simulating event for SensorID: %s by Trolley: %s - Time:%s Length:%s RealSpeed:%s", trolley.nextPosition.address, 
                                trolley.address, travelTime, trolley.currentPosition.length, str("{:.2f}".format(realSpeed)) )
                    event =  trolley.nextPosition.address
                # Simulate random noise on used block
                if randint(0, 999) > 990:
                    event =  trolley.currentPosition.address
        if event: msg.sendSenorReportMsg(event)
        return event


    def isSimulatorEnabled(self):
        return TrolleyAutomation.simulatorEnabled


    def setSimulatorState(self, state):
        TrolleyAutomation.simulatorEnabled = state


    def setSimulatorEnabled(self):
        TrolleyAutomation.simulatorEnabled = True


    def setSimulatorDisabled(self):
        TrolleyAutomation.simulatorEnabled = False
