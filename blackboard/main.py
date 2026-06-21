import sys
import os
import tty
import termios
import select
import time
import subprocess
import math

class variables():
 def __init__(self):
  self.run   = 0
  self.width = 0
  self.height   = 0
  self.prevBuf  = []
  self.buffer   = []
  self.tabs  = []
  self.current  = 0
  self.playerState = 0  # 0=normal 1=move 2=resize
  self.prevMouse = [0, 0]
  self.debug = 0
  self.tabOrder=[]
  self.hotkeys=['\x11', '\x0f', '\x02', '\x13', '\x16', '\x17', '\x0e', '\x04', '\x07', '\x06', '\x12']; self.hotkeyNames=["quit", "open", "help", "save", "paste", "closeTab", "newTab", "run", "goto", "find", "replace"]
  self.thisClick=-1.0
  self.secondTab= 1

v = variables()

class tab():
 def __init__(self, po=[0, 0], si=[40, 15], na= "(save)", co= [-1,-1,-1]):
  self.lines   = ['']
  self.cur  = [0, 0]   # [column, row]
  self.scroll  = [0, 0]
  self.pos  = list(po) # [x, y] absolute terminal cells
  self.size = list(si) # [width, height]
  self.console = False
  self.name = na
  self.color= co
  self.time= 0
  self.directory= ""

  v.tabOrder= [x+1 for x in v.tabOrder]
  v.tabOrder.append(0)

def get_terminal_size():
 try:
  size = os.get_terminal_size()
  return size.lines, size.columns
 except OSError:
  return 24, 80

def windowSize():
 scr_h, scr_w = get_terminal_size()
 if v.height != scr_h or v.width != scr_w:
  v.height = scr_h
  v.width = scr_w
  v.buffer = [""] * v.height
  v.prevBuf = [""] * v.height
  return True
 return False

def t(): return v.tabs[v.current]

def tpx(ta): return ta.pos[0]
def tpy(ta): return ta.pos[1]
reset = "\033[0m"
def bg(c): return f"\033[48;2;{c[0]};{c[1]};{c[2]}m"
def fg(c): return f"\033[38;2;{c[0]};{c[1]};{c[2]}m"
windowSize()
def hideCursor(): sys.stdout.write("\033[?25l")
def showCursor(): sys.stdout.write("\033[?25h")
def goto(r, c): sys.stdout.write(f"\033[{r};{c}H")
def setTitle(text): sys.stdout.write(f"\033]2;{text}\007")
def newOrder(order): v.tabOrder = [o + 1 if o < order else o for o in v.tabOrder]

def tabAt(mx, my):
 best = None
 best_order = float('inf') 
 
 for i, ta in enumerate(v.tabs):
  if (tpx(ta) <= mx < tpx(ta) + ta.size[0]) and (tpy(ta) <= my < tpy(ta) + ta.size[1]):
   if v.tabOrder[i] < best_order:
    best_order = v.tabOrder[i]
    best = i

 if best is None:
  return None

 if v.tabs[best].console:
  best_nc = None
  best_nc_order = float('inf')
  for i, ta in enumerate(v.tabs):
   if not ta.console and v.tabOrder[i] < best_nc_order:
    best_nc_order = v.tabOrder[i]
    best_nc = i
  if best_nc is not None:
   v.secondTab = best_nc
   v.tabs[v.secondTab].time = 5

 return best

def handle_mouse_click(mx, my):
    hit = tabAt(mx, my)
    if hit is not None:
        v.current = hit
        newOrder(v.tabOrder[hit])
        v.tabOrder[hit] = 0
        mouseFunc()
    
    start_x, start_y = tpx(t()), tpy(t())
    
    # Check if click is inside window content boundaries
    if (start_x + 1 <= mx < start_x + t().size[0] - 1) and \
       (start_y + 1 <= my < start_y + t().size[1] - 1):
        
        target_row = max(0, min(my - start_y - 1 + t().scroll[1], len(t().lines) - 1))
        target_col = max(0, min(mx - start_x - 1 + t().scroll[0], len(t().lines[target_row])))
        t().cur = [target_col, target_row]
    # Clicked the borders (Header/Footer handles dragging and resizing)
    else:
        if mx < start_x + t().size[0] // 2:
            v.playerState = 1  # Move state
        else:
            v.playerState = 2  # Resize state
         
        v.prevMouse = [mx, my]

