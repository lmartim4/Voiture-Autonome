#!/usr/bin/env python3
import time
import numpy as np
from interface_serial import *
from interface_lidar import RPLidarReader
from interface_motor import RealMotorInterface
from interface_steer import RealSteerInterface
from algorithm.constants import LIDAR_BAUDRATE

def realizar_meia_volta(steer, motor, sensor_traseiro, dados_lidar):
    """
    Realiza uma meia volta (U-turn) analisando os dados do LiDAR para determinar a melhor direção
    de rotação e garantindo que não há obstáculos no caminho.
    
    Args:
        steer: Interface de direção para controlar a direção do carrinho
        motor: Interface do motor para controlar a velocidade do carrinho
        sensor_traseiro: Interface do sensor ultrassônico para obter dados de distância traseira
        dados_lidar: Array de dados do LiDAR com 360 medições de distância
        
    Returns:
        bool: True se a meia volta foi completada com sucesso, False caso contrário
    """
    # Definir limiares de segurança
    DISTANCIA_SEGURA_MINIMA = 10/1000  # cm para m
    ESPACO_MINIMO_GIRO = 50/1000  # cm para m
    DISTANCIA_PAREDE_TRASEIRA = 15/1000  # cm para m - distância ideal para parar próximo à parede
    
    # Analisando dados do LiDAR para encontrar a melhor direção de rotação
    # Tratando a região frontal que envolve o limite 0/360
    dados_frente = np.concatenate((dados_lidar[350:], dados_lidar[:10]))
    dados_esquerda = dados_lidar[60:120]      # Região à esquerda do carrinho
    dados_direita = dados_lidar[240:300]      # Região à direita do carrinho
    
    # Calcular distâncias médias, ignorando valores zero
    distancia_frente = np.mean(dados_frente[dados_frente > 0]) if np.any(dados_frente > 0) else 0
    # Se distancia_frente ainda for 0, tentar um ângulo frontal mais amplo
    if distancia_frente == 0:
        dados_frente_amplo = np.concatenate((dados_lidar[340:], dados_lidar[:20]))
        distancia_frente = np.mean(dados_frente_amplo[dados_frente_amplo > 0]) if np.any(dados_frente_amplo > 0) else 0
    
    media_esquerda = np.mean(dados_esquerda[dados_esquerda > 0]) if np.any(dados_esquerda > 0) else 0
    media_direita = np.mean(dados_direita[dados_direita > 0]) if np.any(dados_direita > 0) else 0
    
    # Obter dados do sensor ultrassônico para distância traseira
    distancia_traseira = sensor_traseiro.get_ultrasonic_data()
    print(f"LiDAR - Frente: {distancia_frente:.1f}cm, Esquerda: {media_esquerda:.1f}cm, Direita: {media_direita:.1f}cm")
    
    # Verificar valor do sensor traseiro
    if distancia_traseira == -1:
        print("Sensor traseiro indisponível, assumindo caminho livre...")
        distancia_traseira = float('inf')  # Assumir que há espaço suficiente
    else:
        print(f"Distância traseira ultrassônica: {distancia_traseira:.1f}cm")
    
    # Verificar se há espaço suficiente para a manobra
    if distancia_traseira >= 0 and distancia_traseira < DISTANCIA_SEGURA_MINIMA:
        print("Espaço insuficiente atrás para meia volta, abortando...")
        return False
    
    # Verificar se há uma parede ou obstáculo muito próximo na frente
    if distancia_frente < DISTANCIA_SEGURA_MINIMA:
        print("Obstáculo muito próximo na frente, prosseguindo com cautela...")
    
    # Verificar se há espaço suficiente em ambos os lados para virar
    if max(media_esquerda, media_direita) < ESPACO_MINIMO_GIRO:
        print("Espaço insuficiente em ambos os lados para uma meia volta segura, abortando...")
        return False
    
    # Determinar qual lado tem mais espaço e executar a curva de acordo
    if media_esquerda > media_direita:
        print("Espaço livre à esquerda, rotacionando para a esquerda...")
        virar_esquerda = True
    else:
        print("Espaço livre à direita, rotacionando para a direita...")
        virar_esquerda = False
    
    # Executar a volta com verificações de segurança contínuas
    try:
        # Fase 1: Reverso com direção apropriada
        angulo_direcao = +20 if virar_esquerda else -20  # Ângulo mais suave
        steer.set_steering_angle(angulo_direcao)
        motor.set_speed(-0.8)  # Velocidade mais baixa para segurança
        
        # Verificação de segurança durante a fase reversa - continuar até detectar parede
        print("Dando ré até detectar parede...")
        tempo_maximo = 5.0  # Limitar o tempo máximo para evitar problemas (5 segundos)
        inicio_tempo = time.time()
        
        # Loop para dar ré até detectar a parede ou timeout
        while time.time() - inicio_tempo < tempo_maximo:
            distancia_traseira = sensor_traseiro.get_ultrasonic_data()
            
            # Tratar sensor indisponível
            if distancia_traseira == -1:
                print("Sensor traseiro temporariamente indisponível, continuando manobra...")
                time.sleep(0.1)
                continue
                
            print(f"Distância traseira: {distancia_traseira:.3f}m")
            
            # Verificar se está próximo o suficiente da parede
            if distancia_traseira <= DISTANCIA_PAREDE_TRASEIRA:
                print("Parede detectada atrás, parando...")
                break
                
            # Ajustar velocidade se estiver ficando muito próximo
            if distancia_traseira > 0 and distancia_traseira < DISTANCIA_SEGURA_MINIMA / 2:
                motor.set_speed(-0.3)  # Reduzir drasticamente a velocidade
            
            time.sleep(0.1)  # Verificar a cada 100ms
        
        # Fase 2: Parar momentaneamente
        motor.set_speed(0)
        time.sleep(0.5)
        
        # Fase 3: Avançar com direção oposta para completar a volta
        steer.set_steering_angle(-angulo_direcao)
        motor.set_speed(0.7)  # Velocidade reduzida para uma manobra mais suave
        
        # Verificação de segurança durante a fase de avanço
        inicio_tempo = time.time()
        while time.time() - inicio_tempo < 2.5:  # Tempo aumentado para compensar velocidade menor
            # Tentar obter a leitura do sensor traseiro enquanto avança
            distancia_traseira = sensor_traseiro.get_ultrasonic_data()
            if distancia_traseira != -1:
                print(f"Distância traseira durante avanço: {distancia_traseira:.3f}m")
            
            # Varredura rápida do LiDAR da área frontal - tratar corretamente a quebra
            dados_varredura = np.concatenate((dados_lidar[350:], dados_lidar[:10]))
            
            frente_min = np.min(dados_varredura[dados_varredura > 0]) if np.any(dados_varredura > 0) else float('inf')
            # Se não houver leitura válida, tentar com ângulo mais amplo
            if frente_min == float('inf'):
                dados_amplos = np.concatenate((dados_lidar[340:], dados_lidar[:20]))
                frente_min = np.min(dados_amplos[dados_amplos > 0]) if np.any(dados_amplos > 0) else float('inf')
            
            if frente_min < DISTANCIA_SEGURA_MINIMA:
                print("Aviso: Obstáculo detectado à frente, ajustando...")
                motor.set_speed(0.5)  # Desacelerar
            time.sleep(0.1)  # Verificar a cada 100ms
        
        # Fase 4: Endireitar as rodas e normalizar a velocidade (velocidade mais lenta)
        steer.set_steering_angle(0)
        motor.set_speed(0.6)  # Velocidade reduzida após a manobra
    except Exception as e:
        # Parada de emergência se ocorrer algum erro
        print(f"Erro durante a meia volta: {e}")
        motor.set_speed(0)
        steer.set_steering_angle(0)
        return False
    
    print("Meia volta concluída")
    return True

