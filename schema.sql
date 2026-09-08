-- ForgeFit — esquema de base de datos para Supabase (Postgres)
-- Correr esto en el editor SQL de tu proyecto de Supabase (SQL Editor > New query)

create table if not exists historial (
    id bigint generated always as identity primary key,
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

create table if not exists rutinas_generadas (
    id bigint generated always as identity primary key,
    fecha timestamptz not null default now(),
    objetivo text not null check (objetivo in ('bajar', 'mantener', 'subir')),
    nivel text not null check (nivel in ('principiante', 'intermedio', 'avanzado')),
    dias_por_semana integer not null,
    plan jsonb not null
);

create table if not exists dietas_generadas (
    id bigint generated always as identity primary key,
    fecha timestamptz not null default now(),
    calorias_objetivo numeric not null,
    proteinas_g numeric,
    carbos_g numeric,
    grasas_g numeric,
    plan jsonb not null
);

-- Índices para ordenar por fecha rápido en el historial
create index if not exists idx_historial_fecha on historial (fecha desc);
create index if not exists idx_rutinas_fecha on rutinas_generadas (fecha desc);
create index if not exists idx_dietas_fecha on dietas_generadas (fecha desc);
