from environment import Environment 
import pygame
import numpy as np
import params

# To understand the implementation : https://www.youtube.com/watch?v=JbUNsYPJK1U

# Criar o ambiente com visualização local
environment = Environment("track2.png")

# Executar a simulação
environment.run()