# Write-ups CTF — 5 desafíos
En este documento explico como resolvi los 5 ctf, es la primera vez que me enfrento a este tipo de desafios asi que voy a tomar niveles sencillos para adentrarme en el mundo.

## 1. MY GIT — picoCTF 2026

**Categoría:** General Skills

### Objetivo

El desafío daba un servidor Git propio con "reglas propias". Había que clonar un repositorio por SSH y conseguir que el servidor escribiera la flag en `flag.txt`. El README marcaba la condición:

> Only flag.txt pushed by `root:root@academy` will be updated with the flag.

Es decir, el servidor solo aceptaba la flag si el commit venía del usuario `root` con el email `root@academy`.

### Cómo lo resolví

Cloné el repositorio con la contraseña que daba el enunciado:

```bash
git clone ssh://git@chatelaine.cylabacademy.net:31140/git/challenge.git
cd challenge
```

La pista preguntaba cómo se configuran el nombre y el email en Git, y ahí estaba toda la solución. Git no verifica la identidad de quien hace un commit: los campos `user.name` y `user.email` los define cada uno en su propia configuración local, sin ninguna credencial. Así que me hice pasar por `root`:

```bash
git config user.name "root"
git config user.email "root@academy"
```

Después creé el archivo `flag.txt`, lo commiteé con esa identidad falsa y lo pushée:

```bash
touch flag.txt
git add flag.txt
git commit -m "add flag"
git push
```

El servidor validó el autor del commit, lo aceptó como si fuera root y respondió con la flag en la salida del push:

```
remote: Author matched and flag.txt found in commit...
remote: Congratulations! You have successfully impersonated the root user
remote: Here's your flag: academy{...}
```


### Conclusión

Git confía en los campos de autor del commit y no comprueba quién los pone realmente. Cualquiera puede configurar `user.name` y `user.email` con el valor que quiera, así que un servidor que autoriza según esos datos se engaña fácilmente. La defensa real es firmar los commits con GPG o con una clave SSH: así la identidad del autor queda verificada criptográficamente y no basta con escribir un nombre.

## 2. Vigenere — picoCTF 2022

Categoría: Criptografía Dificultad: Media

### Objetivo

El desafío daba un archivo cipher.txt con un mensaje cifrado y la clave CYLAB. Había que descifrarlo con el cifrado de Vigenère para obtener la flag.

### Cómo lo resolví

Al abrir el archivo encontré este texto:

caldfow{O0NU_WQ3_G1G3O3T3_A1AH3S_4c372077}

Lo primero que me llamó la atención fue que empezaba con caldfow, cuando todas las flags de la plataforma arrancan con academy. Eso me confirmó que caldfow era academy cifrado, y me sirvió para verificar que estaba aplicando bien el método.

Vigenère es un cifrado por sustitución donde cada letra se corre según una letra de la clave, que se va repitiendo a lo largo del mensaje (A=0, B=1, …, Y=24). Para descifrar hay que restar la clave: P = (C − K) mod 26. Lo comprobé a mano con las primeras letras:

Cifra	c(2)	a(0)	l(11)	d(3)	f(5)	o(14)	w(22)
Clave	C(2)	Y(24)	L(11)	A(0)	B(1)	C(2)	Y(24)
C − K mod 26	a	c	a	d	e	m	y

Daba academy, así que la clave CYLAB y la fórmula eran correctas.

Un detalle clave: los dígitos y los símbolos no se descifran, se dejan igual, y la clave solo avanza cuando procesa una letra. Por eso partes como 4c372077 quedan tal cual en la flag.

Para no hacer todo a mano, armé un script en Python (apoyándome en IA para escribirlo) que recorre el texto, aplica la resta solo a las letras y deja intactos números y símbolos:

```python
def descifrar_vigenere(texto, clave):
    clave = clave.upper()
    resultado = []
    j = 0  # índice de la clave: solo avanza con letras
    for c in texto:
        if c.isalpha():
            k = ord(clave[j % len(clave)]) - ord('A')
            base = ord('a') if c.islower() else ord('A')
            resultado.append(chr((ord(c) - base - k) % 26 + base))
            j += 1
        else:
            resultado.append(c)  # dígitos y símbolos sin cambios
    return ''.join(resultado)

cifrado = "caldfow{O0NU_WQ3_G1G3O3T3_A1AH3S_4c372077}"
print(descifrar_vigenere(cifrado, "CYLAB"))
```

Corrí el script y obtuve la flag. También lo verifiqué con CyberChef usando la receta Vigenère Decode con la key CYLAB, que dio el mismo resultado.

### Herramientas usadas
Python 3
CyberChef (verificación)

### Flag
academy{D0NT_US3_V1G3N3R3_C1PH3R_4a372077}
### Qué aprendí / qué me costó
Entendí cómo funciona Vigenère: la clave se repite y cada letra se corre un valor distinto, lo que lo hace más fuerte que un César simple.
Reconocer el prefijo esperado de la flag (academy) sirve para verificar que vas por buen camino, incluso antes de descifrar todo.
El detalle que más me costó ver fue que los dígitos y símbolos no se cifran y que la clave no avanza con ellos. Si la clave avanzara con cada carácter, el resultado saldría mal.
En este caso la clave venía dada, pero si no, se podría recuperar conociendo parte del texto claro (K = C − P mod 26).

## 3. Insp3ct0r — picoCTF

**Categoría:** Web Exploitation

### Objetivo

El desafío daba una página web y había que encontrar la flag, que estaba partida en tres pedazos escondidos en el código fuente del sitio.

### Cómo lo resolví

