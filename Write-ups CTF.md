# Write-ups CTF — 5 desafíos
En este documento explico como resolvi los 5 ctf, es la primera vez que me enfrento a este tipo de desafios asi que voy a tomar niveles sencillos para adentrarme en el mundo.

## 2. MY GIT — picoCTF 2026

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


