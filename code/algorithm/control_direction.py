from algorithm.constants import *
from scipy.signal import convolve

def get_nonzero_points_in_hitbox(distances):
    if distances is None:
        raise ValueError("Error: LiDAR input is None.")

    x, y = convert_rad_to_xy(distances, np.arange(0, 360))

    mask_hitbox =  (y > 0) & (np.abs(y) <= HITBOX_H1) & (np.abs(x) <= HITBOX_W) & (y * x != 0.0)

    return x[mask_hitbox], y[mask_hitbox]

@staticmethod
def convert_rad_to_xy(distance, angle_rad):
    y = distance * np.cos(angle_rad)
    x = distance * np.sin(angle_rad)
    return x, y


def calculate_hitbox_polar(w, h1, h2):
    rad_raw_angles = np.linspace(0, 2*np.pi, num=360, endpoint=False)
    
    polar_coords = []
    polar_angles = []
    
    for theta in rad_raw_angles:
        c = np.cos(theta)
        s = np.sin(theta)
        
        candidates = []
        
        if abs(c) > 1e-14:
            x_side = w if c > 0 else -w
            t_x = x_side / c
            if t_x >= 0:
                y_at_x = s * t_x
                if -h2 <= y_at_x <= h1:
                    candidates.append(t_x)
        
        if abs(s) > 1e-14:
            y_side = h1 if s > 0 else -h2
            t_y = y_side / s
            if t_y >= 0:
                x_at_y = c * t_y
                
                if -w <= x_at_y <= w:
                    candidates.append(t_y)
        
        if len(candidates) == 0:
            d = 0.0
        else:
            t = min(candidates)
            d = t
        
        polar_coords.append(d)
        polar_angles.append(theta - np.pi/2)
    
    angle_indices = np.round(
        np.array(polar_angles) / (2 * np.pi / 360)
    ).astype(int) % 360
    
    new_d_linha = np.zeros_like(polar_coords)
    new_d_linha[angle_indices] = polar_coords
    
    return new_d_linha

hitbox = calculate_hitbox_polar(HITBOX_W, HITBOX_H1, HITBOX_H2)

def shrink_space(raw_lidar):
    free_space_shrink_mask = raw_lidar > 0
    shrink_space_lidar = np.copy(raw_lidar)
    shrink_space_lidar[free_space_shrink_mask] -= hitbox[free_space_shrink_mask]
    
    return shrink_space_lidar

def compute_steer_from_lidar(raw_lidar):    
    filtreed_distances, filtreed_angles = convolution_filter(raw_lidar)
    target, _ = compute_angle(filtreed_distances, filtreed_angles, raw_lidar)
    steer = compute_steer(target)

    return steer, target

def compute_angle(filtred_distances, filtred_angles, raw_lidar):
    target_angle = filtred_angles[np.argmax(filtred_distances)]
    delta = 0

    l_angle = 0
    r_angle = 0
    
    for index in range(AVOID_CORNER_MAX_ANGLE, 0, -1):
        l_dist = raw_lidar[(target_angle + index) % 360]
        r_dist = raw_lidar[(target_angle - index) % 360]

        if l_angle == 0 and l_dist < AVOID_CORNER_MIN_DISTANCE:
            l_angle = index

        if r_angle == 0 and r_dist < AVOID_CORNER_MIN_DISTANCE:
            r_angle = index

    #print(f"l_dist: {l_dist} r_dist: {r_dist} {l_angle = } {r_angle = }")

    if l_angle == r_angle:
        delta = 0
    elif l_angle > r_angle:
        delta = -AVOID_CORNER_SCALE_FACTOR * (AVOID_CORNER_MAX_ANGLE - r_angle)
    elif l_angle < r_angle:
        delta = +AVOID_CORNER_SCALE_FACTOR * (AVOID_CORNER_MAX_ANGLE - l_angle)

    #print("delta = ", delta)
    
    target_angle += delta
    
    target_angle = (target_angle + 180) % 360 - 180
    
    return target_angle, delta

def compute_steer(alpha):
    return np.sign(alpha) * lerp(np.abs(alpha), STEER_FACTOR)

def convolution_filter(distances):
    shift = FIELD_OF_VIEW_DEG // 2

    # Create a Gaussian kernel that is heavier near the center
    # so that "front" (which is rolled to the center) gets higher weight.
    # kernel_size = CONVOLUTION_SIZE
    # center = 5
    
    # # x ranges from -center to +center
    # x = np.arange(kernel_size) - center
    
    # # Adjust sigma to control how peaked the kernel is; smaller sigma => sharper peak
    # sigma = kernel_size / 60.0  # Example: 6.0 is arbitrary; tune to taste
    # kernel = np.exp(-0.5 * (x / sigma) ** 2)
    
    # # Normalize the kernel so it sums to 1
    # kernel /= kernel.sum()


    ## Corsi teste
    # percentuais = np.array([ 0.1, 56, 56, 56, 0.1])
    # percentuais = np.array([ 36, 5, 36, 56, 36, 5, 36])
    percentuais = np.array([ 1, 5, 56, 5, 1])
    
    pesos = percentuais / np.sum(percentuais) 

    tamanho_regioes = [int(CONVOLUTION_SIZE * p) for p in pesos]

    tamanho_regioes[-1] += CONVOLUTION_SIZE - sum(tamanho_regioes)

    kernel = np.zeros(CONVOLUTION_SIZE)
    inicio = 0
    for i, tamanho in enumerate(tamanho_regioes):
        kernel[inicio:inicio + tamanho] = pesos[i]
        inicio += tamanho

    #kernel = np.ones(31)
    kernel /= np.sum(kernel)

    ## fim corsi teste

    # Roll angles so the "front" starts around the middle
    angles = np.arange(0, 360)
    angles = np.roll(angles, shift)

    # Roll distances likewise
    distances = np.roll(distances, shift)
    
    # Convolve using our custom kernel
    distances = convolve(distances, kernel, mode="same")

    # Return only the portion corresponding to FIELD_OF_VIEW_DEG
    return distances[:FIELD_OF_VIEW_DEG], angles[:FIELD_OF_VIEW_DEG]

def lerp(value: float, factor: np.ndarray) -> np.ndarray:
    indices = np.nonzero(value < factor[:, 0])[0]

    if len(indices) == 0:
        return factor[-1, 1]

    index = indices[0]

    delta = factor[index] - factor[index - 1]
    scale = (value - factor[index - 1, 0]) / delta[0]

    return factor[index - 1, 1] + scale * delta[1]

