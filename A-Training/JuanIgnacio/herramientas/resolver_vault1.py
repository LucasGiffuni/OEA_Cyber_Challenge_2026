import re
from pathlib import Path

codigo = Path("archivos/VaultDoor1.java").read_text()
pares = re.findall(r"charAt\((\d+)\)\s*==\s*'(.)'", codigo)
caracteres = [""] * 32
for posicion, letra in pares:
    caracteres[int(posicion)] = letra
if len(pares) != 32 or any(letra == "" for letra in caracteres):
    raise ValueError("Faltan posiciones o el código cambió.")
password = "".join(caracteres)
print(password)
print("academy{" + password + "}")
