

import gc
from micropython import const
from machine import Timer
from utime import sleep, ticks_ms, ticks_diff
import webrepl

import network
import espnow
gc.collect()




_verboseA = False

_t_stump    = 0

_CH_SPLIT   = '~'
_BCAST      = b'\xff'*6 #broadcast MAC address
_MAX_ORDER  = const(999)

_PUB_FREQ   = 3*1000 # publications frequence, 3*1000 msec


def pid_gen():
    pid = 0
    while True:
        pid = (pid + 1)%_MAX_ORDER
        yield pid

class Data:
    def __init__(self, topic='', sender_node_name='', payload=bytearray()):
        self.data_id = 0  # only the publisher can change it
        self.topic = topic  # topic name
        self.sender_node_name = sender_node_name
        self.payload = payload
        self.received = False  # True if any subscriber received this data
        
#class containing subscriber/publisher settings
class MessageSetting():
    def __init__(self):
        self.is_publisher = True #boolean to verify if node is publishing to the topic
        self.MAC = _BCAST  # for Subs - Publishers MAC-address - NOT USED (for now)
        self.QoS = 0  # Quality of Service ( 0:Fire&Forget, 1:At least once, 2:Exactly once ) - NOT USED
        self.t_exp = 0  # expire time for News
        self.t_stamp = 0  # timestamp of last message received
        self.latest_id = 0
        self.latest_data = Data() #latest data sent/received


class MeshNet():
    
    _topic = {} #dict of topics publish/subscribed
    
    _pub_que = {} 	# queue of messages
    #_nodes   = {}   # nodes map
    
    _node_name = ''
    _new_pid = pid_gen()
        
    # node_name : this node name
    # on_news : callback called after main callback ends, default : None
    # pub_t : time interval for sending messages
    def __init__(self, node_name, on_news = None, pub_t = _PUB_FREQ):
        
        self._node_name = node_name # node_name name
        
        #  A WLAN interface must be active for send()/recv()
        print('WiFi STA_IF started')
        wifi = network.WLAN(network.STA_IF)
        wifi.active(True)
        local = wifi.config('mac')
        
        print('WiFi AP_IF started')
        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(essid=node_name, password='esp32')
                
       # MeshNet._nodes={node_name:bytearray(local)} # create list of MAC-address & there _nodes

        print('ESPNow node {} started'.format(node_name))
        
        MeshNet.en = espnow.ESPNow()
        MeshNet.en.active(True)
        MeshNet.en.add_peer(_BCAST) # add broadcast peer first
        
        self.on_news = on_news if on_news else self._on_news
        MeshNet.en.irq(self._on_receive)
            
#         _pubsT = Timer(4) # pulse Pubs
#         _pubsT.init(period=pub_t, mode=Timer.PERIODIC, callback=self._pubs_post) 
        
        print('Mesh network started')
        
        
    # empty News
    def _on_news(self,data_id,topic,sender_node_name,payload, received):
        return True
    
    
   
    
    @staticmethod
    def _check_peer(MAC):
        try:
            MeshNet.en.add_peer(MAC)
        except OSError as err:
            if len(err.args) < 2:
                raise err
            elif err.args[1] == 'ESP_ERR_ESPNOW_EXIST':
                ...
            else:
                raise err

    
        
    # packing data
    @staticmethod
    def _pack_msg(data):
        return '{}~{}~{}~{}~{}'.format(data.data_id, data.topic, data.sender_node_name, data.payload, data.received)


    # UnPACK Protocol
    @staticmethod
    def _unpack_msg(data):

        data = Data()
        data.data_id = msg[0]
        data.topic = msg[1]
        data.sender_node_name = msg[2]
        data.payload = msg[3]
        data.received = msg[4]

        return data
      
            
   # main callback routine, analyse all received messages
    def _on_receive(self,en): # on receive callback
        for MAC, data in en: # MAC address and data, of received messages
            
            u_data = data.decode('utf-8')
            data = self._unpack_msg(u_data.split(_CH_SPLIT))
                    
            #Verificar se topic esta em _topic
            #    topic está em _topic 
            #        verificar is_publisher 
            #            se True entao ele é quem emitiu - Publisher - qualquer mensagem recebida com esse topico deve ser descartado, ignorado
            #            se False então ele é quem está inscrito - Subscriber - qualquer mensagem recebida com esse topico dever ser aceita, guardada
            #    topico NÃO está em _topic
            #        repassar mensagem
            
            #	Data():
            #   self.data_id = 0 #only the publisher can change it
            #   self.topic = ''  # topic name
            #   self.sender_node_name = ''
            #   self.payload = bytearray()
            #	self.received = False
            
            #	MessageSetting():
            #	self.is_publisher = True #boolean to verify if node is publishing to the topic
            #	self.MAC = _BCAST  # for Subs - Publishers MAC-address - NOT USED (for now)
            #	self.QoS = 0  # Quality of Service ( 0:Fire&Forget, 1:At least once, 2:Exactly once ) - NOT USED
            #	self.t_exp = 0  # expire time for News
            #   self.t_stamp = 0  # timestamp of last message received
            #	self.latest_id = 0
            #	self.latest_data = Data() #latest data sent/received
            
            if data.topic in self._topic: # the node_name is alive!
                if self._topic[data.topic].is_publisher:
                    #empty for now
                    pass
                else:
                    self._topic[data.topic].t_stamp = ticks_ms() # zero expired time
                    self._topic[data.topic].latest_id = data.data_id
                    self._topic[data.topic].latest_data = data
                    self.on_news(data.data_id, data.topic, data.sender_node_name, data.payload, data.received ) #callback 
            else:
                MeshNet.en.send(_BCAST, MeshNet._pack_msg(data))
                self.on_news(data.data_id, data.topic, data.sender_node_name, data.payload, data.received ) # if not in topic list - just transparent transmission
                
                     
                
    #Subscribe to a topic
    @classmethod
    def subscribe(cls, topic):
        # topic    - subscribe to this topic 
        if not topic in cls._topic: # new subscriber to given topic
            ms = MessageSetting()
            ms.is_publisher = False
            cls._topic[topic] = ms
      

    #Subscriber method for Requesting updates?
    #does it need periodic updates?

    # method for publishing new or updated data
    @classmethod
    def post(cls, topic, payload):
        data = Data(topic, cls._node_name, payload)
        data.sender_node_name = cls._node_name
        data.topic = topic
        data.payload = payload

        if not topic in cls._topic: # new publisher to given topic
            ms = MessageSetting()
            ms.t_stamp = ticks_ms() # zero expired time
            ms.latest_data = data
            cls._topic[topic] = ms
            
        else:
            cls._topic[topic].latest_id += 1
            data.data_id = cls._topic[topic].latest_id
            
            cls._topic[topic].latest_data = data

        cls.en.send(_BCAST, cls._pack_msg(data))





