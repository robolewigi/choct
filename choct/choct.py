import tkinter as tk
from tkinter import *
from tkinter import ttk,filedialog,font
from threading import Thread
import os,json,subprocess,tempfile,ctypes,math,sys,threading,socket

try:
 root = tk.Tk()
except:
 print('root is broken')

root.title("Choct")
try:
 icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Choct.ico")
 root.iconbitmap(icon_path)
except:
 pass

class variables:
 def __init__(self):
  self.focused = 0
  self.menubar = Menu(root)
  root.config(menu=self.menubar)
  self.currentWidget=None
  self.cursor = [0,0]
  self.hotkeys = []
  self.keyFunc=[]
  self.screenXY=[400,300]
  #0-4:saved settings tabs
  self.saved=[None]*10
  self.project=''
  self.colors=['#000000','#ffffff']
  self.sizes=[12,12]
  self.fontFamily='Terminal'
  self.saveDict={}
  self.recent=-20
  self.tabToggle=0
  self.statusFocus=[None,None]
  #0-1:shiftLR 2-3:ctrl 4-5:alt
  self.modifiers=[False]*6
  self.ifSaved=''
  self.commandKey='%'
  self.setCommand= tk.BooleanVar(value=True)
  self.pannerHeight=477
  self.geometryScreen=[1280,720]
  self.definitions= []
  self.geometryShapes=[]
  self.shapeSelect=-1
  self.sock = None
  self.clients = [] 
  self.hostJoin=-1
  self.networkTimer=None
  self.previousContent=' '
  self.saveName= os.path.join(os.path.dirname(os.path.abspath(__file__)), 'variables.json')
  self.recentIndex=0

class notebookClass:
 def __init__(self):
  self.tabs=[]
  self.focused=0
  self.filePaths=[]
  self.frame=None

v=variables()
n=notebookClass()
n2=notebookClass()

class shape:
 def __init__(self,type=0,rgb=[],loc=[0,0],scale=[1,1],points=[]):
  self.points=points
  self.view=[]
  self.locations=loc
  self.scale=scale
  self.rgb=rgb
  self.type=type
  self.widget=None
  self.update()
  self.create()

 def create(self):
  thisWidget= v.notebooks[0].tabs[v.notebooks[0].focused].winfo_children()[0]
  if isinstance(thisWidget,tk.Canvas):
   color= f"#{self.rgb[0]:02x}{self.rgb[1]:02x}{self.rgb[2]:02x}"
   if self.type==0:
    self.widget= thisWidget.create_polygon(self.view, outline="black", fill=color, width=2)
   if self.type==1:
    self.widget= thisWidget.create_polygon(self.view, outline="black", fill=color, width=2)
   if self.type==2:
    self.widget= thisWidget.create_oval(self.view,outline='black',fill=color,width=2)
 def update(self,x=0):
  self.view=[self.points[i]*self.scale[i%2] + self.locations[i%2] for i in range(len(self.points))]
  thisWidget= v.notebooks[0].tabs[v.notebooks[0].focused].winfo_children()[0]
  if isinstance(thisWidget,tk.Canvas):
   if x==1:
     thisWidget.coords(self.widget, *self.view)
    
   
def keyCreate():
 if os.name == "nt":
  mouseWheel='<Control-MouseWheel>'
 else:
  mouseWheel='<Control-Button-5>'
 thisKey= ['<Control-n>','<Control-s>','<Control-o>','<Control-x>','<Control-c>','<Control-v>','<Control-w>','<Control-f>','<Control-g>','<Control-z>','<Control-y>','<F1>','','<Control-d>','<Alt-Up>','<Alt-Down>','<Alt-Left>','<Alt-Right>','<Double-ButtonRelease-1>','','','<Return>','<Control-minus>','<Control-equal>','',mouseWheel,'<Control-Button-4>','<Control-e>','','','','<Control-a>','<Control-comma>','<Control-period>','<Control-b>']
 if len(thisKey)>len(v.hotkeys):
  v.hotkeys=thisKey
 v.keyFunc= [newFunc,saveFunc,openFunc,cutFunc,copyFunc,pasteFunc,closeTabFunc,findFunc,gotoFunc, undoFunc,redoFunc,debugFunc,debugFunc,runFunc,upTab,downTab,leftTab,rightTab,highlightFunc,hotkeyFunc,colorFunc,command,fontDecrease,fontIncrease,fontChange,scrollDown,scrollUp,commandKeyFunc,helpFunc,compareFunc,geometryFunc,selectAll,recentBackwards,recentForwards,quickTest]

def tabFunc(x=0,y=None, name="(save)" ,filePath="",geometry=False):#function
 y= len(v.notebooks[0].tabs) if y is None else y
 y=min(y,len(v.notebooks[x].tabs))
 if 0<=y>=len(v.notebooks[0].tabs) or x==1:
  thisTab=ttk.Frame(v.notebooks[x].frame)
  v.notebooks[x].frame.add(thisTab, text=name)
  if x==0:
   if geometry:
    canvas = tk.Canvas(thisTab, bg="grey")
    canvas.pack( fill="both", expand=True)
    newWidget=canvas
   else:
    textEdit = tk.Text(thisTab, wrap="word",bg=v.colors[1],fg=v.colors[0], undo=True,font=(v.fontFamily, v.sizes[0]))
    textEdit.tag_config("highlight", background="yellow")
    textEdit.tag_config("cursors", background="blue")
    textEdit.config(state='normal')
    textEdit.tag_configure('brightRed', foreground='#ff0000')
    textEdit.tag_configure("black", foreground="black")
    textEdit.tag_configure('red', foreground='#8b0000')
    textEdit.tag_configure('blue', foreground='blue')
    newWidget=textEdit
   v.notebooks[x].filePaths.append(filePath)
   v.notebooks[x].tabs.append(thisTab)
   widgetFocus(0,y)

  elif x==1:
   thisColors=v.colors
   if y==0 and thisColors==['#000000','#ffffff']:
    thisColors=['#ffffff','#0E6B37']
   textEdit= tk.Text(thisTab,bg=thisColors[1], fg=thisColors[0], undo=True,yscrollcommand=lambda *args: scrollbar.set(*args),font=(v.fontFamily, v.sizes[1]),height='5')
   v.notebooks[x].tabs.append(thisTab)
  if not geometry:
   v.currentWidget=textEdit
   scrollbar = tk.Scrollbar(thisTab, orient="vertical", command=v.currentWidget.yview)
   scrollbar.pack(side="right", fill="y")
   v.currentWidget.config(yscrollcommand=lambda *args: scrollbar.set(*args))
   v.currentWidget.pack(fill="both", expand=True)
   for i in range(len(v.keyFunc)):
    if v.hotkeys[i] != "":
     newKey = None 
     if v.hotkeys[i][-3] == '-':
      newKey = v.hotkeys[i][:-2] +  v.hotkeys[i][-2].upper() + v.hotkeys[i][-1]
     if not geometry: 
      v.currentWidget.bind(v.hotkeys[i],v.keyFunc[i])
      if newKey is not None: 
       v.currentWidget.bind(newKey,v.keyFunc[i])  
     else: 
      if i not in [1, 3, 4, 5, 7, 8, 9, 10, 18, 22, 23, 25, 26]: 
       v.currentWidget.bind (v.hotkeys[i],v.keyFunc[i])
       if newKey is not None:
        v.currentWidget.bind(newKey,v.keyFunc[i])  
    v.currentWidget.bind("<KeyPress>", keyPressed)

 else:  
  if v.notebooks[0].tabs:
   v.notebooks[x].frame.forget(y)
   v.notebooks[0].tabs.pop(y)
   v.notebooks[0].filePaths.pop(y)
   v.notebooks[x].focused=min (len(v.notebooks[x].tabs)-1,v.notebooks[x].focused)
   if v.notebooks[x].focused!=-1:
    widgetFocus(0,v.notebooks[x].focused)
   if not v.notebooks[0].tabs:
    tabFunc()

