// engine.cpp
// Motor de simulação do Jogo da Vida de Conway escrito em C++
// Será compilado como uma biblioteca dinâmica (.dll no Windows ou .so no Linux)

#include <iostream>
#include <cstring>
#include <algorithm>
#include <cstdint>
#include <ctime>

int width = 0;
int height = 0;
uint16_t* current_grid = nullptr;
uint16_t* next_grid = nullptr;

extern "C" {

    bool init_game(int w, int h){
        current_grid = new (std::nothrow) uint16_t[w * h]();
        next_grid = new (std::nothrow) uint16_t[w * h]();

        if (!current_grid || !next_grid) {
            std::cerr << "Erro: Falha ao alocar memoria para os grids" << std::endl;
            delete[] current_grid;
            delete[] next_grid;
            current_grid = nullptr;
            next_grid = nullptr;
            return false;
        }
        width = w;
        height = h;
        
        srand(time(NULL));
        
        return true;
    }

    void free_game() {
        delete[] current_grid;
        delete[] next_grid;
        current_grid = nullptr;
        next_grid = nullptr;
    }

    uint16_t* get_grid_pointer() {
        return current_grid;
    }

    void set_cell(int x, int y, uint16_t age) {
        if (x < 0 || x >= width || y < 0 || y >= height) {
            return;
        }
        current_grid[y * width + x] = age;
    }

    void clear_grid() {
        memset(current_grid, 0, width * height * sizeof(uint16_t));
    }

    void randomize_grid(float probability) {
        for(int i = 0; i < width * height; i++) {
            current_grid[i] = ((float)rand() / RAND_MAX) < probability ? 1 : 0;
        }
    }

    int count_alive_neighbors(int x, int y){
        int alive_neighbors = 0;
        
        for(int dy = -1; dy < 2; dy++ ){
            for(int dx = -1; dx < 2; dx++ ){
                if (dx == 0 && dy == 0) continue;

                //calcula a coordenada circular das celulas
                int nx = (x + dx + width) % width;
                int ny = (y + dy + height) % height;

                if(current_grid[ny * width + nx] > 0){
                    alive_neighbors++;
                }
            }
        }

        return alive_neighbors;
    }

    void update_game(){
        for(int y = 0; y < height; y++ ){
            for(int x = 0; x < width; x++ ){
                int alive_neighbors = count_alive_neighbors(x, y);
                int index = y * width + x;
                uint16_t current_cell = current_grid[index];

                if (current_cell == 0){
                    if( alive_neighbors == 3){
                        next_grid[index] = 1;
                    } else {
                        next_grid[index] = 0;
                    }
                }
                
                if (current_cell > 0){
                    if (alive_neighbors < 2){
                        next_grid[index] = 0;
                    }

                    if (alive_neighbors == 2 || alive_neighbors == 3){
                        next_grid[index] = (uint16_t)std::min( (int)current_cell + 1, 65535 );
                    }

                    if (alive_neighbors > 3){
                        next_grid[index] = 0;
                    }
                }
            }
        }
        std::memcpy(current_grid, next_grid, width * height * sizeof(uint16_t));
    }
}
