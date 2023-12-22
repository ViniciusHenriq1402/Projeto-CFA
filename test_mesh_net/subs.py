# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
from machine import Pin
from utime import sleep
from mesh import MeshNet

def toggle_light():
    led.value(not led.value())

#Usado para teste da rede mesh, metodos publisher de 1 a 3 e subscriber1,

# ----------------------------
mesh_net = MeshNet('subscriber1', on_news )
def subscriber1():
    mesh_net.subscribe('button01')
    mesh_net.subscribe('button02')
    mesh_net.subscribe('button03')
# ----------------------------

def on_news(self, data_id, topic, publisher_node_name, payload, sender_node_name):
    print(f'data_id: {data_id}, topic: {topic}, publisher_node_name: {publisher_node_name}, payload: {payload}, sender_node_name: {sender_node_name}')
    return True

#Sinaliza que a rede mesh ja esta configurada
led = Pin(2, Pin.OUT)
led.on()
sleep(0.1)
led.off()
sleep(0.1)
led.on()
sleep(0.1)
led.off()

#chame o metodo subscriber1 (subscribers nao precisam de for pois se inscrevem em um topico e aguardam atualizacao sobre este topico
   
subscriber1()

# ----------------------------
