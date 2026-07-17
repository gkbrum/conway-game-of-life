# main.py
# Interface grafica do Jogo da Vida de Conway em Python
# Utiliza Pygame para renderizacao e ctypes para integracao com o motor C++
# A comunicacao com o C++ e feita via ponteiro de memoria compartilhada (zero-copy)

import pygame
import ctypes
import os
import sys
import shutil

# =============================================================================
# CONSTANTES DE CONFIGURACAO
# =============================================================================

GRID_WIDTH = 120          # Numero de colunas do grid de celulas
GRID_HEIGHT = 80          # Numero de linhas do grid de celulas
CELL_SIZE = 8             # Tamanho de cada celula em pixels
PANEL_HEIGHT = 80         # Altura do painel de controles em pixels
BG_COLOR = (15, 15, 20)   # Cor de fundo (celulas mortas) - escuro cyberpunk
PANEL_BG = (22, 22, 30)   # Cor de fundo do painel de controles
UI_FPS = 60               # FPS da interface (independente da velocidade de simulacao)

# Dimensoes calculadas da janela
WINDOW_WIDTH = GRID_WIDTH * CELL_SIZE
WINDOW_HEIGHT = GRID_HEIGHT * CELL_SIZE + PANEL_HEIGHT

# =============================================================================
# CARREGAMENTO DA DLL VIA CTYPES
# =============================================================================

def load_engine_library():
    """
    Carrega a biblioteca dinamica do motor C++ (engine.dll ou engine.so).
    Resolve caminhos absolutos e adiciona diretorios de busca necessarios
    para o Python 3.8+ no Windows.
    Retorna o objeto ctypes.CDLL pronto para uso.
    """
    # O script roda de src/, mas a DLL fica em app/
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.dirname(script_dir)

    if os.name == 'nt':
        lib_name = "engine.dll"
        # Python 3.8+ no Windows exige add_dll_directory para encontrar dependencias
        if hasattr(os, 'add_dll_directory'):
            os.add_dll_directory(app_dir)
            gxx_path = shutil.which("g++")
            if gxx_path:
                os.add_dll_directory(os.path.dirname(gxx_path))
    else:
        lib_name = "engine.so"

    lib_path = os.path.join(app_dir, lib_name)

    if not os.path.exists(lib_path):
        print(f"ERRO: Biblioteca '{lib_name}' nao encontrada em '{app_dir}'.")
        print("Compile primeiro com: g++ -O3 -shared -fPIC -static-libgcc -static-libstdc++ -o engine.dll src/engine.cpp")
        sys.exit(1)

    try:
        lib = ctypes.CDLL(lib_path)
    except OSError as e:
        print(f"ERRO ao carregar a biblioteca: {e}")
        sys.exit(1)

    # --- Declaracao das assinaturas das funcoes exportadas pelo C++ ---

    # bool init_game(int w, int h)
    lib.init_game.argtypes = [ctypes.c_int, ctypes.c_int]
    lib.init_game.restype = ctypes.c_bool

    # void free_game()
    lib.free_game.argtypes = []
    lib.free_game.restype = None

    # uint8_t* get_grid_pointer()
    lib.get_grid_pointer.argtypes = []
    lib.get_grid_pointer.restype = ctypes.c_void_p

    # void set_cell(int x, int y, uint16_t age)
    lib.set_cell.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint16]
    lib.set_cell.restype = None

    # void clear_grid()
    lib.clear_grid.argtypes = []
    lib.clear_grid.restype = None

    # void randomize_grid(float probability)
    lib.randomize_grid.argtypes = [ctypes.c_float]
    lib.randomize_grid.restype = None

    # void update_game()
    lib.update_game.argtypes = []
    lib.update_game.restype = None

    return lib

# =============================================================================
# FUNCAO DE COR - GRADIENTE HSL NEON
# =============================================================================

def get_cell_color(age):
    """
    Converte a idade de uma celula (0-65535) em uma cor RGB usando o espaco HSL.
    Celulas jovens sao ciano/azul neon, amadurecem para verde, amarelo, laranja
    e as mais antigas ficam rosa/vermelho neon.

    Parametros:
        age (int): Idade da celula (0 = morta, 1-65535 = viva)

    Retorna:
        tuple: (R, G, B) no intervalo 0-255
    """
    if age == 0:
        return BG_COLOR

    # Normaliza a idade de 1..500 para o fator 0.0..1.0 (acima de 500 satura)
    max_color_age = 500
    factor = min((age - 1) / (max_color_age - 1), 1.0)

    # Interpola o Hue (matiz) de 180 (ciano) ate 340 (rosa)
    # Percurso: Ciano(180) -> Verde(120) -> Amarelo(60) -> Laranja(30) -> Vermelho(0/360) -> Rosa(340)
    hue = 180 - (factor * 200)
    if hue < 0:
        hue += 360

    color = pygame.Color(0)
    color.hsla = (hue, 100, 50, 100)
    return (color.r, color.g, color.b)


