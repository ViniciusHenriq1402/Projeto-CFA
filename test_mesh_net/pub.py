# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
from machine import Pin
from utime import sleep
from mesh import MeshNet

def toggle_light():
    led.value(not led.value())

#Usado para teste da rede mesh, metodos publisher de 1 a 3 e subscriber1,
#cada dispositivo mantem somente UM dos blocos abaixo, deletando os demais

# ----------------------------
mesh_net = MeshNet('publisher1')
def publisher1(): #publisher
    topic = 'button01'
    data = 'not pressed'
    mesh_net.post(topic, data)
# ----------------------------
mesh_net = MeshNet('publisher2')
def publisher2(): #publisher     
    topic = 'button02'
    data = 'not pressed'
    mesh_net.post(topic, data)
# ----------------------------
mesh_net = MeshNet('publisher3')
def publisher3(): #publisher     
    topic = 'button03'
    data = 'not pressed'
    mesh_net.post(topic, data)
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

#bloco abaixo com codigo para publishers afim de fazer testes, ao apertar o botao boot do dispositivo ele publicara 

# ----------------------------
#botao boot
pin_boot = Pin(0, Pin.IN, Pin.PULL_UP)  # Pino do botão BOOT
# Loop principal para ler o botao boot do esp32
while True:
    if pin_boot.value() == 0:
        #mudar nome do metodo para o metodo de teste 
        publisher1()
        sleep(0.5)
# ----------------------------
   
