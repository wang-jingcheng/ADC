import sys
import numpy as np
from PyQt5 import QtWidgets
import pyqtgraph as pg
from PyQt5.QtCore import QTimer

import time
import ADS1263
import RPi.GPIO as GPIO
import csv

def get_brain_signal_data(class_ADC):
    
        
    REF = 2.5          # Modify according to actual voltage
                        # external AVDD and AVSS(Default), or internal 2.5V 
    
    # ADC1 test part
    TEST_ADC1       = True
    # ADC2 test part
    TEST_ADC2       = False
    # ADC1 rate test part, For faster speeds use the C program
    TEST_ADC1_RATE   = False
    # RTD test part 
    TEST_RTD        = False

    channel_value = 0
    
    if(TEST_ADC1):       # ADC1 Test
        # channelList = [0]  # The channel must be less than 10
        # ADC_Value = class_ADC.ADS1263_GetAll(channelList)    # get ADC1 value
        channelList = [0]
        ADC_Value_list = class_ADC.ADS1263_GetAll(channelList)
        ADC_Value = ADC_Value_list[0]
        # ADC_Value = class_ADC.ADS1263_Read_ADC_Data()
        if(ADC_Value>>31 ==1):
            
            channel_value = -(REF*2 - ADC_Value * REF / 0x80000000)
            # print("ADC1 IN%d = -%lf" %(i, (REF*2 - ADC_Value[i] * REF / 0x80000000)))  
        else:
        
            channel_value = (ADC_Value * REF / 0x7fffffff)
            # print("ADC1 IN%d = %lf" %(i, (ADC_Value[i] * REF / 0x7fffffff)))   # 32bit    
        
    return channel_value

class ADCPlot(QtWidgets.QMainWindow):
    def __init__(self,adc_class):
        super().__init__()
        self.adc_class = adc_class
        self.screen_refresh_rate = 30
        self.sps = 120
        self.time = 4 
        self.timepoint = self.sps*self.time
        # self.data = np.zeros(self.timepoint)
        self.buffer = np.zeros(self.timepoint)
        self.buffer_index = 0
        
        self.is_paused = False
        self.initUI()
        
        
    def initUI(self):
        
        
        self.centralWidget = QtWidgets.QWidget()
        self.setCentralWidget(self.centralWidget)
        
        self.layout = QtWidgets.QVBoxLayout()
        self.centralWidget.setLayout(self.layout)
        
        self.plotWidget = pg.PlotWidget()
        self.layout.addWidget(self.plotWidget)
        
        self.plotData = self.plotWidget.plot()
        
        
        self.plotWidget.setYRange(-2.5,2)
        self.xrange = (np.arange(self.timepoint)-self.timepoint)/self.sps*1000
        
        self.pauseButton = QtWidgets.QPushButton("Pause")
        self.pauseButton.clicked.connect(self.toggle_pause)
        self.layout.addWidget(self.pauseButton)
        
        self.saveButton = QtWidgets.QPushButton("Save Data")
        self.saveButton.clicked.connect(self.save_data)
        self.layout.addWidget(self.saveButton)
        
    def update(self):
        if not self.is_paused :
            self.plotData.setData(self.xrange, np.roll(self.buffer,-self.buffer_index))
        
    def sample(self):
        if not self.is_paused :
            new_data = get_brain_signal_data(self.adc_class)
            # print(self.buffer_index)
            self.buffer[self.buffer_index] = new_data
            self.buffer_index = (self.buffer_index + 1) % self.timepoint
        
        
    def start(self):
        # print(class_ADC)
        self.sample_timer = QTimer()
        self.sample_timer.timeout.connect(self.sample)
        self.sample_timer.start(1000//self.sps)
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start(1000 // self.screen_refresh_rate)
        
    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pauseButton.setText("Resume")
        else:
            self.pauseButton.setText("Pause")
    def save_data(self):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f'adc_data_{timestamp}.csv'
        with open(filename,'w',newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Index","Value"])
            for i in range(self.timepoint):
                writer.writerow([i,self.buffer[(self.buffer_index+i) % self.timepoint]])
        print("data saved!")
if __name__ == "__main__":

    try:
        ADC = ADS1263.ADS1263()
        
        
        if (ADC.ADS1263_init_ADC1('ADS1263_400SPS') == -1):
            exit()
        ADC.ADS1263_SetMode(1) # 0 is singleChannel, 1 is diffChannel
        
        
        app = QtWidgets.QApplication(sys.argv)
        ADCPlot1 = ADCPlot(ADC)
        ADCPlot1.resize(800,600)
        ADCPlot1.show()
        ADCPlot1.start()
        sys.exit(app.exec_())
        
        ADC.ADS1263_Exit()
        
    except IOError as e:
        print(e)
   
    except KeyboardInterrupt:
        print("ctrl + c:")
        print("Program end")
        ADC.ADS1263_Exit()
        exit()
    

