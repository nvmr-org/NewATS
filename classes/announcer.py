import os
import subprocess

class MessageAnnouncer(object):

    __instance = None
    __textToSpeechCmd = None

    def __init__(self,swingControlToMonitor):
        super(MessageAnnouncer,self).__init__()
        self.__swingControl = swingControlToMonitor
        if self.which('nircmd.exe'): MessageAnnouncer.__textToSpeechCmd=['nircmdc.exe', 'speak', 'text', '%s', '0', '100']
        if self.which('espeak'): MessageAnnouncer.__textToSpeechCmd=['espeak', '\"%s\"']
        pass


    def __new__(cls,swingControlToMonitor):
        if MessageAnnouncer.__instance is None:
            MessageAnnouncer.__instance = object.__new__(cls,swingControlToMonitor)
        return MessageAnnouncer.__instance

    def announceMessage(self, messageToAnnounce):
        if self.__swingControl is None: return
        if MessageAnnouncer.__textToSpeechCmd and self.__swingControl.isSelected():
            messageCmd = map(lambda x: str.replace(x, "%s", messageToAnnounce) ,MessageAnnouncer.__textToSpeechCmd)
            subprocess.Popen(messageCmd)
        return


    def which(self,program):
        def is_exe(fpath):
            return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
        fpath, fname = os.path.split(program)
        if fpath:
            if is_exe(program):
                return program
        else:
            pathsToCheck = os.environ["PATH"].split(os.pathsep)
            pathsToCheck.append('C:\\Program Files (x86)\\JMRI')
            for path in pathsToCheck:
                exe_file = os.path.join(path, program)
                if is_exe(exe_file):
                    return exe_file
        return None
