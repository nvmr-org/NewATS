# Automated Trolley Sequencer
This code uses LocoNet sensor messages to control the movement of trolleys on a DCC controlled
layout.  The software allows the creation of a layout map consisting of consecutive blocks
representing a complete path to be traversed by trolleys.  Each block is associated with a 
LocoNet sensorID and multiple blocks can be grouped together to perform as a single segment for 
occupancy detection.  Multiple trolleys are grouped together as a roster defining each trolley's
DCC address, starting position on the layout, and other attributes.  When run through JMRI, each
trolley is evaluated as to whether it should move or stop based on the occupancy status of blocks
defined in the layout map and other criteria.  Ths iapplication was based ona ATS.py written by
Gerry Wolfson (October 1942 - April 2018), Member: [Northern Virginia Model Railroad] (http://nvmr.org)

##Installation
Download a copy of the NewATS source code as a .zip file.  Extract the contents of the .zip file
to your JMRI/jython directory.
