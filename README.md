# ForgeFit 🔥

App fitness multiusuario con calculadora de métricas corporales, generador de rutinas basado en evidencia científica, generador de dietas, seguimiento de hábitos, progreso corporal y un asistente de IA — todo con cuentas propias y datos privados por usuario.

## Qué incluye

- **Cuentas de usuario**: registro e inicio de sesión con Supabase Auth. Cada persona ve solo sus propios datos (protegido con Row Level Security a nivel de base de datos, no solo en el código).
- **Calculadora**: IMC, TMB (Mifflin-St Jeor), calorías diarias objetivo, macros y agua recomendada.
- **Rutinas**: divididas científicamente por volumen y frecuencia de entrenamiento, basadas en metaanálisis de Schoenfeld et al. (2017, 2019) y las guías ACSM (2009/2026). El volumen de fuerza se mantiene igual en "bajar peso" que en "mantener" (la evidencia muestra que reducirlo durante un déficit no ayuda a preservar músculo), sumando cardio aparte. Cada rutina muestra el volumen semanal real por grupo muscular y un GIF con la técnica de cada ejercicio.
- **Dietas**: plan de comidas simple (desayuno/almuerzo/merienda/cena) ajustado a tus calorías objetivo.
- **Hábitos**: elegí tus propios hábitos físicos y mentales de un catálogo de 16, marcalos cada día y mirá tu anillo de progreso llenarse. Incluye racha de días consecutivos y medallas por hitos.
- **Progreso**: resumen semanal automático, registro de medidas corporales con gráfico de evolución, y galería de fotos de progreso.
- **Historial**: tabla y gráfico de evolución de tus cálculos guardados.
- **Entrenar**: registro real de series con peso y repeticiones (no solo el plan sugerido), con detección automática de récords personales (usando la fórmula de Epley para estimar tu 1RM) y timer de descanso automático entre series.
- **Compras**: lista de compras agrupada por categoría, generada automáticamente desde tu último plan de dieta.
- **Analytics** (dentro de Progreso): gráfico de progresión de fuerza por ejercicio, volumen semanal real comparado contra el rango recomendado por la evidencia, y un calendario tipo mapa de calor de tus últimas 12 semanas de constancia.
- **App instalable (PWA)**: podés instalar ForgeFit en tu celular o compu como una app, con un ícono propio y funcionamiento básico offline para los archivos estáticos.
- **Asistente ForgeFit**: chat flotante con IA (Groq / Llama) para responder dudas de entrenamiento y nutrición. Opcional — funciona sin él, pero necesita su propia clave de API.
- **Modo claro/oscuro**, exportar rutinas/dietas a PDF, y recordatorio si no cargaste tu cálculo del día.

## 1. Instalación local