# Cache de cores: dicionario que armazena cores ja calculadas sob demanda
# Evita pre-computar 65536 entradas; na pratica poucas centenas serao usadas
COLOR_CACHE = {}

def build_color_table():
    """
    Inicializa o cache de cores.
    Deve ser chamada apos pygame.init() pois usa pygame.Color internamente.
    """
    global COLOR_CACHE
    COLOR_CACHE = {0: BG_COLOR}

def get_cached_color(age):
    """
    Retorna a cor para a idade informada, usando cache para evitar recalculos.
    """
    if age not in COLOR_CACHE:
        COLOR_CACHE[age] = get_cell_color(age)
    return COLOR_CACHE[age]

# =============================================================================
# FUNCOES DE DESENHO
# =============================================================================

def draw_grid(screen, shared_grid):
    """
    Desenha todas as celulas do grid na tela do Pygame.
    Le diretamente da memoria compartilhada com o C++ (zero-copy).

    Parametros:
        screen: Surface principal do Pygame
        shared_grid: Array ctypes mapeado sobre a memoria do C++
    """
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            age = shared_grid[y * GRID_WIDTH + x]
            if age > 0:
                color = get_cached_color(age)
                pygame.draw.rect(
                    screen,
                    color,
                    (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE - 1, CELL_SIZE - 1)
                )


def make_button(text, x, y, w=90, h=36):
    """
    Cria um dicionario representando um botao do painel.

    Parametros:
        text (str): Texto exibido no botao
        x, y (int): Posicao do canto superior esquerdo
        w, h (int): Largura e altura em pixels

    Retorna:
        dict: {"rect": pygame.Rect, "text": str}
    """
    return {"rect": pygame.Rect(x, y, w, h), "text": text}


def draw_controls(screen, font, buttons, is_playing, sim_speed, generation):
    """
    Desenha o painel de controles na parte inferior da tela.
    Inclui botoes interativos, indicador de velocidade e contagem de geracao.

    Parametros:
        screen: Surface principal do Pygame
        font: Fonte carregada do Pygame
        buttons (list): Lista de dicionarios de botoes
        is_playing (bool): Se a simulacao esta rodando
        sim_speed (int): Velocidade de simulacao em FPS
        generation (int): Numero da geracao atual
    """
    panel_y = GRID_HEIGHT * CELL_SIZE

    # Fundo do painel
    pygame.draw.rect(screen, PANEL_BG, (0, panel_y, WINDOW_WIDTH, PANEL_HEIGHT))
    # Linha separadora sutil entre o grid e o painel
    pygame.draw.line(screen, (50, 50, 65), (0, panel_y), (WINDOW_WIDTH, panel_y), 2)

    # Pega a posicao do mouse para efeito de hover
    mouse_pos = pygame.mouse.get_pos()

    for btn in buttons:
        rect = btn["rect"]
        text = btn["text"]

        # Cor do botao: destaque se o mouse esta sobre ele
        is_hover = rect.collidepoint(mouse_pos)
        if text == "PAUSE":
            # Botao ativo (simulacao rodando) - cor diferenciada
            btn_color = (50, 180, 100) if not is_hover else (70, 220, 130)
        elif is_hover:
            btn_color = (60, 60, 80)
        else:
            btn_color = (40, 40, 55)

        # Desenha o retangulo do botao com bordas arredondadas
        pygame.draw.rect(screen, btn_color, rect, border_radius=6)
        # Borda sutil
        pygame.draw.rect(screen, (80, 80, 100), rect, width=1, border_radius=6)

        # Renderiza o texto centralizado dentro do botao
        text_surf = font.render(text, True, (220, 220, 235))
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)

    # Indicador de velocidade (lado direito do painel)
    speed_text = font.render(f"FPS: {sim_speed}", True, (180, 180, 200))
    screen.blit(speed_text, (WINDOW_WIDTH - 230, panel_y + 12))

    # Contagem de geracao
    gen_text = font.render(f"Gen: {generation}", True, (140, 140, 160))
    screen.blit(gen_text, (WINDOW_WIDTH - 230, panel_y + 44))

# =============================================================================
# LOOP PRINCIPAL
# =============================================================================

