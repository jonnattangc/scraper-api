# scraper-api

API REST de scraping como servicio, orientada a autenticar miembros de logias masónicas chilenas. Actúa como proxy de autenticación: recibe credenciales cifradas con AES, las valida primero en una base de datos MySQL local (caché) y, si no existen, ejecuta scraping headless en cascada contra múltiples plataformas externas.

---

## Stack tecnológico

| Tecnología | Version | Rol |
|---|---|---|
| **Python** | 3.13 | Runtime principal |
| **Flask** | 3.1.0 | Framework web HTTP, define rutas y levanta el servidor |
| **Flask-Cors** | 5.0.0 | Control de CORS (restringe orígenes permitidos en `/scraper/*`) |
| **Flask-HTTPAuth** | 4.8.0 | Autenticación HTTP Basic en endpoints protegidos |
| **Flask-WTF** | 1.2.2 | `CSRFProtect` (todos los endpoints están exentos de CSRF) |
| **Playwright** | 1.55.0 | Motor de scraping headless con Chromium |
| **pycryptodome** | 3.21.0 | Cifrado AES-CBC 256-bit para payloads (`Crypto.Cipher.AES`) |
| **PyMySQL** | 1.1.1 | Conector MySQL puro Python |
| **Werkzeug** | 3.1.3 | Hash y verificación de contraseñas (`generate_password_hash` / `check_password_hash`) |

---

## Arquitectura

El proyecto sigue una arquitectura en capas:

```
[ HTTP Routes (http-server.py) ]          Flask: define endpoints, decoradores de auth/CORS
          ↓
[ Services Layer ]                         Lógica de negocio y orquestación
  ├── security_service.py                  Autenticación HTTP Basic + preprocesamiento de requests
  ├── health_service.py                    Estado del servidor y BD
  ├── gran_logia_service.py               Endpoints /scraper/logia/*
  ├── bank_service.py                      Endpoints /scraper/bank/*
  └── login_service.py                     Verificación de usuarios (BD + cascada de scrapers)
          ↓
[ Scrapers Layer ]                         Playwright: scraping headless por sitio externo
  ├── base.py                              Clase abstracta BaseScraper
  ├── mimasoneria.py                       Scraper para mimasoneria.cl
  ├── elearn.py                            Scraper para elearning.granlogia.cl
  └── samqh.py                             Scraper para samqh.glch.cl
          ↓
[ Core Layer ]                             PyMySQL: acceso a MySQL como context manager
  └── database.py
          ↓
[ Utilities ]
  └── cipher.py                            AES-CBC 256-bit (cifrado de payloads)
```

---

## Autenticación

Los endpoints sensibles requieren **dos capas de autenticación simultáneas**:

1. **HTTP Basic Auth** — header `Authorization: Basic <base64(user:pass)>`. Las credenciales se verifican contra la tabla `oauth` en MySQL usando `Werkzeug check_password_hash`.
2. **API Key** — header `x-api-key: <key>`. Se verifica contra la variable de entorno `SERVER_API_KEY`.

El endpoint `/scraper/checkall` requiere solo HTTP Basic Auth.

---

## Cifrado de payloads

Los cuerpos de los requests en los endpoints de negocio viajan cifrados con **AES-CBC 256-bit** (`pycryptodome`).

- La clave AES se obtiene de la variable de entorno `AES_KEY` (32 bytes).
- El IV es fijo: `b'1234567890123456'`.
- El payload cifrado se envía como string base64 en el campo `data` del JSON.
- El servidor descifra con `Cipher.aes_decrypt()` antes de procesar.

Ejemplo de body de request:

```json
{ "data": "<AES_CBC_BASE64_ciphertext>" }
```

---

## Endpoints

### Información general

| Método | Ruta | Auth |
|---|---|---|
| `GET/POST` | `/scraper/info` | No |
| `GET` | `/scraper/checkall` | HTTP Basic |
| `GET/POST` | `/scraper` | No (redirige a `/info`) |
| `GET/POST` | `/scraper/<cualquier_ruta>` | No (redirige a `/info`) |

---

### `GET/POST /scraper/info`

Retorna información básica del servidor.

**Response 200:**
```json
{
  "Servidor": "dev.jonnattan.com",
  "Nombre": "API de Scrapper para distitnas cosas",
  "Docs": "proximamente"
}
```

---

### `GET /scraper/checkall`

Health check del servidor y la base de datos.

**Headers requeridos:** `Authorization: Basic <b64>`

**Response 200:**
```json
{
  "Server": "dev.jonnattan.com",
  "Owner": "Jonnattan Griffiths Catalan",
  "Files": true,
  "Data Base": true,
  "Time": 0.000123
}
```

- `Data Base`: booleano que indica si MySQL responde.
- `Time`: latencia de la comprobación en segundos (`time.monotonic()`).

