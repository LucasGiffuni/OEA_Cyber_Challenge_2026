"""
Núcleo S.A. - Panel Interno
CTF web (dificultad media). Un único contenedor Flask.

Cadena de solución intencional:
  1. Recon: / -> comentario HTML apunta a /portal
  2. Login demo guest:guest -> cookie `token` = JWT HS256 {role:user}
  3. /dashboard filtra el SECRETO REAL de firma, ofuscado con CSS `order`
     (el DOM queda desordenado; a la vista se lee bien)
  4. Trampas: /static/js/app.js tiene un secreto DECOY que NO firma válido
  5. Forjar JWT {role:admin} con el secreto real
  6. /flag exige cabecera X-Core-Token (calculada por el JS del dashboard)
     + token válido + role admin -> devuelve la flag
"""
import os
import hmac
import json
import base64
import random
import hashlib

from flask import Flask, request, render_template_string, Response, redirect

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Configuración del desafío
# ---------------------------------------------------------------------------
# Secreto REAL de firma. Es una frase, NO está en rockyou ni en wordlists
# comunes: el brute-force offline (hashcat/john) no llega. Hay que LEERLO.
REAL_SECRET = "nucleo-prod-7F3a-llave-2026"

# Secreto DECOY (trampa). Aparece en /static/js/app.js como si fuera el bueno.
# Forjar con esto da 401: es el cebo para scanners y solvers automáticos.
DECOY_SECRET = "dev-secret-123"

# Cabecera que el cliente interno "firma" en cada request sensible.
# El JS del dashboard la calcula como btoa('nucleo'). Está a la vista en el
# fuente: replicarla es trivial para un humano, pero rompe el curl ciego.
CLIENT_TOKEN = base64.b64encode(b"nucleo").decode()  # -> "bnVjbGVv"

FLAG = "FLAG{n0_t0d0_s3_cr4ck34_c0n_r0ckyou}"

DEMO_USER = {"guest": "guest"}


# ---------------------------------------------------------------------------
# JWT (HS256) implementado a mano para no depender de nada externo
# ---------------------------------------------------------------------------
def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(seg: str) -> bytes:
    return base64.urlsafe_b64decode(seg + "=" * (-len(seg) % 4))


