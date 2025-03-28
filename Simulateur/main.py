# To understand the implementation: https://www.youtube.com/watch?v=JbUNsYPJK1U
from environment import Environment 

# Create environment with local view
environment = Environment("track0.png", show_global_view=False)

# Run the simulation
environment.run()