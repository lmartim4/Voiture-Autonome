funcao meia volta
	deve chamar essa função nos casos : detecção de sentido inverso na pista; e colisão
	
	colisão detectada se : rodinha do carrinho está parada por x tempo
	sentido inverso detectado por câmera
	

função meia volta por sentido inverso:

	mede lado com mais espaço (lado L)
	control = 0
	while (control == 0 and (media das cores nao correta))
		gira rodinha pro lado L
		while (sinal_sensor_ultrasonico >= X or tempo < y segundos):
			#aciona ré enquanto o sensor de distancia detectar uma distancia maior ou igual a x ou por y tempo (o que vier primeiro)
			acionar ré
		gira a rodinha para o lado inverso
		while (tempo < y segundos):
			aciona marcha pra frente
			if sinal_lidar_45graus < Largura_Pista:
				control = 1
		
		
função ré por colisão;
	
	se ficar mais de x tempo com a rodinha parada, detectado colisao
	se a camera detectar mais de 9x% de vermelho ou verde (bateu contra uma parede):
		gira a rodinha para o lado correspondente à cor (se for vermelho, gira pra esquerda, se for verde, gira pra direita, pra manter o sentido correto)
		aciona ré por 1 segundo
		libera algoritmo normal
		
	senao (deve ter batido contra um obstáculo e só a rodinha ficou presa):
		aciona ré por 0.5 segundo
		libera algoritmo normal