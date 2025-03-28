# To understand the implementation: https://www.youtube.com/watch?v=JbUNsYPJK1U
from environment import Environment 
from display import Display

environment = Environment("track1.png")
    
# Create display with environment
display = Display(environment, show_global_view=False, show_point_car=False)
    
# Run the simulation
display.run_simulation()