```bash
cd forgefit
python -m venv venv
source venv/bin/activate      # en Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Configurar Supabase (con autenticación)

1. Andá a [supabase.com](https://supabase.com), creá una cuenta y un proyecto nuevo.
2. En **SQL Editor** → **New query**, pegá y ejecutá **todo** el contenido de `schema.sql`. 

   ⚠️ **Este script borra las tablas de la versión anterior sin login** (si tenías datos de prueba cargados, se pierden — no había forma de asociarlos a una cuenta real porque las cuentas no existían todavía).

3. Andá a **Authentication** → **Providers** en el menú de Supabase y confirmá que **Email** esté habilitado (viene activado por defecto).
   - Si querés que cualquiera pueda registrarse sin confirmar el email (más simple para probar), andá a **Authentication** → **Settings** y desactivá "Confirm email". Si lo dejás activado, cada persona que se registre va a recibir un mail de confirmación antes de poder iniciar sesión.
4. Andá a **Project Settings** → **API** y copiá tu **Project URL** y tu **anon public key**.
5. Copiá `.env.example` a `.env`:
   ```bash
   cp .env.example .env
   ```
6. Completá `.env`:
   ```
   SUPABASE_URL=https://tu-proyecto.supabase.co
   SUPABASE_KEY=tu-api-key-anon-publica
   FLASK_SECRET_KEY=generá-un-texto-random-largo-acá
   ```
   Para generar una clave random para `FLASK_SECRET_KEY`, corré en una terminal:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

## 3. Si ya tenías la app instalada: sumá las tablas nuevas

Si ya veías registrando cálculos, rutinas o hábitos, **no vuelvas a correr `schema.sql` completo** (empieza con `DROP TABLE` y te borraría las cuentas y datos que ya tenés). En su lugar, corré solo el archivo `migracion_entrenamiento.sql` en el SQL Editor de Supabase — es seguro, no borra nada, solo agrega las tablas `registro_series` y `lista_compras`.

## 4. (Opcional) Activar el asistente de IA

1. Creá una cuenta gratis en [console.groq.com](https://console.groq.com) y generá una API key.
2. Agregala a tu `.env`:
   ```
   GROQ_API_KEY=tu-clave-de-groq
   ```
   Si no configurás esto, el resto de la app funciona igual — el chat solo va a mostrar un aviso pidiendo la clave cuando lo abras.
   Por defecto usa el modelo `llama-3.3-70b-versatile`; si querés otro, agregá `GROQ_MODEL=...` al `.env`.

## 5. Correr la app

```bash
python app.py
```

Abrí tu navegador en **http://localhost:5000** — te va a pedir crear una cuenta o iniciar sesión antes de ver la app.

## Estructura del proyecto

```
forgefit/
├── app.py                  # rutas de Flask (páginas + API) y protección de sesión
├── auth.py                  # registro / login / logout con Supabase Auth
├── asistente.py              # chat con IA (Groq) para dudas de fitness
├── calculos.py                # fórmulas: IMC, TMB, calorías, macros, agua
├── rutinas.py                  # generador de rutinas basado en evidencia científica
├── dietas.py                    # lógica para armar el plan de comidas
├── habitos.py                    # catálogo, selección, racha y logros de hábitos
├── entrenamiento.py                # PRs, progresión de fuerza, volumen real, calendario
├── compras.py                        # lista de compras agrupada por categoría
├── resumen.py                     # cálculo del resumen semanal
├── database.py                     # conexión a Supabase, cada función recibe el token del usuario
├── schema.sql                       # esquema multiusuario con Row Level Security
├── migracion_entrenamiento.sql       # migración no destructiva (tablas de entrenamiento/compras)
├── datos/
│   ├── ejercicios.json                # ejercicios clasificados compuesto/aislamiento/cardio
│   ├── alimentos.json                  # base de alimentos con calorías/macros
│   └── habitos.json                     # catálogo de hábitos físicos y mentales
├── templates/                             # páginas HTML (Jinja2), incluye login/signup
├── public/                                # lo que Vercel sirve directo desde su CDN
│   ├── sw.js                               # service worker (cachea archivos estáticos)
│   └── static/
│       ├── style.css                        # identidad visual
│       ├── script.js                         # lógica de frontend
│       ├── manifest.json                      # configuración de la PWA
│       ├── icons/                              # íconos de la app instalable
│       └── gifs/                                # GIFs de los ejercicios + index.json
├── scripts/generar_gifs.py                   # regenera los GIFs si agregás ejercicios
├── vercel.json / .python-version              # configuración de Vercel
├── requirements.txt
└── .env.example                             # plantilla de variables de entorno
```

## Notas técnicas

- **Seguridad multiusuario**: cada tabla en Supabase tiene Row Level Security (RLS) activado con una política que compara `auth.uid()` contra el `user_id` de cada fila. Esto significa que aunque alguien consiga la anon key de tu proyecto, no puede leer ni escribir datos de otro usuario — la restricción vive en la base de datos, no solo en el código de la app.
- El **IMC** es una referencia general: no distingue masa muscular de grasa corporal.
- El **TMB** usa la fórmula de Mifflin-St Jeor.
- Las **rutinas** siguen recomendaciones de volumen (10+ series semanales por músculo para hipertrofia) y frecuencia según metaanálisis de Schoenfeld et al., con rangos de reps/descanso según ACSM. Los GIFs de técnica vienen de ExerciseDB.
- El **registro de entrenamientos** detecta récords personales estimando tu 1RM con la fórmula de Epley (peso × (1 + reps/30)) y comparándolo contra tu mejor marca histórica en ese ejercicio.
- El **service worker** (PWA) es deliberadamente conservador: solo cachea archivos estáticos (CSS, JS, íconos). Nunca cachea páginas HTML ni respuestas de la API, para evitar mostrarte información vieja o interferir con el login.
- El **asistente de IA** no reemplaza a un profesional. Está configurado para sugerir consultar a un médico/nutricionista/entrenador ante dudas que requieran evaluación individual.
- Si todavía no configuraste Supabase, la calculadora y los generadores van a seguir funcionando igual (te van a mostrar el resultado), pero vas a ver un aviso de que no se pudo guardar.


## GIFs de ejercicios

Cada ejercicio de **Rutinas** y de **Entrenar** tiene un botón ▶ que abre un GIF con la posición inicial y final del movimiento.
Los 40 GIFs ya vienen dentro del proyecto (`public/static/gifs/`), así que no dependen de ninguna API externa y funcionan igual en tu PC y en Vercel.

Se generaron con `scripts/generar_gifs.py` a partir de las fotos del catálogo público
[free-exercise-db](https://github.com/yuhonas/free-exercise-db) (dominio público). Si agregás ejercicios nuevos en
`datos/ejercicios.json`, sumá su nombre en inglés en `CATALOGO` (dentro del script) y corré:

```bash
pip install pillow
python scripts/generar_gifs.py
```

## Subirlo a Vercel

1. **Subí la carpeta a GitHub** (repositorio privado). El `.gitignore` ya deja afuera tu `.env`, así que tus claves no se suben.
   ```bash
   git init
   git add .
   git commit -m "ForgeFit"
   git branch -M main
   git remote add origin https://github.com/TU-USUARIO/forgefit.git
   git push -u origin main
   ```
2. En [vercel.com](https://vercel.com) → **Add New… → Project** → importá ese repositorio. Vercel detecta Flask solo (usa `app.py`, `requirements.txt`, `.python-version` y `vercel.json`); no hace falta tocar nada del build.
3. Antes de tocar **Deploy**, abrí **Environment Variables** y cargá estas (los mismos valores de tu `.env`):

   | Nombre | Valor |
   |---|---|
   | `SUPABASE_URL` | la URL de tu proyecto de Supabase |
   | `SUPABASE_KEY` | la clave anon (`eyJ...`) |
   | `FLASK_SECRET_KEY` | un texto largo y random (obligatorio: si no, las sesiones se rompen) |
   | `GROQ_API_KEY` | tu clave de Groq (opcional, solo para el asistente) |

4. **Deploy.** Cuando termine, abrí la URL que te da Vercel e iniciá sesión con tu cuenta de siempre.

Notas:
- Cada vez que hagas `git push`, Vercel vuelve a desplegar solo.
- En Vercel los guardados se hacen antes de responder (no hay hilos en segundo plano), así que puede sentirse un poquito más lento que en tu PC.
- Vercel limita cada respuesta a 4,5 MB; por eso la galería de progreso muestra las últimas 20 fotos.
- Los proyectos gratis de Supabase se pausan tras ~7 días sin uso: si el login da `getaddrinfo failed`, entrá a supabase.com y tocá **Restore**.