def notebookCreate():
 paned_window = ttk.PanedWindow(root, orient='vertical')
 paned_window.pack(fill='both', expand=True)
 top_frame = ttk.Frame(paned_window)
 bottom_frame = ttk.Frame(paned_window)
 paned_window.add(top_frame)  
 paned_window.add(bottom_frame)
 v.notebooks = [n,n2]
 v.notebooks[0].frame=ttk.Notebook(top_frame, height=v.pannerHeight-26)
 v.notebooks[1].frame=ttk.Notebook(bottom_frame, height=v.screenXY[1]-v.pannerHeight)
 for books in v.notebooks:
  books.frame.pack(fill='both', expand=True)
 statusBar = tk.Label(root, text="", anchor="w", bg="lightgrey")
 statusBar.pack(side="bottom", fill="x")
 statusBar.pack_forget()
 
def defineFunc(event=None):
 if v.definitions==[]:
  v.definitions= [
  f'pygame.draw.polygon(screen, ({v.commandKey}r,{v.commandKey}g,{v.commandKey}b), [{v.commandKey}p, {v.commandKey}p), ({v.commandKey}p, {v.commandKey}p), ({v.commandKey}p, {v.commandKey}p)])',
  f'pygame.draw.rect(screen, (({v.commandKey}r,{v.commandKey}g,{v.commandKey}b)), ({v.commandKey}p, {v.commandKey}p, {v.commandKey}x, {v.commandKey}y))',
  f'pygame.draw.circle(screen, ({v.commandKey}r,{v.commandKey}g,{v.commandKey}b)), ({v.commandKey}p, {v.commandKey}p), {v.commandKey}x)']

def saveFunc(event=None):
 if isinstance (v.notebooks[0].tabs[v.notebooks[0].focused]. winfo_children()[0],tk.Text):
  if v.notebooks[0].focused >= 0:
   widgetFocus(0,v.notebooks[0].focused)
   if v.notebooks[0].filePaths[v.notebooks[0].focused] is None or not os.path.isfile(v.notebooks[0].filePaths[v.notebooks[0].focused]):
    currentPath = filedialog.asksaveasfilename(defaultextension="*.*", filetypes=[("All Files", "*.*"), ("Text Files", "*.txt"), ("Python Files", "*.py")])
    if type(currentPath)== str and currentPath!='':
     v.notebooks[0].filePaths[v.notebooks[0].focused] = currentPath
     v.notebooks[0].frame.tab(v.notebooks[0].focused, text=currentPath)
    else:
     return  
   else:
    currentPath = v.notebooks[0].filePaths[v.notebooks[0].focused]
   if currentPath:
    with open(currentPath, 'w') as file:
     print("save to:",currentPath)
     file.write(v.currentWidget.get(1.0, 'end-1c'))
     v.ifSaved=''
     setText(x=1)
     fileName = os.path.basename(currentPath)
     v.notebooks[0].frame.tab(v.notebooks[0].focused, text=fileName)
     save(event)
   else:
    print("did not save")
 return "break"
 
def newFunc(event=None):
 v.notebooks[0].filePaths.append('')
 tabFunc()
 return "break"

def openFunc(event=None,filePath=None):
 currentPath=filePath
 if currentPath is None:
  currentPath = filedialog.askopenfilename(filetypes=[("All Files", "*.*"), ("Text Files", "*.txt"),("Python Files", "*.py")])
 openContinue(currentPath)
 return "break"
def openContinue(path=None):
 if path and os.path.exists(path):
  with open(path, 'r', encoding="utf-8") as file:
   fileContent = file.read()
   fileName = os.path.basename(path)
   tabFunc(filePath=path)
    #!!filepaths error append filepath
   v.currentWidget.delete(1.0, 'end-1c')  
   v.currentWidget.insert(1.0, fileContent)
   v.notebooks[0]. frame.tab(len(v.notebooks[0].tabs)-1, text=fileName)
   setText(x=1)
   widgetFocus(x=0,y=len(v.notebooks[0].tabs)-1)
   print("opened:",path)
 else:
  if path in v.notebooks[0].filePaths:
   v.notebooks[0].filePaths.remove(path)

def closeTabFunc(event=None):
 if v.notebooks[0].tabs:
  tabFunc(0,v.notebooks[0].focused)
 return "break"
def copyFunc(event=None):
 v.currentWidget.event_generate("<<Copy>>")
 return "break"
def pasteFunc(event=None):
  if v.focused==0:
   if v.currentWidget.tag_ranges("sel"):
    v.currentWidget.delete(tk.SEL_FIRST, tk.SEL_LAST)
   v.currentWidget.insert("insert", root.clipboard_get(), "red")
  else:
   v.currentWidget.event_generate("<<Paste>>")
  v.ifSaved='*'
  titleUpdate()
  return "break"
def cutFunc(event=None):
  v.currentWidget.event_generate("<<Cut>>")
  return "break"
def undoFunc(event=None):
 try:
  if v.currentWidget.edit_modified():
   v.currentWidget.edit_undo()
 except tk.TclError:
  pass  
 return "break"
def redoFunc(event=None):
 try:
  v.currentWidget.edit_redo()
 except tk.TclError:
  pass     
 return "break"
def findFunc(event=None):
 selectedText=''
 if isinstance(v.currentWidget,tk.Text):
  if v.currentWidget.tag_ranges(tk.SEL):
   selectedText= v.notebooks[0].tabs[v.notebooks[0].focused].winfo_children()[0].get(tk.SEL_FIRST, tk.SEL_LAST)
 addText(f"{v.commandKey}find {selectedText}")
 v.cursor=[int(x) for x in v.currentWidget.index(tk.INSERT).split('.')]
 if selectedText!='':
  command()
 return "break"

def hotkeyFunc(event=None):
 keyText=""
 for i in range(len(v.keyFunc)):
  keyText= keyText+f"{v.keyFunc[i].__name__}:{i}{v.commandKey}{v.hotkeys[i]}\n"
 keyText= keyText+"\n"
 v.notebooks[1] .tabs[0].winfo_children()[0].insert("end", keyText)
 addText(f"{v.commandKey}command {v.commandKey}:\nNew Tab=ctrl+q instead ctrl+n\n{v.commandKey}hotkey 0{v.commandKey}<Control-q>")
 return "break"

