# Índice
- [Índice](#-ndice)
- [Projeto - Mesh Comigo](#projeto-mesh-comigo)
- [Introdução](#introdu-o)
- [Projeto de Jogo Interativo com Comunicação Sem Fio usando ESP32](#projeto-de-jogo-interativo-com-comunica-o-sem-fio-usando-esp32)
  * [Objetivos Gerais](#objetivos-gerais)
  * [Motivações](#motiva-es)
- [Materiais e Métodos](#materiais-e-m-todos)
  * [Materiais](#materiais)
  * [Pinos usados](#pinos-usados)
  * [Montagem](#montagem)
  * [Como Transferir os arquivos para o ESP32](#como-transferir-os-arquivos-para-o-esp32)
  * [Configuração do Código](#configura-o-do-c-digo)
  * [Implementação](#implementa-o)
  * [Etapa 1: Criação da Rede Mesh com Micropython](#etapa-1-cria-o-da-rede-mesh-com-micropython)
  * [Jogo de Touchpad em Rede Mesh](#jogo-de-touchpad-em-rede-mesh)
  * [Regras](#regras)
    + [Pré-início](#pr-in-cio)
    + [Durante o jogo](#durante-o-jogo)
  * [Como Iniciar o Jogo](#como-iniciar-o-jogo)
  * [Pareamento das Caixas](#pareamento-das-caixas)
  * [Referências](#refer-ncias)

# Projeto - Mesh Comigo

# Introdução
## Projeto de Jogo Interativo com Comunicação Sem Fio usando ESP32

Inicialmente, nosso projeto visava criar um jogo interativo explorando as capacidades de comunicação sem fio oferecidas pelos dispositivos ESP32. O jogo consistiria em 4 ou 5 nodos, com um deles atuando como o controlador principal do jogo. Cada nodo seria composto por um ESP32 e um botão conectado a ele. A proposta do jogo era que nodos localizados em pontos distantes precisariam ser pressionados em uma determinada sequência.

No início da disciplina, tínhamos apenas a ideia do projeto, sem implementação prática, e a decisão de utilizar uma rede mesh foi orientada pelo professor, com o objetivo de reduzir a latência entre os nodos.

Durante o período de paralisações, enfrentamos desafios devido à escassez de materiais, especificamente os ESP32s, o que limitou nossas possibilidades de montar algo com comunição sem fio, visto que nosso grupo ficou com apenas 1 dispositivos ESP32. Apesar disso, conseguimos avançar na pesquisa, explorando protocolos como MQTT e ESP MESH, examinando bibliotecas relevantes, como PainlessMesh, e revisando projetos similares no GitHub.

Embora tenhamos encontrado uma variedade de recursos sobre a implementação de redes mesh, notamos uma lacuna em informações específicas para o uso com Micropython. Isso nos levou a considerar duas opções: continuar com Micropython ou migrar para C++/Arduino IDE. Durante nossa busca, encontramos um projeto chamado [SMesh](https://github.com/zoland/SMesh), que implementa uma rede mesh, embora parte da documentação esteja em russo. Com o fim da paralização, podemos enfim começar a desenvolver o nosso projeto. 

Este breve relato descreve o ponto em que começamos o desenvolvimento do projeto.

Com isso, podemos dividir o projeto em 2 etapas, a primeira, consiste na criação e implementação de uma rede mesh utilizando Micropython, e na segunda, criar um jogo interativo que utilize essa rede mesh. As etapas serão discutidas na seção de Implementação. 


## Objetivos Gerais

O projeto consiste na criação de um jogo interativo utilizando uma rede mesh implementada em Micropython. A dinâmica do jogo envolve 3 ESP32 e 3 placas sensíveis ao toque, que servirão como botões. O objetivo dos jogadores é pressionar essas placas em uma sequência específica para avançar no jogo.

## Motivações

Conforme mencionado na introdução, iremos explorar as amplas oportunidades de comunicação sem fio proporcionadas pelos ESP32. Poucas experiências são tão interativas quanto um jogo que aproveita ao máximo essas capacidades.

# Materiais e Métodos

## Materiais

    - 3 ESP32: Instalados com a versão 1.21.0 do Micropython.
    - 3 Placas sensíveis ao toque.
    - 3 Jumpers Femea/Femea: Ligando os ESPs às placas.
    - 3 Cabos USB micro-B.
    - 2 ou 3 Recarregadores: usados para fornecer energia ao ESPs
    - Thonny IDE

## Pinos usados

    - Pino GPIO14: oferece Capacitive Touch. [Link](https://randomnerdtutorials.com/esp32-pinout-reference-gpios/) usados para referência dos Pinos

## Montagem 

Conforme a Imagem, ligue os jumpers nas placas, e a outra ponta ao pino GPIO14 do ESP, faça isso para os outros ESPs.

## Como Transferir os arquivos para o ESP32

Instale a Thonny, após a instalação, abra e clique EDIT, na aba superior, e clique em files, conecte o ESP. Caso você já tenha o Micropython instalado, clique no canto direito infeiror e escolha a opção ESP32 que aparecer. Caso contrário, vá em RUN, Configure Interpreter..., no dropdown inferior, escolha a porta em que o ESP está conectado e clique em install or update micropython, preencha de acordo com as especificações de seu ESP32, para as versão mais novas do Thonny, ele mesmo faz o download do firmware e instala.

Em seguida, extraia os arquivos deste repositório e acesse pelo Thonny (janelinha do cando direito), com o ESP conectado, selecione os arquivos e faça o upload para o ESP. 

## Configuração do Código

Duas partes do código do jogo ficou de maneira estática, dentro de main.py, nas linhas 37 a 39, descomente uma das linhas, faça o mesmo em 147 a 149. Cada ESP deve descomentar um, de maneira a não se repetir

## Implementação

## Etapa 1: Criação da Rede Mesh com Micropython

Nesta fase inicial, o foco está na criação e implementação de uma rede mesh utilizando Micropython. Essa rede mesh é construída sobre o protocolo ESP Now, uma tecnologia que permite comunicação sem fio entre dispositivos ESP32, eliminando a necessidade de um roteador intermediário.

A arquitetura escolhida para a comunicação na rede mesh é o Publish/Subscribe do MQTT. Essa abordagem permite que os dispositivos atuem como publishers, enviando mensagens para tópicos específicos, e/ou subscribers, que se inscrevem para receber atualizações sobre tópicos de seu interesse. 
Na arquitetura com ESP Now, aproveitamos a funcionalidade de broadcast, permitindo que os dispositivos ESP32 enviem mensagens para vários destinatários simultaneamente.

Ao combinar o broadcast com a arquitetura Publish/Subscribe do MQTT, estabelecemos uma comunicação dinâmica e escalável. Isso possibilita a transmissão eficiente de atualizações ou comandos para toda a rede, sem a necessidade de conhecimento prévio sobre os destinatários. Essa abordagem destaca-se em ambientes distribuídos, reforçando a flexibilidade e eficiência da rede mesh.

Ao receber uma mensagem, são realizadas as seguintes verificações (1, 2, 1.1, etc.), onde os blocos marcados como A representam condições verdadeiras, e os blocos marcados como B representam condições falsas, abaixo estão as verificações:

    1) Verificar se topic(da mensagem recebida) esta em _topics
        A) topic está em _topics 
            1.1) verificar data_object.is_publisher 
                A) Este nodo emitiu a mensagem recebida - Publisher deste topico
                    1.2) Verifica is_subscriber   
                        A)  
                        1.3) Verifica o ID da mensagem
                            A) ID da mensagem recebida é igual da ultima mensagem recebido, do topico - Mensagem repassada atrassada 
                            B) ID da mensagem recebida não é diferente da ultima mensagem recebida - Mensagem nova - aceitar 
                B) Este nodo está inscrito no topico - Subscriber deste topico
                    1.4) Verifica o ID da mensagem
                        A) ID da mensagem recebida é igual da ultima mensagem recebido, do topico - Mensagem repassada atrassada 
                        B) ID da mensagem recebida não é diferente da ultima mensagem recebida - Mensagem nova - aceitar 
        B) topic NÃO está em _topics
                2.1) verificar se topic está em _topic_last_id
                    A) topic está em _topic_last_id
                        2.2) Verificar data_id em _topic_last_id
                            A) ID da mensagem recebida é igual ao ultimo ID da mensagem recebida, do topico - NÃO repassa mensagem
                            B) ID da mensagem recebida é diferente do ID da ultima mensagem recebida - repassa mensagem
                    B) topic NÂO está em _topic_last_id
                            A) cria topic em _topic_last_id e repassa mensagem

                    
Essa rede mesh foi desenvolvida para operar de maneira autônoma, o que significa que o código foi projetado independentemente e não requer integração com outras partes do projeto. Sua autonomia possibilita sua reutilização em diferentes contextos e projetos, promovendo uma solução versátil e simplificada para comunicação distribuída em ambientes com vários dispositivos interconectados.

O objetivo principal desta parte do projeto é estabelecer uma infraestrutura de comunicação distribuída, onde os dispositivos conectados podem atuar como nodos, desempenhando o papel de publishers (emissores de mensagens para um tópico específico) e/ou subscribers (receptores de mensagens de um tópico ao qual estão inscritos). Com isso, podemos partir para a segunda etapa do nosso projeto, a implementação de um jogo que faz uso dessa rede mesh.



## Jogo de Touchpad em Rede Mesh

O jogo consiste em uma distribuição de touchpads espalhados em um ambiente, comunicando-se por uma rede mesh. Um ou mais jogadores devem descobrir a sequência correta para vencer o jogo. Ao iniciar, uma sequência aleatória de touchpads, sem repetições, é gerada. Os jogadores precisam acertar a sequência com agilidade, sendo a memória uma habilidade fundamental. Se um touchpad incorreto for pressionado, a sequência é zerada, exigindo a memorização da sequência anterior para facilitar a vitória.

## Regras

### Pré-início
1. Momento que é possível fazer o pareamento de mais botões.
2. Toda vez que o jogo é iniciado, uma sequência de touchpads aleatórios, sem repetições, é gerada.

### Durante o jogo
3. Para vencer, os jogadores devem acertar a sequência secreta. Em caso de vitória, então o jogo retorna para o **PRÉ-INÍCIO**.
4. Se um jogador pressionar um touchpad **CORRETO**, este se acenderá e assim permanecerá. Se a sequência secreta for descoberta, os jogadores vencem; caso contrário, o jogo continua.
5. Se um jogador pressionar um touchpad **INCORRETO**, todos os touchpads se apagarão, e os jogadores voltarão à estaca zero. A sequência secreta não se altera, mas os jogadores precisarão refazer seus passos.

## Como Iniciar o Jogo

Para iniciar o jogo, as caixas devem estar no estado de **PRÉ-INÍCIO** e depois deve-se pressione o pequeno botão de boot localizado na parte inferior da caixa do touchpad.

## Pareamento das Caixas

Primeiramente, as caixas devem estar no estado de **PRÉ-INÍCIO**, depois o pareamento das caixas é realizado encostando no próprio touchpad localizado na parte superior da caixa.


## Referências

https://en.wikipedia.org/wiki/Wireless_mesh_network

https://computer.howstuffworks.com/how-wireless-mesh-networks-work.htm

https://www.espressif.com/en/solutions/low-power-solutions/esp-now

https://mqtt.org/ (Seções de Getting Started)

https://docs.micropython.org/en/latest/library/espnow.html

https://randomnerdtutorials.com/esp-mesh-esp32-esp8266-painlessmesh/