---

### Endpoints `/scraper/logia/*`

Todos requieren: `Authorization: Basic <b64>` + `x-api-key: <key>`

El body de todos los requests es JSON con payload cifrado AES:
```json
{ "data": "<AES_CBC_BASE64_ciphertext>" }
```

---

#### `POST /scraper/logia/login`

Autentica un usuario validando sus credenciales. Implementa una **cascada de tres scrapers Playwright** con caché en MySQL.

**Payload descifrado:** `"usuario|||contraseña"`

**Flujo detallado:**

```
1. Flask recibe el request y verifica HTTP Basic Auth contra tabla `oauth` (PyMySQL + Werkzeug)
2. GranLogiaService valida el header x-api-key
3. Cipher.aes_decrypt() descifra el payload → "usuario|||contraseña"
4. LoginService.login_cascade(user, password):

   PASO 1 — Consulta caché MySQL:
     SELECT * FROM secure WHERE username = ?
     Si existe → check_password_hash → retorna (name, grade) inmediatamente

   PASO 2 — Cascada de scrapers Playwright (si no está en caché):

     Intento 1: Mimasoneria (mimasoneria.cl)
       → Playwright lanza Chromium headless
       → Navega a https://www.mimasoneria.cl/web/login
       → Rellena inputs XPath: //input[@id='login'], //input[@id='password']
       → Click en botón de login
       → Espera //img[@alt='Biblioteca'] (timeout 5000ms)
       → Detecta grado verificando presencia de 'Biblioteca Maestros' o 'Biblioteca Compañeros'
       → Si éxito: grade=3 (Maestro), grade=2 (Compañero), grade=1 (Aprendiz)

     Intento 2: Elearning (elearning.granlogia.cl) — si Mimasoneria falla
       → Playwright navega a https://elearning.granlogia.cl/login/index.php
       → Rellena username/password → click loginbtn
       → Espera botón de usuario → extrae nombre (4 primeras palabras)
       → Navega a página de cursos y detecta grado por XPath en la lista de cursos:
           [21] "Catecismo del Grado de Compañero" → grade=2
           [15] "Catecismo del Grado de Maestro"   → grade=3

     Intento 3: Samqh (samqh.glch.cl) — si Elearning falla
       → Playwright navega a https://samqh.glch.cl
       → Rellena id_sc_field_login / id_sc_field_pswd → click sub_form_b
       → Espera //a[@id='item_33'] → click → espera //span[@id='lin1_col2']
       → Extrae nombre (3 primeras palabras)
       → grade = 1 fijo (Aprendiz)

   Si los 3 scrapers fallan → 409 "El usuario es inválido"

5. Si algún scraper tiene éxito:
   → INSERT INTO secure (username, password_hash, grade, name, ...) — caché para próximas consultas
   → Retorna (name, grade, http_code=201)
```

**Response 200/201:**
```json
{
  "message": "Ok",
  "user": "rut_usuario",
  "grade": "3",
  "name": "Juan Carlos",
  "maintainer": false
}
```

- `grade`: `1`=Aprendiz, `2`=Compañero, `3`=Maestro, `0`=Inválido.

**Response 409:**
```json
{ "message": "El usuario es inválido" }
```

---

#### `POST /scraper/logia/grade`

Consulta el grado masónico de un usuario desde la caché MySQL. No realiza scraping.

**Payload descifrado:** `"rut_usuario"`

**Flujo:**
```
Cipher.aes_decrypt() → username
LoginService.get_grade(username):
  → SELECT * FROM secure WHERE username = ?
  → Si existe → retorna grade (1, 2 o 3)
  → Si no existe → 409
```

**Response 200:**
```json
{ "message": "Grado 3", "grade": "3" }
```

**Response 409:**
```json
{ "message": "Usuario no existe", "grade": "0" }
```

---

#### `POST /scraper/logia/access`

Verifica si un usuario tiene el grado mínimo requerido para acceder a un recurso.

**Payload descifrado:** `"rut_usuario&&grado_requerido"`

**Flujo:**
```
Cipher.aes_decrypt() → "rut_usuario&&2"
LoginService.validate_access(user, grade_requerido):
  → SELECT * FROM secure WHERE username = ?
  → Si grade_usuario >= grade_requerido → code=4500, 200
  → Si grade_usuario < grade_requerido → code=-1, 401
```

**Response 200:**
```json
{ "message": "Usuario es de grado 3", "code": "4500" }
```

**Response 401:**
```json
{ "message": "Usuario no autorizado", "code": "-1" }
```

---

#### `POST /scraper/logia/docs/url`

Genera una URL temporal/firmada para acceder a un documento PDF, con control de acceso por grado.

**Payload descifrado:** `"nombre_archivo.pdf;grado_requerido;rut_usuario"`