def colorFunc(event=None):
 v.notebooks[1]. tabs[0].winfo_children()[0].insert("end", "(p)color 0(p)#ff0000: red text\n(p)color  1(p)#005500: dark green background\n")
 addText("{v.commandKey}color 1{v.commandKey}#008800")
 return "break"
def fontChange(event=None):
 v.notebooks[1].tabs[0]. winfo_children()[0].insert("end", f"{v.fontFamily}\nexamples: System/Terminal/Modern/Courier/Arial/Courier New/Times New Roman/Cascadia Mono\n")
 addText(f"{v.commandKey}font ")
 return "break"
def gotoFunc(event=None):
 addText(f"{v.commandKey}line ")
 return "break"
def focusFunc(event=None):
 if v.tabToggle==1:
  content= v.notebooks[1].tabs[4]. winfo_children()[0].get('1.0','end')
  lines = content.splitlines()
  amount=1
  for line in lines:
   loc=line.find(f'{v.commandKey}focus')+7
   line=line[loc:loc+1]
   if line.isdigit():
    if int(line)>amount:
     amount=int(line)+1
  addText(f"{v.commandKey}focus {amount}{v.commandKey}:\n{v.commandKey}focus {amount}{v.commandKey}:\n{v.commandKey}focus {amount}{v.commandKey}",1,4)
 return "break"

def runFunc(event=None):
    if v.hostJoin==0:
     sendMessage('run:')
    temp_file_path = None
    try:
     if v.currentWidget is v.notebooks[1].tabs[3].winfo_children()[0]:
         with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp", mode="w") as temp_file:
             temp_file.write(v.notebooks[1].tabs[3].winfo_children()[0].get(1.0, tk.END))
             temp_file_path = temp_file.name
     executed = False
     fileLocation= v.notebooks[0].filePaths[v.notebooks[0].focused]
     fileLocation= '/'.join(fileLocation.split('/')[:-1])
    except:
     pass
    print( 'location-',fileLocation,'\npaths-',v.notebooks[0].filePaths,'\nfocus-',v.notebooks[0].focused)
    if fileLocation:
     os.chdir(fileLocation)
     executed=True
     if os.name == "nt":
      fileLocation=fileLocation+'/run.bat'
      if os.path.exists(fileLocation):
       subprocess.Popen(["python", temp_file_path] if temp_file_path else ["cmd", "/c", fileLocation])
      else:
       executed=False
     else:
      fileLocation=fileLocation+'/run.sh'
      if os.path.exists(fileLocation):
       subprocess.Popen(["python3", temp_file_path] if temp_file_path else ["bash", fileLocation])
      else:
       executed=False
    if not executed:
        v.notebooks[1].tabs[0]. winfo_children()[0].insert(tk.END, "Cannot find 'run'\n")
        widgetFocus(1, 0)

    return "break"



def leftTab(event=None):
 widgetFocus (v.focused,(v.notebooks[v.focused].focused-1)%len(v.notebooks[v.focused].tabs))
 return "break"
def rightTab(event=None):
 widgetFocus (v.focused,(v.notebooks[v.focused].focused+1)%len(v.notebooks[v.focused].tabs))
 return "break"
def upTab(event=None):
 widgetFocus (0,v.notebooks[0].focused)
 return "break"
def downTab(event=None):
 widgetFocus (1,v.notebooks[1].focused)
 return "break"

def addText(word=f"{v.commandKey}find",x=1,y=0,last=':'):
 widgetFocus(x,y)
 newLine=''
 lastLine= v.currentWidget.index('end-1c').split('.')
 if lastLine[1] != '0':
  newLine='\n'
 v.currentWidget.insert(tk.END, f"{newLine}{word}{last}\n")
 if last!='':
  v.currentWidget.mark_set("insert", v.currentWidget.index(f"end-{len(last)+2}c"))
  v.currentWidget.see("end")

def highlightFunc(event=None):
    cursor_position = v.currentWidget.index(f"@{event.x},{event.y}")
    start_idx = f"{cursor_position} wordstart"
    end_idx = f"{cursor_position} wordend"
    selectedWord = v.currentWidget.get(start_idx, end_idx).strip()
    highlightWord(selectedWord)


def highlightWord(word=None):
 if not word:
  return
 sel_ranges = v.currentWidget.tag_ranges("sel")
 start_idx = '1.0'
 while True:
  start_idx = v.currentWidget.search(word, start_idx, stopindex=tk.END,nocase=1)
  if not start_idx:  # If no more occurrences, break
   break
  end_idx = f"{start_idx}+{len(word)}c"  # Calculate end index of the word
  v.currentWidget.tag_add("highlight", start_idx, end_idx)
  start_idx = end_idx  # Move start index for the next search

  if sel_ranges:
   v.currentWidget.tag_remove("highlight", sel_ranges[0], sel_ranges[-1])

def widgetFocus(x=0,y=0):
 if len(v.notebooks[x].tabs)>0:
  try:
   v.notebooks[x].frame.select(y)
   v.currentWidget= v.notebooks[x].tabs[y].winfo_children()[0]
   v.currentWidget.focus_set()
   v.focused=x
   v.notebooks[x].focused=y
   if isinstance(v.currentWidget,tk.Text):
    v.cursor= [int(v.currentWidget.index(tk.INSERT).split('.')[0]),int(v.currentWidget.index(tk.INSERT).split('.')[1])]
  except:
   pass

