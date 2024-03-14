import json

from typing import Union

from customtkinter import *

set_appearance_mode("Dark")

from rpi_hardware_pwm import HardwarePWM


steer_pwm = HardwarePWM(pwm_channel=1, hz=50)
speed_pwm = HardwarePWM(pwm_channel=0, hz=50)

steer_pwm.start(0)
speed_pwm.start(0)


with open("parameters.json", "r") as file:
    parameters = json.load(file)


def set_entry(entry: CTkEntry, value: float) -> None:
    entry.delete(0, END)
    entry.insert(0, f"{value:.2f}")


def get_entry(entry: CTkEntry) -> Union[float, None]:
    try:
        return float(entry.get())
    except ValueError:
        return None


def changed_controllers(motor: str) -> None:
    global steer_pwm, speed_pwm

    min_value = get_entry(min_steer if motor == "steer" else min_speed)
    max_value = get_entry(max_steer if motor == "steer" else max_speed)

    if min_value is None or max_value is None:
        return

    parameters[motor] = [min_value, max_value]

    slider = slider_steer if motor == "steer" else slider_speed
    value = min_value + slider.get() * (max_value - min_value)

    set_entry(cur_steer if motor == "steer" else cur_speed, value)

    pwm = steer_pwm if motor == "steer" else speed_pwm
    pwm.change_duty_cycle(value)


def changed_current(motor: str) -> None:
    min_value = get_entry(min_steer if motor == "steer" else min_speed)
    max_value = get_entry(max_steer if motor == "steer" else max_speed)
    cur_value = get_entry(cur_steer if motor == "steer" else cur_speed)

    if min_value is None or max_value is None or cur_value is None:
        return

    slider = slider_steer if motor == "steer" else slider_speed
    slider.set((cur_value - min_value) / (max_value - min_value))

    pwm = steer_pwm if motor == "steer" else speed_pwm
    pwm.change_duty_cycle(min(max(cur_value, min_value), max_value))


def align_command() -> None:
    slider_steer.set(0.5)
    changed_controllers("steer")


def stop_command() -> None:
    slider_speed.set(0.0)
    changed_controllers("speed")


app = CTk()
app.title("Calibration and test")


#================================================#
#                                                #
#                  Header frame                  #
#                                                #
#================================================#

steer_header = CTkFrame(master=app)
steer_header.pack(expand=True, fill="x", padx=16, pady=(16, 8))

steer_title = CTkLabel(
    master=steer_header, text="Steer calibration and test", text_color="gray")
steer_title.pack(anchor="w", padx=16, pady=4)


#================================================#
#                                                #
#                Calibration frame               #
#                                                #
#================================================#

steer_frame = CTkFrame(master=app)
steer_frame.pack(expand=True, padx=16)

align_steer = CTkButton(
    master=steer_frame, text="align", width=72, height=24, command=align_command)
align_steer.grid(row=0, column=1, pady=(16, 0))

min_steer = CTkEntry(master=steer_frame, width=48, height=24, justify="center")
min_steer.grid(row=1, column=0, padx=(16, 0), pady=16)
set_entry(min_steer, parameters["steer"][0])
min_steer.bind("<KeyRelease>", lambda event: changed_controllers("steer"))

max_steer = CTkEntry(master=steer_frame, width=48, height=24, justify="center")
max_steer.grid(row=1, column=2, padx=(0, 16), pady=16)
set_entry(max_steer, parameters["steer"][1])
max_steer.bind("<KeyRelease>", lambda event: changed_controllers("steer"))

slider_steer = CTkSlider(
    master=steer_frame, command=lambda event: changed_controllers("steer"))
slider_steer.grid(row=1, column=1, padx=12, pady=16)

cur_steer = CTkEntry(master=steer_frame, width=48, height=24, justify="center")
cur_steer.grid(row=2, column=1, pady=(0, 16))
cur_steer.bind("<KeyRelease>", lambda event: changed_current("steer"))

changed_controllers("steer")


#================================================#
#                                                #
#                  Header frame                  #
#                                                #
#================================================#

speed_header = CTkFrame(master=app)
speed_header.pack(expand=True, fill="x", padx=16, pady=(24, 8))

speed_title = CTkLabel(
    master=speed_header, text="Speed calibration and test", text_color="gray")
speed_title.pack(anchor="w", padx=16, pady=4)


#================================================#
#                                                #
#                Calibration frame               #
#                                                #
#================================================#

speed_frame = CTkFrame(master=app)
speed_frame.pack(expand=True, padx=16, pady=(0, 16))

align_speed = CTkButton(
    master=speed_frame, text="stop", width=72, height=24, command=stop_command)
align_speed.grid(row=0, column=1, pady=(16, 0))

min_speed = CTkEntry(master=speed_frame, width=48, height=24, justify="center")
min_speed.grid(row=1, column=0, padx=(16, 0), pady=16)
set_entry(min_speed, parameters["speed"][0])
min_speed.bind("<KeyRelease>", lambda event: changed_controllers("speed"))

max_speed = CTkEntry(master=speed_frame, width=48, height=24, justify="center")
max_speed.grid(row=1, column=2, padx=(0, 16), pady=16)
set_entry(max_speed, parameters["speed"][1])
max_speed.bind("<KeyRelease>", lambda event: changed_controllers("speed"))

slider_speed = CTkSlider(
    master=speed_frame, command=lambda event: changed_controllers("speed"))
slider_speed.grid(row=1, column=1, padx=12, pady=16)
slider_speed.set(0.0)

cur_speed = CTkEntry(master=speed_frame, width=48, height=24, justify="center")
cur_speed.grid(row=2, column=1, pady=(0, 16))
cur_speed.bind("<KeyRelease>", lambda event: changed_current("speed"))

changed_controllers("speed")

app.mainloop()

with open("parameters.json", "w") as file:
    file.write(json.dumps(parameters, indent=4))
