import cv2
import os
import numpy as np

class Camera:
    def __init__(self, width=1920, height=1080):
        self.width = width
        self.height = height
        pass
    
    def read_frame(self):
        frame = cv2.imread('photos/test.jpg')
        self.width = frame.shape[1]
        self.height = frame.shape[0]
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return frame
    
    def process_stream(self):
        frame = self.read_frame()
        frame_hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)

        red_lower = np.array([0, 180, 180])     # EN HSV, A AJUSTER POUR QUE LE MUR SOIT DETECTE
        red_upper = np.array([10, 220, 230])    # EN HSV, A AJUSTER POUR QUE LE MUR SOIT DETECTE

        green_lower = np.array([35, 100, 100])  # EN HSV, A AJUSTER POUR QUE LE MUR SOIT DETECTE
        green_upper = np.array([85, 255, 255])  # EN HSV, A AJUSTER POUR QUE LE MUR SOIT DETECTE
     
        mask_r = cv2.inRange(frame_hsv, red_lower, red_upper)
        mask_g = cv2.inRange(frame_hsv, green_lower, green_upper)

        stack_r = np.column_stack(np.where(mask_r > 0))
        avg_r = 0
        # If no white pixels, return None
        if len(stack_r) == 0:
            avg_r = -1
        else:
            avg_r = np.mean(stack_r[:, 1])/self.width # POSITION MOYENNE DE LA COULEUR ROUGE

        stack_g = np.column_stack(np.where(mask_g > 0))
        avg_g = 0
        # If no white pixels, return None
        if len(stack_g) == 0:
            avg_g = -1
        else:
            avg_g = np.mean(stack_g[:, 1])/self.width # POSITION MOYENNE DE LA COULEUR VERTE

        #cv2.imshow('R', mask_r)
        #cv2.imshow('G', mask_g)
        #frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        #cv2.imshow('image', frame)
        
        #cv2.waitKey()
        #cv2.destroyAllWindows()
        

        count_r = np.count_nonzero(mask_r)/(self.width*self.height) # POURCENTAGE DE LA COULEUR ROUGE
        count_g = np.count_nonzero(mask_g)/(self.width*self.height) # POURCENTAGE DE LA COULEUR VERTE

        return avg_r, avg_g, count_r, count_g
    
        
# EXEMPLE D'IMPLEMENTATION DANS LE MAIN 

def main():
    camera = Camera()
    avg_r, avg_g, count_r, count_g = camera.process_stream()
    print(f"avg_r: {avg_r}, avg_g: {avg_g}, count_r: {count_r}, count_g: {count_g}")
   

if __name__ == '__main__':
    main()
