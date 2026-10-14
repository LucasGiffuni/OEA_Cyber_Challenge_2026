#!/usr/bin/env python3
"""Comprueba los datos reales de los desafíos y guarda un registro de la ejecución."""
import argparse
import base64
import codecs
import hashlib
import json
import re
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("modo", choices=["numeros", "rot13", "java", "metadatos", "head"])
    parser.add_argument("entrada", help="Archivo de entrada; para head, URL de la instancia")
    parser.add_argument("--registro", help="Archivo JSON donde guardar la evidencia")
    args = parser.parse_args()
    resultado = {"modo": args.modo, "entrada": args.entrada}
    if args.modo != "head":
        ruta = Path(args.entrada)
        datos = ruta.read_bytes()
        resultado["sha256"] = hashlib.sha256(datos).hexdigest()
    if args.modo == "numeros":
        texto = datos.decode().strip()
        if not re.fullmatch(r"[0-9\s{}]+", texto):
            raise ValueError("La transcripción debe contener números, espacios y llaves.")
        valores = [int(n) for n in re.findall(r"\d+", texto)]
        if any(n < 1 or n > 26 for n in valores):
            raise ValueError("Hay números fuera del rango de A1Z26 (1 a 26).")
        salida = re.sub(r"\d+", lambda m: chr(int(m.group()) + 64), texto)
        resultado["salida"] = re.sub(r"\s+", "", salida)
    elif args.modo == "rot13":
        resultado["salida"] = codecs.decode(datos.decode().strip(), "rot_13")
    elif args.modo == "java":
        texto = datos.decode()
        password = re.search(r'password\.equals\("([^"\\]*)"\)', texto)
        prefijo = re.search(r'substring\("([^"\\]*)"\.length\(\)', texto)
        if not password or not prefijo:
            raise ValueError("El archivo no coincide con la comparación simple esperada. Revisá el código.")
        resultado["prefijo_en_codigo"] = prefijo.group(1)
        resultado["password"] = password.group(1)
        resultado["salida"] = prefijo.group(1) + password.group(1) + "}"
        resultado["nota"] = "Reconstrucción del código. El formato aceptado se comprueba en la plataforma."
    elif args.modo == "metadatos":
        identificacion = subprocess.run(["file", str(ruta)], capture_output=True, text=True, check=True)
        resultado["identificacion"] = identificacion.stdout.strip()
        cadenas = subprocess.run(["strings", str(ruta)], capture_output=True, text=True, check=True)
        licencia = re.search(r"<cc:license\s+rdf:resource=['\"]([^'\"]+)['\"]", cadenas.stdout)
        if not licencia:
            raise ValueError("No apareció cc:license en las cadenas; revisá los metadatos con otra herramienta.")
        resultado["campo"] = "cc:license / rdf:resource (XMP)"
        resultado["valor"] = licencia.group(1)
        resultado["salida"] = base64.b64decode(licencia.group(1), validate=True).decode()
    else:
        if not args.entrada.startswith(("http://", "https://")):
            raise ValueError("Indicá una URL HTTP de la instancia autorizada del desafío.")
        respuesta = subprocess.run(["curl", "--silent", "--show-error", "--head", "--max-time", "20", args.entrada], capture_output=True, text=True, check=True)
        resultado["salida"] = respuesta.stdout
    resultado["validacion_en_plataforma"] = "No realizada por este script"
    texto = json.dumps(resultado, ensure_ascii=False, indent=2)
    print(texto)
    if args.registro:
        destino = Path(args.registro)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(texto + "\n")


if __name__ == "__main__":
    main()
