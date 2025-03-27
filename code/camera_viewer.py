import cv2
import numpy as np
from voiture_algorithm import VoitureAlgorithm

# Atualizado para utilizar a função process_stream da RealCameraInterface

def draw_points(frame, green_points, red_points, avg_g, avg_r):
    for pt in green_points:
        cv2.circle(frame, tuple(pt), 5, (0, 255, 0), -1)

    for pt in red_points:
        cv2.circle(frame, tuple(pt), 5, (0, 0, 255), -1)

    if avg_g >= 0:
        avg_g_x = int(avg_g)
        avg_g_y = frame.shape[0] // 2
        cv2.circle(frame, (avg_g_x, avg_g_y), 7, (0, 255, 0), -1)

    if avg_r >= 0:
        avg_r_x = int(avg_r)
        avg_r_y = frame.shape[0] // 2
        cv2.circle(frame, (avg_r_x, avg_r_y), 7, (0, 0, 255), -1)

    return frame


def camera_viewer(algorithm: VoitureAlgorithm):
    green_points = []  # Você pode carregar ou atualizar os pontos verdes
    red_points = []    # Você pode carregar ou atualizar os pontos vermelhos

    while True:
        algorithm.run_step()

        frame = algorithm.camera.get_camera_frame()

        if frame is None:
            continue

        avg_r, avg_g, _, _ = algorithm.camera.process_stream()

        frame_with_points = draw_points(frame, green_points, red_points, avg_g, avg_r)

        cv2.imshow('Camera Viewer', frame_with_points)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    camera_viewer(algorithm)