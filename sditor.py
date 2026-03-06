import os
import sys
import platform
import colorama
from termcolor import colored

colorama.init()

usersys = platform.system()

if usersys == "Windows":
    import msvcrt
else:
    import tty
    import termios

if len(sys.argv) > 1:
    filei = sys.argv[1]
else:
    print(colored("No file given", 'red'))
    print("\nUsage: sditor", colored("<file>", 'blue'), colored(".<extension>", 'red'))
    print("Example: ", colored("sditor file.py", 'red'))
    exit()

def clearscreen():
    if usersys == "Windows":
        os.system("cls")
    else:
        os.system("clear")

def getch():
    if usersys == "Windows":
        return msvcrt.getwch()
    else:
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        return ch

def getarrow():
    if usersys == "Windows":
        return msvcrt.getwch()
    else:
        ch2 = getch()
        if ch2 == '[':
            ch3 = getch()
            return ch3
        return None

# MODE: 'normal' or 'insert'
mode = 'normal'

def render(lines, crow, ccol, mode, status=""):
    clearscreen()
    # Header
    print(colored(f"sditor - {filei}", 'yellow') + "  " +
          colored(f"[{'INSERT' if mode == 'insert' else 'NORMAL'}]",
                  'cyan' if mode == 'insert' else 'magenta'))
    if mode == 'normal':
        print(colored("i = insert  o = new line below  O = new line above  Ctrl+S = save  Ctrl+Q = save & exit", 'yellow'))
    else:
        print(colored("ESC = normal mode  Ctrl+S = save  Ctrl+Q = save & exit", 'yellow'))
    print("-" * 40)
    for i, line in enumerate(lines):
        if i == crow:
            print(colored("* ", 'green') + line)
        else:
            print("  " + line)
    # Status message if any
    if status:
        print(colored(f"\n{status}", 'green'))
    print(f"\033[{crow + 3};{ccol + 3}H", end='', flush=True)

# Load existing file if it exists
if os.path.exists(filei):
    with open(filei, 'r') as f:
        lines = f.read().splitlines()
    if not lines:
        lines = ['']
else:
    lines = ['']

crow = 0
ccol = 0
status = ""

render(lines, crow, ccol, mode)

while True:
    ch = getch()
    status = ""  # clear status each keypress

    #Ctrl+S (both modes)
    if ch == '\x13':
        with open(filei, 'w') as f:
            f.write('\n'.join(lines))
        status = "Saved"

    # --- Ctrl+Q (both modes) ---
    elif ch == '\x11':
        with open(filei, 'w') as f:
            f.write('\n'.join(lines))
        print(colored("\nSaved and Exited", 'red'))
        os._exit(0)

    # --- Arrow keys (both modes) ---
    elif ch in ('\xe0', '\x00', '\x1b'):
        arr = getarrow()
        if arr in ('H', 'A'):    # Up
            if crow > 0:
                crow -= 1
                ccol = min(ccol, len(lines[crow]))
        elif arr in ('P', 'B'):  # Down
            if crow < len(lines) - 1:
                crow += 1
                ccol = min(ccol, len(lines[crow]))
        elif arr in ('K', 'D'):  # Left
            if ccol > 0:
                ccol -= 1
            elif crow > 0:
                crow -= 1
                ccol = len(lines[crow])
        elif arr in ('M', 'C'):  # Right
            if ccol < len(lines[crow]):
                ccol += 1
            elif crow < len(lines) - 1:
                crow += 1
                ccol = 0

    #normal mode
    elif mode == 'normal':

        if ch == 'i':
            # Insert at current position
            mode = 'insert'

        elif ch == 'a':
            # Insert after current character
            ccol = min(ccol + 1, len(lines[crow]))
            mode = 'insert'

        elif ch == 'o':
            # New line below
            lines.insert(crow + 1, '')
            crow += 1
            ccol = 0
            mode = 'insert'

        elif ch == 'O':
            # New line above
            lines.insert(crow, '')
            ccol = 0
            mode = 'insert'

        elif ch in ('h',):  # Left (vim style)
            if ccol > 0:
                ccol -= 1

        elif ch == 'l':  # Right (vim style)
            if ccol < len(lines[crow]):
                ccol += 1

        elif ch == 'k':  # Up (vim style)
            if crow > 0:
                crow -= 1
                ccol = min(ccol, len(lines[crow]))

        elif ch == 'j':  # Down (vim style)
            if crow < len(lines) - 1:
                crow += 1
                ccol = min(ccol, len(lines[crow]))

        elif ch == '0':  # Start of line
            ccol = 0

        elif ch == '$':  # End of line
            ccol = len(lines[crow])

        elif ch == 'G':  # Go to last line
            crow = len(lines) - 1
            ccol = min(ccol, len(lines[crow]))

        elif ch == 'g':  # Go to first line (gg)
            next_ch = getch()
            if next_ch == 'g':
                crow = 0
                ccol = min(ccol, len(lines[crow]))

        elif ch == 'd':  # dd = delete line
            next_ch = getch()
            if next_ch == 'd':
                if len(lines) > 1:
                    lines.pop(crow)
                    if crow >= len(lines):
                        crow = len(lines) - 1
                    ccol = min(ccol, len(lines[crow]))
                else:
                    lines[0] = ''
                    ccol = 0

        elif ch == 'x':  # Delete character under cursor
            if lines[crow] and ccol < len(lines[crow]):
                lines[crow] = lines[crow][:ccol] + lines[crow][ccol+1:]
                ccol = min(ccol, len(lines[crow]))

    #insert mode
    elif mode == 'insert':

        if ch == '\x1b':  # ESC - back to normal
            mode = 'normal'
            ccol = max(0, ccol - 1)

        elif ch in ('\r', '\n'):  # Enter
            rest = lines[crow][ccol:]
            lines[crow] = lines[crow][:ccol]
            crow += 1
            lines.insert(crow, rest)
            ccol = 0

        elif ch in ('\x08', '\x7f'):  # Backspace
            if ccol > 0:
                lines[crow] = lines[crow][:ccol-1] + lines[crow][ccol:]
                ccol -= 1
            elif crow > 0:
                prev_len = len(lines[crow - 1])
                lines[crow - 1] += lines[crow]
                lines.pop(crow)
                crow -= 1
                ccol = prev_len

        elif ch >= ' ':  # Printable character
            lines[crow] = lines[crow][:ccol] + ch + lines[crow][ccol:]
            ccol += 1

    render(lines, crow, ccol, mode, status)