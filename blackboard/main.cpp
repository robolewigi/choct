#include <cstdio>
#include <string>
#include <vector>
#include <termios.h>
#include <unistd.h>
#include <cstdlib>
#include <signal.h>
#include <fstream>
#include <filesystem>
#include <algorithm>
#include <sstream>

struct tab{
 std::vector<std::string> lines= {""};
 int column = 0;
 int line= 0;
 int scrollX = 0; 
 int scrollY = 0;
 int columnSave=0;
 std::string directory="";
 std::string name="";
};
tab current;

struct termios orig;
std::vector<tab> tabs;
int width = -1; int height = -1;
int focused = 0;
int selects[2]= {-1,-1};
int running=0;
//std::string greenBackground = "\u001B[48;2;14;107;55m";
std::string reset= "\u001B[0m";
std::string reverse= "\u001B[7m";
std::string saveString="";
std::string status="";
int displayDir[3]= {-1,-1,-1};
int mx=0; int my=0; int button=-1;
int consoleState=0;// 0-textEditor 1-consoleDrag 2-directory 3-open 4-name 5-console 6-help 7-goto
std::vector<std::string> previousBuffer;
std::vector<std::string> buffer;
std::vector<std::string> plainText;
std::vector<std::string> commandList;
int getTermValue(const char* cmd), readKey();
std::vector <std::string> hotkeyName= {"exit","save","directory/file", "console","help","copy", "cut","paste","goto", "recentBack","recentForward", "undo", "redo"};
std::vector<int> hotkeys={17,19,20, 4,8,3, 24,22,7, 5,18,26, 25};
int defaultHotkey= hotkeys.size();
std::vector<int> recentList(50, -1); //recentList recentIdx
int recentIdx=0;
int recentCurrent=0;
std::vector<std::string> history;
std::vector<int> historyLines;
//int historyIdx=0;
//int historyMax=1000;

void begin(), onExit(), graphics(int line), draws(int line), onSave(), onOpen(), saveSettings(), loadSettings(), buttonFunc(), copyToClipboard(const std::string& text), recentFunc(int line), pushHistory();
bool processKey(int key), deleteSelects();
std::vector<std::string> splitWords(std::string str, std::string split);
std::vector<int> extractSelects(int line);
std::string pasteFromClipboard();

/*
void pushHistory() {
 if (historyIdx > 0 &&
  std::abs((int)current.lines[current.line].length() - (int)history[historyIdx-1].length()) < 6){
  return;
 }
 if (historyIdx < (int)history.size()){
  history.erase(history.begin() + historyIdx, history.end());
  historyLines.erase(historyLines.begin() + historyIdx, historyLines.end());
 }
 history.push_back(current.lines[current.line]);
 historyLines.push_back(current.line);

 if ((int)history.size() > historyMax){
  history.erase(history.begin());
  historyLines.erase(historyLines.begin());
 }else{
  historyIdx++;
 }
}
*/

void recentFunc(int line){
 if(recentList[0]==-1 || std::abs(recentCurrent- line)>= 6){
  recentList.insert(recentList.begin(), line);
  recentList.pop_back();
  recentIdx=0;
 }
 recentCurrent= line;
}

std::string pasteFromClipboard() {
 FILE* pipe = popen("wl-paste --no-newline", "r");
 if (!pipe) return "";
 std::string result;
 char buf[256];
 while (fgets(buf, sizeof(buf), pipe))
  result += buf;
 pclose(pipe);
 return result;
}

void copyToClipboard(const std::string& text) {
 FILE* pipe = popen("wl-copy", "w");
 if (!pipe) return;
 fwrite(text.c_str(), 1, text.length(), pipe);
 pclose(pipe);
}

