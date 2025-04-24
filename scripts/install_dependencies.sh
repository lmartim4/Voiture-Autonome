#!/bin/bash

# Script para verificar e instalar Python 3.11 ou superior

# Cores para mensagens
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Função para exibir mensagens de erro e sair
error_exit() {
    echo -e "${RED}ERRO: $1${NC}"
    exit 1
}

# Função para exibir mensagens de sucesso
success_message() {
    echo -e "${GREEN}SUCESSO: $1${NC}"
}

# Função para exibir mensagens de informação
info_message() {
    echo -e "${YELLOW}INFO: $1${NC}"
}

# Verificando se Python está instalado
info_message "Verificando instalação do Python..."

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    info_message "Python $PYTHON_VERSION encontrado."
    
    # Verificar se a versão é 3.11 ou superior
    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
        success_message "Python $PYTHON_VERSION já está instalado e atende aos requisitos (3.11 ou superior)."
        exit 0
    else
        info_message "A versão atual do Python ($PYTHON_VERSION) é menor que a requerida (3.11)."
    fi
else
    info_message "Python 3 não encontrado no sistema."
fi

# Verificando conexão com a internet
info_message "Verificando conexão com a internet..."
if ! ping -c 1 google.com &> /dev/null; then
    error_exit "Sem conexão com a internet! Verifique sua conexão e tente novamente."
fi

# Atualizando os repositórios
info_message "Atualizando lista de pacotes..."
sudo apt-get update || error_exit "Falha ao atualizar repositórios!"

# Instalando Python 3.11 ou superior
info_message "Instalando Python 3.11 ou superior..."

# Em sistemas baseados em Debian/Ubuntu mais recentes
if [ -n "$(command -v apt)" ]; then
    # Adicionando repositório deadsnakes (comum para versões mais recentes do Python)
    sudo apt-get install -y software-properties-common || error_exit "Falha ao instalar software-properties-common!"
    sudo add-apt-repository -y ppa:deadsnakes/ppa || error_exit "Falha ao adicionar repositório deadsnakes!"
    sudo apt-get update || error_exit "Falha ao atualizar após adicionar repositório!"
    
    # Tentando instalar Python 3.11
    sudo apt-get install -y python3.11 python3.11-venv python3.11-dev || error_exit "Falha ao instalar Python 3.11!"
    
    # Verificar se a instalação foi bem-sucedida
    if command -v python3.11 &> /dev/null; then
        PYTHON_VERSION=$(python3.11 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        success_message "Python $PYTHON_VERSION foi instalado com sucesso!"
        
        # Configurando como padrão (opcional)
        info_message "Configurando Python 3.11 como padrão para 'python3'..."
        sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
    else
        error_exit "Falha ao instalar Python 3.11. Por favor, instale manualmente."
    fi
else
    error_exit "Gerenciador de pacotes 'apt' não encontrado. Por favor, instale Python 3.11 ou superior manualmente."
fi

# Verificação final
info_message "Verificando instalação final..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
        success_message "Python $PYTHON_VERSION está instalado e pronto para uso!"
    else
        info_message "Python $PYTHON_VERSION está instalado, mas a versão padrão ainda é menor que 3.11."
        info_message "Use 'python3.11' para executar com a versão correta."
    fi
else
    error_exit "Algo deu errado. Python 3 não está disponível."
fi

exit 0