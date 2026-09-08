# ForgeFit 🔥

App fitness multiusuario con calculadora de métricas corporales, generador de rutinas basado en evidencia científica, generador de dietas, seguimiento de hábitos, progreso corporal y un asistente de IA — todo con cuentas propias y datos privados por usuario.

## Qué incluye

- **Cuentas de usuario**: registro e inicio de sesión con Supabase Auth. Cada persona ve solo sus propios datos (protegido con Row Level Security a nivel de base de datos, no solo en el código).
- **Calculadora**: IMC, TMB (Mifflin-St Jeor), calorías diarias objetivo, macros y agua recomendada.
- **Rutinas**: divididas científicamente por volumen y frecuencia de entrenamiento, basadas en metaanálisis de Schoenfeld et al. (2017, 2019) y las guías ACSM (2009/2026). El volumen de fuerza se mantiene igual en "bajar peso" que en "mantener" (la evidencia muestra que reducirlo durante un déficit no ayuda a preservar músculo), sumando cardio aparte. Cada rutina muestra el volumen semanal real por grupo muscular y un link para ver la técnica correcta de cada ejercicio en YouTube.
- **Dietas**: plan de comidas simple (desayuno/almuerzo/merienda/cena) ajustado a tus calorías objetivo.
- **Hábitos**: elegí tus propios hábitos físicos y mentales de un catálogo de 16, marcalos cada día y mirá tu anillo de progreso llenarse. Incluye racha de días consecutivos y medallas por hitos.
- **Progreso**: resumen semanal automático, registro de medidas corporales con gráfico de evolución, y galería de fotos de progreso.
- **Historial**: tabla y gráfico de evolución de tus cálculos guardados.
- **Asistente ForgeFit**: chat flotante con IA (Claude) para responder dudas de entrenamiento y nutrición. Opcional — funciona sin él, pero necesita su propia clave de API.
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

## 3. (Opcional) Activar el asistente de IA

1. Creá una cuenta en [console.anthropic.com](https://console.anthropic.com) y generá una API key.
2. Agregala a tu `.env`:
   ```
   ANTHROPIC_API_KEY=tu-clave-de-anthropic
   ```
   Si no configurás esto, el resto de la app funciona igual — el chat solo va a mostrar un aviso pidiendo la clave cuando lo abras.

## 4. Correr la app

```bash
python app.py
```

Abrí tu navegador en **http://localhost:5000** — te va a pedir crear una cuenta o iniciar sesión antes de ver la app.

## Estructura del proyecto

```
forgefit/
├── app.py                  # rutas de Flask (páginas + API) y protección de sesión
├── auth.py                  # registro / login / logout con Supabase Auth
├── asistente.py              # chat con IA (Claude) para dudas de fitness
├── calculos.py                # fórmulas: IMC, TMB, calorías, macros, agua
├── rutinas.py                  # generador de rutinas basado en evidencia científica
├── dietas.py                    # lógica para armar el plan de comidas
├── habitos.py                    # catálogo, selección, racha y logros de hábitos
├── resumen.py                     # cálculo del resumen semanal
├── database.py                     # conexión a Supabase, cada función recibe el token del usuario
├── schema.sql                       # esquema multiusuario con Row Level Security
├── datos/
│   ├── ejercicios.json                # ejercicios clasificados compuesto/aislamiento/cardio
│   ├── alimentos.json                  # base de alimentos con calorías/macros
│   └── habitos.json                     # catálogo de hábitos físicos y mentales
├── templates/                             # páginas HTML (Jinja2), incluye login/signup
├── static/
│   ├── style.css                           # identidad visual
│   └── script.js                            # lógica de frontend
├── requirements.txt
└── .env.example                             # plantilla de variables de entorno
```

## Notas técnicas

- **Seguridad multiusuario**: cada tabla en Supabase tiene Row Level Security (RLS) activado con una política que compara `auth.uid()` contra el `user_id` de cada fila. Esto significa que aunque alguien consiga la anon key de tu proyecto, no puede leer ni escribir datos de otro usuario — la restricción vive en la base de datos, no solo en el código de la app.
- El **IMC** es una referencia general: no distingue masa muscular de grasa corporal.
- El **TMB** usa la fórmula de Mifflin-St Jeor.
- Las **rutinas** siguen recomendaciones de volumen (10+ series semanales por músculo para hipertrofia) y frecuencia según metaanálisis de Schoenfeld et al., con rangos de reps/descanso según ACSM. El link de "ver técnica" abre una búsqueda de YouTube, no un video específico verificado — usalo como punto de partida, no como única fuente.
- El **asistente de IA** no reemplaza a un profesional. Está configurado para sugerir consultar a un médico/nutricionista/entrenador ante dudas que requieran evaluación individual.
- Si todavía no configuraste Supabase, la calculadora y los generadores van a seguir funcionando igual (te van a mostrar el resultado), pero vas a ver un aviso de que no se pudo guardar.