def menuCreate(group='File',name='New'):
 file_menu = Menu(v.menubar, tearoff=0)
 file_menu.add_command(label="New", command=lambda: newFunc(), accelerator=v.hotkeys[0])
 file_menu.add_command(label="Open", command=lambda: openFunc(), accelerator=v.hotkeys[2])
 file_menu.add_command(label="Save", command=lambda: saveFunc(), accelerator=v.hotkeys[1])
 file_menu.add_separator()
 file_menu.add_command(label="Close Tab", command=lambda: closeTabFunc(), accelerator=v.hotkeys[6])
 file_menu.add_command(label="Exit", command=root.quit, accelerator="alt+F4")
 v.menubar.add_cascade(label="File", menu=file_menu, underline=0)

 edit_menu = Menu(v.menubar, tearoff=0)
 edit_menu.add_command(label="Cut", command=lambda: cutFunc(), accelerator="ctrl+x")
 edit_menu.add_command(label="Copy", command=lambda: copyFunc(), accelerator="ctrl+c")
 edit_menu.add_command(label="Paste", command=lambda: pasteFunc(), accelerator="ctrl+v")
 edit_menu.add_command(label="Undo", command=lambda: undoFunc(), accelerator=v.hotkeys[9])
 edit_menu.add_command(label="Redo", command=lambda: redoFunc(), accelerator=v.hotkeys[10])
 edit_menu.add_separator()
 edit_menu.add_command(label="Goto", command=lambda: gotoFunc(), accelerator=v.hotkeys[8])
 edit_menu.add_command(label="Find", command=lambda: findFunc(), accelerator=v.hotkeys[7])
 edit_menu.add_checkbutton (label="Command",variable=v.setCommand, accelerator=v.hotkeys[27])
 v.menubar.add_cascade(label="Edit", menu=edit_menu, underline=0)

 settings_menu = Menu(v.menubar, tearoff=0)
 settings_menu.add_command(label="Help", command=lambda: helpFunc())
 settings_menu.add_command(label="Save Settings", command=lambda: saveFunc(),accelerator=v.hotkeys[1])
 settings_menu.add_command(label="Hotkeys", command=lambda: hotkeyFunc(),accelerator=v.hotkeys[19])
 settings_menu.add_command(label="Color", command=lambda: colorFunc(),accelerator=v.hotkeys[20])
 settings_menu.add_command(label="Font", command=lambda: fontChange(),accelerator=v.hotkeys[24])
 v.menubar.add_cascade(label="Settings", menu=settings_menu, underline=0)

 feature_menu = Menu(v.menubar, tearoff=0)
 feature_menu.add_command(label="Run", command=lambda: runFunc(), accelerator=v.hotkeys[13])
 feature_menu.add_command(label="Change Tab",accelerator="ctrl+Arrows", command=lambda: downTab())
 feature_menu.add_command(label="Compare", command=lambda: compareFunc())
 feature_menu.add_separator()
 feature_menu.add_command(label="More Tabs", command=lambda: toggleTabs())
 feature_menu.add_command(label="Add Focus", command=lambda: focusFunc())
 feature_menu.add_command(label="Geometry", command=lambda: geometryFunc())
 feature_menu.add_separator()
 feature_menu.add_command(label="Host", command=lambda: addText(f'{v.commandKey}host 127.0.0.1'))
 feature_menu.add_command(label="Join", command=lambda: addText(f'{v.commandKey}join 127.0.0.1'))
 feature_menu.add_command(label="Refresh", command=lambda: sendMessage('all:'))
 v.menubar.add_cascade(label="Feature", menu=feature_menu, underline=0)

def startNetwork(x, ip='localhost'):
    target_func = startServer if x == 0 else startClient
    networkThread = Thread(target=target_func, args=(ip,), daemon=True)
    networkThread.start()


def startServer(ip='localhost'):
        v.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
         v.sock.bind((ip, 18484)) 
         v.hostJoin=0
        except:
         addText('Port already used')
        v.sock.listen(5)
        addText("Server started",last='')
        Thread(target=acceptClients, daemon=True).start()

def startClient(ip='localhost'):
 v.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
 try:
  try:
   v.sock.connect((ip, 18484))
  except:
   addText('Cannot find')
  addText("Connected",last='')
  v.hostJoin=1
  Thread(target=receiveMessages, args=(v.sock,), daemon=True).start()
 except ConnectionRefusedError:
  addText("No connection")

def sendMessage(message,notClient=None):
    if not message:
        return
    message = message.encode()
    total_length = len(message)
    total_header = f"{total_length:08}".encode()
    if v.hostJoin == 0:  # Server mode
        for client in v.clients:	
         if notClient:
          if client.getpeername()[1]==notClient:
           continue
         try:
                client.sendall(total_header)
         except BrokenPipeError:
                v.clients.remove(client)
    elif v.sock:  # Client mode
        v.sock.sendall(total_header)
    
    chunk_size = 1024  # Define a fixed chunk size
    for i in range(0, total_length, chunk_size):
        chunk = message[i:i+chunk_size]
        chunk_header = f"{len(chunk):04}".encode() 
        chunk_data = chunk_header + chunk
        if v.hostJoin == 0:  # Server mode
            for client in v.clients:
             if notClient:
              if client.getpeername()[1]==notClient:
               continue
             try:
                    client.sendall(chunk_data)
             except BrokenPipeError:
                    v.clients.remove(client)
        elif v.sock:  # Client mode
            v.sock.sendall(chunk_data)

def receiveMessages(sock2):
    while v.hostJoin > -1:
        try:
            total_header = sock2.recv(8).decode()
            total_length_str = ''.join(c for c in total_header if c.isdigit())
            if not total_header and not total_header.isdigit() and total_length_str.isdigit():
                break
            try:
             total_length = int(total_header)
            except:
             break
            received_data = bytearray()
            remaining = total_length
            while remaining > 0:
                chunk_header = sock2.recv(4).decode()
                if not chunk_header:
                    break
                chunk_length = int(chunk_header)
                
                chunk_data = sock2.recv(chunk_length)
                received_data.extend(chunk_data)
                remaining -= len(chunk_data)
            
            data = received_data.decode()
            codes = data.split(':')[:1]
            message=':'.join(data.split(':')[1:])
            focusText=v.notebooks[0].tabs[v.notebooks[0].focused] .winfo_children()[0]   
            if codes[0] == 'msg':
                codes=message[:1]
                message=' '.join(message[1:])
                focusText.insert(f'{codes[0]}.0',message)
            elif codes[0] == 'all':
                sendMessage('msgAll:'+focusText.get('1.0', 'end-1c'))
            elif codes[0]=='msgAll':
                focusText.delete('1.0','end')
                focusText.insert('1.0',message)
                textColor('blue','1.0','end' ,focusText)

                v.previousContent=message
            elif codes[0]=='update':
             newMessage=json.loads(message)
             ensureLines(newMessage[2],focusText)
             for line in newMessage[1]:
              if line[0] in newMessage[0]:
               focusText.delete(f'{line[0]}.0', f'{line[0]}.end')
               newMessage[0].remove(line[0])
              focusText.insert(f'{line[0]}.0', line[1])
              textColor('blue',f'{line[0]}.0',f'{line[0]}.end' ,focusText,True)
             for line in newMessage[0]:
              focusText.delete(f'{line}.0', f'{line+1}.0')
             v.previousContent=focusText.get('1.0','end-1c')
             if v.hostJoin==0:
              sendMessage('update:'+message,sock2.getpeername()[1])
            elif codes[0]=='run':
             runFunc()
        except ConnectionResetError:
            addText("Connection lost.")
            break

def ensureLines(numLines,textWidget):
    lineCount = int(textWidget.index("end-1c").split(".")[0])
    if lineCount < numLines:
        for _ in range(numLines- lineCount):
            textWidget.insert("end", "\n")

def acceptClients():
 while v.hostJoin>-1:
  if v.sock is None:
   break
  client, addr = v.sock.accept()
  v.clients.append(client)
  addText(f"Client {addr}",last='')
  Thread(target=receiveMessages, args=(client,), daemon=True).start()
  sendMessage('msgAll:'+v.notebooks[0].tabs[v.notebooks[0].focused]. winfo_children()[0].get('1.0', 'end'))

