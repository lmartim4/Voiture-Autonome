import numpy as np
import matplotlib.pyplot as plt
from control import compute_steer, compute_pwm
from constants import DC_STEER_MIN, DC_STEER_MAX

def main():
    target_angles = np.linspace(-90, 90, 181)
    
    steer_values = []
    pwm_values = []
    
    for angle in target_angles:
        steer = compute_steer(-angle)
        pwm = compute_pwm(steer)
        steer_values.append(steer)
        pwm_values.append(pwm)
    
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    ax1.plot(target_angles, steer_values, 'b-', label='Steer Value')
    ax1.set_xlabel('Target Angle (degrees)')
    ax1.set_ylabel('Steer Value', color='b')
    ax1.tick_params(axis='y', labelcolor='b')
    ax1.grid(True)
    
    ax2 = ax1.twinx()
    ax2.plot(target_angles, pwm_values, 'r-', label='PWM')
    ax2.set_ylabel('PWM', color='r')
    ax2.tick_params(axis='y', labelcolor='r')
    
    ax2.axhline(DC_STEER_MIN, color='green', linestyle='--', label='DC_STEER_MIN')
    ax2.axhline(DC_STEER_MAX, color='purple', linestyle='--', label='DC_STEER_MAX')
    
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper center')
    
    plt.title('Steer Value and PWM vs. Target Angle')
    plt.show()

if __name__ == "__main__":
    main()
