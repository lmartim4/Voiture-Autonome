#!/bin/bash

# Script para configurar o script de inicialização rápida bash para o projeto Voiture-Autonome

# Cores para mensagens
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Caminho para o diretório home do usuário
HOME_DIR="$HOME"
STARTUP_SCRIPT="$HOME_DIR/.bash_quick_startup.sh"
BASHRC_FILE="$HOME_DIR/.bashrc"

# Conteúdo do script de inicialização rápida
QUICK_STARTUP_CONTENT="#!/bin/bash
# ~/.bash_quick_startup.sh

RED='\\\033[1;31m'
GREEN='\\\033[1;32m'
YELLOW='\\\033[1;33m'
CYAN='\\\033[1;36m'
NC='\\\033[0m'  # No Color

# Change to the project directory
cd ~/Voiture-Autonome/code || { echo -e \"\${RED}Error: Directory not found!\${NC}\"; exit 1; }

# Activate the virtual environment and check if it was successful
if source ./venv/bin/activate; then
  echo -e \"\${YELLOW}=============================================${NC}\"
  echo -e \"\${GREEN}        Welcome to Voiture Jaune!${NC}\"
  echo -e \"\${YELLOW}=============================================${NC}\"
  echo -e \"\${CYAN}Current Date: ${NC}\$(date)\"
  echo -e \"\${CYAN}User:         ${NC}\$(whoami)\"
  echo -e \"\${CYAN}Project Dir:  ${NC}~/Voiture-Autonome/code\"
  echo -e \"\${YELLOW}--------------------------------------------${NC}\"
  echo -e \"\${YELLOW}NOTE: ${NC}You are now in a Python virtual environment\"
  echo -e \"      Type \${GREEN}deactivate${NC} to exit the environment\"
  echo -e \"\${YELLOW}=============================================${NC}\"

  # Clean Command History and Preload with Three Commands
  history -c
  history -w

  # Add only the three desired commands to the history (in order)
  history -s \"python multiplot.py\"
  history -s \"python calibrate.py\"
  history -s \"python main.py\"
else
  echo -e \"\${RED}Error: Could not activate virtual environment!\${NC}\"
fi
"

# Criando o script de inicialização rápida
echo -e "${YELLOW}Criando script de inicialização rápida em $STARTUP_SCRIPT${NC}"
echo "$QUICK_STARTUP_CONTENT" > "$STARTUP_SCRIPT"

# Tornando o script executável
chmod +x "$STARTUP_SCRIPT"

# Verificando se a criação foi bem-sucedida
if [ -x "$STARTUP_SCRIPT" ]; then
    echo -e "${GREEN}Script de inicialização rápida criado com sucesso!${NC}"
else
    echo -e "${RED}Falha ao criar script de inicialização rápida!${NC}"
    exit 1
fi

# Verificando se a linha já existe no .bashrc
if grep -q "source ~/.bash_quick_startup.sh" "$BASHRC_FILE"; then
    echo -e "${YELLOW}O script de inicialização rápida já está configurado no .bashrc${NC}"
else
    # Adicionando a linha ao .bashrc
    echo -e "${YELLOW}Adicionando script de inicialização ao .bashrc${NC}"
    echo -e "\n# Carregando script de inicialização rápida para o projeto Voiture-Autonome" >> "$BASHRC_FILE"
    echo -e "if [ -f ~/.bash_quick_startup.sh ]; then" >> "$BASHRC_FILE"
    echo -e "   source ~/.bash_quick_startup.sh" >> "$BASHRC_FILE"
    echo -e "fi" >> "$BASHRC_FILE"
    
    # Verificando se a adição foi bem-sucedida
    if grep -q "source ~/.bash_quick_startup.sh" "$BASHRC_FILE"; then
        echo -e "${GREEN}Script de inicialização configurado com sucesso no .bashrc!${NC}"
    else
        echo -e "${RED}Falha ao configurar script de inicialização no .bashrc!${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}Configuração do script de inicialização rápida concluída com sucesso!${NC}"
echo -e "${YELLOW}Para ativar o script imediatamente, execute: source ~/.bash_quick_startup.sh${NC}"
echo -e "${YELLOW}Ou abra um novo terminal para que as alterações tenham efeito.${NC}"

exit 0