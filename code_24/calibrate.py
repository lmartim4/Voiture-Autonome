import re
import time

from typing import Any, Union

from customtkinter import *

set_appearance_mode("Dark")

from core import *


lines = []

parameters = {
    "steer": {"min": None, "max": None},
    "speed": {"min": None, "max": None}
}

with open("constants.py", "r") as file:
    lines = file.readlines()

    for index, line in enumerate(lines):
        search = re.search(r"^DC_[A-Z_]+ *= *", line)

        if search is None:
            continue

        slicer = search.span()[1]

        search = re.search(r"\d+\.\d+", line[slicer:])
        value = float(search.group())

        search = re.search(f"_[A-Z]+_[A-Z]+", line[:slicer])

        if search is None:
            continue

        substring = search.group().lower()

        parameters[substring[1:6]][substring[7:]] = [index, value]


steer_pwm = PWM(channel=1, frequency=50.0)
speed_pwm = PWM(channel=0, frequency=50.0)

steer_pwm.start(7.5)
speed_pwm.start(7.5)

time.sleep(0.5)


def set_entry(entry: CTkEntry, value: float) -> None:
    """
    Sets the value of a custom tkinter Entry widget.

    Args:
        entry (CTkEntry): custom tkinter Entry widget.
        value (float): value to set in the Entry widget.
    """

    entry.delete(0, END)
    entry.insert(0, f"{value:.2f}")


def get_entry(entry: CTkEntry) -> Union[None, float]:
    """
    Gets the value from a custom tkinter Entry widget.

    Args:
        entry (CTkEntry): custom tkinter Entry widget.

    Returns:
        Union[None, float]: value from the Entry widget if
        it can be converted to a float, otherwise None.
    """

    try:
        return float(entry.get())

    except ValueError:
        return None


def select(steer: Any, speed: Any, selector: str) -> Any:
    """
    Selects between two values based on a selector.

    Args:
        steer (Any): value for the "steer" selector.
        speed (Any): value for the "speed" selector.
        selector (str): selector string.

    Returns:
        Any: value corresponding to the selector.
    """

    return steer if selector == "steer" else speed


def changed_controllers(selector: str) -> None:
    """
    Updates controller parameters and widgets based on user input.

    Args:
        selector (str): selector string indicating which widgets to update.
    """

    global steer_pwm, speed_pwm

    min_value = get_entry(select(min_steer, min_speed, selector))
    max_value = get_entry(select(max_steer, max_speed, selector))

    if min_value is None or max_value is None:
        return

    parameters[selector]["min"][1] = min_value
    parameters[selector]["max"][1] = max_value

    slider = select(slider_steer, slider_speed, selector)
    value = min_value + slider.get() * (max_value - min_value)

    set_entry(select(cur_steer, cur_speed, selector),value)

    pwm = select(steer_pwm, speed_pwm, selector)
    pwm.set_duty_cycle(value)


def changed_current(selector: str) -> None:
    """
    Updates current value and related widgets based on user input.

    Args:
        selector (str): selector string indicating which widgets to update.
    """

    min_value = get_entry(select(min_steer, min_speed, selector))
    max_value = get_entry(select(max_steer, max_speed, selector))
    cur_value = get_entry(select(cur_steer, cur_speed, selector))

    if min_value is None or max_value is None or cur_value is None:
        return

    slider = select(slider_steer, slider_speed, selector)
    slider.set((cur_value - min_value) / (max_value - min_value))

    pwm = select(steer_pwm, speed_pwm, selector)
    pwm.set_duty_cycle(min(max(cur_value, min_value), max_value))


def align_command() -> None:
    """
    Sets the slider for steering command to the center
    position and updates the controller accordingly.
    """

    slider_steer.set(0.5)
    changed_controllers("steer")


def stop_command() -> None:
    """
    Sets the slider for speed command to zero
    and updates the controller accordingly.
    """

    slider_speed.set(0.0)
    changed_controllers("speed")


app = CTk()
app.title("Calibrate")


#================================================#
#                                                #
#                  Header frame                  #
#                                                #
#================================================#