def handle_mouse_motion(mx, my):
    """Handles window moving and resizing based on mouse dragging state."""
    if v.playerState not in [1, 2]:
        return
        
    delta_x = mx - v.prevMouse[0]
    delta_y = my - v.prevMouse[1]
    
    if v.playerState == 1:  # Move
        t().pos[0] = max(0, min(t().pos[0] + delta_x, v.width - t().size[0]))
        t().pos[1] = max(0, min(t().pos[1] + delta_y, v.height - t().size[1]))
    elif v.playerState == 2:  # Resize
        t().size[0] = max(4, min(t().size[0] + delta_x, v.width - t().pos[0]))
        t().size[1] = max(3, min(t().size[1] + delta_y, v.height - t().pos[1]))

def handle_escape_sequences(data, active_tab):
    if not (len(data) > 2 and data[1] == '['):
        return False

    nxt2 = data[2]
    last = data[-1]

    # Mouse Event SGR Format (\x1b[<...)
    if nxt2 == '<':
        seq = data[3:]
        end_M = seq.find('M')
        end_m = seq.find('m')
        
        if end_M == -1 and end_m == -1: return False
        end = min(x for x in (end_M, end_m) if x != -1)
        is_press = (seq[end] == 'M')
        
        btn, cx, cy = map(int, seq[:end].split(';'))
        mx, my = cx - 1, cy - 1

        start_x, start_y = tpx(active_tab), tpy(active_tab)
        is_inside = (start_x <= mx < start_x + active_tab.size[0]) and (start_y <= my < start_y + active_tab.size[1])

        if btn == 0:
            if is_press:
                handle_mouse_click(mx, my)
            else:
                v.playerState = 0  # Release drag/resize
        elif is_inside and btn == 64:    # Scroll Up
            if active_tab.scroll[1] > 0:
                active_tab.scroll[1] -= 1
                return True
        elif is_inside and btn == 65:  # Scroll Down
            if active_tab.scroll[1] < len(active_tab.lines) - 1:
                active_tab.scroll[1] += 1
                return True
        elif is_inside and btn == 68:  # Shift + Scroll Up (Scroll Left)
            if active_tab.scroll[0] > 0:
                active_tab.scroll[0] -= 1
                return True
        elif is_inside and btn == 69:  # Shift + Scroll Down (Scroll Right)
         if active_tab.scroll[0] < len(t().lines[t().cur[1]])-1:
            active_tab.scroll[0] += 1
            return True

        handle_mouse_motion(mx, my)
        v.prevMouse = [mx, my]

    # Arrow Keys & Page Jumping
    elif last in ('A', 'B', 'C', 'D'):
        step = 5 if ';5' in data else 1
        alt_mode = ';3' in data

        if last == 'A' and not t().console:    # Up
             if active_tab.cur[1] - step< 0:
              active_tab.cur[0]= 0
             active_tab.cur[1] = max(0, active_tab.cur[1] - step)
        elif last == 'B' and not t().console:  # Down
             if active_tab.cur[1] + step>= len(active_tab.lines):
              active_tab.cur[0]= len(active_tab.lines[len(active_tab.lines)- 1])
             active_tab.cur[1] = min(len(active_tab.lines) - 1, active_tab.cur[1] + step)
        elif last == 'C':  # Right
            if alt_mode:
                focusTab((v.current-1)%len(v.tabs))
            else:
                for _ in range(step):
                    if active_tab.cur[0] < len(active_tab.lines[active_tab.cur[1]]): active_tab.cur[0] += 1
                    elif active_tab.cur[1] < len(active_tab.lines) - 1:
                        active_tab.cur[1] += 1
                        active_tab.cur[0] = 0
        elif last == 'D':  # Left
            if alt_mode:
                focusTab((v.current+1)%len(v.tabs))
            else:
                for _ in range(step):
                    if active_tab.cur[0] > 0: active_tab.cur[0] -= 1
                    elif active_tab.cur[1] > 0:
                        active_tab.cur[1] -= 1
                        active_tab.cur[0] = len(active_tab.lines[active_tab.cur[1]])
        
        # Clamp columns after vertical adjustments
        active_tab.cur[0] = min(active_tab.cur[0], len(active_tab.lines[active_tab.cur[1]]))

    # Delete Key (\x1b[3~)
    elif last == '~' and data.startswith('\x1b[3'):
        step = 5 if ';5' in data else 1
        for _ in range(step):
            cur_col, cur_row = active_tab.cur[0], active_tab.cur[1]
            if cur_col < len(active_tab.lines[cur_row]):
                active_tab.lines[cur_row] = active_tab.lines[cur_row][:cur_col] + active_tab.lines[cur_row][cur_col + 1:]
            elif cur_row < len(active_tab.lines) - 1:
                active_tab.lines[cur_row] += active_tab.lines[cur_row + 1]
                active_tab.lines.pop(cur_row + 1)
                
    return False

