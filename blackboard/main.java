import java.util.List;
import java.util.ArrayList;
import java.util.Arrays;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.IOException;

public class main{
 static class tab {
  List<String> lines = new ArrayList<>();
  int column = 0;
  int line= 0;
  int scrollX = 0; 
  int scrollY = 0;
  int saveColumn=0;
  String fileName="";
  String directory="";

  public tab(String fi) {
   lines.add("");
   this.fileName= fi; 
  }
 }

static int width = 80; static int height = 20;
static int focused = 0; static tab current;
static List<tab> tabs = new ArrayList<>();
static int tick=0; static int[] debug={0,0};
static int[] select= {-1,-1};
static String greenBackground = "\u001B[48;2;14;107;55m";
static String reset= "\u001B[0m";
static String reverse= "\u001B[7m";
static int[] hotkeyByte= {14,19, 15, 24, 23, 7, 4, 17, 5, 14, 15, 2};
String[] hotkeyName= {"new","save","open","cut", "close", "goto", "run", "leftTab", "rightTab", "recentBack", "recentForward", "quickTest"};
static int[] displayDir= {-1,-1,-1};
static int consoleHeight=1;
static String[] screenBuffer = new String[10];
static int[] readKeys= {0,0,0,0,0,0};
static int step=6;
static int mx=-1; static int my=-1;
static List<String> console= new ArrayList<>(Arrays.asList(""));
static int consoleState=0;// 0-textEditor 1-consoleDrag 2-console

public static int[] getTerminalSize() {
 int[] size = new int[2];
 try {
  Process p1 = Runtime.getRuntime().exec(new String[]{"bash", "-c", "tput cols < /dev/tty"});
  BufferedReader br1 = new BufferedReader(new InputStreamReader(p1.getInputStream()));
  String widthValue = br1.readLine();
  br1.close();
  size[0] = Integer.parseInt(widthValue.trim());

  Process p2 = Runtime.getRuntime().exec(new String[]{"bash", "-c", "tput lines < /dev/tty"});
  BufferedReader br2 = new BufferedReader(new InputStreamReader(p2.getInputStream()));
  String heightValue = br2.readLine();
  br2.close();
  size[1] = Integer.parseInt(heightValue.trim());
        
 } catch (Exception e) {
  size[0] = 82;  // fallback width
  size[1] = 24;  // fallback height
 }
 return size;
}
   
static void handleMouse(int button){
 if(mx!=-1&& consoleState==0){
  current.line= readKeys[5]+ current.scrollY;
  current.column= readKeys[4]+ current.scrollX;
  current.line= Math.max(0, Math.min(current.line, current.lines.size()-1));
  current.column= Math.min(current.column, current.lines.get(current.line). length());
  current.saveColumn= current.column;
 }

 //32 64 35 click drag release
 if(button==35&& readKeys[5]>= height-consoleHeight){
  consoleState=2;
 }else if(button== 35&& consoleState==0){
  mx=-1; my=-1;
  if(select[0]== current.column&& select[1]== current.line){
   select[0]=-1; select[1]=-1;
  }
 }else if(button== 32&& readKeys[5]< height-consoleHeight){
  consoleState=0;
  select[1]= current.line;
  select[0]= current.column;
 }else if(button==32){
  consoleState=1;
 }else if(button== 64&& consoleState==1){
  consoleHeight= height- readKeys[5];
 }
}

static boolean deleteSelect(){
 if(select[0]==-1&& (current.line!= select[1]|| current.column!=select[0])){
  select[0]=-1; select[1]=-1;
  return false;
 }
 int smallest= Math.min(current.line, select[1]);
 int highest= Math.max(current.line, select[1]);
 String remainder="";
 for(int i= highest; i>= smallest; i--){
  int convertI= i+ current.scrollY;
  String line= current.lines.get(convertI);
  int[] textI= extractSelect(convertI);
  current.lines.set(convertI, line.substring(0, textI[0]) + line.substring(textI[1]));
  line= current.lines.get(convertI);

  if(convertI== smallest&& convertI!= highest)
  {current.lines.set(convertI, line+ remainder);}
  else if(convertI== highest)
  {remainder= line;}
  if(convertI!= smallest)
  {current.lines.remove(convertI);}
 }
 current.column= Math.min(current.column, select[0]);
 current.line= smallest;
 select[0]=-1; select[1]=-1;
 return true;
}

static void escapeKeys(){
 boolean upDownArrow= false;
 boolean leftRightArrow= false;
 int newStep= 1;
 if (readKeys[0] == 91) { // '['
  if(readKeys[3]==53){
   newStep= step;
  }
  if(readKeys[1]>=65&& readKeys[1]<=68){
   select[0]=-1; select[1]=-1;
  }else if(readKeys[4]>=65&& readKeys[4]<=68&& readKeys[1]==49&& readKeys[3]== 50){
   if(select[0]==-1){
    select[0]= current.column;
    select[1]= current.line;
   }
  }
  if(readKeys[1]==65|| (readKeys[1]==49&& readKeys[4]==65)) { // Up arrow
   current.line= current.line- newStep;
   current.column= current.saveColumn;
   upDownArrow=true;
  }else if(readKeys[1]==66|| (readKeys[1]==49&& readKeys[4]==66)){ // Down arrow
   current.line= current.line+ newStep;
   current.column= current.saveColumn;
   upDownArrow=true;
  }else if(readKeys[1]==67|| (readKeys[1]==49&& readKeys[4]==67)){// right arrow
   current.column= current.column+ newStep;
   leftRightArrow= true;
  }else if(readKeys[1]==68|| (readKeys[1]==49&& readKeys[4]==68)){ // Left arrow
   current.column= current.column- newStep; 
   leftRightArrow= true;
  }else if (readKeys[1] == 51) { 
   if (readKeys[2]== 126){ //del
    String line = current.lines.get(current.line);
    if(deleteSelect()){
    }else if (current.column!= line.length()) {
     current.lines.set(current.line, line.substring(0, current.column) + line.substring(current.column+1));
    } else if (current.line!= current.lines.size()-1) {
     current.lines.set(current.line, line+ current.lines.get(current.line+ 1));
     current.lines.remove( current.line+ 1);
 }}}}

 if(current.line< current.lines.size()&& current.line>-1&& !upDownArrow){
  if(current.column> current.lines.get(current.line).length()&& current.line< current.lines.size()-1) {
   current.line++; current.column= 0;
  }else if(current.column< 0&& current.line>0){
   current.line--;
   current.column= current.lines.get(current.line).length();
  }
 }
 current.line= Math.max(0, Math.min(current.lines.size() - 1, current.line));
 current.column= Math.max(0, Math.min(current.lines.get(current.line).length(), current.column));
 if(leftRightArrow)
 {current.saveColumn= current.column;}
}
 
static void inputEvents(int key) throws IOException{
 for(int i= 0; i<readKeys.length;i++)
 {readKeys[i]=-1;}
 boolean redraw= true;

 if (key == 27) { // ESC character
 for(int i= 0; i<readKeys.length;i++){
  }
  if (System.in.available() > 0) {
   readKeys[0] = System.in.read();
   if (System.in.available() > 0) {
    readKeys[1] = System.in.read();
    if(readKeys[1]==77){//mouse
     if (System.in.available() >= 3) {
      readKeys[3]= System.in.read(); //button 
      readKeys[4]= System.in.read()- 33; //x
      readKeys[5]= System.in.read()- 33;// y
      mx=readKeys[4]; my= readKeys[5];
      handleMouse(readKeys[3]);
     }
    }
    if (System.in.available() > 0) {
     readKeys[2] = System.in.read();
     if(readKeys[2]== 59){ //;
      readKeys[3] = System.in.read();// modifier
      readKeys[4] = System.in.read();// actionChar
     }
    }
    escapeKeys();
   }
  }
 }else if (key == 17) { //ctrl+q
  System.exit(0);
 }else if (key == 13) { // Enter key
  deleteSelect();
  current.lines.add(current.line + 1, current.lines.get(current.line).substring(current.column));
  current.lines.set(current.line, current.lines.get(current.line).substring(0, current.column));
  current.line++; current.column = 0;

 } else if (key == 127) { // Backspace
  if(deleteSelect()){
  }else if (current.column > 0) {
   String line = current.lines.get(current.line);
   current.lines.set(current.line, line.substring(0, current.column - 1) + line.substring(current.column));
   current.column--;
  } else if (current.line > 0) {
   current.column = current.lines.get(current.line - 1).length();
   current.lines.set(current.line - 1, current.lines.get(current.line - 1) + current.lines.get(current.line));
   current.lines.remove(current.line);
   current.line--;
   current.saveColumn= current.column;
  }
 }

 if (key >= 32 && key <= 126) { //chars
  deleteSelect();
  current.lines.set(current.line, current.lines.get(current.line).substring(0, current.column) + (char)key + current.lines.get(current.line).substring(current.column));
  current.column++;
  current.saveColumn= current.column;
 }else if(key==hotkeyByte[0]){
  
 }

 if(redraw){
  scrollFunc();
  drawLines();
 }
}

static int[] extractSelect(int line){
 if(line<0|| line>current.lines.size()){
  return new int[] {0,0,0};
 }
 String currentStr= current.lines.get(line);
 int max= currentStr.length();
 if(select[0]==-1){
  return new int[] {max,max,max};
 }
 boolean selectBig= current.line> select[1]|| (current.line== select[1]&& current.column> select[0]);
 int startY = (!selectBig) ? current.line : select[1];
 int endY = (selectBig) ? current.line : select[1];
 int startX = (!selectBig) ? current.column : select[0];
 int endX = (selectBig) ? current.column : select[0];

 if(line> startY&& line< endY){
  return new int[] {0,max,max};
 }else if(line==startY&& line==endY){
  return new int[] {startX, endX,max};

 }else if(line==startY){
  return new int[] {startX, max,max};  
 }else if(line==endY){
  return new int[] {0, endX,max};   
 }

 return new int[] {max,max,max};
}

static void updateCursor() {
 System.out.print("\033[" + (current.line- current.scrollY + 1) + ";" + (current.column- current.scrollX + 1) + "H");
}

static void drawLines() {
 System.out.print("\033[?25l"); // cursor hide
 StringBuilder output = new StringBuilder();
 for (int i = 0; i < screenBuffer.length; i++) {
  int convertI = i + current.scrollY;
  String lineContent= " ".repeat(width);
  int displayLength=0;
        
  if (convertI >= 0 && convertI < current.lines.size()&& i<height- consoleHeight) {
   String fullLine= current.lines.get(convertI);
   if( fullLine.length()>=current.scrollX){
    char startChar='\0';
    char endChar='\0';
    String partLine= fullLine.substring(current.scrollX, Math.min(fullLine.length(), current.scrollX+ width));
    displayLength= partLine.length();
    if(fullLine.length()>= current.scrollX + width){
     endChar= fullLine.charAt(current.scrollX + width - 1);
     partLine= partLine.substring(0,width-1);
    }
    if(fullLine.length()>0&& current.scrollX!= 0){
     if(partLine.length()>0){
      startChar= partLine.charAt(0);
      partLine= partLine.substring(1);
     }else{
      startChar=' ';
     }
    }
    int[] textI= extractSelect(convertI);
    for(int j=0;j<3;j++)
    {textI[j]= Math.min(width, Math.min(textI[j]- current.scrollX, partLine.length()));}
    String[] texts = {"", "", ""};
    texts[0] = partLine.substring(0, textI[0]);
    texts[1] = partLine.substring(textI[0], textI[1]);
    texts[2] = partLine.substring(textI[1], textI[2]);
                  
    lineContent = greenBackground+ startChar+ reset+ texts[0] + reverse + texts[1] + reset + texts[2]+ greenBackground+ endChar+ reset;
   }else{ //fullLine<scrollX
    if(current.lines. get(convertI).length()> 0){
     displayLength=1;
     lineContent= greenBackground+ ' '+ reset;
    }
   }
  }else if(i>=height-consoleHeight){ 
   if(i==height- consoleHeight)
   {lineContent= greenBackground;}
   lineContent+= " ".repeat(width);
   if(i==height-1)
   {lineContent+= reset;}
   displayLength= width;
  }

  if (displayLength < width)
  {lineContent= lineContent+ " ".repeat( width- displayLength);}

  if ((screenBuffer[i] == null || !screenBuffer[i].equals(lineContent))) {
   output.append("\033[").append(i + 1).append(";1H");
   output.append(lineContent);
   screenBuffer[i] = lineContent;
  }
 } 
 if (output.length() > 0) {
  System.out.print(output.toString());
  debug[0]= output.toString().length();
 }
    
 updateCursor();
 System.out.print("\033[?25h"); //cursorshow
 System.out.flush();
}

static boolean scrollFunc(){
 double threshold= (readKeys[4]==-1)? 0.15: 0.00;
 boolean active=false;

 if(height*threshold+1>= current.line- current.scrollY&& current.scrollY!=0){
  current.scrollY= Math.max(0, current.scrollY-1);
  active=true;
 }else if( height*(1.0-threshold)-1<= current.line- current.scrollY){
  current.scrollY= Math.min(current.lines.size(), current.scrollY+1);
  active=true;
 }
 if(current.column+1>=width+ current.scrollX){
  current.scrollX= Math.max(0, current.column- width+1);
  active=true;
 }
 if(current.column<= current.scrollX&& current.scrollX!=0){
  current.scrollX= Math.max(0,current.column-1);
  active=true;
 }
 return active;
}

