
#executar main.py
file_to_execute = "main.py"
with open(file_to_execute, "r") as file:
    exec(file.read())