def sendInfo():
 tabFocus=v.notebooks[0].tabs[v.notebooks[0].focused]
 data=json.dumps(compareTexts (v.previousContent,tabFocus,1))
 sendMessage('update:'+ data)
 v.previousContent=tabFocus.winfo_children()[0].get('1.0','end-1c')

def timerFunc(seconds=6):
 if v.networkTimer is not None:
  v.networkTimer.cancel()
 v.networkTimer = threading.Timer(seconds, sendInfo)
 v.networkTimer.start()

def keyPressed(event):
 #print (event.state,event.keycode,event.keysym,v.modifiers,(event.state & 0x08))
 if v.hostJoin>-1:
  timerFunc(2)
 modKeys=['Shift_L','Shift_R','Control_L','Control_R', 'Alt_L','Alt_R']
 if event.keysym in modKeys:
  v.modifiers[modKeys.index(event.keysym)]=True
 if event.keysym in ['Shift_L','Shift_R']:
  return 'break'

 if v.colors==['#000000','#ffffff']:
  if not (v.modifiers[2] or v.modifiers[3] or v.modifiers[4] or v.modifiers[5]) and v.focused==0:
   if event.keysym not in ['BackSpace','Enter','Escape','Delete','Up', 'Down','Left','Right','Prior','Next','Insert','Home','End'] and len(v.notebooks[0].tabs)>0 and isinstance(v.currentWidget,tk.Text):
    recentFunc()
    v.ifSaved='*'
    v.currentWidget.tag_remove("highlight", "1.0", tk.END)
    if v.currentWidget.tag_ranges("sel"):
     v.currentWidget.delete(tk.SEL_FIRST, tk.SEL_LAST)
    setText(event=event)
    v.recentIndex=0
    return "break"

def recentFunc():
  if abs(v.recent-v.cursor[0])>6:
   getName= v.notebooks[0].frame.tab(v.notebooks[0].focused, "text")
   getText= v.currentWidget.get(f"{v.cursor[0]}.0", f"{v.cursor[0]}.end")
   v.notebooks[1]. tabs[2].winfo_children()[0].insert("1.0" ,f"\n{v.commandKey}line {v.cursor[0]}:{getName}:{getText}")
   v.recent=v.cursor[0]
 
def inputReleased(event):
 modKeys=['Shift_L','Shift_R','Control_L','Control_R', 'Alt_L','Alt_R']
 if event.keysym in modKeys:
  v.modifiers[modKeys.index(event.keysym)]=False
 if getParent(event.widget,tk.Text):
  v.currentWidget=event.widget
 focusedWidget=getParent(event.widget,ttk.Notebook)
 if focusedWidget==v.notebooks[0].frame:
  v.focused=0
 elif focusedWidget==v.notebooks[1].frame:
  v.focused=1
 if v.notebooks[0].tabs:
  v.notebooks[v.focused].focused= v.notebooks[v.focused].frame.index(v.notebooks[v.focused].frame.select())
 if isinstance(event.widget,tk.Text):
  v.cursor=[int(x) for x in v.currentWidget.index(tk.INSERT).split('.')]
 titleUpdate()

def titleUpdate():
 root.title (f"{v.ifSaved}Choct - L:{v.cursor[0]} C:{v.cursor[1]} F:{v.notebooks[0].filePaths[v.notebooks[0].focused]}")

def lmb(event=None):
 v.pannerHeight=v.notebooks[0].frame.winfo_height()
 if event.widget.winfo_name()=='!text':
  inputReleased(event)
 v.shapeSelect=-1

def enter(event=None):
 inputReleased(event)

