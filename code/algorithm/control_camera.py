import time
import numpy as np
from algorithm.interfaces import CameraInterface, SteerInterface, MotorInterface

def check_reversed_camera(camera: CameraInterface) -> bool:
    """
      Checks if the trolley is upside down (turned 180° in relation to the track)
    using the camera data.

    The function calls camera.process_stream() to get:
      - avg_r: average position of the red pixels (left wall in normal orientation)
      - avg_g: average position of green pixels (right wall in normal orientation)

    In a normal orientation, avg_r < avg_g is expected. If avg_r > avg_g,
    the image shows that the red wall is on the right and the green wall is on the left,
    i.e. the trolley is upside down.

    Args:
        camera (Camera): Instance of the Camera class.

    Returns:
        bool: True if the trolley is upside down, False otherwise.

    """
    avg_r, avg_g, count_r, count_g = camera.process_stream()
    print(f"Avg_r: {avg_r} Avg_g: {avg_g}")
    
    if avg_r < 0 or avg_g < 0:
        return False
     
    return avg_r < avg_g


def reversing_direction(steer: SteerInterface, motor: MotorInterface, raw_lidar):

    # Analisando os dados do LiDAR para encontrar a melhor direção de rotação

    l_side = raw_lidar[60:120]   # Região à esquerda do carrinho
    r_side = raw_lidar[240:300]  # Região à direita do carrinho
                
    avg_left = np.mean(l_side[l_side > 0])
    avg_right = np.mean(r_side[r_side > 0])
                
    if avg_left > avg_right:
        print("Espace libre à gauche, rotation vers la gauche...")
        steer.set_steering_angle(+20)
        motor.set_speed(-2)
        time.sleep(2.0)
        motor.set_speed(0)
        steer.set_steering_angle(-20)
        motor.set_speed(1.0)
        time.sleep(2.0)
        return
    else:
        print("Espace libre à droite, rotation vers la droite...")
        steer.set_steering_angle(-20)
        motor.set_speed(-2)
        time.sleep(2.0)
        motor.set_speed(0)
        steer.set_steering_angle(+20)
        motor.set_speed(1.0)
        time.sleep(2.0)
        return