def handler():
    try:
        data = os.read(sys.stdin.fileno(), 32).decode('utf-8', errors='replace')
    except OSError:
        return False

    if not data:
        return False

    if hotkeyFunc(data[0]) == 1:
        return True

    is_mouse_wheel = False

    if data[0] == '\x1b' and len(data) > 1:
        # Check if backspace variants slipped into escape data block
        if data[1] in ('\x7f', '\x08'):
            step = 5
            for _ in range(step):
                cur_col, cur_row = t().cur[0], t().cur[1]
                if cur_col > 0:
                    t().lines[cur_row] = t().lines[cur_row][:cur_col - 1] + t().lines[cur_row][cur_col:]
                    t().cur[0] -= 1
                elif cur_row > 0:
                    prev_len = len(t().lines[cur_row - 1])
                    t().lines[cur_row - 1] += t().lines[cur_row]
                    t().lines.pop(cur_row)
                    t().cur[1] -= 1
                    t().cur[0] = prev_len
        else:
            is_mouse_wheel = handle_escape_sequences(data, t())
    else:
        # Standard Key Input Loop
        for ch in data:
            cur_row = max(0, min(t().cur[1], len(t().lines) - 1))
            cur_col = max(0, min(t().cur[0], len(t().lines[cur_row])))

            # Backspace Handling
            if ch in ('\x7f', '\x08'):
                step = 5 if ch == '\x08' else 1
                for _ in range(step):
                    cur_row = max(0, min(t().cur[1], len(t().lines) - 1))
                    cur_col = max(0, min(t().cur[0], len(t().lines[cur_row])))
                    if cur_col > 0:
                        t().lines[cur_row] = t().lines[cur_row][:cur_col - 1] + t().lines[cur_row][cur_col:]
                        t().cur[0] -= 1
                    elif cur_row > 0:
                        prev_len = len(t().lines[cur_row - 1])
                        t().lines[cur_row - 1] += t().lines[cur_row]
                        t().lines.pop(cur_row)
                        t().cur[1] -= 1
                        t().cur[0] = prev_len

            # Return / Enter Execution
            elif ch in ('\n', '\r'):
             if t().console:
              commandFunc(t().lines[0])
             else:
                t().cur[1] = max(0, min(t().cur[1], len(t().lines) - 1))
                cur_row = t().cur[1]
                
                commandFunc(t().lines[cur_row], v.current)
                
                # Fetch fresh tab settings post command calculation in case context modified active windows
                cur_row = max(0, min(t().cur[1], len(t().lines) - 1))
                cur_col = max(0, min(t().cur[0], len(t().lines[cur_row])))
                
                current_str = t().lines[cur_row]
                t().lines.insert(cur_row + 1, current_str[cur_col:])
                t().lines[cur_row] = current_str[:cur_col]
                t().cur[1] += 1
                t().cur[0] = 0

            # Normal Characters
            elif 32 <= ord(ch) <= 126:
                if t().console: 
                 t().lines[0]= t().lines[0][:cur_col] + ch + t().lines[0][cur_col:]
                else:
                 t().lines[cur_row] = t().lines[cur_row][:cur_col] + ch + t().lines[cur_row][cur_col:]
                t().cur[0] += 1

    if not is_mouse_wheel:
        max_w = t().size[0] - 2
        max_h = t().size[1] - 2
        t().cur[1] = max(0, min(t().cur[1], len(t().lines) - 1))
        
        if t().cur[1] < t().scroll[1]:
            t().scroll[1] = t().cur[1]
        elif t().cur[1] - t().scroll[1] >= max_h:
            t().scroll[1] = t().cur[1] - max_h + 1
            
        if t().cur[0] < t().scroll[0]:
            t().scroll[0] = t().cur[0]
        elif t().cur[0] - t().scroll[0] >= max_w:
            t().scroll[0] = t().cur[0] - max_w + 1

    for i in range(v.height):
        graphics(i)

    return False

