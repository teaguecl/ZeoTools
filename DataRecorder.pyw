#!/usr/bin/python -d
# -*- coding: utf-8 -*-

# DataRecorder.pyw
#
# Streams the real-time data coming from a Zeo unit into .csv files.

import sys
import time
import csv
import os
from serial import *
from glob import glob
from ZeoRawData import BaseLink, Parser
#import DynamicAlarm
from DynamicAlarm import *

def scanPorts():
    portList = []
    
    # Helps find USB>Serial converters on linux
    for p in glob('/dev/ttyUSB*'):
        portList.append(p)
    #Linux and Windows
    for i in range(256):
        try:
            ser = Serial(i)
            if ser.isOpen():
                #Check that the port is actually valid
                #Otherwise invalid /dev/ttyS* ports may be added
                portList.append(ser.portstr)
            ser.close()
        except SerialException:
            pass

    return portList

class ZeoToCSV:
    def __init__(self, parent=None):
        samplesFileName = 'raw_samples.csv'
        sgramFileName = 'spectrogram.csv'
        hgramFileName = 'hypnogram.csv'
        eventsFileName = 'events.csv'
        
        self.hypToHeight = {'Undefined' : 0,
                            'Deep'      : 1,
                            'Light'     : 2,
                            'REM'       : 3,
                            'Awake'     : 4}
        
        # Only create headers when the files are being created for the first time.
        # After that, all new data should be appended to the existing files.
        samplesNeedHeader = False
        sgramNeedHeader = False
        hgramNeedHeader = False
        eventsNeedHeader = False
        
        if not os.path.isfile(samplesFileName):
            samplesNeedHeader = True
        
        if not os.path.isfile(sgramFileName):
            sgramNeedHeader = True
        
        if not os.path.isfile(hgramFileName):
            hgramNeedHeader = True
    
        if not os.path.isfile(eventsFileName):
            eventsNeedHeader = True
        
        self.rawSamples = csv.writer(open(samplesFileName, 'a+b'), delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)
        self.spectrogram = csv.writer(open(sgramFileName, 'a+b'), delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)
        self.hypnogram = csv.writer(open(hgramFileName, 'a+b'), delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)
        self.eventsOut = csv.writer(open(eventsFileName, 'a+b'), delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        if samplesNeedHeader:
            self.rawSamples.writerow(["Time Stamp","Version","SQI","Impedance","Bad Signal (Y/N)","Voltage (uV)"])
        
        if sgramNeedHeader:
            self.spectrogram.writerow(["Time Stamp","Version","SQI","Impedance","Bad Signal (Y/N)",
                                    "2-4 Hz","4-8 Hz","8-13 Hz","11-14 Hz","13-18 Hz","18-21 Hz","30-50 Hz"])
        
        if hgramNeedHeader:
            self.hypnogram.writerow(["Time Stamp","Version","SQI","Impedance","Bad Signal (Y/N)","State (0-4)","State (named)"])
        
        if eventsNeedHeader:
            self.eventsOut.writerow(["Time Stamp","Version","Event"])
    
    def updateSlice(self, slice):
        
        timestamp = slice['ZeoTimestamp']
        ver = slice['Version']
                                        
        if not slice['SQI'] == None:
            sqi = str(slice['SQI'])
        else:
            sqi = '�'
                                        
        if not slice['Impedance'] == None:
            imp = str(int(slice['Impedance']))
        else:
            imp = '�'

        if slice['BadSignal']:
            badSignal = 'Y'
        else:
            badSignal = 'N'

        if not slice['Waveform'] == []:
            self.rawSamples.writerow([timestamp,ver,sqi,imp,badSignal] + slice['Waveform'])

        if len(slice['FrequencyBins'].values()) == 7:
            f = slice['FrequencyBins']
            bins = [f['2-4'],f['4-8'],f['8-13'],f['11-14'],f['13-18'],f['18-21'],f['30-50']]
            self.spectrogram.writerow([timestamp,ver,sqi,imp,badSignal] + bins)

        if not slice['SleepStage'] == None:
            stage = slice['SleepStage']
            self.hypnogram.writerow([timestamp,ver,sqi,imp,badSignal] +
                                     [self.hypToHeight[stage],str(stage)])
    
    def updateEvent(self, timestamp, version, event):
        self.eventsOut.writerow([timestamp,version,event])

if __name__ == '__main__':
    
    # Find ports.
    # TODO: offer a command line option for selecting ports.
    ports = scanPorts()
    if len(ports) > 0 :
        print "Found the following ports:"
        for port in ports:
            print port
        print ""
        print "Using port "+ports[0]
        print ""
        portStr = ports[0]
    else:
        sys.exit("No serial ports found.")
    
    # Initialize
    output = ZeoToCSV()
    link = BaseLink.BaseLink(portStr)
    parser = Parser.Parser()
    alarm = DynamicAlarm()
    # Add callbacks
    link.addCallback(parser.update)
    parser.addEventCallback(output.updateEvent)
    parser.addSliceCallback(output.updateSlice)
    parser.addEventCallback(alarm.updateEvent)
    parser.addSliceCallback(alarm.updateSlice)
    # Start Link
    link.start()
    
    # TODO: perhaps use a more forgiving key?  This would require polling the keyboard without blocking.
    print "Hit ctrl-C at any time to stop."
    while True:
        time.sleep(5)
    
    sys.exit()