void processHotkey(int key){
 if (key == hotkeys[0]) { // ctrl+q exit
  running=2;
 }else if (key == hotkeys[1]) { // ctrl+s save
  saveString="";
  if(current.directory=="" || current.name==""){
   saveString= current.directory;
   if(consoleState==2){
    consoleState=0; status="";
   }else{consoleState=2;}
  }else{
   onSave();
  }
 } else if (key == hotkeys[2]) { // ctrl+t file/directory
  saveString="";
  if(consoleState==3){
   consoleState=0; status="";
  }else{consoleState= 3;}
  saveString=current.directory;
 } else if (key == hotkeys[3]) { // ctrl+d console
  saveString="";
  if(consoleState==5){
   consoleState=0; status="";
   saveString="";
   for(int i=0;i<height;++i){draws(i);}
  }else{
   consoleState=5;
  }
 }else if (key == hotkeys[4]) { // ctrl+h help
  saveString="";
  if(consoleState==6){
   consoleState=0; status="";
   for(int i=0; i<height; ++i){draws(i);}
  }else{
   consoleState=6;
   saveString="exit 2";
   printf("\033[H\033[2J\033[3J");
   fflush(stdout);
   for(int i=0; i<hotkeys.size();++i){
    printf("%s= ctrl+%c\n", hotkeyName[i].c_str(), (char) hotkeys[i]+64);
   }
  }

 }else if (key == hotkeys[5]|| key == hotkeys[6]) { // ctrl+c copy || ctrl+x
  auto selected= extractSelects(-1);
  std::string total;
  for(int i=0; i< selected.size(); i+=3){
   total+= current.lines[selected[i]].substr(selected[i+1], selected[i+2]- selected[i+1]);
   if(i+3< selected.size()){
    total+= "\n";
   }
  }
  copyToClipboard(total);
  if(key== hotkeys[6]){deleteSelects();}

 }else if (key == hotkeys[7]) { // ctrl+v paste
  std::string text = pasteFromClipboard();
  if(text.empty()) return;
  deleteSelects();
  auto parts = splitWords(text, "\n");
  // insert first part on current line
  current.lines[current.line].insert(current.column, parts[0]);
  current.column += parts[0].size();
  // insert remaining parts as new lines
  for(int i = 1; i < (int)parts.size(); i++){
   std::string remainder = current.lines[current.line].substr(current.column);
   current.lines[current.line] = current.lines[current.line].substr(0, current.column);
   current.lines.insert(current.lines.begin() + current.line + 1, parts[i]);
   current.line++;
   current.column = parts[i].size();
   current.lines[current.line] += remainder;
  }
  current.columnSave = current.column;

 }else if (key == hotkeys[8]) { // ctrl+g goto
  if(consoleState!=7){
   consoleState=7;
   for(int i=0; i<height; ++i){draws(i);}
  }else{
   consoleState=0; status="";
  }
 }else if (key == hotkeys[9]|| key == hotkeys[10]) { // ctrl+e recentBack ctrl+r recentForward
  int newInt= recentIdx;
  if(key== hotkeys[9]){
   newInt+=1;
  }else{
   newInt-=1;
  }
  if(newInt>-1 && newInt<50){
   if(recentList[newInt]!=-1){
    current.line= std::min(recentList[newInt], (int)current.lines.size()-1);
    current.column= 0;
    recentIdx= newInt;
   }
  }
/*
 }else if (key == hotkeys[11]|| key == hotkeys[12]) { // ctrl+z undo ctrl+y redo
  if(key==hotkeys[11]){
   if(historyIdx-1>= 0){
    historyIdx-=1;
    current.lines[historyLines[historyIdx]]= history[historyIdx];
    current.line= historyLines[historyIdx];
   }
  }else{
   if(historyIdx+1< history.size()){
    historyIdx+=1;
    current.lines[historyLines[historyIdx]]= history[historyIdx];
    current.line= historyLines[historyIdx];
   }
  }
*/

 }else {
  auto it = std::find(hotkeys.begin()+ defaultHotkey, hotkeys.end(), key);
  if (it != hotkeys.end()) {
   int idx = std::distance(hotkeys.begin()+ defaultHotkey, it);
   std::string cmd = "bash -l -c '"+  commandList[idx] + "'";
   system(cmd.c_str());
  }
 }
}

int getTermValue(const char* cmd) { // "tput lines" "tput cols"
 FILE* pipe = popen(cmd, "r");
 int val = 0;
 fscanf(pipe, "%d", &val);
 pclose(pipe);
 return val;
}

