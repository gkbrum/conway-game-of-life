# Makefile
# Script de automação para compilação da DLL do C++ e execução do Jogo da Vida

CXX = g++
CXXFLAGS = -O3 -shared -fPIC -static-libgcc -static-libstdc++

# Identifica se está rodando no Windows ou Unix/Linux/macOS
ifeq ($(OS),Windows_NT)
    TARGET = engine.dll
    RM = del /Q /F
else
    TARGET = engine.so
    RM = rm -f
endif

# Regra padrão: compila a DLL/SO
all: $(TARGET)

$(TARGET): src/engine.cpp
	$(CXX) $(CXXFLAGS) -o $(TARGET) src/engine.cpp

# Compila a DLL e executa o jogo
run: all
	python src/main.py

# Compila a DLL e roda os testes básicos
test: all
	python src/test_engine.py

# Remove a DLL compilada
clean:
	$(RM) $(TARGET)