def make_jwt(payload: dict, secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = (
        _b64(json.dumps(header, separators=(",", ":")).encode())
        + "."
        + _b64(json.dumps(payload, separators=(",", ":")).encode())
    )
    sig = hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
    return signing_input + "." + _b64(sig)


def verify_jwt(token: str, secret: str):
    """Devuelve el payload si la firma HS256 es válida, si no None.
    Rechaza alg:none porque exige coincidencia HMAC exacta."""
    try:
        signing_input, sig = token.rsplit(".", 1)
        expected = _b64(
            hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(expected, sig):
            return None
        _, body = signing_input.split(".")
        return json.loads(_unb64(body))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Ofuscación visual: CSS flex `order`.
# El texto se parte en spans cuyo orden en el DOM se baraja, pero cada span
# lleva order:<posición visual>. Render -> correcto. get_page_text / scraping
# de DOM -> caracteres desordenados. Se regenera por request (sin cache).
# ---------------------------------------------------------------------------
def scramble(text: str) -> str:
    positions = list(range(len(text)))
    dom_order = positions[:]
    random.shuffle(dom_order)
    spans = []
    for i in dom_order:
        ch = text[i]
        disp = "&nbsp;" if ch == " " else (ch.replace("<", "&lt;").replace(">", "&gt;"))
        spans.append(f'<span style="order:{i}">{disp}</span>')
    return (
        '<div style="display:flex;flex-wrap:wrap;font-family:monospace;'
        'font-size:15px;letter-spacing:1px">' + "".join(spans) + "</div>"
    )


# ---------------------------------------------------------------------------
# Plantillas
# ---------------------------------------------------------------------------
BASE_CSS = """
<style>
  :root { color-scheme: dark; }
  body { background:#0b0e14; color:#c8d0e0; font-family:system-ui,Arial,sans-serif;
         max-width:760px; margin:40px auto; padding:0 20px; line-height:1.55; }
  a { color:#6ea8fe; }
  .card { background:#11161f; border:1px solid #1e2636; border-radius:10px;
          padding:20px 24px; margin:18px 0; }
  h1,h2 { color:#eaf0fb; }
  code,pre { background:#0d1119; border:1px solid #1e2636; border-radius:6px;
             padding:2px 6px; color:#9ad1a3; }
  input { background:#0d1119; border:1px solid #28324a; color:#eaf0fb;
          padding:8px 10px; border-radius:6px; width:100%; box-sizing:border-box;
          margin:6px 0 14px; }
  button { background:#2b6cff; color:#fff; border:0; padding:9px 18px;
           border-radius:6px; cursor:pointer; }
  .muted { color:#6b7690; font-size:13px; }
  .err { color:#ff8b8b; }
</style>
"""

LANDING = BASE_CSS + """
<!-- NOTA infra: el portal de staging se movió a /portal tras el incidente -->
<h1>Núcleo S.A.</h1>
<div class="card">
  <p>Sistema de gestión interna. El acceso público al sitio corporativo
  está deshabilitado durante el mantenimiento.</p>
  <p class="muted">Empleados: usá el portal interno. Soporte: no responde por este canal.</p>
</div>
<p class="muted">v2.3.1 · build staging</p>
"""

PORTAL = BASE_CSS + """
<h1>Portal interno</h1>
<div class="card">
  <form method="post" action="/portal">
    <label>Usuario</label><input name="user" autocomplete="off">
    <label>Contraseña</label><input name="password" type="password" autocomplete="off">
    <button type="submit">Ingresar</button>
  </form>
  {% if error %}<p class="err">{{ error }}</p>{% endif %}
</div>
<div class="card">
  <p class="muted">Mientras se migran las cuentas, quedó habilitada una
  <b>cuenta de demostración</b> de solo lectura:</p>
  <p class="muted">usuario <code>guest</code> · contraseña <code>guest</code></p>
  <p class="muted">La cuenta <code>admin</code> real quedó con contraseña rotada;
  usala solo si sos del equipo de plataforma.</p>
</div>
"""

DASHBOARD = BASE_CSS + """
<h1>Panel · <span class="muted">sesión: {{ role }}</span></h1>

<div class="card">
  <h2>Resumen</h2>
  <p>Hola <b>{{ user }}</b>. Tu rol actual es <code>{{ role }}</code>.
  El tablero de administración y <code>/flag</code> requieren rol
  <code>admin</code>.</p>
  <p id="out" class="muted">consultando /flag…</p>
</div>

<div class="card">
  <h2>Documentación interna · configuración de sesión</h2>
  <p class="muted">Recordatorio del equipo de plataforma (no borrar):</p>
  {{ leak|safe }}
  <p class="muted">⚠ No reutilizar esta clave fuera de staging.</p>
</div>

<script>
  // Cliente interno Núcleo: todo request al endpoint sensible va firmado.
  function coreToken() { return btoa('nucleo'); }
  fetch('/flag', { headers: { 'X-Core-Token': coreToken() } })
    .then(r => r.text())
    .then(t => { document.getElementById('out').textContent = t; })
    .catch(() => {});
</script>
"""


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template_string(LANDING)


@app.route("/robots.txt")
def robots():
    # Rabbit holes para scanners automáticos: rutas que no llevan a nada.
    body = "User-agent: *\nDisallow: /portal\nDisallow: /backups/\nDisallow: /admin.php\n"
    return Response(body, mimetype="text/plain")


@app.route("/admin.php")
def admin_php():
    # Cebo: parece una vía PHP legacy, es un callejón sin salida.
    return Response("Forbidden", status=403)


@app.route("/backups/")
def backups():
    return Response("Not Found", status=404)


@app.route("/portal", methods=["GET", "POST"])
def portal():
    if request.method == "POST":
        u = request.form.get("user", "")
        p = request.form.get("password", "")
        if DEMO_USER.get(u) == p:
            token = make_jwt({"user": u, "role": "user"}, REAL_SECRET)
            resp = redirect("/dashboard")
            resp.set_cookie("token", token, httponly=False, samesite="Lax")
            return resp
        return render_template_string(PORTAL, error="Credenciales inválidas.")
    return render_template_string(PORTAL, error=None)


@app.route("/dashboard")
def dashboard():
    token = request.cookies.get("token", "")
    data = verify_jwt(token, REAL_SECRET)
    if not data:
        return redirect("/portal")
    leak_text = f"JWT signing key (HS256): {REAL_SECRET}"
    return render_template_string(
        DASHBOARD,
        user=data.get("user", "?"),
        role=data.get("role", "?"),
        leak=scramble(leak_text),
    )


@app.route("/flag")
def flag():
    # Gate 1: cabecera de cliente (se calcula en el JS del dashboard).
    if request.headers.get("X-Core-Token") != CLIENT_TOKEN:
        return Response(
            "Falta la cabecera de cliente X-Core-Token "
            "(mirá cómo la arma el script del dashboard).",
            status=428,
        )
    # Gate 2: token firmado con la clave REAL (el decoy no pasa de acá).
    token = request.cookies.get("token", "")
    data = verify_jwt(token, REAL_SECRET)
    if not data:
        return Response(
            "Token ausente o firmado con la clave equivocada.", status=401
        )
    # Gate 3: rol admin (hay que forjarlo: no existe login admin accesible).
    if data.get("role") != "admin":
        return Response(
            f"Rol insuficiente. Tu token dice role={data.get('role')!r}, "
            "se necesita role='admin'.",
            status=403,
        )
    return Response(FLAG, mimetype="text/plain")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
