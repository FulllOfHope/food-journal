#!/usr/bin/env bash
set -e
APP=bhu_meal_tracker
PREFIX=/opt/$APP
BIN=/usr/local/bin/bhu-meal-tracker
DESK=/usr/share/applications/bhu-meal-tracker.desktop
AUTOSTART=~/.config/autostart/bhu-meal-tracker-reminder.desktop

sudo mkdir -p $PREFIX
sudo cp -r ./* $PREFIX/
sudo chmod +x $PREFIX/meal_app.py $PREFIX/meal_reminder.py $PREFIX/meal_gui.py $PREFIX/meal_watcher.py

# venv
if [ ! -d "$PREFIX/venv" ]; then
  python3 -m venv $PREFIX/venv
fi
$PREFIX/venv/bin/pip install -q pystray pillow

# bin
sudo tee $BIN > /dev/null << EOF
#!/usr/bin/env bash
APP_DIR=$PREFIX
case "\$1" in
  gui)       exec $PREFIX/venv/bin/python3 "\$APP_DIR/meal_gui.py" ;;
  tray)      exec $PREFIX/venv/bin/python3 "\$APP_DIR/meal_app.py" tray ;;
  watch)     exec $PREFIX/venv/bin/python3 "\$APP_DIR/meal_watcher.py" ;;
  remind)    exec $PREFIX/venv/bin/python3 "\$APP_DIR/meal_reminder.py" ;;
  analytics) exec $PREFIX/venv/bin/python3 "\$APP_DIR/meal_app.py" analytics ;;
  *)         exec $PREFIX/venv/bin/python3 "\$APP_DIR/meal_gui.py" ;;
esac
EOF
sudo chmod +x $BIN

# desktop
sudo cp meal-tracker.desktop $DESK
sudo sed -i "s|^Exec=.*|Exec=$BIN gui|" $DESK

# nag on login until the day is logged
mkdir -p ~/.config/autostart
cat > $AUTOSTART << EOF
[Desktop Entry]
Type=Application
Name=BHU Meal Tracker Reminder
Comment=Nag the daily meal log until it is complete
Exec=$BIN watch
Icon=restaurant-symbolic
Terminal=false
Categories=Utility;
NoDisplay=true
X-GNOME-Autostart-enabled=true
EOF

echo "Installed."
echo "  GUI:      bhu-meal-tracker gui"
echo "  Nag loop: started automatically at every graphical login"
echo "  Tune it:  ~/.config/$APP/config.ini (poll_interval_minutes, nag_until)"