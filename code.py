import time
import board
import busio
import digitalio
import microcontroller
import displayio
import terminalio
import sys
from adafruit_display_text import label
from adafruit_st7789 import ST7789

# IMPORT YOUR NEW LIBRARY
from cardputeradvkey import Keyboard

# =========================================
# 1. DISPLAY CONFIGURATION
# =========================================
COLOR_BG     = 0x000000  # Black
COLOR_TEXT   = 0x00FF00  # Phosphor Green
COLOR_DIM    = 0x005500  # Dim Green
COLOR_ERROR  = 0xFF0000  # Red

displayio.release_displays()

# Force Backlight
try:
    bl = digitalio.DigitalInOut(microcontroller.pin.GPIO38)
    bl.direction = digitalio.Direction.OUTPUT
    bl.value = True
except: pass

# Init SPI Display
spi = busio.SPI(clock=microcontroller.pin.GPIO36, MOSI=microcontroller.pin.GPIO35)
try:
    from fourwire import FourWire
    display_bus = FourWire(spi, command=microcontroller.pin.GPIO34, chip_select=microcontroller.pin.GPIO37, reset=microcontroller.pin.GPIO33)
except ImportError:
    display_bus = displayio.FourWire(spi, command=microcontroller.pin.GPIO34, chip_select=microcontroller.pin.GPIO37, reset=microcontroller.pin.GPIO33)

display = ST7789(display_bus, rotation=270, width=240, height=135, rowstart=40, colstart=53)
splash = displayio.Group()
display.root_group = splash

# UI Setup
bg_bitmap = displayio.Bitmap(240, 135, 1)
bg_palette = displayio.Palette(1)
bg_palette[0] = COLOR_BG
splash.append(displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette, x=0, y=0))

console_label = label.Label(terminalio.FONT, text="PYTHON REPL\nREADY...", color=COLOR_DIM, x=2, y=5, scale=1, line_spacing=1.0)
splash.append(console_label)

# Divider
line = displayio.Bitmap(240, 1, 1)
line_pal = displayio.Palette(1)
line_pal[0] = COLOR_DIM
splash.append(displayio.TileGrid(line, pixel_shader=line_pal, x=0, y=110))

# Input Prompt
prompt_label = label.Label(terminalio.FONT, text=">>> ", color=COLOR_TEXT, x=2, y=122, scale=1)
input_label = label.Label(terminalio.FONT, text="_", color=COLOR_TEXT, x=28, y=122, scale=1)
splash.append(prompt_label)
splash.append(input_label)

# =========================================
# 2. REPL LOGIC
# =========================================
history_lines = ["", ""]
MAX_LINES = 9

def print_to_console(text, color=COLOR_TEXT):
    global history_lines
    raw_lines = str(text).split('\n')
    for line in raw_lines:
        if len(line) > 40:
            history_lines.append(line[:40])
            history_lines.append(line[40:])
        else:
            history_lines.append(line)
    history_lines = history_lines[-MAX_LINES:]
    console_label.text = "\n".join(history_lines)
    console_label.color = color

def virtual_print(*args, sep=" ", end="\n"):
    out_str = sep.join(str(a) for a in args)
    print_to_console(out_str, COLOR_TEXT)

# Custom Environment
REPL_ENV = {
    "print": virtual_print,
    "board": board,
    "time": time,
    "digitalio": digitalio,
    "sys": sys,
    "microcontroller": microcontroller
}

def execute_code(code_str):
    print_to_console(f"> {code_str}", COLOR_DIM)
    try:
        try:
            result = eval(code_str, REPL_ENV, REPL_ENV)
            if result is not None:
                print_to_console(str(result), COLOR_TEXT)
        except SyntaxError:
            exec(code_str, REPL_ENV, REPL_ENV)
        except Exception as e:
            print_to_console(f"Err: {e}", COLOR_ERROR)
    except Exception as e:
        print_to_console(f"Err: {e}", COLOR_ERROR)

# =========================================
# 3. INITIALIZATION & MAIN LOOP
# =========================================

# Initialize the Keyboard using your new library
kb = Keyboard()
current_input = ""

print("System Active.")

while True:
    # Check for a keystroke using the library
    char = kb.check()
    
    if char:
        if char == "ENTER":
            execute_code(current_input)
            current_input = ""
        elif char == "DEL":
            current_input = current_input[:-1]
        elif char == "TAB":
            current_input += "  "
        elif char == "SPACE":
            current_input += " "
        elif len(char) == 1:
            current_input += char
            
        # Update Screen
        input_label.text = current_input + "_"
            
    # Small delay is handled efficiently inside the library via check(),
    # but we add a tiny sleep here to yield to the OS background tasks.
    time.sleep(0.005)