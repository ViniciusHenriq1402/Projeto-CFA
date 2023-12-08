import gc
from micropython import const
from machine import Timer
from utime import sleep, ticks_ms
import webrepl

import network
import espnow
gc.collect()

_CH_SPLIT   = '~' # caracter que separa os campos no empacotamento das mensagens 
_BCAST      = b'\xff'*6 #broadcast MAC address
_PUB_FREQ	= 0

# Classe com os dados a serem enviados
class Data:
    def __init__(self, topic='', sender_node_name='', payload=bytearray()):
        self.data_id = 0  # Somente o Publisher pode modificar
        self.topic = topic  # topico da mensagem
        self.sender_node_name = sender_node_name # nome do nodo de quem enviou
        self.payload = payload # conteudo da mensagem
        self.received = False  # True se algum inscrito recebeu essa mensagem
        
# Classe contendo dados que serão verificados apos receber uma mensagem
class MessageSetting():
    def __init__(self):
        self.is_publisher = True #Boolean True se esse nodo é um publisher ou False caso contrario
        self.MAC = _BCAST  # em caso de necessidade de criar um mapa dinamico, MAC de que enviou
        self.QoS = 0  # Quality of Service ( 0:Fire&Forget, 1:At least once, 2:Exactly once ) - NOT USED
        self.t_exp = 0  # Tempo de expiramento da mensagem
        self.t_stamp = 0  # timestamp da ultima mensagem recebida que ele esta inscrito
        self.latest_id = 0 # ultimo id da mensagem recebida
        self.latest_data = Data() # ultimo conteudo da mensagem data enviada ou recebida


#classe principal da criacao da rede mesh
class MeshNet():
    
    _topic = {} #dicionario topico: MessageSetting, contendo os topicos que este nodo é um publisher ou subscriber 
    _topic_last_id = {} #dicionario topico: ultimo id recebido do topico
    _node_name = '' #nome do nodo 
    
    #construtor
    # node_name : nome do nodo
    # on_news : callback chamada apos o subscriber recebe a mensagem na qual ele esta inscrito, default : None
    # pub_t : intervalo de tempo para o envio de mensagem
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
        webrepl.start()
        
       # MeshNet._nodes={node_name:bytearray(local)} # create list of MAC-address & _nodes

        print('ESPNow node {} started'.format(node_name))
        MeshNet.en = espnow.ESPNow()
        MeshNet.en.active(True)
        MeshNet.en.add_peer(_BCAST) # add broadcast peer first
        
        self.on_news = on_news if on_news else self._empty_callback
        MeshNet.en.irq(self._on_receive)
        
        #caso seja preciso publicar com um certa periodicidade - não usado