def command(event=None):
 for i in range(len(v.notebooks[1].tabs)):
  if v.currentWidget==v.notebooks[1].tabs[i].winfo_children()[0] and i not in [3] and v.setCommand.get():
   entireText=v.currentWidget.get(f"{v.cursor[0]}.0", f"{v.cursor[0]}.end")
   v.currentWidget.tag_add("highlight", f"{v.cursor[0]}.0", f"{v.cursor[0]}.end")

   names= [f'{v.commandKey}line',f'{v.commandKey}find',f'{v.commandKey}replace', f'{v.commandKey}hotkey', f'{v.commandKey}color',f'{v.commandKey}font',f'{v.commandKey}focus',f'{v.commandKey}geometry',f'{v.commandKey}command',f'{v.commandKey}help',f'{v.commandKey}compare',f'{v.commandKey}host',f'{v.commandKey}join']
   for func in names:
    start=entireText.find(func)
    last=entireText.find(':', start + len(func))
    if start!=-1 and last!=-1:
     getText=entireText[start + len(func)+1:last]
     middle=getText.find(f'{v.commandKey}', 1)
     oldText=getText[start:middle]
     newText=getText[middle+1:last]

     if func==f"{v.commandKey}find":
      if isinstance(v.notebooks[0].tabs[v.notebooks[0]. focused].winfo_children()[0],tk.Text):
       v.notebooks[1].tabs[1].winfo_children()[0].delete(1.0, "end")
       highlightWord(getText)
       content = v.notebooks[0].tabs[v.notebooks[0].focused].winfo_children()[0].get("1.0", tk.END)
       lines = content.splitlines()
       matching_lines = []
       for i in range(len(lines)):
        if getText.lower() in lines[i].lower():
         matching_lines.append(i+1)
       v.notebooks[1].tabs[1].winfo_children()[0] .insert(tk.END,f"{v.commandKey}replace {getText}{v.commandKey}:")
       for i in range(len(matching_lines)):
        v.notebooks[1].tabs[1].winfo_children()[0] .insert(tk.END,f"\n{v.commandKey}line {matching_lines[i]}:{lines[matching_lines[i]-1]}")
       widgetFocus(1,1)
      return "break"

     elif func==f"{v.commandKey}line":
      if getText.isdigit() and isinstance(v.notebooks[0].tabs[v.notebooks[0]. focused].winfo_children()[0],tk.Text):
       widgetFocus(0,v.notebooks[0].focused)
       v.currentWidget.see(f"{int(getText)}.0")
       v.currentWidget.tag_add("highlight", f"{int(getText)}.0", f"{int(getText)}.end")
       v.currentWidget.mark_set("insert", f"{int(getText)}.0")
       return "break"

     elif func==f"{v.commandKey}replace":
      if newText!="" and middle!=-1:
       content = v.notebooks[0].tabs[v.notebooks[0].focused] .winfo_children()[0].get("1.0", tk.END)
       updated_content = content.replace(oldText, newText)
       v.notebooks[0].tabs[v.notebooks[0].focused] .winfo_children()[0].delete("1.0", tk.END)
       v.notebooks[0].tabs[v.notebooks[0].focused] .winfo_children()[0].insert("1.0", updated_content.strip())
       v.currentWidget.mark_set("insert", "end")
       widgetFocus(1,0)
       return "break"

     elif func==f"{v.commandKey}hotkey":
      if middle!=-1:
       try:
        for note in v.notebooks:
         for tab in note.tabs:
          if int(oldText)!=18:
           tab. winfo_children()[0].unbind(v.hotkeys[int(oldText)])
           if newText!="":
            tab.winfo_children()[0].bind(newText, v.keyFunc[int(oldText)])
          elif note==v.notebooks[1]:
           tab. winfo_children()[0].unbind(v.hotkeys[int(oldText)])
           if newText!="":
            tab.winfo_children()[0].bind(newText, v.keyFunc[int(oldText)])
        v.hotkeys[int(oldText)]=newText
        return "break"
       except:
        pass

     elif func==f"{v.commandKey}color":
      if middle!=-1:
       newText=newText.replace(" ", "").lower()
       try:
        oldText=min(max(int(oldText),0),1)
        int(newText[1:], 16)
        v.colors[oldText]=newText
        for note in v.notebooks:
         for tab in note.tabs:
          tab.winfo_children()[0]. config(fg=v.colors[0],bg=v.colors[1])
        v.currentWidget.tag_add("sel", f"{v.cursor[0]}.0", f"{v.cursor[0]}.end")
        return "break"
       except:
        pass
   
     elif func==f"{v.commandKey}font":
      v.fontFamily=getText
      for i in range(len(v.notebooks)):
       for tab in v.notebooks[i].tabs:
        tab.winfo_children()[0] .configure(font=(v.fontFamily,v.sizes[i]))
      return "break"

     elif func==f"{v.commandKey}focus":
      if oldText=='':
       if v.statusFocus==[newText,None]:
        v.statusFocus=[None,None]
       else:
        v.statusFocus=[newText,None]
      else:
       if v.statusFocus==[oldText,newText]:
        v.statusFocus=[None,None]
       else:
        v.statusFocus=[oldText,newText]
      if v.statusFocus[0] is None and v.statusFocus[1] is None:
       root.winfo_children()[2].pack_forget()
      else:
       root.winfo_children()[2].pack(side=tk.BOTTOM, fill=tk.X)
       content = v.notebooks[1].tabs[4].winfo_children()[0].get("1.0", tk.END).strip()
       lines = content.split("\n")
       if oldText=='':
        matchingLines = [line for line in lines if f'{v.commandKey}focus {newText}' in line]
       else:
        matchingLines = [line for line in lines if f'{v.commandKey}focus {oldText}' in line]
        if newText.isdigit():
         matchingLines = [
    string for string in matchingLines
    if string[string.find(f'{v.commandKey}', 1) + 1:string.find(':')].isdigit() and
    int(newText) <= int(string[string.find(f'{v.commandKey}', 1) + 1:string.find(':')])]
       matchingLines= [item.replace(f"{v.commandKey}focus", "").strip() for item in matchingLines]
       root.winfo_children()[2]. config(text=f'{oldText}{v.commandKey}{newText}{matchingLines}')
      return "break"

     elif func==f"{v.commandKey}geometry":
      for i in range(len(v.notebooks[0].tabs)):
       if isinstance(v.notebooks[0].tabs[i].winfo_children()[0],tk.Canvas):
        widgetFocus(0,i)
      canvas= v.notebooks[0].tabs[v.notebooks[0].focused].winfo_children()[0]
      if not isinstance(canvas,tk.Canvas):
       geometryFunc()
       canvas= v.notebooks[0].tabs[v.notebooks[0].focused].winfo_children()[0]
      if getText=='0':
       v.notebooks[1].tabs[5].winfo_children()[0].delete('1.0','end')
       words=['p','r','g','b','x','y']
       for geometryShape in v.geometryShapes:
         thisText=v.definitions[geometryShape.type]
         findIndex=0
         times=0
         geometryShape.update()
         while findIndex!=-1 and times<50:
          findIndex=thisText.find(f'{v.commandKey}',findIndex)
          if findIndex!=-1:
           for i in range(len(words)):
            if thisText[findIndex+1:findIndex+2]==words[i]:
             if i==0:
              if len(geometryShape.view)>times:
               vText=geometryShape.view[times]
               times+=1
              else:
               vText=f'({len(geometryShape.view)} points {len(geometryShape.scale)} sizes)'
             if i==1:
              vText=geometryShape.rgb[0]
             elif i==2:
              vText=geometryShape.rgb[1]
             elif i==3:
              vText=geometryShape.rgb[2]
             elif i==4:
              if len(geometryShape.scale)>=1:
               vText=geometryShape.scale[0]
              else:
               vText=f'({len(geometryShape.view)} points {len(geometryShape.scale)} sizes)'
             elif i==5:
              if len(geometryShape.scale)>=2:
               vText=geometryShape.scale[1]
              else:
               vText=f'({len(geometryShape.view)} points {len(geometryShape.scale)} sizes)'
             if vText is not None:
              thisText= thisText.replace(f'{v.commandKey}{words[i]}',str(vText),1)
           findIndex+=1
         addText(f'{thisText}',1,5,'')

      if getText=='2':
        v.geometryShapes.append( shape(0,[188,0,0],[100,100],[55,55],[0,-1,-1,1,1,1]))
      elif getText=='4':
        v.geometryShapes.append( shape(1,[0,188,0],[155,155],[55,55],[-1,-1,-1,1,1,1,1,-1]))
      elif getText=='6':
        v.geometryShapes.append( shape(2,[0,0,188],[111,222],[55,55],[-1,-1,1,1]))
      elif getText=='1':
        addText(f'{v.definitions[0]}',1,5,'')
      elif getText=='3':
        addText(f'{v.definitions[1]}',1,5,'')
      elif getText=='5':
        addText(f'{v.definitions[2]}',1,5,'')
      if oldText=='1':
       v.definitions[0]= newText
      elif oldText=='3':
       v.definitions[1]= newText
      elif oldText=='5':
       v.definitions[2]= newText
      if newText.isdigit():
       if oldText=='7':
        v.geometryScreen[0]= int(newText)
       elif oldText=='8':
        v.geometryScreen[1]= int(newText)
      if getText=='9':
       v.shapeSelect=-1
       v.geometryShapes=[]
       closeTabFunc()

      return "break"
    
     elif func==f'{v.commandKey}command':
      v.commandKey=getText
      return "break"

     elif func==f'{v.commandKey}help':
      addText(f'{names}',last='')
      if v.tabToggle==1:
       addText(f"0:print text 1:define triangle/2:draw triangle\n3-4:square 5-6:circle 9:clear shapes \n{v.commandKey}geometry 3{v.commandKey}{v.definitions[1]}:\nCommands:p=points, r/g/b=red green blue, x/y=sizeXY\nlmb:move shape / lmb+shift:change size\n%geometry 2:",1,5,'')
      return "break"

     elif func==f'{v.commandKey}compare':
      if oldText.isdigit() and newText.isdigit() and len(v.notebooks[0].tabs)-1>=int(oldText) and len(v.notebooks[0].tabs)-1>=int(newText):
       compareTexts(v.notebooks[0].tabs[int(oldText)] ,v.notebooks[0].tabs[int(newText)])
      return "break"

     elif func==f'{v.commandKey}host':
      startNetwork(0,getText)
      return "break"

     elif func==f'{v.commandKey}join':
      startNetwork(1,getText)
      return "break"

     if names.index(func)==len(names)-1:
      return "break"

