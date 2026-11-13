-- ForgeFit — migración incremental (rutina activa)
-- Correr esto en el SQL Editor de Supabase.
--
-- IMPORTANTE: este script es seguro de correr aunque ya tengas cuentas y datos
-- reales — usa "if not exists" en todo, así que NO borra ni pisa nada de lo
-- que ya tenés. NO vuelvas a correr el archivo schema.sql completo: ese
-- empieza con DROP TABLE y te borraría las cuentas de usuario que ya creaste.

-- Agrega la marca de "rutina activa": la rutina que el usuario eligió guardar
-- para que el resto de la app (Entrenar, Dietas, Compras, Hábitos) la use
-- como referencia, sin tener que regenerarla cada vez que cambia de sección.
alter table rutinas_generadas add column if not exists activa boolean not null default false;

create index if not exists idx_rutinas_usuario_activa on rutinas_generadas (user_id, activa);
