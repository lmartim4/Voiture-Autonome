import cv2
from picamera2 import Picamera2
import numpy as np

class Camera:
    def __init__(self, width=640, height=480):
        self.picam2 = Picamera2()
        
        config = self.picam2.create_preview_configuration(
            main={"size": (width, height)},
            lores={"size": (width, height)}
        )
        self.picam2.configure(config)
        
        try:
            self.picam2.start()
            print("Initialisation réussie de la caméra")
        except Exception as e:
            print(f"Erreur d'initialisation de la caméra: {e}")
            raise

        self.width = width
        self.height = height
    
    def read_frame(self):
        frame = self.picam2.capture_array()
        if frame is None:
            print("Le cadre de la caméra n'a pas pu être capturé")
            return None
        return frame
    
    def process_stream(self):
        frame = self.read_frame()
        frame_hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)

        red_lower = np.array([0, 150, 150])     # EN HSV, A AJUSTER POUR QUE LE MUR SOIT DETECTE
        red_upper = np.array([10, 255, 255])    # EN HSV, A AJUSTER POUR QUE LE MUR SOIT DETECTE

        green_lower = np.array([50, 100, 100])  # EN HSV, A AJUSTER POUR QUE LE MUR SOIT DETECTE
        green_upper = np.array([70, 255, 255])  # EN HSV, A AJUSTER POUR QUE LE MUR SOIT DETECTE

        mask_r = cv2.inRange(frame_hsv, red_lower, red_upper)
        mask_g = cv2.inRange(frame_hsv, green_lower, green_upper)

        stack_r = np.column_stack(np.where(mask_r > 0))
        avg_r = 0
        # If no white pixels, return None
        if len(stack_r) == 0:
            avg_r = -1
        else:
            avg_r = np.mean(stack_r[:, 1]) # POSITION MOYENNE DE LA COULEUR ROUGE

        stack_g = np.column_stack(np.where(mask_g > 0))
        avg_g = 0
        # If no white pixels, return None
        if len(stack_g) == 0:
            avg_g = -1
        else:
            avg_g = np.mean(stack_g[:, 1]) # POSITION MOYENNE DE LA COULEUR VERTE

        count_r = np.count_nonzero(mask_r)/(self.width*self.height) # POURCENTAGE DE LA COULEUR ROUGE
        count_g = np.count_nonzero(mask_g)/(self.width*self.height) # POURCENTAGE DE LA COULEUR VERTE

        return avg_r, avg_g, count_r, count_g

                              
               
        
        
# EXEMPLE D'IMPLEMENTATION DANS LE MAIN 

def main():
    camera = Camera(width=640, height=480)
    try:
            while True:
                avg_r, avg_g, count_r, count_g = camera.process_stream()

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    except Exception as e:
            print(f"Error in video processing: {e}")
        
    finally:
        cv2.destroyAllWindows()
        camera.picam2.stop()

    

if __name__ == '__main__':
    main()
