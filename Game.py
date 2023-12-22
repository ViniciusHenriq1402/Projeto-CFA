import random

'''
A função custom_shuffle utiliza o algoritmo de Fisher-Yates para embaralhar a lista. 
Ela troca elementos aleatórios da lista em cada iteração, resultando em uma ordem aleatória.
'''
def custom_shuffle(lst):
    for i in range(len(lst) - 1, 0, -1):
        j = random.randint(0, i)
        lst[i], lst[j] = lst[j], lst[i]

class Game:

    def __init__(self, lista_botao=None, _GOAL=None):
        self._GOAL = _GOAL
        if lista_botao:
            if _GOAL: # Se _GOAL NÃO é None, então teremos apenas uma atribuição de valor
                self._GOAL = _GOAL
            else:     # Se _GOAL é None, então se trata de uma nova instância do Game, então gera-se uma nova string aleatória
                self._GOAL = self.gera_string_random(lista_botao)

        self.sequencia = ''
        
    
    def gera_string_random(self, lista_botao):

        # Converta o conjunto em uma lista para facilitar a manipulação
        lista_strings = list(lista_botao)

        # Embaralhe a lista aleatoriamente
        custom_shuffle(lista_strings)

        # Concatene os elementos da lista para formar a string aleatória
        string_aleatoria = ''.join(lista_strings)

        # print("_GOAL " + string_aleatoria)
        return string_aleatoria
    
    '''
    Função responsável pela verificação de vitória, ou seja, se a sequência está correta.
    '''
    def is_over(self):
        return self._GOAL == self.sequencia

    '''
    Função de inicio de jogo, gera uma string aleatoria dado a lista de botoes e esvazia a sequencia
    lista_botao: set contendo os botoes (id_botao) que farao parte do jogo
    '''
    def start(self, lista_botao, goal = None):
        if goal: # Se goal NÃO é None, então teremos apenas uma atribuição de valor
            self._GOAL = goal
        else:     # Se goal é None, então se trata de um novo inicio de jogo, então gera-se uma nova string aleatória
            self._GOAL = self.gera_string_random(lista_botao)
            
        self.sequencia = ''
