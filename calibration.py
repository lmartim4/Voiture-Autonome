import tkinter as tk
from tkinter import ttk
from rpi_hardware_pwm import HardwarePWM

pwm_dir = HardwarePWM(pwm_channel=1, hz=50)

def main() -> None:
    root = tk.Tk()
    root.geometry("700x70")
    root.resizable(False, False)
    root.title("Steer calibration")
    
    root.columnconfigure(0, weight=1)
    root.columnconfigure(1, weight=3)
    root.columnconfigure(2, weight=1)

    # slider current value
    current_value = tk.DoubleVar()


    def get_current_value():
        return '{: .2f}'.format(current_value.get())


    def slider_changed(event):
        min_value = float(min_entry.get())
        max_value = float(max_entry.get())

        slider_value = current_value.get()
        value = min_value + slider_value * (max_value - min_value)
        text = f"{value:.2f}"
        pwm_dir.change_duty_cycle(value)

        value_label.configure(text=text)


    min_entry = ttk.Entry(root, width=5)
    min_entry.grid(column=0, row=0, sticky=tk.E, padx=5, pady=5)
    min_entry.insert(0, "6.0")
    
    max_entry = ttk.Entry(root, width=5)
    max_entry.grid(column=2, row=0, sticky=tk.E, padx=5, pady=5)
    max_entry.insert(0, "10.0")

    pwm_dir.start(8)
    
    #  slider
    slider = ttk.Scale(root, orient="horizontal", command=slider_changed, variable=current_value)
    slider.grid(column=1, row=0, sticky='we')

    # value label
    value_label = ttk.Label(root, text=get_current_value())
    value_label.grid(row=1, column=1, sticky='n')

    root.mainloop()


if __name__ == "__main__":
    main()
