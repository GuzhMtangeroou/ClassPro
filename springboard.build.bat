@echo off
nuitka --standalone --onefile --enable-plugin=pyqt6 --windows-disable-console --windows-icon-from-ico=springboard.ico --output-dir=dist --follow-imports --remove-output --jobs=0 springboard.py