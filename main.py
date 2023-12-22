from machine import Pin, TouchPad
import time
from time import sleep 
from Game import *
from mesh import MeshNet

if __name__ == '__main__':

    '''
    1) Inicio jogo
        a) Gera uma lista aletória de sequencia dos botoes
        b) Está iniciando: pisca (igual a formula 1)
    2) Jogo iniciou
        a) botão foi pressionado: acende um led // e logo após se apaga
        b) botão não foi pressionado: led fica apagado
    3) Regras da sequência
        a) Erra a sequencia ordem_botoes: sinaliza o erro, porém com a mesma sequencia_objetivo (retorne ao passo 1b)
        b) Acertou um botão:
            - if len(ordem_botoes) < len(sequencia_objetivo): Acende led botão
            - elif ordem_botoes == sequencia_objetivo: Sinaliza que o jogador venceu (led)

    sequencia_objetivo [1, 2, 3, 4]
    ordem_botoes: [1]
    '''

    topic_goal = 'goal'
    topic_sequencia = 'sequencia'
    topic_end_game = 'end_game'
    topic_pairing = 'pairing'
    
    lista_botao = set()

    #TODO: Criacao de um metodo para gerar string de ID aleatoria, e verificar se entre os demais nodos ela é realmente unica (1)
    # Por enquanto, ID é estatico para todos os nodos.
    # ID DEVE SER UM CARACTER UNICO, pois sera transformado em String
    # DESCOMENTAR SOMENTE UM, SEM REPETIR ENTRE NODOS
    #id_botao = "a"
    #id_botao = "b"
    #id_botao = "c"

    lista_botao.add(id_botao)
    
    game = Game()
    is_game_started = False
    is_right = False

    pin_led = Pin(2, Pin.OUT)  # Substitua 2 pelo número do pino onde o LED está conectado
    pin_boot = Pin(0, Pin.IN, Pin.PULL_UP)  # Pino do botão BOOT
    touch_pad = TouchPad(Pin(14))

    #Callback para quando nodo receber uma mensagem na qual ele está inscrito,
    #Dividio em IFs para diferentes topicos
    #os argumentos dessa callback é composto pelas variaveis do objeto Data(),  
    def mesh_callback(self, data_id, topic, publisher_node_name, payload, sender_node_name):
        
        #PAREAMENTO
        if topic == topic_pairing:
            if payload:
                if payload not in lista_botao:
                    lista_botao.add(payload)
                    pisca_led_por(0.1)
                    pisca_led_por(0.1)
                    print("Pareamento feito com " + payload)
                    print("lista de botoes:", end=' ')
                    for elemento in lista_botao:
                        print(elemento, end=' ')
                    print()

                else:
                    pisca_led_por(0.2)
                    print("lista de botoes:", end=' ')
                    for elemento in lista_botao:
                        print(elemento, end=' ')
                    print()

        
        #LISTA SEQUENCIA OBJETIVO
        elif topic == topic_goal:
            if payload:               

                # INICIO DO JOGO
                print("Recebido topic_goal")
                print("payload " + payload)
                if id_botao in payload:
                    global game
                    # Inicio o Game com a sequencia objetivo (payload)
                    game.start(lista_botao, payload)
                    global is_game_started
                    is_game_started = True
                    print("Jogo Iniciado por outro nodo")
                    print("_GOAL: " + game._GOAL)
                    pisca_led_por(0.5)
                    pisca_led_por(0.5)
                    pisca_led_por(1)
        
        #ATUALIZACAO DA SEQUENCIA
        elif topic == topic_sequencia:
            #payload == None
            if payload is None:
                pass
            #payload == ""
            elif not payload:
                global is_right
                is_right = False
                pin_led.off()
                
            global game
            game.sequencia = payload
               
                

        #FIM DE JOGO               
        elif topic == topic_end_game:
            if payload:
                if id_botao in payload:
                    print("Jogo Finalizado por outro nodo! Indo ao pre-inicio")
                    pisca_led_por(.2)
                    pisca_led_por(.2)
                    pisca_led_por(.2)
                    pisca_led_por(.2)
                    pisca_led_por(.2)
                    global is_game_started
                    is_game_started = False
                    global is_right
                    is_right = False
            
        return True
    
    #Metodo para pareamento, faz um postagem com topico de pareamento com conteudo id_botao 
    def pairing():
        mesh.post(topic_pairing, id_botao)
        pisca_led_por(0.1)
        pisca_led_por(0.1)

    #Metodo para piscar led do ESP32. Recebe como argumento quantos segundos, o led, deve ficar aceso  
    def pisca_led_por(seconds):
        sleep(seconds)
        pin_led.on()
        sleep(seconds)
        pin_led.off()
        


    #Criacao da rede mesh
    #TODO:fazer algo parecido com to do (1)
    # DESCOMENTAR SOMENTE UM, SEM REPETIR ENTRE NODOS
    #mesh = MeshNet("nodo1", mesh_callback)
    #mesh = MeshNet("nodo2", mesh_callback)
    #mesh = MeshNet("nodo3", mesh_callback)

    #Inscricoes em topicos que serao usados no jogo
    mesh.subscribe(topic_goal)
    mesh.subscribe(topic_sequencia)
    mesh.subscribe(topic_end_game)
    mesh.subscribe(topic_pairing)

    pin_led.off()

    # Configurar o pino sensível ao toque
    calibragem = 300

    # Loop principal para ler o botao boot do esp32 ou ler se for pressionado o touch pad
    # Pressionando o Botao Boot, o Jogo é iniciado;
    # Pressionando o Touch Pad, o nodo envia um sinal de pareamento
    pisca_led_por(0.1)
    print("Loop Principal Iniciado")
    while True:

        # Condição indicando que jogo ainda nao foi iniciado
        if not is_game_started:
            
            # INICIA JOGO
            if pin_boot.value() == 0:
                print("Iniciando Jogo!")
                
                # Inicio o Game, com a criacao aleatoria da sequencia objetivo dado a lista de botoes
                game.start(lista_botao)
                is_game_started = True
                mesh.post(topic_goal, game._GOAL)
                pisca_led_por(0.5)
                pisca_led_por(0.5)
                pisca_led_por(1)
                print("Jogo Iniciado")
                print("_GOAL: " + game._GOAL)
            
            # PAREAMENTO
            elif touch_pad.read() < calibragem:
                pairing()
                
                
        # Condição para inicio do jogo
        elif is_game_started:
            
            touch_value = touch_pad.read()
            if touch_value < calibragem and is_right == False:
                print("Toque lido")
                pisca_led_por(0.1)

                # INSERE BOTAO NA SEQUENCIA 
                game.sequencia += id_botao

                print("Sequencia: " + game.sequencia)
                # VENCEU O GAME                
                if game.is_over():
                    mesh.post(topic_end_game, game._GOAL)
                    pisca_led_por(.2)
                    pisca_led_por(.2)
                    pisca_led_por(.2)
                    pisca_led_por(.2)
                    pisca_led_por(.2)
                    is_right = False
                    is_game_started = False

                    print("Jogo Finalizado! Indo ao pre-inicio")

                # JOGO CONTINUA                     
                else:
                    # VERIFICA SE BOTAO ESTA CORRETO NA SEQUENCIA  
                    if game._GOAL.startswith(game.sequencia):
                        print("Acertou!")
                        pin_led.on()
                        is_right = True

                        
                    # RESETA SEQUENCIA 
                    else:
                        print("Errou!")
                        is_right = False
                        pin_led.off()
                        game.sequencia = ''
                        
                    mesh.post(topic_sequencia, game.sequencia)
                
        time.sleep(0.1)