def graphics(line):
 v.buffer[line] = ""
 
 order = sorted(range(len(v.tabs)), key=lambda i: v.tabOrder[i], reverse=True)
 for i in order:
  ta= v.tabs[i]
  top_y = tpy(ta)
  bot_y = tpy(ta) + ta.size[1] - 1
  start_x = tpx(ta)
  width = ta.size[0]
  max_w = width - 2
  newCol= [99,99,99]
  newCol2= [155,155,155]
  if ta.color[0]!= -1:
   newCol= ta.color
   newCol2= ta.color
  if ta.time>0:
   newCol= [min(255,int(x*1.5)) for x in newCol]
   newCol2= [min(255,int(x*1.5)) for x in newCol2]

  if line == top_y:
   border = bg(newCol) + " " * (ta.size[0]//2) + bg(newCol2) + " " * math.ceil(ta.size[0]/2)
   newName= ta.name
   if ta.console:
    newName= ta.directory
   v.buffer[line] +=  f"\033[{line + 1};{start_x + 1}H{border}\033[{line + 1};{start_x + 3}H"+ bg(newCol) + f"{newName}"+ reset
   
  elif line == bot_y:
   border = bg(newCol) + " " * (ta.size[0]//2) + bg(newCol2) + " " * math.ceil(ta.size[0]/2)
   v.buffer[line] += f"\033[{line + 1};{start_x + 1}H{border}"+ reset
   
  elif top_y < line < bot_y:
   idx = line - top_y - 1 + ta.scroll[1]
   if idx < len(ta.lines):
    sx = ta.scroll[0]
    display_line = ta.lines[idx][sx : sx + max_w]
   else:
    display_line = ""
    
   padded_line = display_line.ljust(max_w)
   v.buffer[line] += f"\033[{line + 1};{start_x + 1}H" + bg(newCol) + " " + reset + f"{padded_line}" + bg(newCol2) + " " + reset
 v.buffer[line] = v.buffer[line]

def draw():
 hideCursor()
 
 for y in range(v.height):
  if v.buffer[y] == v.prevBuf[y]: 
   continue
  v.prevBuf[y] = v.buffer[y]
  sys.stdout.write(f"\033[{y+1};1H\033[2K{v.prevBuf[y]}")

 sc = tpx(t()) + t().cur[0] - t().scroll[0] + 2
 sr = tpy(t()) + t().cur[1] - t().scroll[1] + 2
 goto(sr, sc)
 
 debugText = ''
 if v.debug != 0:
  debugText = str(v.debug)
  
 setTitle(str(t().cur) + debugText + " - blackboard")
 showCursor()
 sys.stdout.flush()

#@others

def helpFunc():
 if not t().console: return
 allCommands= []
 for i in range(len(v.hotkeys)):
  allCommands.append(v.hotkeyNames[i] + f"= {chr(ord(v.hotkeys[i]) + 64)}")

 if v.tabs[0].size[1]<6:
  v.tabs[0].pos=[0,v.height//2]
  v.tabs[0].size= [v.width, v.height//2]
 v.tabs[0].lines= ["", "(function)= ([ctrl+]letter)"]+ allCommands
 focusTab(0) 

def hotkeyFunc(data):
 for i in range(len(v.hotkeys)):
  if v.hotkeys[i]=='':
   continue
  if data == v.hotkeys[i]:
   if i==0:
    return 1
   else:
    commandFunc(v.hotkeyNames[i], 0)

 return 0

def mouseFunc():
 currentClick= time.time()
 if currentClick- v.thisClick < 0.4:
  if t().console:
   commandFunc(t().lines[t().cur[1]], v.current)
 v.thisClick= time.time()

def commandFunc(command='', idx=0):
 words = command.split()
 if not words:
  return

 cmd = words[0]

 if cmd == "help":
   helpFunc()

 elif cmd== "quit":
  v.run= 2

 elif cmd[:4] == "save":
   if len(words) > 1:
    path = words[1]
    if not os.path.isabs(path):
     path = os.path.join(os.getcwd(), path)
    try:
     folder = os.path.dirname(path)
     if folder:
      os.makedirs(folder, exist_ok=True)
     with open(path, 'w') as f:
      f.write('\n'.join(v.tabs[v.secondTab].lines))
     v.tabs[v.secondTab].name = os.path.basename(path)
     v.tabs[v.secondTab].directory= path
    except Exception as e:
     v.tabs[0].lines.append(f" error: {e}")

   else:
    focusTab(0)
    v.tabs[0].lines= ["save " + v.tabs[0].directory + v.tabs[v.secondTab].name]
    v.tabs[0].cur= [len(v.tabs[0].lines[0]), 0]
   saveSettings()

 elif cmd[:4] == "open":
   if len(words) > 1:
    path = words[1]
    if not os.path.isabs(path):
     path = os.path.join(os.getcwd(), path)
    try:
     with open(path, 'r') as f:
      content = f.read()
     new_tab = tab([2, 2], [v.width//2, v.height//2], os.path.basename(path))
     new_tab.lines = content.split('\n')
     v.tabs.append(new_tab)
     v.current = len(v.tabs) - 1
    except Exception as e:
     v.tabs[0].lines.append(f" error: {e}")

   else:
    focusTab(0)
    v.tabs[0].lines= ["open " + v.tabs[0].directory + v.tabs[v.secondTab].name]
    v.tabs[0].cur= [len(v.tabs[0].lines[0]), 0]

 elif cmd == "paste":
   clip_text = getClipboard()
   if clip_text:
    active_tab = t()
    cur_col = active_tab.cur[0]
    cur_row = active_tab.cur[1]
    paste_lines = clip_text.replace('\r', '').split('\n')
    current_line = active_tab.lines[cur_row]
    left_side = current_line[:cur_col]
    right_side = current_line[cur_col:]
    active_tab.lines[cur_row] = left_side + paste_lines[0]
    for next_line in paste_lines[1:]:
     cur_row += 1
     active_tab.lines.insert(cur_row, next_line)
    active_tab.lines[cur_row] += right_side
    active_tab.cur[1] = cur_row
    active_tab.cur[0] = len(active_tab.lines[cur_row]) - len(right_side)

 elif cmd == "closeTab":
   if not t().console:
    if len(v.tabs) > 1:
     del v.tabs[v.current]
     del v.tabOrder[v.current]
     order = sorted(range(len(v.tabOrder)), key=lambda i: v.tabOrder[i])
     new_order = [0] * len(v.tabOrder)
     for rank, i in enumerate(order):
      new_order[i] = rank
     v.tabOrder = new_order
     v.current = min(v.current, len(v.tabs) - 1)

   else:
    v.tabs[0].lines = ['']
    v.tabs[0].cur = [0, 0]
    v.tabs[0].scroll = [0, 0]

 elif cmd == "newTab":
   v.tabs.append(tab([3, 3], [15, 7]))

 elif cmd[:3] == "run":
    if len(words) > 1:
        # Extract everything after the word "run"
        shell_cmd = ' '.join(words[1:]) 
        
        # Check if the intended terminal command is a directory change
        if words[1] == "cd":
            try:
                # If they just typed 'run cd', go home, otherwise extract the path target
                target = ' '.join(words[2:]) if len(words) > 2 else os.path.expanduser("~")
                
                # Resolve relative paths (like 'test') against Python's current pwd
                os.chdir(os.path.abspath(target))
                
                # Sync your custom tab visual variable
                v.tabs[0].directory = str(os.getcwd()) + "/"
            except Exception as e:
                v.tabs[0].lines.append(f" error: {e}")
        else:
            # Fallback for normal commands like ls, clear, python3 script.py
            runCommand(shell_cmd)
            
        v.tabs[0].directory = str(os.getcwd()) + "/"
    v.tabs[0].lines[0]= ""

 elif cmd[:4] == "goto":
   if len(words) > 1:
    try:
     line_num = int(words[1]) - 1  # 1-indexed input
     ta = v.tabs[v.secondTab]
     ta.cur = [0, max(0, min(line_num, len(ta.lines) - 1))]
     ta.scroll=[0, max(0, min(line_num, len(ta.lines) - 1))]
     focusTab(v.secondTab)
    except ValueError:
     v.tabs[0].lines.append(f"error: not a number")
   else:
    focusTab(0)
    v.tabs[0].lines= ["goto "]
    v.tabs[0].cur= [len(v.tabs[0].lines[0]), 0]

 elif cmd[:4]== "find":
   if len(words) > 1:
    allLines=[]
    for i in range(len(v.tabs[v.secondTab].lines)):
     if words[1] in v.tabs[v.secondTab].lines[i]:
      allLines.append(f"goto {i}")
    t().lines= allLines
   else:
    focusTab(0)
    v.tabs[0].lines= ["find "]
    v.tabs[0].cur= [len(v.tabs[0].lines[0]), 0]

 elif cmd[:7]== "replace":
   if len(words) > 2:
    for i in range(len(v.tabs[v.secondTab].lines)):
     v.tabs[v.secondTab].lines[i]= v.tabs[v.secondTab].lines[i].replace(words[1], words[2])
   else:
    focusTab(0)
    v.tabs[0].lines= ["replace "]
    v.tabs[0].cur= [len(v.tabs[0].lines[0]), 0]

 elif cmd[:5]!="noCom":
  v.tabs[0].lines[0]= f"noCommand: {cmd}"
 else:
  v.tabs[0].lines[0]= ""

 if cmd[:4]!= "open" and cmd[:4]!= "save":
  t().cur[0]= 0

 for i in range(v.height):
  graphics(i)

def getClipboard():
 for cmd in [
  ['xclip', '-selection', 'clipboard', '-o'],
  ['xsel', '--clipboard', '--output'],
  ['wl-paste', '--no-newline'],
 ]:
  try:
   result = subprocess.check_output(cmd, text=True, stderr=subprocess.PIPE)
   return result
  except FileNotFoundError:
   t().lines[0] = f"not found: {cmd[0]}"
  except subprocess.CalledProcessError as e:
   t().lines[0] = f"error {cmd[0]}: {e.stderr.strip()}"
 return None

def timersFunc():
 forTrue= False
 for tab in v.tabs:
  if tab.time>0:
   tab.time-=1
   forTrue= True
 if forTrue:
  for i in range(v.height): graphics(i)
  
def runCommand(cmd):
 try:
  result = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT)
  lines = result.split('\n')
  if lines and lines[-1] == '':
   lines.pop()
  v.tabs[0].lines += lines
 except subprocess.CalledProcessError as e:
  output = e.output.split('\n')
  if output and output[-1] == '':
   output.pop()
  v.tabs[0].lines += output

def focusTab(idx):
 v.current = idx
 newOrder(v.tabOrder[idx])
 v.tabOrder[idx] = 0

def saveSettings():
 settingsPath = os.path.join(os.getcwd(), 'settings.txt')
 def tabData(ta):
  return {
   'lines': ta.lines,
   'cur': ta.cur,
   'scroll': ta.scroll,
   'pos': ta.pos,
   'size': ta.size,
   'name': ta.name,
   'directory': ta.directory,
   'color': ta.color,
  }
 newSecond= None
 if len(v.tabs)>1:
  newSecond= tabData(v.tabs[v.secondTab])

 data = {
  'hotkeys': v.hotkeys,
  'hotkeyNames': v.hotkeyNames,
  'currentTab': tabData(v.tabs[v.current]),
  'secondTab': newSecond,
 }

 with open(settingsPath, 'w') as f:
  for key, val in data.items():
   f.write(f"{key}={repr(val)}\n")

def loadSettings():
 settingsPath = os.path.join(os.getcwd(), 'settings.txt')
 if not os.path.exists(settingsPath):
  return
 with open(settingsPath, 'r') as f:
  for line in f:
   if '=' not in line:
    continue
   key, val = line.split('=', 1)
   key = key.strip()
   try:
    parsed = eval(val.strip())
   except:
    continue

   if key == 'hotkeys':
    v.hotkeys = parsed
   elif key == 'hotkeyNames':
    v.hotkeyNames = parsed

   elif key in ('currentTab', 'secondTab'):
    if key == 'currentTab':
     ta = v.tabs[v.current]
    else:
     ta = v.tabs[v.secondTab]

    if parsed is None: continue
    ta.lines = parsed.get('lines', [''])
    ta.name = parsed.get('name', '(save)')
    ta.directory = parsed.get('directory', '')
    ta.color = parsed.get('color', [-1, -1, -1])

    size = parsed.get('size', [40, 15])
    size[0] = max(4, min(size[0], v.width))
    size[1] = max(3, min(size[1], v.height))
    ta.size = size

    pos = parsed.get('pos', [0, 0])
    pos[0] = max(0, min(pos[0], v.width - size[0]))
    pos[1] = max(0, min(pos[1], v.height - size[1]))
    ta.pos = pos

    cur = parsed.get('cur', [0, 0])
    cur[1] = max(0, min(cur[1], len(ta.lines) - 1))
    cur[0] = max(0, min(cur[0], len(ta.lines[cur[1]])))
    ta.cur = cur

    scroll = parsed.get('scroll', [0, 0])
    scroll[1] = max(0, min(scroll[1], len(ta.lines) - 1))
    scroll[0] = max(0, scroll[0])
    ta.scroll = scroll
  focusTab(v.current)

#@othersEnd

if __name__ == "__main__":
 v.tabs.append(tab([0, v.height-3], [v.width, 3], "console", [14, 107, 55]))
 v.tabs[-1].directory= str(os.getcwd())+ "/"
 v.tabs[-1].lines[0]= "help #doubleClick or enter"
 v.tabs[-1].console= True
 v.tabs.append(tab([0, 0], [v.width, v.height-3]))
 loadSettings()
 for i in range(v.height): graphics(i)

 fd = sys.stdin.fileno()
 old_settings = termios.tcgetattr(fd)
 try:
  tty.setraw(fd)
  sys.stdout.write("\033[?25l\033[?1002h\033[?1006h")
  sys.stdout.flush()
  while v.run == 0:
   if windowSize():
    for i in range(v.height): graphics(i)
   draw()
   timersFunc()
   
   rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
   if rlist:
    if handler():
     v.run = 2
 
 except KeyboardInterrupt:
  v.run = 1
 finally:
  termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)        
  sys.stdout.write( "\033[?1002l\033[?1006l\033[2J\033[H\033[?25h")
  sys.stdout.flush()