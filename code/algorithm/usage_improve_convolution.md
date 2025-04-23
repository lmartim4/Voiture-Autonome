# Tuning Parameters for Improved Convolution Filter

## Core Parameters

1. **`convolution_size` (default=60)**
   - This controls the width of your convolution kernel
   - Larger values create smoother filtering but may miss small obstacles
   - Smaller values preserve more detail but may be more sensitive to noise
   - Try values between 30-120 depending on your sensor resolution and vehicle speed

2. **`sigma_base` (kernel_size / 8.0)**
   - Controls the sharpness of the base Gaussian response
   - Smaller values (e.g., kernel_size / 12.0) create a sharper focus on immediate obstacles
   - Larger values (e.g., kernel_size / 4.0) provide smoother transitions but may blur obstacle boundaries

3. **`sigma_safety` (kernel_size / 4.0)**
   - Controls the width of the safety margin component
   - Larger values create a wider safety buffer around detected objects
   - Try adjusting between kernel_size / 6.0 and kernel_size / 3.0

## Safety Components

4. **`kernel_safety * 2.0` weight**
   - Increases this multiplier (e.g., to 3.0 or 4.0) to be more conservative around edges
   - Decrease it (e.g., to 1.0) if the vehicle is avoiding obstacles too early or aggressively

5. **`peak_width` (10)**
   - Controls how focused the central detection is
   - Smaller values (5-8) create very precise central detection
   - Larger values (12-20) provide more robustness but less precision

6. **`kernel[peak_start:peak_end] = 15.0`**
   - This value controls the intensity of immediate obstacle detection
   - Higher values (20-30) make the system extremely responsive to obstacles directly ahead
   - Lower values (8-12) create a more balanced response between immediate and peripheral obstacles

7. **`safety_factor` (0.9)**
   - This is a global scaling factor that creates a 10% safety margin
   - More conservative: 0.8 (20% margin)
   - Less conservative: 0.95 (5% margin)
   - Test this in various environments to find the right balance

8. **`turn_safety_factor` (0.85)**
   - Additional safety during turns (15% margin)
   - More conservative in tight spaces: 0.75-0.8
   - Less conservative in open areas: 0.9

## Detection Thresholds

9. **`turning_threshold` (np.std(gradient) * 2)**
   - Controls when the system identifies a turning scenario
   - Increase the multiplier (e.g., to 3 or 4) if the system applies turn safety unnecessarily
   - Decrease it (e.g., to 1.5) if the system fails to detect turns properly

## Tuning Process

1. **Start with baseline parameters** and test in a simple environment
2. **Adjust one parameter at a time** and observe the effects
3. **Test in progressively more complex environments** to ensure robustness
4. **Consider creating environment-specific parameter sets** (e.g., indoor vs. outdoor, narrow vs. wide spaces)
5. **Log and visualize the filter output** to understand how each change affects performance