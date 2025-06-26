#!/bin/bash

INSTALL_DIR="$(dirname "$(realpath "$0")")"
DESKTOP_FILE="$HOME/.local/share/applications/choct.desktop"
echo "Installing Choct from: $INSTALL_DIR"
read -p "continue:[Y/n] " choice
choice=${choice:-Y}

if [[ "$choice" == "Y" || "$choice" == "y" ]]; then
mkdir -p "$HOME/.local/share/applications"
cat > "$DESKTOP_FILE" <<EOL
[Desktop Entry]
Name=Choct
Exec=$INSTALL_DIR/choct %U
Type=Application
Terminal=false
Categories=Utility;TextEditor;
Icon=$INSTALL_DIR/_internal/icon.png
MimeType=text/plain;
StartupWMClass=Tk
EOL
update-desktop-database ~/.local/share/applications/
else
 echo "failed"
fi
echo "setting alias and path in bashrc"
read -p "continue:[Y/n] " choice2
choice2=${choice2:-Y}
if [[ "$choice2" == "Y" || "$choice2" == "y" ]]; then
    if ! grep -q "alias choct=\"$INSTALL_DIR/choct\"" ~/.bashrc; then
        echo "alias choct=\"$INSTALL_DIR/choct\"" >> ~/.bashrc
    fi
    if ! grep -q "export PATH=\$PATH:$INSTALL_DIR" ~/.bashrc; then
        echo "export PATH=\$PATH:$INSTALL_DIR" >> ~/.bashrc
    fi
    source ~/.bashrc
else
    echo "failed"
fi
read -p ""