steer_header = CTkFrame(master=app)
steer_header.pack(expand=True, fill="x", padx=16, pady=(16, 8))

steer_title = CTkLabel(master=steer_header,
    text="Steer calibration and test", text_color="gray")
steer_title.pack(anchor="w", padx=16, pady=4)


#================================================#
#                                                #
#                Calibration frame               #
#                                                #
#================================================#

steer_frame = CTkFrame(master=app)
steer_frame.pack(expand=True, padx=16)

align_steer = CTkButton(master=steer_frame,
    text="align", width=72, height=24, command=align_command)
align_steer.grid(row=0, column=1, pady=(16, 0))

min_steer = CTkEntry(master=steer_frame,
    width=48, height=24, justify="center")
min_steer.grid(row=1, column=0, padx=(16, 0), pady=16)
set_entry(min_steer, parameters["steer"]["min"][1])
min_steer.bind(
    "<KeyRelease>", lambda event: changed_controllers("steer"))

max_steer = CTkEntry(master=steer_frame,
    width=48, height=24, justify="center")
max_steer.grid(row=1, column=2, padx=(0, 16), pady=16)
set_entry(max_steer, parameters["steer"]["max"][1])
max_steer.bind(
    "<KeyRelease>", lambda event: changed_controllers("steer"))

slider_steer = CTkSlider(master=steer_frame,
    command=lambda event: changed_controllers("steer"))
slider_steer.grid(row=1, column=1, padx=12, pady=16)

cur_steer = CTkEntry(master=steer_frame,
    width=48, height=24, justify="center")
cur_steer.grid(row=2, column=1, pady=(0, 16))
cur_steer.bind(
    "<KeyRelease>", lambda event: changed_current("steer"))


#================================================#
#                                                #
#                  Header frame                  #
#                                                #
#================================================#

speed_header = CTkFrame(master=app)
speed_header.pack(expand=True, fill="x", padx=16, pady=(24, 8))

speed_title = CTkLabel(master=speed_header,
    text="Speed calibration and test", text_color="gray")
speed_title.pack(anchor="w", padx=16, pady=4)


#================================================#
#                                                #
#                Calibration frame               #
#                                                #
#================================================#

speed_frame = CTkFrame(master=app)
speed_frame.pack(expand=True, padx=16, pady=(0, 16))

align_speed = CTkButton(master=speed_frame,
    text="stop", width=72, height=24, command=stop_command)
align_speed.grid(row=0, column=1, pady=(16, 0))

min_speed = CTkEntry(master=speed_frame,
    width=48, height=24, justify="center")
min_speed.grid(row=1, column=0, padx=(16, 0), pady=16)
set_entry(min_speed, parameters["speed"]["min"][1])
min_speed.bind(
    "<KeyRelease>", lambda event: changed_controllers("speed"))

max_speed = CTkEntry(master=speed_frame,
    width=48, height=24, justify="center")
max_speed.grid(row=1, column=2, padx=(0, 16), pady=16)
set_entry(max_speed, parameters["speed"]["max"][1])
max_speed.bind(
    "<KeyRelease>", lambda event: changed_controllers("speed"))

slider_speed = CTkSlider(master=speed_frame,
    command=lambda event: changed_controllers("speed"))
slider_speed.grid(row=1, column=1, padx=12, pady=16)
slider_speed.set(0.0)

cur_speed = CTkEntry(master=speed_frame,
    width=48, height=24, justify="center")
cur_speed.grid(row=2, column=1, pady=(0, 16))
cur_speed.bind(
    "<KeyRelease>", lambda event: changed_current("speed"))

changed_controllers("steer")
changed_controllers("speed")

app.mainloop()

with open("constants.py", "w") as file:
    for key in ["steer", "speed"]:
        index, value = parameters[key]["min"]
        lines[index] = re.sub(r"\d+\.\d+", str(value), lines[index])

        index, value = parameters[key]["max"]
        lines[index] = re.sub(r"\d+\.\d+", str(value), lines[index])

    for line in lines:
        file.write(line)

steer_pwm.stop()
speed_pwm.stop()