std::vector<std::string> splitWords(std::string str,std::string split=" "){
 size_t start = 0, end;
 std::vector<std::string> result;
 while ((end = str.find(split, start)) != std::string::npos) {
  result.push_back(str.substr(start, end - start));
  start = end + 1;
 }
 result.push_back(str.substr(start));
 return result;
}

void buttonFunc(){
 //status= std::to_string(button);
 if (button == 0 || button == 32){
  if(button==0){
   selects[0]=-1; selects[1]=-1;
  }
  int targetLine = my + current.scrollY;
  int targetCol = mx + current.scrollX;
  if(selects[0]==-1&& button==32){
   selects[0]= targetCol; selects[1]= targetLine;
  }
  current.line = std::max(0, std::min(targetLine, (int)current.lines.size() - 1));
  current.column = std::max(0, std::min(targetCol, (int)current.lines[current.line].length()));
  current.columnSave = current.column;
 }
 if (button == 0){
  selects[0]= current.column; selects[1]= current.line;
 }
}

void onExit(){
 printf("\033[?1003l\033[?1006l");  // disable mouse
 printf("\033[H\033[2J\033[3J");    // clear screen + scrollback
 printf("\033[?25h");               // show cursor
 printf("\033[0m");                 // reset colors/attributes
 printf("\033[H");                  // move cursor to top-left
 printf("\033[0 q"); // restore default cursor
 fflush(stdout);
 tcsetattr(STDIN_FILENO, TCSANOW, &orig);  // restore terminal
}

int readKey() { //up=1000 down=1001 right=1002 left=1003 del=1004 home=1005 end=1006
 fd_set fds;
 struct timeval tv = {0, 4000}; // zero timeout = instant poll
 FD_ZERO(&fds);
 FD_SET(STDIN_FILENO, &fds);
 if (select(STDIN_FILENO + 1, &fds, NULL, NULL, &tv) <= 0){return -1;}
 unsigned char c;
 read(STDIN_FILENO, &c, 1);
 if (c == '\x1b') {
  unsigned char seq[3];
  if (read(STDIN_FILENO, &seq[0], 1) != 1) return '\x1b';
  if (read(STDIN_FILENO, &seq[1], 1) != 1) return '\x1b';
  if (seq[0] == '[') {
   if (seq[1] == '<') { // mouse event (SGR mode)
    unsigned char ch;
    std::string nums = "";
    while (read(STDIN_FILENO, &ch, 1) == 1 && ch != 'M' && ch != 'm'){
     nums += ch;
    }
    sscanf(nums.c_str(), "%d;%d;%d", &button, &mx, &my);
    if(ch=='m'){button=-1;}
    mx-=1; my-=1;
    buttonFunc();
   }else if (seq[1] >= '0' && seq[1] <= '9') {
    unsigned char seq2;
    if (read(STDIN_FILENO, &seq2, 1) != 1) return '\x1b';
     if (seq2 == '~') {
      switch (seq[1]) {
       case '3': return 1004;
       case '1': return 1005;
       case '4': return 1006;
      }
     }
    } else {
     switch (seq[1]) {
      case 'A': return 1000;
      case 'B': return 1001;
      case 'C': return 1002;
      case 'D': return 1003;
      case 'H': return 1005;
      case 'F': return 1006;
     }
    }
   }
   return '\x1b';
  }
 return (int)c;
}

void loadSettings() {
 std::ifstream inFile("settings.txt");
 if (inFile.is_open()) {
  std::string line;
  hotkeys.clear();
  hotkeyName.clear();
  commandList.clear();
  while (std::getline(inFile, line)) {
   std::istringstream iss(line);
   std::string name, command;
   int key;
   if (iss >> name >> key) {
    
    hotkeyName.push_back(name);
    hotkeys.push_back(key);
    if (iss >> command) {
     commandList.push_back(command);
    }
   }
  }
  inFile.close();
 } else {
  printf("loadSettingsError");
 }
}   

