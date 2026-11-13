-- ForgeFit — migración incremental (registro de entrenamientos + lista de compras)
-- Correr esto en el SQL Editor de Supabase.
--
-- IMPORTANTE: este script es seguro de correr aunque ya tengas cuentas y datos
-- reales — usa "if not exists" en todo, así que NO borra ni pisa nada de lo
-- que ya tenés. NO vuelvas a correr el archivo schema.sql completo: ese
-- empieza con DROP TABLE y te borraría las cuentas de usuario que ya creaste.

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

create index if not exists idx_series_usuario_fecha on registro_series (user_id, fecha desc);
create index if not exists idx_series_usuario_ejercicio on registro_series (user_id, ejercicio);

-- ---------- Row Level Security ----------

alter table registro_series enable row level security;
alter table lista_compras enable row level security;

drop policy if exists "cada usuario ve y edita solo lo suyo" on registro_series;
create policy "cada usuario ve y edita solo lo suyo" on registro_series
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "cada usuario ve y edita solo lo suyo" on lista_compras;
create policy "cada usuario ve y edita solo lo suyo" on lista_compras
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