def main():
    try:
        print("Inicializando componentes para meia volta...")
        
        # Inicializar LiDAR
        I_Lidar = RPLidarReader(port="/dev/ttyUSB0", baudrate=LIDAR_BAUDRATE)
        I_Lidar.start_live_plot()  # Iniciar o gráfico ao vivo para visualizar os dados do LiDAR
        print("LiDAR inicializado")
        
        # Inicializar direção e motor
        I_Steer = RealSteerInterface(channel=1, frequency=50.0)
        I_Motor = RealMotorInterface(channel=0, frequency=50.0)
        print("Direção e motor inicializados")
        
        # Inicializar sensor ultrassônico
        init_serial(port="/dev/ttyACM0", baudrate=9600, timeout=1.0)
        I_back_wall_distance_reading = SharedMemUltrasonicInterface()
        print("Sensor ultrassônico inicializado")
        
        # Aguardar o LiDAR começar a fornecer dados
        print("Aguardando leituras do LiDAR...")
        contagem_nao_zero = np.count_nonzero(I_Lidar.get_lidar_data())
        while contagem_nao_zero < 150:  # Reduzido para 150 pontos mínimos
            contagem_nao_zero = np.count_nonzero(I_Lidar.get_lidar_data())
            print(f"Pontos de dados do LiDAR: {contagem_nao_zero}/180")
            time.sleep(0.5)
        
        print("Todos os componentes inicializados. Realizando meia volta em 3 segundos...")
        time.sleep(3)
        
        # Executar meia volta
        resultado = realizar_meia_volta(
            steer=I_Steer,
            motor=I_Motor,
            sensor_traseiro=I_back_wall_distance_reading,
            dados_lidar=I_Lidar.get_lidar_data()
        )
        
        if resultado:
            print("Meia volta executada com sucesso!")
        else:
            print("Meia volta falhou ou foi abortada.")
        
        # Aguardar um momento antes de parar tudo
        time.sleep(2)
        
    except KeyboardInterrupt:
        print("Interrompido pelo usuário.")
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        print("Limpando recursos...")
        try:
            I_Motor.stop()
            I_Steer.stop()
            I_Lidar.stop()
            shutdown_serial()
        except:
            pass
        print("Concluído.")

if __name__ == "__main__":
    main()