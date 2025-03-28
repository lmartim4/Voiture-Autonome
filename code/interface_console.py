import re
from algorithm.interfaces import ConsoleInterface

class ColorConsoleInterface(ConsoleInterface):
    """
    Console implementation that supports Minecraft-style color codes.
    Color codes start with '&' followed by a character:
    &0: Black           &8: Dark Gray
    &1: Dark Blue       &9: Blue
    &2: Dark Green      &a: Green
    &3: Dark Aqua       &b: Aqua
    &4: Dark Red        &c: Red
    &5: Dark Purple     &d: Light Purple
    &6: Gold            &e: Yellow
    &7: Gray            &f: White
    
    Format codes:
    &l: Bold            &o: Italic
    &n: Underline       &m: Strikethrough
    &r: Reset
    """
    
    # ANSI color codes
    COLORS = {
        '&0': '\033[30m',    # Black
        '&1': '\033[34m',    # Dark Blue
        '&2': '\033[32m',    # Dark Green
        '&3': '\033[36m',    # Dark Aqua
        '&4': '\033[31m',    # Dark Red
        '&5': '\033[35m',    # Dark Purple
        '&6': '\033[33m',    # Gold
        '&7': '\033[37m',    # Gray
        '&8': '\033[90m',    # Dark Gray
        '&9': '\033[94m',    # Blue
        '&a': '\033[92m',    # Green
        '&b': '\033[96m',    # Aqua
        '&c': '\033[91m',    # Red
        '&d': '\033[95m',    # Light Purple
        '&e': '\033[93m',    # Yellow
        '&f': '\033[97m',    # White
        # Format codes
        '&l': '\033[1m',     # Bold
        '&o': '\033[3m',     # Italic
        '&n': '\033[4m',     # Underline
        '&m': '\033[9m',     # Strikethrough
        '&r': '\033[0m',     # Reset
    }
    
    RESET = '\033[0m'
    
    def __init__(self, enable_colors=True):
        """
        Initialize the ColorConsole.
        
        Args:
            enable_colors (bool): Whether to enable color output. Useful for environments
                                that don't support ANSI color codes.
        """
        self.enable_colors = enable_colors
    
    def print_to_console(self, message: str):
        """
        Prints a message to console with Minecraft-style color codes.
        
        Args:
            message (str): The message to print, may contain color codes starting with '&'
        """
        if not self.enable_colors:
            # Strip all color codes if colors are disabled
            clean_message = re.sub(r'&[0-9a-fA-Flnomr]', '', message)
            print(clean_message)
            return
        
        # Process the message and replace color codes
        formatted_message = message
        for code, ansi in self.COLORS.items():
            formatted_message = formatted_message.replace(code, ansi)
        
        # Print with reset at the end to avoid color bleeding
        print(formatted_message + self.RESET)
    
    def log_info(self, message: str):
        """Log an info message (green)"""
        self.print_to_console(f"&a[INFO] {message}")
    
    def log_warning(self, message: str):
        """Log a warning message (yellow)"""
        self.print_to_console(f"&e[WARNING] {message}")
    
    def log_error(self, message: str):
        """Log an error message (red)"""
        self.print_to_console(f"&c[ERROR] {message}")
    
    def log_debug(self, message: str):
        """Log a debug message (gray)"""
        self.print_to_console(f"&7[DEBUG] {message}")


# Example usage
if __name__ == "__main__":
    console = ColorConsoleInterface()
    
    # Basic colors
    console.print_to_console("&aThis text is green")
    console.print_to_console("&cThis text is red")
    
    # Formatted text
    console.print_to_console("&eYellow &lbold &rtext")
    console.print_to_console("&bAqua and &nunderlined")
    
    # Mixed formatting
    console.print_to_console("&9Blue &lBold Blue &cRed &lBold Red &rNormal")
    
    # Predefined log levels
    console.log_info("System started successfully")
    console.log_warning("Low memory detected")
    console.log_error("Connection failed")
    console.log_debug("Processing item #1042")