call venv\Scripts\activate
pyinstaller --onefile --icon=static\icon.ico --distpath=aviator_parser aviator_parser.py

copy config.ini aviator_parser\config.ini

rmdir /s /q build
del /q /f aviator_parser.spec