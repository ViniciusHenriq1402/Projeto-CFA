# Projeto de CFA 

O projeto, dividido em 2 etapas, na primeira, consiste na criação e implementação de uma rede mesh utilizando Micropython, e na segunda, criar um jogo interativo que utilize essa rede mesh. 

Etapa 1: Criação da Rede Mesh com Micropython:

Nesta fase inicial, o foco está na criação e implementação de uma rede mesh utilizando Micropython. Essa rede mesh é construída sobre o protocolo ESP Now, uma tecnologia que permite comunicação sem fio entre dispositivos ESP32, eliminando a necessidade de um roteador intermediário.

A arquitetura escolhida para a comunicação na rede mesh é o Publish/Subscribe do MQTT. Essa abordagem permite que os dispositivos atuem como publishers, enviando mensagens para tópicos específicos, e/ou subscribers, que se inscrevem para receber atualizações sobre tópicos de seu interesse. 
Na arquitetura com ESP Now, aproveitamos a funcionalidade de broadcast, permitindo que os dispositivos ESP32 enviem mensagens para vários destinatários simultaneamente.

Ao combinar o broadcast com a arquitetura Publish/Subscribe do MQTT, estabelecemos uma comunicação dinâmica e escalável. Isso possibilita a transmissão eficiente de atualizações ou comandos para toda a rede, sem a necessidade de conhecimento prévio sobre os destinatários. Essa abordagem destaca-se em ambientes distribuídos, reforçando a flexibilidade e eficiência da rede mesh.

Os dispositivos ao receberem alguma mensagem, elas precisam:
Verificar se o tópico está na lista de tópicos (_topic).

    Se o tópico está na lista de tópicos:
        Verificar se é um publisher (is_publisher).
            Se for True, significa que o dispositivo é o emissor (Publisher), então a mensagem deve ser descartada ou ignorada.
            Se for False, indica que o dispositivo é um inscrito (Subscriber), e a mensagem com esse tópico deve ser aceita e guardada. A prioridade pode ser dada à mensagem que chega primeiro.

    Se o tópico NÃO está na lista de tópicos:
        Repassar a mensagem para outros dispositivos na rede.

O objetivo principal do projeto é estabelecer uma infraestrutura de comunicação robusta e distribuída, onde os dispositivos conectados podem atuar como nodos, desempenhando o papel de publishers (emissores de mensagens para um tópico específico) e/ou subscribers (recebedores de mensagens de um tópico ao qual estão inscritos).

Etapa 2: Criação do jogo interativo utilizando a rede mesh

# Referências 

https://www.espressif.com/en/solutions/low-power-solutions/esp-now

https://mqtt.org/

https://docs.micropython.org/en/latest/library/espnow.html

https://randomnerdtutorials.com/esp-mesh-esp32-esp8266-painlessmesh/