**Flujo:**
```
Cipher.aes_decrypt() → "manual.pdf;2;rut_usuario"
LoginService.validate_access(rut_usuario, "2"):
  → Si el usuario no tiene grado suficiente → 401

Cipher.aes_encrypt("manual.pdf") → ciphertext_base64
URL = "{proto}://{host}/logia/docs/pdf/{time.monotonic_ns()}/{ciphertext_base64}"
```

- El timestamp en nanosegundos (`time.monotonic_ns()`) hace la URL única.
- El nombre del documento va cifrado con AES en la URL.

**Response 200:**
```json
{ "url": "https://host/logia/docs/pdf/1234567890/abc123==" }
```

**Response 401:**
```json
{ "message": "Usuario no autorizado", "code": "-1" }
```

---

#### `POST /scraper/logia/saved`

Registra manualmente un usuario en la caché MySQL con grado 1 (Aprendiz).

**Payload descifrado:** `"usuario|||contraseña"`

**Flujo:**
```
Cipher.aes_decrypt() → "usuario|||contraseña"
INSERT INTO secure (username, password_hash, grade=1, name="Desconocido", ...)
```

**Response 201:**
```json
{ "Response": "Ok" }
```

**Response 500:**
```json
{ "message": "Error al guardar" }
```

---

### Endpoints `/scraper/bank/*`

Todos requieren: `Authorization: Basic <b64>` + `x-api-key: <key>`

A diferencia de los endpoints de logia, el body puede enviar el payload **cifrado o en texto claro**:

```json
{ "type": "encrypted", "data": "<AES_CBC_BASE64_ciphertext>" }
```
```json
{ "type": "plain", "data": { "username": "usuario", "password": "contraseña" } }
```

---

#### `POST /scraper/bank/login`

Autentica un usuario directamente en `mimasoneria.cl` mediante Playwright. No usa caché.

**Flujo:**
```
SecurityService.preproccess_request():
  → Valida x-api-key
  → Si type="encrypted": Cipher.aes_decrypt() → json.loads() → dict con username/password
  → Si type="plain": usa data directamente

Mimasoneria().login(username, password):
  → Playwright lanza Chromium headless
  → Flujo idéntico al scraper de Mimasoneria descrito en /logia/login
  → Retorna (grade, name)
```

**Response 200:**
```json
{
  "message": "Servicio ejecutado exitosamente",
  "grade": 2,
  "name": "Juan Carlos"
}
```

---

### `POST /scraper/cipher/test`

Endpoint de prueba para verificar el ciclo cifrar/descifrar AES. Requiere solo HTTP Basic Auth.

**Body:**
```json
{ "data": "texto a cifrar" }
```

**Flujo:**
```
Cipher.aes_encrypt(data) → ciphertext_base64
Cipher.aes_decrypt(ciphertext_base64) → texto original
```

**Response 200:**
```json
{
  "message": "Ok",
  "data_cipher": "<BASE64_ciphertext>",
  "data_clean": "texto a cifrar"
}
```

---

## Variables de entorno

Las variables se cargan desde un archivo externo (`../envs/file_scraper.env`, fuera del repositorio).

| Variable | Descripción |
|---|---|
| `AES_KEY` | Clave AES de 32 bytes para cifrado/descifrado de payloads |
| `SERVER_API_KEY` | Valor esperado en el header `x-api-key` |
| `HOST_BD` | Host del servidor MySQL |
| `PORT_BD` | Puerto MySQL (default: `3306`) |
| `USER_BD` | Usuario MySQL |
| `PASS_BD` | Contraseña MySQL |
| `SCHEMA_BD` | Schema/base de datos principal (default: `gral-purpose`) |

---

## Base de datos MySQL

| Tabla | Schema | Campos principales | Uso |
|---|---|---|---|
| `oauth` | `SCHEMA_BD` | `username`, `password` | Usuarios para HTTP Basic Auth |
| `secure` | `SCHEMA_BD` | `username`, `password`, `grade`, `name`, `maintainer` | Caché de hermanos autenticados |

---

## Despliegue con Docker

```bash
docker compose up -d
```

- **Imagen:** `jonnattangc/scraperservice:1.0.0`
- **Puerto:** `8090`
- **Red:** `db-net` (red Docker externa compartida con el contenedor MySQL)
- **Chromium:** instalado en la imagen en `PLAYWRIGHT_BROWSERS_PATH=/usr/local/share/playwright`
- **Usuario:** proceso corre como usuario no-root `jonnattan` (UID 10100)

---

## CORS

Las peticiones cross-origin solo se aceptan desde los siguientes orígenes en todas las rutas bajo `/scraper/*`:

- `dev.jonnattan.com`
- `logia.buenaventuracadiz.cl`