void saveSettings(){
 std::ofstream outFile("settings.txt");
 if (outFile.is_open()) {
  for(int i=0; i<hotkeyName.size(); i++){
   if(i<defaultHotkey){
    outFile << hotkeyName[i]+ " "+  std::to_string(hotkeys[i])+ "\n";
   }else{
    outFile << hotkeyName[i]+ " "+  std::to_string(hotkeys[i])+ " "+  commandList[i-defaultHotkey]+ "\n";
   }
  }
  outFile.close();
 } else {
  printf("settingsError");
 }
}

bool deleteSelects(){
 if(selects[0]==-1 || (current.line == selects[1] && current.column == selects[0])){
  selects[0]=-1; selects[1]=-1;
  return false;
 }
 auto textI = extractSelects(-1);
 if(textI.empty()) return false;

 int numLines = (int)textI.size() / 3;
 int firstLine = textI[0];
 int firstX    = textI[1];
 int lastLine  = textI[(numLines-1)*3];
 int lastEndX  = textI[(numLines-1)*3 + 2];

 std::string tail = current.lines[lastLine].substr(lastEndX);

 for(int i = numLines-1; i >= 1; i--)
  current.lines.erase(current.lines.begin() + textI[i*3]);

 current.lines[firstLine] = current.lines[firstLine].substr(0, firstX) + tail;

 current.column = firstX;
 current.line   = firstLine;
 selects[0]=-1; selects[1]=-1;
 return true;
}

std::vector<int> extractSelects(int line=-1){
 if(selects[1] >= (int)current.lines.size() && (current.column!= selects[0]&& current.line!= selects[1])|| selects[0]==-1){
  return {};
 }
 bool selectBig = current.line > selects[1] || (current.line == selects[1] && current.column > selects[0]);
 int startY = (!selectBig) ? current.line : selects[1];
 int endY   = ( selectBig) ? current.line : selects[1];
 int startX = (!selectBig) ? current.column : selects[0];
 int endX   = ( selectBig) ? current.column : selects[0];
 std::vector<int> total;
 int realEnd= endY;
 if(line!=-1){realEnd= line; }
 for(int i=startY; i<realEnd+1; ++i){
  total.push_back(i);
  int maxLen = (int)current.lines[i].length();
  if(i > startY && i < endY){
   total.push_back(0); total.push_back(maxLen);
  } else if(i == startY && i == endY){
   total.push_back(startX); total.push_back(endX);
  } else if(i == startY){
   total.push_back(startX); total.push_back(maxLen);
  } else if(i == endY){
   total.push_back(0); total.push_back(endX);
  }else{
   total.push_back(maxLen); total.push_back(maxLen);
  }
 }
 return total;
}

