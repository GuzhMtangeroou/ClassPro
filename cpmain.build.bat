@echo off
nuitka --standalone --onefile --enable-plugin=pyside6 --windows-disable-console --windows-icon-from-ico=cp.ico --output-dir=dist --follow-imports --remove-output --jobs=0 cpmain.py