def save(event=None):
    newPaths = [v.notebooks[0].filePaths[v.notebooks[0].focused]]
    newTabs=[]
    for i in range(6):
     newTabs. append(v.notebooks[1].tabs[i].winfo_children()[0].get("1.0", 'end-1c'))
     if newTabs[i] is None:
      newTabs[i]=""
    data = {
     "filePaths": newPaths,
     "screenXY": v.screenXY,
     "key": v.hotkeys,
     "recent": newTabs[2],
     "chalk": newTabs[0],
     "geometry": newTabs[5],
     "color": v.colors,
     "size": v.sizes,
     "test": newTabs[3],
     "focus": newTabs[4],
     "toggle": v.tabToggle,
     "commandKey": v.commandKey,
     "pannerHeight": v.pannerHeight,
     "definitions": v.definitions,
     "font": v.fontFamily,
     "lastLocaion": v.recent
    }
    with open(v.saveName, "w") as file:
        json.dump(data, file, indent=4)

def load():
   if os.path.exists(v.saveName):
    with open(v.saveName, "r") as file:
     try:
      data = json.load(file)
      n.filePaths = data["filePaths"]
      v.screenXY = data["screenXY"]
      v.hotkeys=data["key"]
      v.saved[0] = data["recent"]
      v.saved[1] = data["chalk"]
      v.saved[2]= data["test"]
      v.saved[3]= data["focus"]
      v.saved[4]= data["geometry"]
      v.colors=data["color"]
      v.sizes=data["size"]
      v.fontFamily=data["font"]
      v.tabToggle= data["toggle"]
      v.pannerHeight= data["pannerHeight"]
      v.commandKey= data["commandKey"]
      v.definitions= data["definitions"]
      v.recent= data["lastLocation"]
     except:
      pass

def loadContinue():
 if os.path.exists(v.saveName):
     root.geometry(f"{v.screenXY[0]}x{v.screenXY[1]}")
     v.notebooks[1]. tabs[2].winfo_children()[0].insert("1.0", v.saved[0])
     v.notebooks[1]. tabs[0].winfo_children()[0].insert("1.0", v.saved[1])
     if v.saved[2].__class__.__name__=='str':
      v.notebooks[1]. tabs[3].winfo_children()[0].insert("1.0", v.saved[2])
     v.notebooks[1]. tabs[4].winfo_children()[0].insert("1.0", v.saved[3])
     v.notebooks[1]. tabs[5].winfo_children()[0].insert('1.0', v.saved[4])
 else:
  v.notebooks[1]. tabs[4].winfo_children()[0].insert("1.0", f"{v.commandKey}focus 1{v.commandKey}1:create window\n{v.commandKey}focus 1{v.commandKey}2:create text widget\n{v.commandKey}focus 1{v.commandKey}2:create 2nd text widget\n{v.commandKey}focus 1{v.commandKey}3:create scroll bar\n\n{v.commandKey}focus 2:create hotkey list\nrequires fullscreen")
  v.notebooks[1].tabs[3]. winfo_children()[0].insert("1.0", "input('Press ENTER to exit') #make sure you have run.bat(windows)")
  helpFunc()
 if v.notebooks[0].filePaths and type(v.notebooks[0].filePaths[0])== str:
  openFunc(filePath= v.notebooks[0].filePaths[0])
  v.notebooks[0].filePaths.pop(-1)
 
def resize(event=None):
 if event.widget.__class__.__name__=="Tk":
  v.screenXY=[event.width,event.height]

def getParent(widget=None,instance=ttk.Notebook):
    while widget:
        if isinstance(widget, instance):
            return widget
        widget = widget.master
    return None

def singleClick(event=None):
 if isinstance(v.notebooks[0].tabs[v.notebooks[0].focused]. winfo_children()[0],tk.Text):
  v.notebooks[0].tabs[v.notebooks[0].focused]. winfo_children()[0].tag_remove("highlight", "1.0", tk.END)
  v.notebooks[0].tabs[v.notebooks[0].focused]. winfo_children()[0].tag_remove("cursors", "1.0", tk.END)
 elif isinstance(event.widget,tk.Canvas):
  getShapes= event.widget.find_closest(event.x, event.y)
  if len(getShapes)>0:
   if math.sqrt((event.x - v.geometryShapes[getShapes[0]-1].locations[0]) ** 2 + (event.y - v.geometryShapes[getShapes[0]-1].locations[1]) ** 2)<(v.geometryShapes[getShapes[0]-1].scale[0]+v.geometryShapes[getShapes[0]-1].scale[1])/2:
    v.shapeSelect=getShapes[0]
  else:
   v.shapeSelect=-1

def mouseMotion(event=None):
 if isinstance(event.widget,tk.Canvas):
  if v.shapeSelect>-1:
   if v.modifiers[0] or v.modifiers[1]:
     v.geometryShapes[v.shapeSelect-1].scale= [event.x-v.geometryShapes[v.shapeSelect-1].locations[0],event.y-v.geometryShapes[v.shapeSelect-1].locations[1]]
     v.geometryShapes[v.shapeSelect-1].scale= [max(scales, 3) for scales in v.geometryShapes[v.shapeSelect-1].scale]
     v.geometryShapes[v.shapeSelect-1].update(1)
   else:
    newLoc= [event.x-v.geometryShapes[v.shapeSelect-1].locations[0],event.y-v.geometryShapes[v.shapeSelect-1].locations[1]]
    event.widget.move(v.shapeSelect,newLoc[0],newLoc[1])
    v.geometryShapes[v.shapeSelect-1].locations=[event.x,event.y]

def setText(event=None,x=0):
 if v.colors==['#000000','#ffffff']:
  if x==0:
   v.notebooks[0].tabs[v.notebooks[0].focused] .winfo_children()[0].insert("insert", event.char, 'red')
  if x==1:
   textColor()

def fontDecrease(event=None):
 v.sizes[v.focused]-=1
 for tab in v.notebooks[v.focused].tabs:
  tab.winfo_children()[0].configure(font=(v.fontFamily, v.sizes[v.focused]))
 
def fontIncrease(event=None):
 v.sizes[v.focused]+=1
 for tab in v.notebooks[v.focused].tabs:
  tab.winfo_children()[0].configure(font=(v.fontFamily, v.sizes[v.focused]))

def scrollDown(event=None):
 visible_range = v.currentWidget.yview()
 if event.delta:
  if event.delta > 0:
   new_position = visible_range[0] - (5 / 100)
  elif event.delta < 0:
   new_position = visible_range[0] + (5 / 100)
 else:
  new_position = visible_range[0] + (5 / 100)
 
 new_position = max(0, min(1, new_position))
 v.currentWidget.yview_moveto(new_position)
def scrollUp(event=None):
 visible_range = v.currentWidget.yview()
 if event.delta:
  pass
 else:
  new_position = visible_range[0] - (5 / 100)
 new_position = max(0, min(1, new_position))
 v.currentWidget.yview_moveto(new_position)

