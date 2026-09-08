# ForgeFit 🔥

App fitness con calculadora de métricas corporales, generador de rutinas y generador de dietas, con historial guardado en Supabase.

## Qué incluye

- **Calculadora**: IMC, TMB (Mifflin-St Jeor), calorías diarias objetivo, macros y agua recomendada.
- **Rutinas**: rutinas base según objetivo (bajar / mantener / subir), personalizables por nivel y días disponibles.
- **Dietas**: plan de comidas simple (desayuno/almuerzo/merienda/cena) ajustado a tus calorías objetivo.
- **Historial**: tabla y gráfico de evolución de tus cálculos guardados.

## 1. Instalación local

```bash
cd forgefit
python -m venv venv
source venv/bin/activate      # en Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Configurar Supabase

1. Andá a [supabase.com](https://supabase.com), creá una cuenta y un proyecto nuevo (es gratis).
2. Una vez creado el proyecto, andá a **SQL Editor** (en el menú lateral) → **New query**.
3. Copiá y pegá todo el contenido del archivo `schema.sql` (está en la raíz del proyecto) y ejecutalo (botón "Run"). Esto crea las tablas `historial`, `rutinas_generadas` y `dietas_generadas`.
4. Andá a **Project Settings** → **API**. Ahí vas a ver:
   - **Project URL** → esto va en `SUPABASE_URL`
   - **anon public key** → esto va en `SUPABASE_KEY`
5. En la raíz del proyecto, copiá el archivo `.env.example` y renombralo a `.env`:
   ```bash
   cp .env.example .env
   ```
6. Abrí `.env` y pegá tus datos:
   ```
   SUPABASE_URL=https://tu-proyecto.supabase.co
   SUPABASE_KEY=tu-api-key-copiada
   ```

**Importante:** el archivo `.env` nunca se sube a GitHub (ya está en `.gitignore`). Cada persona que use el proyecto necesita su propio `.env` con sus propias credenciales.

## 3. Correr la app

```bash
python app.py
```

Abrí tu navegador en **http://localhost:5000**

## Estructura del proyecto

```
forgefit/
├── app.py                  # rutas de Flask (páginas + API)
├── calculos.py              # fórmulas: IMC, TMB, calorías, macros, agua
├── rutinas.py                # lógica para armar rutinas de entrenamiento
├── dietas.py                 # lógica para armar el plan de comidas
├── database.py               # conexión y queries a Supabase
├── schema.sql                 # esquema de tablas para correr en Supabase
├── datos/
│   ├── ejercicios.json        # base de ejercicios por grupo muscular
│   └── alimentos.json          # base de alimentos con calorías/macros
├── templates/                 # páginas HTML (Jinja2)
├── static/
│   ├── style.css               # identidad visual
│   └── script.js                # lógica de frontend
├── requirements.txt
└── .env.example                # plantilla de variables de entorno
```

## Notas técnicas

- El **IMC** es una referencia general: no distingue masa muscular de grasa corporal.
- El **TMB** usa la fórmula de Mifflin-St Jeor, considerada la más precisa entre las fórmulas estándar sin equipamiento especial.
- Las **rutinas** combinan una plantilla base por objetivo con una selección de ejercicios filtrada por nivel (un nivel avanzado incluye ejercicios de niveles más básicos también).
- Las **dietas** escalan porciones de una base fija de alimentos para acercarse a las calorías objetivo — no reemplazan el consejo de un nutricionista, son una referencia práctica.
- Si todavía no configuraste Supabase, la calculadora y los generadores van a seguir funcionando igual (te van a mostrar el resultado), pero vas a ver un aviso de que no se pudo guardar el historial.