 public static void main(String[] args)throws Exception {
  try {
 String[] cmd = {"/bin/sh", "-c", "clear;  stty -echo raw </dev/tty"};
 Runtime.getRuntime().exec(cmd) .waitFor();
 System.out.print("\033[?1002h");
 tabs.add(new tab("(save)"));
 current= tabs.get(focused);

 int[] screenSize1 = getTerminalSize();
 width = screenSize1[0];
 height = screenSize1[1];
 screenBuffer = new String[height];
 drawLines();

new Thread(() -> {
 while(true){
  try{
   tick++;
   if(tick>=10000000) tick=0;
   System.out.printf("\033]0;L:%d C:%d %d %d %d %d\007", current.line, current.column,debug[0], readKeys[3], select[0], consoleHeight);
   int[] screenSize = getTerminalSize();
   if(width!= screenSize[0]|| height!= screenSize[1]){
    width = screenSize[0]; height = screenSize[1];
    screenBuffer= Arrays.copyOf(screenBuffer, height);
   }
   if(select[1]!=-1) handleMouse(-1);
   if(scrollFunc()) drawLines();
   Thread.sleep(100); 
  } catch (InterruptedException e) {
   break;
  }
 }
}).start();

 while(true){
  int key = System.in.read();
  inputEvents(key);
 }
  }finally{
   new ProcessBuilder("/bin/sh", "-c", "stty sane </dev/tty").start();
   System.out.print("\033[?1002l");
  }
 }//void
}//class