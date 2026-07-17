# Jogo da Vida de Conway (C++ + Python)

Este projeto implementa uma versão interativa e de alto desempenho do clássico **Jogo da Vida de Conway** (*Conway's Game of Life*). A arquitetura do projeto combina a eficiência de cálculo do **C++** (motor de simulação) com a facilidade e flexibilidade do **Python** + **Pygame** (renderização gráfica e controle de interface), integrados via **ctypes** com comunicação de cópia zero (*zero-copy*).

---

## 🚀 Arquitetura e Integração

O projeto foi projetado seguindo um modelo híbrido para maximizar o desempenho de simulação sem abrir mão de uma interface rica:

*   **Motor em C++ (`src/engine.cpp`):** Gerencia o estado das células em uma matriz linear alocada dinamicamente no heap. Processa o cálculo de vizinhança circular (topologia em toro) e atualiza o estado de todas as células a cada geração.
*   **Interface em Python (`src/main.py`):** Utiliza **Pygame** para capturar cliques do mouse, teclado e renderizar o tabuleiro a 60 FPS estáveis.
*   **Interoperabilidade via `ctypes` (Cópia Zero):** O Python invoca funções do C++ para alterar ou atualizar o tabuleiro. Para desenhar o estado atual na tela de forma ultraveloz, o Python obtém diretamente o ponteiro de memória da matriz C++ (`get_grid_pointer()`) e cria uma visão compartilhada (`ctypes.c_uint16 * size`), eliminando a necessidade de transferir ou duplicar dados entre as linguagens a cada frame.

---

## 🎨 Características Especiais

*   **Gradiente de Cores por Idade:** Em vez de células simplesmente "vivas" ou "mortas", o motor em C++ rastreia a idade de cada célula sobrevivente (incrementada a cada geração até o limite de 65535). O Python converte essa idade em um gradiente de cores neon dinâmico usando o espaço de cor HSL:
    *   *Células jovens:* Ciano e azul neon.
    *   *Células maduras:* Transicionam por verde, amarelo e laranja.
    *   *Células antigas:* Rosa e vermelho neon.
*   **Interatividade Total:** Permite pausar e desenhar livremente com o mouse ou testar gerações passo a passo.
*   **Física Desacoplada da Renderização:** A interface gráfica roda suavemente a 60 FPS, enquanto a simulação física das células avança na velocidade (gerações por segundo) escolhida pelo usuário.

---

## 🛠️ Requisitos e Dependências

Para rodar este projeto, você precisará de:

1.  **Python 3.8 ou superior**
2.  **Pygame** instalado no Python:
    ```bash
    pip install pygame
    ```
3.  **Compilador C++ (G++ / GCC)** habilitado no seu `PATH`.
4.  **Make** (opcional, para automação com o `Makefile`).

---

## 🏗️ Como Compilar e Executar

### Método 1: Utilizando o Makefile (Recomendado)

O projeto inclui um `Makefile` configurado para detectar automaticamente o sistema operacional (Windows ou Unix-like) e executar as ações necessárias.

No diretório raiz do projeto, execute os comandos abaixo no terminal:

*   **Compilar a biblioteca dinâmica:**
    ```bash
    make
    ```
    *(Gera `engine.dll` no Windows ou `engine.so` no Linux/macOS)*.

*   **Compilar e executar o jogo imediatamente:**
    ```bash
    make run
    ```

*   **Limpar arquivos gerados na compilação:**
    ```bash
    make clean
    ```

---

### Método 2: Compilação Manual via Terminal

Caso não possua o utilitário `make` instalado, você pode compilar manualmente usando o `g++`:

#### No Windows:
```bash
# Compilar a biblioteca DLL
g++ -O3 -shared -fPIC -static-libgcc -static-libstdc++ -o engine.dll src/engine.cpp

# Executar a aplicação
python src/main.py
```

#### No Linux / macOS:
```bash
# Compilar a biblioteca compartilhada .so
g++ -O3 -shared -fPIC -o engine.so src/engine.cpp

# Executar a aplicação
python src/main.py
```

---

## 🎮 Controles da Aplicação

Você pode controlar e desenhar na simulação tanto usando o mouse quanto o teclado:

### Controles de Mouse
*   **Botão Esquerdo (Arrastar):** Desenha/revive células (define idade como 1).
*   **Botão Direito (Arrastar):** Apaga/mata células.

### Botões do Painel & Atalhos do Teclado

| Ação / Controle | Botão na Tela | Atalho de Teclado | Descrição |
| :--- | :--- | :--- | :--- |
| **Play / Pause** | `PLAY` / `PAUSE` | `Espaço` | Inicia ou pausa a evolução automática da simulação. |
| **Avançar Frame** | `STEP` | `N` | Avança exatamente 1 geração (ótimo com o jogo pausado). |
| **Limpar Tela** | `CLEAR` | `C` | Mata todas as células e reseta o contador de gerações. |
| **Randomizar** | `RANDOM` | `R` | Preenche o tabuleiro de forma aleatória com 20% de densidade. |
| **Diminuir Velocidade** | `[-]` | `Seta para Baixo` | Reduz o limite de atualizações por segundo (mínimo de 1 FPS). |
| **Aumentar Velocidade** | `[+]` | `Seta para Cima` | Aumenta o limite de atualizações por segundo (máximo de 120 FPS). |

---

## 📁 Estrutura do Repositório

```text
conway-game-of-life/
│
├── src/
│   ├── engine.cpp          # Código fonte do motor de simulação (C++)
│   └── main.py             # Interface e renderização gráfica (Python)
│
├── Makefile                # Script de automação de compilação
├── README.md               # Documentação do projeto (este arquivo)
│
# Arquivos gerados após compilação:
├── engine.dll              # Biblioteca compilada para Windows (se aplicável)
└── engine.so               # Biblioteca compilada para Unix/Linux (se aplicável)
```
