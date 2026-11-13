-- ForgeFit — esquema de base de datos MULTIUSUARIO para Supabase (Postgres)
-- Correr esto completo en el SQL Editor de tu proyecto de Supabase.
--
-- ADVERTENCIA: este script BORRA las tablas anteriores (de la versión sin
-- login) y las vuelve a crear con soporte multiusuario. Si tenías datos de
-- prueba cargados, se van a perder — no había forma de asociarlos a una
-- cuenta real porque no existían las cuentas todavía.

drop table if exists historial cascade;
drop table if exists rutinas_generadas cascade;
drop table if exists dietas_generadas cascade;
drop table if exists habitos_dia cascade;
drop table if exists habitos_config cascade;
drop table if exists medidas cascade;
drop table if exists fotos_progreso cascade;
drop table if exists perfil cascade;

-- ---------- Historial de cálculos ----------

create table historial (
    id bigint generated always as identity primary key,
    user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
    fecha timestamptz not null default now(),
    peso numeric not null,
    altura numeric not null,
    edad integer not null,
    sexo text not null check (sexo in ('masculino', 'femenino')),
    nivel_actividad text not null,
    objetivo text not null check (objetivo in ('bajar', 'mantener', 'subir')),
    imc numeric,
    categoria_imc text,
    tmb numeric,
    calorias_objetivo numeric,
    proteinas_g numeric,
    carbos_g numeric,
    grasas_g numeric,
    agua_litros numeric
);

-- ---------- Rutinas generadas ----------

create table rutinas_generadas (
    id bigint generated always as identity primary key,
    user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
    fecha timestamptz not null default now(),
    objetivo text not null check (objetivo in ('bajar', 'mantener', 'subir')),
    nivel text not null check (nivel in ('principiante', 'intermedio', 'avanzado')),
    dias_por_semana integer not null,
    plan jsonb not null
);

-- ---------- Dietas generadas ----------

create table dietas_generadas (
    id bigint generated always as identity primary key,
    user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
    fecha timestamptz not null default now(),
    calorias_objetivo numeric not null,
    proteinas_g numeric,
    carbos_g numeric,
    grasas_g numeric,
    plan jsonb not null
);

-- ---------- Hábitos diarios (una fila por usuario y día) ----------

create table habitos_dia (
    user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
    fecha date not null,
    completados jsonb not null default '[]'::jsonb,
    primary key (user_id, fecha)
);

-- ---------- Selección de hábitos (una fila por usuario) ----------

create table habitos_config (
    user_id uuid not null default auth.uid() references auth.users(id) on delete cascade primary key,
    seleccionados jsonb not null default '[]'::jsonb
);

-- ---------- Medidas corporales ----------

create table medidas (
    id bigint generated always as identity primary key,
    user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
    fecha timestamptz not null default now(),
    peso numeric,
    cintura numeric,
    cadera numeric,
    pecho numeric,
    brazo numeric,
    pierna numeric
);

-- ---------- Fotos de progreso ----------

create table fotos_progreso (
    id bigint generated always as identity primary key,
    user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
    fecha timestamptz not null default now(),
    imagen_base64 text not null,
    nota text
);

-- ---------- Perfil (una fila por usuario) ----------

create table if not exists perfil (
    user_id uuid not null default auth.uid() references auth.users(id) on delete cascade primary key,
    peso numeric,
    altura numeric,
    edad integer,
    sexo text,
    nivel_actividad text,
    objetivo text
);

-- ---------- Registro real de entrenamientos (series con peso/reps) ----------

create table if not exists registro_series (
    id bigint generated always as identity primary key,
    user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
    fecha timestamptz not null default now(),
    ejercicio text not null,
    grupo text not null,
    serie_numero integer not null,
    peso numeric not null,
    reps integer not null,
    es_pr boolean not null default false
);

-- ---------- Lista de compras ----------

create table if not exists lista_compras (
    user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
    item text not null,
    categoria text not null default 'almacen',
    comprado boolean not null default false,
    primary key (user_id, item)
);

-- ---------- Índices ----------

create index if not exists idx_historial_usuario_fecha on historial (user_id, fecha desc);
create index if not exists idx_rutinas_usuario_fecha on rutinas_generadas (user_id, fecha desc);
create index if not exists idx_dietas_usuario_fecha on dietas_generadas (user_id, fecha desc);
create index if not exists idx_medidas_usuario_fecha on medidas (user_id, fecha desc);
create index if not exists idx_fotos_usuario_fecha on fotos_progreso (user_id, fecha desc);
create index if not exists idx_series_usuario_fecha on registro_series (user_id, fecha desc);
create index if not exists idx_series_usuario_ejercicio on registro_series (user_id, ejercicio);

-- ---------- Row Level Security: cada usuario solo ve y modifica sus datos ----------

alter table historial enable row level security;
alter table rutinas_generadas enable row level security;
alter table dietas_generadas enable row level security;
alter table habitos_dia enable row level security;
alter table habitos_config enable row level security;
alter table medidas enable row level security;
alter table fotos_progreso enable row level security;
alter table perfil enable row level security;
alter table registro_series enable row level security;
alter table lista_compras enable row level security;

create policy "cada usuario ve y edita solo lo suyo" on historial
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "cada usuario ve y edita solo lo suyo" on rutinas_generadas
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "cada usuario ve y edita solo lo suyo" on dietas_generadas
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "cada usuario ve y edita solo lo suyo" on habitos_dia
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "cada usuario ve y edita solo lo suyo" on habitos_config
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "cada usuario ve y edita solo lo suyo" on medidas
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "cada usuario ve y edita solo lo suyo" on fotos_progreso
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "cada usuario ve y edita solo lo suyo" on perfil
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "cada usuario ve y edita solo lo suyo" on registro_series
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "cada usuario ve y edita solo lo suyo" on lista_compras
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
