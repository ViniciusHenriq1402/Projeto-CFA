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
        self.is_subscriber = False


#classe principal da criacao da rede mesh
class MeshNet():
    
    _topics = {} #dicionario topico: MessageSetting, contendo os topicos que este nodo é um publisher ou subscriber 
    _topic_last_id = {} #dicionario topico: ultimo id recebido do topico
    _node_name = None
    
    #construtor
    # node_name : nome do nodo
    # on_news : callback chamada apos o subscriber recebe a mensagem na qual ele esta inscrito, default : None
    # essa callback deve estar composta por 
    # self.on_news(self, data_object.data_id, data_object.topic, data_object.publisher_node_name, data_object.payload, data_object.sender_node_name ) #callback 
    # TODO: arrumar essa callback, nao devia precisar de tanto argumento
    def __init__(self, node_name, on_news=None):
        
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
        data.data_id = int(msg[0])
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
            #1) Verificar se topic(da mensagem recebida) esta em _topics
            #   A) topic está em _topics 
            #        1.1) verificar data_object.is_publisher 
            #            A) Este nodo emitiu a mensagem recebida - Publisher deste topico
            #               1.2) Verifica is_subscriber   
            #                   A)  
            #                   1.3) Verifica o ID da mensagem
            #                       A) ID da mensagem recebida é igual da ultima mensagem recebido, do topico - Mensagem repassada atrassada 
            #                       B) ID da mensagem recebida não é diferente da ultima mensagem recebida - Mensagem nova - aceitar 
            #            B) Este nodo está inscrito no topico - Subscriber deste topico
            #                1.4) Verifica o ID da mensagem
            #                    A) ID da mensagem recebida é igual da ultima mensagem recebido, do topico - Mensagem repassada atrassada 
            #                    B) ID da mensagem recebida não é diferente da ultima mensagem recebida - Mensagem nova - aceitar 
            #   B) topic NÃO está em _topics
            #            2.1) verificar se topic está em _topic_last_id
            #                A) topic está em _topic_last_id
            #                    2.2) Verificar data_id em _topic_last_id
            #                        A) ID da mensagem recebida é igual ao ultimo ID da mensagem recebida, do topico - NÃO repassa mensagem
            #                        B) ID da mensagem recebida é diferente do ID da ultima mensagem recebida - repassa mensagem
            #                B) topic NÂO está em _topic_last_id
            #                        A) cria topic em _topic_last_id e repassa mensagem

            #   Verificação 1)
            if topic in self._topics:
                #	Bloco A) topic está em _topics
                #   Verificação 1.1)
                if self._topics[topic].is_publisher:
                    #	Bloco A)
                    #   1.2)
                    if self._topics[topic].is_subscriber:
                        #   Bloco A)
                        #   Verificação 1.3)
                        if data_object.data_id == self._topics[topic].latest_id:
                            #   Bloco A)
                            continue
                        else:
                            #   Bloco B)
                            self._topics[topic].t_stamp = ticks_ms() # timestamp de quando recebe, para subscribers
                            self._topics[topic].latest_id = data_object.data_id
                            self._topics[topic].latest_data = data_object 
                            #Callback passada na inicialização da MeshNet
                            self.on_news(self, data_object.data_id, data_object.topic, data_object.publisher_node_name, data_object.payload, data_object.sender_node_name ) #callback 
                
                    else:
                        #   Bloco )
                        continue
                else:
                    #	Bloco B)
                    #   Verificação 1.4)
                    if data_object.data_id == self._topics[topic].latest_id:
                        #   Bloco A)
                        continue
                    else:
                        #   Bloco B)
                        self._topics[topic].t_stamp = ticks_ms() # timestamp de quando recebe, para subscribers
                        self._topics[topic].latest_id = data_object.data_id
                        self._topics[topic].latest_data = data_object 
                        #Callback passada na inicialização da MeshNet
                        self.on_news(self, data_object.data_id, data_object.topic, data_object.publisher_node_name, data_object.payload, data_object.sender_node_name ) #callback 
            
            #	Bloco B) topico NÃO está em _topics
            else:
                #   Verificação 2.1)
                if topic in self._topic_last_id:
                    #   Bloco A) 
                    #   Verificação 2.2
                    if data_object.data_id == self._topic_last_id[topic]:
                        #   Bloco A)
                        continue

                    else:
                        #   Bloco B)
                        self._topic_last_id[topic] = data_object.data_id #atualiza o ultimo id
                        data_object.sender_node_name = self._node_name
                        en.send(_BCAST, MeshNet._pack_msg(data_object))
                
                else:
                    #   2.1 Bloco B)
                    data_object.sender_node_name = self._node_name
                    self._topic_last_id[topic] = data_object.data_id #cria topico em _topic_last_id
                    en.send(_BCAST, MeshNet._pack_msg(data_object))

                
                    
    #Inscreve no topic
    #topic: topic a ser inscrito
    @classmethod
    def subscribe(cls, topic):
        if not topic in cls._topics: # novo inscrito
            ms = MessageSetting()
            ms.is_subscriber = True
            ms.is_publisher = False
            cls._topics[topic] = ms
            print('Inscrito em {}'.format(topic))

        else:
            cls._topics[topic].is_subscriber = True
            print("Topico já inscrito ou este nodo publica para este topico")
    
    
    #Cancela a inscricao em um topic
    #topic: topico a ser cancelado
    @classmethod
    def unsubscribe(cls, topic):
        if topic in cls._topics:
            del cls._topics[topic]
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
        if not topic in cls._topics: 
            ms = MessageSetting()
            ms.t_stamp = ticks_ms() #timestamp da ultima publicação, publisher 
            ms.latest_id = data.data_id
            ms.latest_data = data
            
            #False por default
            #ms.is_subscriber = False
            
            cls._topics[topic] = ms
            
            
        
        #Atualização sobre um topico, incrementa id, e substitui id no objeto data
        else:
            cls._topics[topic].latest_id += 1
            data.data_id = cls._topics[topic].latest_id
            cls._topics[topic].t_stamp = ticks_ms() #timestamp da ultima publicação, publisher
            cls._topics[topic].latest_data = data

        cls.en.send(_BCAST, cls._pack_msg(data))
        #print(f'Post feito para topic: {data.topic} - data_id: {data.data_id}, sender_node_name: {data.sender_node_name}, payload: {data.payload}')


        #Talvez acrescentar uma forma do subscriber requisitar uma atualização do publisher? ou metodo para verificar ultimo dado recebido?
        #data_id = 0, pode ser usado como handshake inicial, para verificar se existe algum inscrito dado alguma topico e registrar o topico nos nodos de rota
        #Impoe restricoes sobre o publisher? como somente 1 publisher pode publicar nesse topico
        