bool processKey(int key){
 if (key == -1) return true;
 processHotkey(key);
 if(key >= 32 && key <= 126){ //normalKeys
  if(consoleState==0){
   //pushHistory();
   deleteSelects();
   current.lines[current.line].insert(current.column, 1, (char)key);
   current.column++;
   current.columnSave= current.column;
   recentFunc(current.line);
  }else if(consoleState>=2 && consoleState<=7){
   saveString+= (char)key;
  }
 }else if(key==10){ //enter
  if(consoleState==0){
   //pushHistory();
   deleteSelects();
   std::string remainder = current.lines[current.line].substr(current.column);
   current.lines[current.line] = current.lines[current.line].substr(0, current.column);
   current.lines.insert(current.lines.begin() + current.line + 1, remainder);
   current.line++;
   current.column=0; current.columnSave=0;
   recentFunc(current.line);
  }else{
   if (consoleState==2){
    if(saveString.back() != '/'){
     saveString+="/";
    }
   if (access(current.directory.c_str(), F_OK) == 0) {
    consoleState=4;
    current.directory= saveString;
   }
   }else if(consoleState==3){
    onOpen();
   }else if (consoleState==4){
    current.name= saveString;
    onSave();
    consoleState=0; status="";
   }else if (consoleState==5){
    printf("\033[H\033[2J\033[3J");
    fflush(stdout);
    std::string cmd = "bash -l -c 'cd " + current.directory + " && " + saveString + "'";
    system(cmd.c_str());

   }else if(consoleState==6){
    std::vector<std::string> result= splitWords(saveString, " ");
    auto it = std::find(hotkeyName.begin(), hotkeyName.end(), result[0]);
    try {
     int n = std::stoi(result[1]);
     if (it != hotkeyName.end()) {
      int index = (int)(it - hotkeyName.begin()); 
      hotkeys[index]= n;
     }else{
      hotkeyName.push_back(result[0]);
      hotkeys.push_back(n);
      commandList.push_back(result[2]);
     }
     printf("\033[H\033[2J\033[3J");
     fflush(stdout);
     for(int i=0; i<hotkeys.size();++i){
      printf("%s= ctrl+%c\n", hotkeyName[i].c_str(), (char) hotkeys[i]+64);
     }
     saveSettings();
    } catch (...) {}
   }else if(consoleState==7){
    try{
     current.line= std::min(std::stoi(saveString), (int)current.lines.size()-1);
     current.column= 0;
    }catch(...){}
   }
   if(consoleState!=4 && consoleState!=2&& consoleState!=5&& consoleState!=6){
    consoleState=0; status="";
   }
   saveString="";
  }
 }else if(key==127){ //backspace
  if (consoleState==0){
   //pushHistory();
   if(!deleteSelects()){
    current.column--;
    if(current.column>=0){
     current.lines[current.line].erase(current.column, 1);
    }else if(current.line>0){
     current.line--;
     current.column = current.lines[current.line].length();
     current.lines[current.line] += current.lines[current.line+1];
     current.lines.erase(current.lines.begin() + current.line+1);
    }
    current.columnSave= current.column;
   }
   recentFunc(current.line);
  }else if(consoleState>=2 && consoleState<=7){
   if (saveString.length()>0){
    saveString.pop_back();
   } 
  }
 }else if(key==1004){ //del
  if(consoleState==0){
   //pushHistory();
   if(!deleteSelects()){
    if(current.column!= current.lines[current.line].length()){
     current.lines[current.line].erase(current.column, 1);
    }else if((int)current.lines.size()> current.line+1){
     current.lines[current.line] += current.lines[current.line+1];
     current.lines.erase(current.lines.begin() + current.line+1);
    }
   }
   recentFunc(current.line);
  }
 }else if(key==1000){
  current.line--;
 }else if(key==1001){
  current.line++;
 }else if(key==1003){
  current.column--;
 }else if(key==1002){
  current.column++;
 }

 if(consoleState==2){status= "directory: ";}else
 if(consoleState==3){status= "open: ";}else
 if(consoleState==4){status= "name: ";}else
 if(consoleState==5){status= "console: ";}else
 if(consoleState==6){status= "hotkey: ";}else
 if(consoleState==7){status= "goto: ";}
 if(consoleState>=2 && consoleState<=7){status += saveString + " ";}

 if(current.line < 0) current.line = 0;
 else if(current.line >= (int)current.lines.size()) current.line = (int)current.lines.size()-1;

 if (key== 1000 || key== 1001){
  current.column= current.columnSave;
  current.column= std::min(current.column, (int)current.lines[current.line].length());
 }
 if(current.column<0){
  if (current.line== 0){
   current.column=0;
  }else{
   current.line--;
   current.column= current.lines[current.line].length();
  }
 }else if(current.column> current.lines[current.line].length()){
  if(current.line+1< (int)current.lines.size()){
   current.column=0;
   current.line++;
  }else{
   current.column= (int)current.lines[current.line].length();
  }
 }
 if(current.line<0){
  current.line=0;
 }else if(current.line>= current.lines.size()){
  current.line= current.lines.size()-1;
  current.column= current.lines[current.line].length();
 }
 if(key==1002 || key==1003){
  current.columnSave= current.column;
 }
 for(int i=0; i<height; ++i) graphics(i);
 return false;
}

