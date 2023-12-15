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

# Classe com os dados a serem enviados
class Data:
    def __init__(self, topic='', publisher_node_name='', payload=bytearray()):
        self.data_id = 1  # Somente o Publisher pode modificar
        self.topic = topic  # topico da mensagem
        self.publisher_node_name = publisher_node_name # nome do nodo de quem enviou
        self.payload = payload # conteudo da mensagem
        self.sender_node_name = ''  # nome do nodo que enviou a mensagem
        
# Classe contendo dados que serão verificados apos receber uma mensagem
class MessageSetting():
    def __init__(self):
        self.is_publisher = True #Boolean True se esse nodo é um publisher ou False caso contrario
        self.MAC = _BCAST  # em caso de necessidade de criar um mapa dinamico, MAC de que enviou
        self.t_stamp = 0  # timestamp da ultima mensagem recebida que ele esta inscrito
        self.latest_id = 0 # ultimo id da mensagem recebida
        self.latest_data = Data() # ultimo conteudo da mensagem data enviada ou recebida


#classe principal da criacao da rede mesh
class MeshNet():
    
    _topic = {} #dicionario topico: MessageSetting, contendo os topicos que este nodo é um publisher ou subscriber 
    _topic_last_id = {} #dicionario topico: ultimo id recebido do topico
    _node_name = None
    
    #construtor
    # node_name : nome do nodo
    # on_news : callback chamada apos o subscriber recebe a mensagem na qual ele esta inscrito, default : None
    # pub_t : intervalo de tempo para o envio de mensagem
    def __init__(self, node_name, on_news = None):
        
        MeshNet._node_name = node_name # node_name name
        
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
        
        print('Mesh network started')
        
        
    # callback vazia, para quando callback incluido no contrutor for vazia
    def _empty_callback(self, data_id, topic, publisher_node_name, payload, sender_node_name):
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
        return '{}~{}~{}~{}~{}'.format(data.data_id, data.topic, data.publisher_node_name, data.payload, data.sender_node_name)


    # Desempacotamento dos dados recebidos, colocando-os no objeto Data
    # msg: array contendo os dadas da mensagem
    @staticmethod
    def _unpack_msg(msg):

        data = Data()
        data.data_id = msg[0]
        data.topic = msg[1]
        data.publisher_node_name = msg[2]
        data.payload = msg[3]
        data.sender_node_name = msg[4]

        return data
      
            
   # callback principal de quando este nodo recebe uma mensagem, usado no metodo do ESPNOW irq()
    def _on_receive(self, en):

        while True:  # Read out all messages waiting in the buffer
            mac, msg = en.irecv(0)  # Don't wait if no messages left
            if mac is None: return
            u_data = msg.decode('utf-8') # recebe dados em bytes e devem ser decodificado 
            data_object = MeshNet._unpack_msg(u_data.split(_CH_SPLIT)) # desempacotamento em objeto da classe Data()
            topic = data_object.topic
            #print(f'publisher:{data_object.publisher_node_name} - sender:{data_object.sender_node_name}')
            
            #Verificação feita na callback principal       
            #Verificar se topic(da mensagem recebida) esta em _topic
            #    1) topic está em _topic 
            #		verificar data_object.is_publisher 
            #			A) se True entao este nodo emitiu a mensagem recebida - Publisher deste topico                 
            #           B) se False então este nodo está inscrito no topico - Subscriber deste topico
            #               1.1) Verifica o ID da mensagem
            #                   A) ID da mensagem recebida é igual da ultima mensagem recebido, do topico - Mensagem repassada atrassada - ignorar
            #                   B) ID da mensagem recebida não é diferente da ultima mensagem recebida - Mensagem nova - aceitar (chamar callback)
            #    2) topic NÃO está em _topic
            #			verificar se topic está em _topic_last_id
            #				2.1) topic está em _topic_last_id
            #					Verificar data_id em _topic_last_id
            #						A)ID da mensagem recebida é igual ao ultimo ID da mensagem recebida, do topico - NÃO repassa mensagem
            #						B)ID da mensagem recebida é diferente do ID da ultima mensagem recebida - repassa mensagem
            #				2.2) topic NÂO está em _topic_last_id
            #                   cria topic em _topic_last_id e repassa mensagem
            
            if topic in self._topic:

                #	1) topic está em _topic
                if self._topic[topic].is_publisher:
                    #	A) 
                    #vazia
                    continue
                else:
                    #	B)
                    #   1.1)
                    if data_object.data_id == self._topic[topic].latest_id:
                        #   A)
                        continue
                    else:
                        #   B)
                        self._topic[topic].t_stamp = ticks_ms() # timestamp de quando recebe, para subscribers
                        self._topic[topic].latest_id = data_object.data_id
                        self._topic[topic].latest_data = data_object 
                        self.on_news(self, data_object.data_id, data_object.topic, data_object.publisher_node_name, data_object.payload, data_object.sender_node_name ) #callback 
            else:
                #	2) topico NÃO está em _topic
                if topic in self._topic_last_id:
                    #   2.1)
                    if data_object.data_id == self._topic_last_id[topic]:
                        #   A)
                        continue
                    else:
                        #   B)
                        self._topic_last_id[topic] = data_object.data_id #atualiza o ultimo id
                        data_object.sender_node_name = self._node_name
                        en.send(_BCAST, MeshNet._pack_msg(data_object))
                else:
                    #   2.2)
                    data_object.sender_node_name = self._node_name
                    self._topic_last_id[topic] = data_object.data_id #cria topico e ultimo id
                    en.send(_BCAST, MeshNet._pack_msg(data_object))

                
                     
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
    
    
    #Cancela a inscricao em um topic
    #topic: topico a ser cancelado
    @classmethod
    def unsubscribe(cls, topic):
        if topic in cls._topic:
            del cls._topic[topic]
            print("Inscrição cancelada em topico {}".format(topic))
        else:
            print("Topico nao existe")
            
    
    # metodo para enviar nova ou uma atualizacao sobre um topico
    # topic: topico da mensagem
    # payload: dados a serem enviados
    @classmethod
    def post(cls, topic, payload):
        data = Data(topic=topic, publisher_node_name=cls._node_name, payload=payload)
        data.sender_node_name = data.publisher_node_name

        #Nova publicação para algum topico, necessario atualizar o valor de latest_id, de MessageSetting.
        if not topic in cls._topic: 
            ms = MessageSetting()
            ms.t_stamp = ticks_ms() #timestamp da ultima publicação, publisher 
            ms.latest_id = data.data_id
            ms.latest_data = data
            cls._topic[topic] = ms
            
        
        #Atualização sobre um topico, incrementa id, e substitui id no objeto data
        else:
            cls._topic[topic].latest_id += 1
            data.data_id = cls._topic[topic].latest_id
            cls._topic[topic].t_stamp = ticks_ms() #timestamp da ultima publicação, publisher
            cls._topic[topic].latest_data = data

        cls.en.send(_BCAST, cls._pack_msg(data))
        print(f'Post feito para topic: {data.topic} - data_id: {data.data_id}, sender_node_name: {data.sender_node_name}, payload: {data.payload}')


        #Talvez acrescentar uma forma do subscriber requisitar uma atualização do publisher? ou metodo para verificar ultimo dado recebido?
        #data_id = 0, pode ser usado como handshake inicial, para verificar se existe algum inscrito dado alguma topico e registrar o topico nos nodos de rota
        #Impoe restricoes sobre o publisher? como somente 1 publisher pode publicar nesse topico
        