def main():
    """
    Funcao principal do programa.
    Inicializa o Pygame, carrega a DLL do C++, mapeia a memoria compartilhada
    e executa o loop de eventos/renderizacao.
    """
    # --- Inicializacao ---
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Jogo da Vida de Conway - C++ / Python")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 26)

    # Constroi a tabela de cores (precisa do pygame inicializado)
    build_color_table()

    # Carrega o motor C++
    lib = load_engine_library()

    # Inicializa o grid no C++
    if not lib.init_game(GRID_WIDTH, GRID_HEIGHT):
        print("ERRO: Falha ao inicializar o motor C++.")
        pygame.quit()
        sys.exit(1)

    # Mapeia o ponteiro da memoria do C++ para um array acessivel em Python
    ptr = lib.get_grid_pointer()
    GridArrayType = ctypes.c_uint16 * (GRID_WIDTH * GRID_HEIGHT)
    shared_grid = GridArrayType.from_address(ptr)

    # --- Variaveis de estado ---
    is_playing = False    # Simulacao pausada ao iniciar
    sim_speed = 10        # Velocidade inicial: 10 geracoes por segundo
    generation = 0        # Contador de geracoes
    sim_accumulator = 0.0 # Acumulador de tempo para desacoplar FPS da velocidade

    # --- Definicao dos botoes do painel ---
    panel_y = GRID_HEIGHT * CELL_SIZE
    btn_y = panel_y + 18

    buttons = [
        make_button("PLAY", 20, btn_y),
        make_button("STEP", 120, btn_y),
        make_button("CLEAR", 220, btn_y, w=80),
        make_button("RANDOM", 310, btn_y, w=95),
        make_button("[-]", 415, btn_y, w=45),
        make_button("[+]", 470, btn_y, w=45),
    ]

    # --- Loop principal ---
    running = True
    while running:

        dt = clock.tick(UI_FPS) / 1000.0  # Delta time em segundos

        # =====================================================================
        # FASE 1: CAPTURA DE EVENTOS
        # =====================================================================
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                # Tecla ESPACO: alterna Play/Pause
                if event.key == pygame.K_SPACE:
                    is_playing = not is_playing
                    buttons[0]["text"] = "PAUSE" if is_playing else "PLAY"

                # Tecla N: avanca um step
                elif event.key == pygame.K_n:
                    lib.update_game()
                    generation += 1

                # Tecla C: limpa o grid
                elif event.key == pygame.K_c:
                    lib.clear_grid()
                    generation = 0
                    is_playing = False
                    buttons[0]["text"] = "PLAY"

                # Tecla R: randomiza o grid
                elif event.key == pygame.K_r:
                    lib.randomize_grid(ctypes.c_float(0.20))
                    generation = 0

                # Setas: controle de velocidade
                elif event.key == pygame.K_UP:
                    sim_speed = min(sim_speed + 5, 120)
                elif event.key == pygame.K_DOWN:
                    sim_speed = max(sim_speed - 5, 1)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos

                # Clique na area do painel: verifica se acertou um botao
                if my >= GRID_HEIGHT * CELL_SIZE:
                    for btn in buttons:
                        if btn["rect"].collidepoint(mx, my):
                            action = btn["text"]

                            if action in ("PLAY", "PAUSE"):
                                is_playing = not is_playing
                                btn["text"] = "PAUSE" if is_playing else "PLAY"

                            elif action == "STEP":
                                lib.update_game()
                                generation += 1

                            elif action == "CLEAR":
                                lib.clear_grid()
                                generation = 0
                                is_playing = False
                                buttons[0]["text"] = "PLAY"

                            elif action == "RANDOM":
                                lib.randomize_grid(ctypes.c_float(0.20))
                                generation = 0

                            elif action == "[-]":
                                sim_speed = max(sim_speed - 5, 1)

                            elif action == "[+]":
                                sim_speed = min(sim_speed + 5, 120)
                            break

        # =====================================================================
        # FASE 2: MOUSE CONTINUO (ARRASTAR PARA PINTAR/APAGAR)
        # =====================================================================
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0] or mouse_buttons[2]:
            mx, my = pygame.mouse.get_pos()
            # So desenha se o mouse esta dentro da area do grid
            if 0 <= mx < WINDOW_WIDTH and 0 <= my < GRID_HEIGHT * CELL_SIZE:
                gx = mx // CELL_SIZE
                gy = my // CELL_SIZE
                # Garante que as coordenadas estao dentro dos limites
                if 0 <= gx < GRID_WIDTH and 0 <= gy < GRID_HEIGHT:
                    if mouse_buttons[0]:
                        lib.set_cell(gx, gy, 1)     # Botao esquerdo: pintar
                    elif mouse_buttons[2]:
                        lib.set_cell(gx, gy, 0)     # Botao direito: apagar

        # =====================================================================
        # FASE 3: ATUALIZACAO DA FISICA
        # =====================================================================
        # Desacopla a velocidade da simulacao do FPS de renderizacao.
        # A interface roda a 60 FPS, mas a fisica avanca conforme sim_speed.
        if is_playing:
            sim_accumulator += dt
            step_interval = 1.0 / sim_speed
            while sim_accumulator >= step_interval:
                lib.update_game()
                generation += 1
                sim_accumulator -= step_interval

        # =====================================================================
        # FASE 4: DESENHO
        # =====================================================================
        screen.fill(BG_COLOR)
        draw_grid(screen, shared_grid)
        draw_controls(screen, font, buttons, is_playing, sim_speed, generation)

        # =====================================================================
        # FASE 5: ATUALIZA A TELA
        # =====================================================================
        pygame.display.flip()

    # --- Finalizacao ---
    lib.free_game()
    pygame.quit()
    sys.exit()

# =============================================================================
# PONTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    main()