Abrí la página (`http://xebec.cylabacademy.net:42345/`) y, con el **inspector de elementos de Chrome** (F12), revisé los tres archivos que cargaba el sitio. En cada uno había un comentario con una parte de la flag:

1. En el **HTML** (`index`):

   ```html
   <!-- Html is neat. Anyways have 1/3 of the flag: academy{tru3_d3 -->
   ```

2. En el **CSS** (`mycss.css`):

   ```css
   /* You need CSS to make pretty pages. Here's part 2/3 of the flag: t3ct1ve_0r_ju5t */
   ```

3. En el **JavaScript** (`myjs.js`):

   ```javascript
   /* Javascript sure is neat. Anyways part 3/3 of the flag: _lucky?d04ce271} */
   ```

Los comentarios estaban numerados (1/3, 2/3, 3/3), así que los uní en ese orden para armar la flag completa.

### Herramientas usadas

- Navegador Chrome
- DevTools / Inspector de elementos (pestañas Sources y Elements)

### Flag

```
academy{tru3_d3t3ct1ve_0r_ju5t_lucky?d04ce271}
```

### Qué aprendí / qué me costó

- Todo lo que el navegador muestra —HTML, CSS y JavaScript— se descarga al cliente y cualquiera lo puede leer. No existe "código oculto" del lado del navegador.
- Nunca hay que dejar datos sensibles en comentarios ni en el código del frontend: credenciales, claves o flags quedan a la vista de cualquier usuario.
- Lo más entretenido fue darme cuenta de que la flag estaba repartida en los tres archivos y había que juntarlos respetando el orden 1/3, 2/3 y 3/3.


## 4. GDB baby step 1 — Reverse Engineering

**Categoría:** Reverse Engineering
**Dificultad:** Media

### Objetivo

El desafío daba un binario (`debugger0_a`) y había que averiguar qué valor quedaba en el registro `eax` al final de la función `main`. La flag era ese valor en decimal, con el formato `academy{n}`.

### Cómo lo resolví

Primero descargué el binario y le di permisos de ejecución:

```bash
wget https://challenge-files.cylabacademy.net/.../debugger0_a
chmod +x debugger0_a
```

En x86, `eax` es el registro donde una función deja su **valor de retorno**, así que había que buscar lo último que se le escribe antes del `ret`. Para verlo usé **GDB**, desensamblando `main` sin necesidad de ejecutar el programa:

```bash
gdb debugger0_a
```

Dentro de GDB:

```
disassemble main
```

Salida:

```
Dump of assembler code for function main:
   ...
   0x...1138 <+15>:    mov    $0x86342,%eax
   0x...113d <+20>:    pop    %rbp
   0x...113e <+21>:    ret
End of assembler dump.
```

La instrucción relevante es `mov $0x86342,%eax`: carga el valor `0x86342` en `eax` justo antes del `pop %rbp` y el `ret`. Como ninguna otra instrucción toca `eax` después, ese es el valor final.

Solo faltaba pasarlo de hexadecimal a decimal:

```bash
python3 -c "print(0x86342)"
# 549698
```

### Herramientas usadas

- GDB (GNU Debugger)
- Python 3 (conversión hex → decimal)

### Flag

```
academy{549698}
```

### Qué aprendí / qué me costó

- Primer contacto con GDB: con `disassemble main` se lee el código ensamblador de una función sin tener que ejecutar el binario.
- Entendí que `eax` es el registro de retorno en x86, así que para saber qué devuelve una función hay que mirar qué se escribe ahí al final.
- El sintaxis AT&T de GDB pone el destino a la derecha (`mov origen, destino`), al revés de lo que esperaba. Confirmar que el `mov eax` estaba justo antes del `ret`, sin nada en el medio que modificara el registro, fue lo que había que mirar con cuidado.
- La flag pedía el número en decimal, así que hubo que convertir `0x86342` a `549698`.


## 6. Glory of the Garden — Forensics

**Categoría:** Forense
**Dificultad:** Fácil

### Objetivo

El desafío daba una imagen (un jardín) y había que encontrar una flag escondida dentro del archivo.

### Cómo lo resolví

Descargué la imagen y, en lugar de abrirla con un visor, miré su contenido en crudo. Usé **CyberChef** con la operación **To Hex**, que muestra todos los bytes del archivo.

Al recorrer la salida hasta el final, después de los datos de la imagen, apareció la flag en texto plano:

```
academy{more_than_m33ts_the_3y3caff56ca}
```

El mismo resultado se obtiene desde la terminal con `strings`, que extrae las cadenas de texto legibles de un archivo binario:

```bash
strings imagen.jpg | tail
```

La flag no estaba cifrada ni oculta con esteganografía real: estaba escrita tal cual al final del archivo. Un visor de imágenes lee solo hasta donde terminan los datos de la foto e ignora todo lo que viene después, así que la flag queda invisible al abrir la imagen, pero visible al inspeccionar los bytes. De ahí el nombre de la flag: *"more than meets the eye"* (hay más de lo que se ve a simple vista).

### Herramientas usadas

- CyberChef (operación To Hex)
- `strings` (alternativa por terminal)

### Flag

```
academy{more_than_m33ts_the_3y3caff56ca}
```

### Qué aprendí / qué me costó

- Un archivo de imagen puede tener datos extra después del contenido de la foto, y esos datos no se ven al abrirla normalmente.
- Herramientas simples como `strings` o un visor hexadecimal alcanzan para encontrar texto escondido dentro de un binario; no siempre hace falta algo complejo.
- Aprendí la diferencia entre *esconder* (poner algo donde no se mira) y *cifrar* (transformar el dato para que no se entienda). Acá la flag solo estaba escondida, no cifrada.