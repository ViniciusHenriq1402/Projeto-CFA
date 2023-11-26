# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)


#teste para um nodo publisher
#incluido no boot do microcontrolador

from machine import Pin
def toggle_light():
    led = Pin(2, Pin.OUT)
    led.value(not led.value())
    
import machine; 
def reset():
    machine.reset()

from utime import sleep

from mesh import MeshNet

def on_news(self,data_id,topic,sender_node_name,payload, received):
    print('data_id:{}, topic:{}, sender_node_name{}, payload:{}, received:{}'.format(data_id, topic, sender_node_name,  payload, received))
    return True
    
MeshNet('publisher2', on_news )   
  
def publisher(): #publisher

    while True:
        
        topic = 'button02'
        data = 'not pressed'
        MeshNet.post(topic, data)
        sleep(4)










