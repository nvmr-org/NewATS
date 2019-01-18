import logging
import time
import java.awt.event
from classes.trolleyRoster import TrolleyRoster
from classes.messengerFacade import Messenger

logger = logging.getLogger("ATS."+__name__)
trolleyRoster = TrolleyRoster()
msg = Messenger()

# *************************************************************************
# WindowListener is a interface class and therefore all of it's           *
# methods should be implemented even if not used to avoid AttributeErrors *
# *************************************************************************
class AtsWinListener(java.awt.event.WindowListener):
    logger = logging.getLogger(__name__)
    def windowClosing(self, event):
        global killed, fr
        killed = True #this will signal scanReporter thread to exit
        trolleyRoster.destroy()
        msg.destroyListener()
        return

    def windowActivated(self, event):
        return

    def windowDeactivated(self, event):
        return

    def windowOpened(self, event):
        return

    def windowClosed(self, event):
        global fr
        trolleyRoster.destroy()
        time.sleep(3.0) #wait 3 seconds before moving on to allow last free to complete
        logger.info('slots freed and exited')
        msg.destroyListener()
        return

    def windowIconified(self, event):
        return

    def windowDeiconified(self, event):
        return

