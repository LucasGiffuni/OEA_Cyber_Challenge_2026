# Manual de ejecución — Núcleo S.A.

Guía para levantar el desafío desde cero. Cualquier persona con Docker debería
poder ponerlo en marcha sin ayuda.

## Requisitos

- Docker y Docker Compose (v2, comando `docker compose`).
- Puerto **5000** libre en la máquina host.
- No requiere acceso a Internet una vez construida la imagen.

## Estructura de archivos

```
nucleo-ctf/
├── app.py                 # aplicación Flask (lógica + flag)
├── requirements.txt       # Flask 3.0.3
├── Dockerfile
├── docker-compose.yml
└── static/
    └── js/
        └── app.js         # JS del cliente (contiene una trampa)
```

## Levantar el desafío

Desde la carpeta `nucleo-ctf/`:

```bash
docker compose up --build -d
```

Verificá que esté arriba:

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:5000/
# debe imprimir: 200
```

Abrí en el navegador: <http://localhost:5000>

## Alternativa sin Docker

```bash
pip install -r requirements.txt
python3 app.py
# sirve en http://0.0.0.0:5000
```

## Parar y limpiar

```bash
docker compose down
```

## Puertos y endpoints

| Puerto | Uso                          |
|--------|------------------------------|
| 5000   | HTTP de la aplicación        |

| Endpoint        | Descripción                                             |
|-----------------|---------------------------------------------------------|
| `/`             | Landing (contiene una pista en un comentario HTML)      |
| `/portal`       | Login (acepta `guest:guest`)                            |
| `/dashboard`    | Panel del usuario; filtra el secreto de firma ofuscado  |
| `/flag`         | Devuelve la flag si el token forjado cumple las 3 condiciones |
| `/static/js/app.js` | JS del cliente (secreto DECOY)                      |
| `/robots.txt`, `/admin.php`, `/backups/` | señuelos / callejones sin salida |

## Notas de configuración (para el docente)

Todo está en `app.py`, al principio:

- `REAL_SECRET` — clave real de firma HS256. **No está en rockyou**; hay que leerla
  de la pantalla. Cambiala si querés rotar el reto.
- `DECOY_SECRET` — clave falsa que aparece en `app.js` (la trampa).
- `CLIENT_TOKEN` — valor de la cabecera `X-Core-Token` (= `base64("nucleo")`).
- `FLAG` — la flag que entrega `/flag`.

El servidor usa el server de desarrollo de Flask, suficiente para un CTF de aula.
No lo expongas a Internet tal cual.