def toggleTabs(event=None,x=-1):
 if x==-1:
  v.tabToggle=1-v.tabToggle
 else:
  v.tabToggle=x
 if v.tabToggle==1:
  names=['','','','Test','Focus','Geometry']
  for i in range(len(v.notebooks[1].tabs)):
   if i>=3:
    v.notebooks[1].frame.add(v.notebooks[1].tabs[i], text=names[i])
 elif v.tabToggle==0:
  for i in range(len(v.notebooks[1].tabs)):
   if i>=3:
    v.notebooks[1]. frame.forget(v.notebooks[1].tabs[i])

def tabChanged(event=None):
 for note in v.notebooks:
  if event.widget.nametowidget(event.widget.select()) in note.tabs:
   note.focused=note.tabs .index(event.widget.nametowidget(event.widget.select()))
 titleUpdate()

def focusAway(event=None):
 v.modifiers=[False]*6

def commandKeyFunc(event=None):
 current_state = v.setCommand.get()
 v.setCommand.set(not current_state)

def compareTexts(x=None, y=None,z=0):
    if not isinstance(x,str):
     content1 = x.winfo_children()[0].get('1.0', 'end-1c')
    else:
     content1=x
    if not isinstance(y,str):
     content2 = y.winfo_children()[0].get('1.0', 'end-1c')
    else:
     content2=y
    content2 = [[i + 1, line] for i, line in enumerate(content2.splitlines())]
    content1 = [[i + 1, line] for i, line in enumerate(content1.splitlines())]
    lineCount=len(content2)
    content1.reverse()
    if z==0:
     textColor('brightRed','1.0','end',x.winfo_children()[0])
     textColor('brightRed','1.0','end',y.winfo_children()[0])
    for i in range(len(content1) - 1, -1, -1): 
     for line2 in content2: 
      if content1[i][1] == line2[1]:
       if z == 0:
        x.winfo_children()[0].tag_add('black', f'{content1[i][0]}.0', f'{content1[i][0]}.end')
        if not isinstance(y, str):
         y.winfo_children()[0].tag_add('black', f'{line2[0]}.0', f'{line2[0]}.end')
       content2.remove(line2)  # Remove the matched item
       content1.pop(i)  # Remove from content1
       break  # Stop processing this `i`
    if z==1:
     content1 = [item[0] for item in content1]
     return [content1,content2,lineCount]

def compareFunc(event=None):
 addText(f'{v.commandKey}compare {v.notebooks[0].focused}{v.commandKey}(tab index)')

def helpFunc(event=None):
 addText(f'{v.commandKey}help:\n^^^DoubleClick or Enter',1,0,'')
 if v.tabToggle==1:
  addText(f'{v.commandKey}help:',1,5,'')

def textColor(color='black',start='1.0',last='end' ,widget=None,keep=False):
 if widget is None:
  widget=v.notebooks[0].tabs[v.notebooks[0].focused].winfo_children()[0]
 if not keep:
  widget.tag_remove('brightRed', "1.0", "end")
  widget.tag_remove('black', "1.0", "end")
  widget.tag_remove('red', "1.0", "end")    
  widget.tag_remove('blue', "1.0", "end")   
 widget.tag_add(color, start, last)

def selectAll(event=None):
 v.currentWidget.tag_add("sel", "1.0", "end-1c")
 return "break"

def recentScroll(x):
 v.recentIndex= min(max(1,v.recentIndex+x),int(v.notebooks[1].tabs[2].winfo_children()[0].index('end-1c').split('.')[0]))

 if v.recentIndex!=-1:
  line= v.notebooks[1].tabs[2].winfo_children()[0].get(f"{v.recentIndex+1}.0", f"{v.recentIndex+1}.end")
  start= line.find(f'{v.commandKey}line')
  last= line.find(':', start + len(f'{v.commandKey}line'))
  if start!=-1 and last!=-1:
   getText= line[start + len(f'{v.commandKey}goto')+1:last]
   if getText.isdigit():
    widgetFocus(0,v.notebooks[0].focused)
    v.currentWidget.tag_remove("highlight", "1.0", tk.END)
    v.currentWidget.see(f"{getText}.0")
    v.currentWidget.tag_add("highlight", f"{getText}.0", f"{getText}.end")
    v.currentWidget.mark_set("insert", f"{getText}.0")
    
def recentBackwards(event=None):
 recentScroll(1)

def recentForwards(event=None):
 recentScroll(-1)

def quickTest(event=None):
 widgetFocus(1,3)
 v.currentWidget.delete("1.0", "end")
 v.currentWidget.event_generate("<<Paste>>")
 runFunc()

def geometryFunc(event=None):
 for i in range(len(v.notebooks[0].tabs)):
  if isinstance(v.notebooks[0].tabs[i].winfo_children()[0],tk.Canvas):
   break
  elif i==len(v.notebooks[0].tabs)-1:
   tabFunc(name="canvas" ,geometry=True)

def endStart():
 if os.name == "nt":
  ctypes.windll.shcore.SetProcessDpiAwareness(1)
 if len(sys.argv)>1:
  openWith = sys.argv[1].replace('\\', '/')
  if openWith not in v.notebooks[0].filePaths: 
   openFunc(filePath= openWith)

def onClose():
 v.hostJoin = -1
 if v.sock:
  v.sock.close()
 for client in v.clients:
  client.close()
 root.destroy()


def debugFunc(event=None):
 print("widget:",v.currentWidget,"\nfocuses:", v.notebooks[0].focused,v.notebooks[1].focused,v.focused,"\nfilePath:",v.notebooks[0].filePaths,"\ntabs:",v.notebooks[0].tabs,v.notebooks[1].tabs,"\ncursor:",v.cursor,"\nkeys:",v.hotkeys,'\nColors:',v.colors,'\nCommandKey',v.commandKey,v.setCommand,'\nrecentIndex: ',v.recentIndex)

load()#b2
notebookCreate()
keyCreate()
defineFunc()
tabFunc(1,0,'Chalk')
tabFunc(1,1,'Find')
tabFunc(1,2,'Recent')
tabFunc(1,3,'Test')
tabFunc(1,4,'Focus')
tabFunc(1,5,'Geometry')
toggleTabs(x=v.tabToggle)
menuCreate()
loadContinue()
endStart()
v.currentWidget.see(f"{v.recent}.0")
v.currentWidget.mark_set("insert", f"{v.recent}.0")
if len(v.notebooks[0].tabs)==0:
 tabFunc(0)

root.bind("<ButtonRelease-1>", lmb)
root.bind("<Configure>", resize)
root.bind("<Button-1>", singleClick)
root.bind("<Double-ButtonRelease-1>",command)
root.bind(v.hotkeys[21], command)
root.bind("<KeyRelease>",inputReleased)
root.bind("<<NotebookTabChanged>>", tabChanged)
root.bind("<FocusOut>", focusAway)
root.bind("<Motion>", mouseMotion)
root.protocol("WM_DELETE_WINDOW", onClose)

#debug()
root.mainloop()