void graphics(int line){
 if(running!=0){return;}
 if (line== height-1){
  buffer[line]= "";
  std::string newStatus=status;
  if(consoleState!=0){
   newStatus=status;
   if(consoleState==2|| consoleState==3){
    if (access(saveString.c_str(), F_OK) == 0) {
     newStatus= status+ "(T)";
    }else{
     newStatus= status+ "(F)";
    } 
   }
  }

  std::string result;
  int count = 0;
  for (char c : current.directory) {
   if (c == '/') { result += c; count = 0; }
   else if (count < 3) { result += c; count++; }
  }
  buffer[line]= newStatus+ "L:"+ std::to_string(current.line)+ " C:"+ std::to_string(current.column)+ " "+ result;
  buffer[line]= buffer[line].substr(0, width);
 }else{
  if(current.column> current.scrollX+ width-1){
   current.scrollX= current.column- width+1;
  }else if(current.column< current.scrollX){
   current.scrollX= current.column;
  }
  if(current.line> current.scrollY+ height-2){
   current.scrollY= current.line- height+2;
  }else if(current.line< current.scrollY){
   current.scrollY= current.line;
  }
  int actualLine = line + current.scrollY;
  if(actualLine < (int)current.lines.size()){
   if(current.scrollX < (int)current.lines[actualLine].size()){
    plainText[line] = (current.scrollX < (int)current.lines[actualLine].size())
 ? current.lines[actualLine].substr(current.scrollX, width)
 : "";
    buffer[line] = plainText[line];
    auto selectExtract = extractSelects(actualLine);
    int s0 = 0, s1 = 0;
    if (!selectExtract.empty()) {
     s0 = std::max(0, std::min((int)plainText[line].size(), selectExtract[selectExtract.size()-2] - current.scrollX));
     s1 = std::max(0, std::min((int)plainText[line].size(), selectExtract[selectExtract.size()-1] - current.scrollX));
    }
    buffer[line] = plainText[line].substr(0, s0) + reverse + plainText[line].substr(s0, s1-s0) + reset + plainText[line].substr(s1);
   }else{
    buffer[line]= "";
   }
  }else{
   buffer[line]= "";
  }
 }
}

void draws(int line){
 previousBuffer[line]= buffer[line];
 printf("\033[%d;%dH", line+1, 0);
 printf("\033[2K\r%s", buffer[line].c_str());
 printf("\033[%d;%dH", current.line- current.scrollY+ 1, current.column- current.scrollX+1);
}

void onSave(){
 std::string path = current.directory + current.name;
 std::ofstream f(path);
 for (const auto& line : current.lines){
  f << line << '\n';
 }
}

void onOpen(){
 namespace fs = std::filesystem;
 fs::path path(saveString);

 if(fs::is_directory(path)){
  if(saveString.back() != '/') saveString += '/';
  current.directory = saveString;
  return;
 }

 std::ifstream f(saveString);
 if(!f.is_open()){ status="invalid"; return; }

 size_t slash = saveString.rfind('/');
 current.directory = saveString.substr(0, slash + 1);
 current.name = saveString.substr(slash + 1);

 current.lines.clear();
 std::string line;
 while(std::getline(f, line))
  current.lines.push_back(line);
 if(current.lines.empty()) current.lines.push_back("");
 current.line=0; current.column=0;
 current.scrollX=0; current.scrollY=0;
}

void begin() {
 signal(SIGINT, SIG_IGN);
 struct termios t;
 tcgetattr(STDIN_FILENO, &orig);
 t = orig;
 t.c_lflag &= ~(ICANON | ECHO | ISIG); 
 t.c_iflag &= ~(IXON | IXOFF); 
 char cwd[1024];
 getcwd(cwd, sizeof(cwd));
 current.directory = std::string(cwd) + '/';
 tcsetattr(STDIN_FILENO, TCSANOW, &t);
 printf("\033[?1003h\033[?1006h"); // enable mouse tracking
 printf("\033[H\033[2J\033[3J"); //clear screen
 printf("\033[1 q");//cursor blink
 fflush(stdout);
 loadSettings();
}

int main() {
 begin();
 while (running!=2) {
  int y= getTermValue("tput lines");
  int x= getTermValue("tput cols");
  if(x!= width || y!= height){
   width=x; height=y;
   previousBuffer.resize(height);
   buffer.resize(height);
   plainText.resize(height);
   for(int i=0; i<height; ++i){
    graphics(i); draws(i);
   }
  }
  fflush(stdout);
  if(processKey(readKey())) continue;

  for(int i=0; i<height; ++i){
   if (previousBuffer[i]!= buffer[i]){
    draws(i);
   }
  }

 }
 onExit();
}