#         _pubsT = Timer(4) # pulse Pubs
#         _pubsT.init(period=pub_t, mode=Timer.PERIODIC, callback=self._pubs_post) 
        
        print('Mesh network started')
        
        
    # callback vazia, para quando callback incluido no contrutor for vazia
    def _empty_callback(self, data_id, topic, sender_node_name, payload, received):
        return True
   
    #Verifica o peer dado um endereço MAC dado - NÂO USADO
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

    
        
    # Empacotamento dos dados a serem enviados
    # data: Objeto da classe Data, da mensagem a ser enviada
    @staticmethod
    def _pack_msg(data):
        return '{}~{}~{}~{}~{}'.format(data.data_id, data.topic, data.sender_node_name, data.payload, data.received)


    # Desempacotamento dos dados recebidos, colocando-os no objeto Data
    # msg: array contendo os dadas da mensagem
    @staticmethod
    def _unpack_msg(msg):

        data = Data()
        data.data_id = msg[0]
        data.topic = msg[1]
        data.sender_node_name = msg[2]
        data.payload = msg[3]
        data.received = msg[4]

        return data
      
            
   # callback principal de quando este nodo recebe uma mensagem, usado no metodo do ESPNOW irq()
    def _on_receive(self,en):
        for MAC, data in en: # lista com endereço MAC e dados da mensagem recebida
            
            u_data = data.decode('utf-8') # recebe dados em bytes e devem ser decodificado 
            data = self._unpack_msg(u_data.split(_CH_SPLIT)) # desempacotamento em objeto da classe Data()
            topic = data.topic
            
            #Verificação feita na callback principal       
            #Verificar se topic(da mensagem recebida) esta em _topic
            #    1) topic está em _topic 
            #		verificar data.is_publisher 
            #			A) se True entao ele é quem emitiu - Publisher - qualquer mensagem recebida com esse topico deve ser descartado, ignorado
            #           B) se False então ele é quem está inscrito - Subscriber - qualquer mensagem recebida com esse topico dever ser aceita, guardada
            #    2) topic NÃO está em _topic
            #			verificar se topic está em _topic_last_id
            #				2.1) topic está em _topic_last_id
            #					Verificar data_id em _topic_last_id
            #						A)ID da mensagem recebida é igual ao ultimo ID da mensagem recebida, do topico - NÃO repassa mensagem
            #						B)ID da mensagem recebida é diferente do ID da ultima mensagem recebida - repassa mensagem
            #				2.2) topic NÂO está em _topic_last_id
            #                   cria topic em _topic_last_id e repassa mensagem
            
            
            if topic in self._topic: # the node_name is alive!
                #	1) topic está em _topic
                if self._topic[topic].is_publisher:
                    #	A) Publisher - qualquer mensagem recebida com esse topico deve ser descartado, ignorado
                    #vazia por enquanto,
                    #talvez acrescentar algum forma de avisar, o publisher, se a mensagem foi recebida por algum subscriber, variavel received de Data. 
                    pass
                else:
                    #	B) Subscriber - qualquer mensagem recebida com esse topico dever ser aceita, guardada
                    self._topic[topic].t_stamp = ticks_ms() # timestamp de quando recebe, para subscribers
                    self._topic[topic].latest_id = data.data_id
                    self._topic[topic].latest_data = data
                    self.on_news(data.data_id, data.topic, data.sender_node_name, data.payload, data.received ) #callback 
            else:
                #	2) topico NÃO está em _topic
                if topic in self._topic_last_id:
                    #2.1)
                    if data.data_id == self._topic_last_id[topic]:
                        #A)
                        #vazia
                        #se for preciso limitar a quantidade de repasse
                        pass
                    else:
                        #B)
                        self._topic_last_id[topic] = data.data_id #atualiza o ultimo id
                        MeshNet.en.send(_BCAST, MeshNet._pack_msg(data))
                else:
                    #2.2)
                    self._topic_last_id[topic] = data.data_id #cria topico e ultimo id
                    MeshNet.en.send(_BCAST, MeshNet._pack_msg(data))

                
                     
    #Inscreve no topic
    #topic: topic a ser inscrito
    @classmethod
    def subscribe(cls, topic):
        if not topic in cls._topic: # novo inscrito
            ms = MessageSetting()
            ms.is_publisher = False
            cls._topic[topic] = ms
            print('Inscrito em {}'.format(topic))

        else:
            print("Topico já inscrito")
            
    @classmethod
    def unsubscribe(cls, topic):
        if topic in cls._topic:
            del cls._topic[topic]
            print("Inscrição cancelada em topico {}".format(topic))
        else:
            print("Topico nao inscrito")
            
    
    # metodo para enviar nova ou uma atualizacao sobre um topico
    # topic: topico da mensagem
    # payload: dados a serem enviados
    @classmethod
    def post(cls, topic, payload):
        data = Data(topic, cls._node_name, payload)
        print('post to {} {}'.format(topic,payload))

        #Nova publicação para alguma topico
        if not topic in cls._topic: 
            ms = MessageSetting()
            ms.t_stamp = ticks_ms() #timestamp da ultima publicação, publisher 
            ms.latest_data = data
            cls._topic[topic] = ms
        
        #Atualização sobre um topico
        else:
            cls._topic[topic].latest_id += 1
            data.data_id = cls._topic[topic].latest_id
            cls._topic[topic].t_stamp = ticks_ms() #timestamp da ultima publicação, publisher
            cls._topic[topic].latest_data = data

        cls.en.send(_BCAST, cls._pack_msg(data))


        #Talvez acrescentar uma forma do subscriber requisitar uma atualização do publisher? ou metodo para verificar ultimo dado recebido?
        #data_id = 0, pode ser usado como handshake inicial, para verificar se existe algum inscrito dado alguma topico e registrar o topico nos nodos de rota
        #Impoe restricoes sobre o publisher? como somente 1 publisher pode publicar nesse topico