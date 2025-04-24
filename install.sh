#!/bin/bash

# Script de instalação principal para o projeto Voiture-Autonome
# Autor: [Seu Nome]
# Data: $(date +%Y-%m-%d)

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

# Verificando se estamos em uma Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    error_exit "Este script deve ser executado em uma Raspberry Pi!"
fi

# Verificando se o diretório do projeto existe no local correto
PROJECT_DIR=~/Voiture-Autonome
if [ ! -d "$PROJECT_DIR" ]; then
    error_exit "Diretório do projeto não encontrado em $PROJECT_DIR! Por favor, clone o repositório primeiro."
fi

# Verificando permissões de sudo
if [ "$EUID" -ne 0 ]; then
    info_message "Este script requer permissões de sudo para algumas operações."
    if ! sudo -n true 2>/dev/null; then
        echo "Por favor, digite sua senha sudo:"
        sudo -v || error_exit "Falha ao obter permissões de sudo!"
    fi
fi

# Mudando para o diretório do projeto
cd "$PROJECT_DIR" || error_exit "Não foi possível acessar o diretório do projeto!"

# Verificando se o diretório de scripts existe
if [ ! -d "$PROJECT_DIR/scripts" ]; then
    error_exit "Diretório de scripts não encontrado em $PROJECT_DIR/scripts! Verifique a estrutura do repositório."
fi

# Verificando se os scripts necessários existem
SCRIPTS=(
    "./scripts/configure_pwm.sh"
    "./scripts/configure_udev.sh"
    "./scripts/setup_bash_startup.sh"
    "./scripts/install_dependencies.sh"
)

for script in "${SCRIPTS[@]}"; do
    if [ ! -f "$script" ]; then
        error_exit "Script $script não encontrado! Verifique a estrutura do repositório."
    fi
done

# Tornando os scripts executáveis
chmod +x ./scripts/*.sh || error_exit "Falha ao tornar os scripts executáveis!"

# Executando os scripts individuais na ordem correta
info_message "Iniciando processo de instalação..."

echo "1/4 - Configurando PWM..."
sudo "./scripts/configure_pwm.sh" || error_exit "Falha na configuração PWM!"
success_message "Configuração PWM concluída!"

echo "2/4 - Configurando regras udev..."
sudo "./scripts/configure_udev.sh" || error_exit "Falha na configuração udev!"
success_message "Configuração udev concluída!"

echo "3/4 - Instalando dependências..."
"./scripts/install_dependencies.sh" || error_exit "Falha na instalação de dependências!"
success_message "Instalação de dependências concluída!"

echo "4/4 - Configurando script de inicialização rápida..."
"./scripts/setup_bash_startup.sh" || error_exit "Falha na configuração do script de inicialização!"
success_message "Configuração do script de inicialização concluída!"

# Finalizando a instalação
success_message "Instalação do projeto Voiture-Autonome concluída com sucesso!"
info_message "Reinicie o sistema para aplicar todas as configurações: sudo reboot"

exit 0