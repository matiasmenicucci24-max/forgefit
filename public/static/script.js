// ============================================
// ForgeFit — lógica de frontend
// ============================================

// ---------- Service worker (PWA) e instalación ----------

if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
        navigator.serviceWorker.register("/sw.js").catch(() => {
            // Si falla el registro, la app sigue funcionando normal sin PWA.
        });
    });
}

let eventoInstalacionPendiente = null;

window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    eventoInstalacionPendiente = e;
    mostrarBannerInstalar();
});

function mostrarBannerInstalar() {
    const main = document.querySelector(".main");
    if (!main || document.querySelector(".instalar-banner")) return;

    const banner = document.createElement("div");
    banner.className = "instalar-banner";
    banner.innerHTML = `
        <span>📲 Instalá ForgeFit como app en tu celular o compu.</span>
        <button type="button" id="btn-instalar-pwa">Instalar</button>
    `;
    main.prepend(banner);

    banner.querySelector("#btn-instalar-pwa").addEventListener("click", async () => {
        if (!eventoInstalacionPendiente) return;
        eventoInstalacionPendiente.prompt();
        await eventoInstalacionPendiente.userChoice;
        eventoInstalacionPendiente = null;
        banner.remove();
    });
}

// ---------- Tema claro / oscuro ----------

function inicializarTema() {
    const guardado = localStorage.getItem("forgefit-theme") || "dark";
    document.documentElement.setAttribute("data-theme", guardado);

    const sidebar = document.querySelector(".sidebar");
    if (!sidebar) return;

    const boton = document.createElement("button");
    boton.className = "theme-toggle";
    boton.innerHTML = iconoTema(guardado);
    boton.addEventListener("click", () => {
        const actual = document.documentElement.getAttribute("data-theme") || "dark";
        const nuevo = actual === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", nuevo);
        localStorage.setItem("forgefit-theme", nuevo);
        boton.innerHTML = iconoTema(nuevo);
    });

    const footer = sidebar.querySelector(".sidebar-footer");
    sidebar.insertBefore(boton, footer || null);
}

function iconoTema(tema) {
    if (tema === "dark") {
        return `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M1 12h2M21 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4"/></svg> Modo claro`;
    }
    return `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z"/></svg> Modo oscuro`;
}

inicializarTema();
inicializarBannerRutinaActiva();

// Banner compartido (Dietas, Compras, Hábitos) que muestra la rutina activa
// del usuario, para que sepa en base a qué objetivo está trabajando el resto
// de la app sin tener que ir a mirar la sección Rutinas. No hace nada si la
// página actual no tiene el contenedor (ej. Calculadora, Entrenar, etc.).
async function inicializarBannerRutinaActiva() {
    const contenedor = document.getElementById("banner-rutina-activa");
    if (!contenedor) return;

    const data = await getJSON("/api/rutinas/activa");
    const NOMBRES_OBJETIVO = { bajar: "Bajar peso", mantener: "Mantener", ganar: "Ganar masa" };

    if (!data.rutina) {
        contenedor.innerHTML = `<div class="banner-rutina">
            <span>Todavía no tenés una rutina activa guardada.</span>
            <a href="/rutinas" class="banner-rutina-link">Generar una rutina →</a>
        </div>`;
        return;
    }

    const r = data.rutina;
    const objetivo = NOMBRES_OBJETIVO[r.objetivo] || r.objetivo;
    contenedor.innerHTML = `<div class="banner-rutina">
        <span>📋 Rutina activa: <strong>${objetivo}</strong> · ${r.dias_por_semana} días/semana · nivel ${r.nivel}</span>
        <a href="/rutinas" class="banner-rutina-link">Cambiar rutina →</a>
    </div>`;
}

// ---------- Helpers ----------

async function postJSON(url, data) {
    try {
        const resp = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        return await resp.json();
    } catch (e) {
        // Si el servidor no respondió con JSON (caída de red, servidor reiniciando,
        // etc.) devolvemos un error prolijo en vez de romper la página entera.
        return { error: "No se pudo conectar con el servidor. Revisá tu conexión y probá de nuevo." };
    }
}

async function getJSON(url) {
    try {
        const resp = await fetch(url);
        return await resp.json();
    } catch (e) {
        return { error: "No se pudo conectar con el servidor. Revisá tu conexión y probá de nuevo." };
    }
}

function setupSegmented(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.querySelectorAll("button").forEach((btn) => {
        btn.addEventListener("click", () => {
            container.querySelectorAll("button").forEach((b) => b.classList.remove("selected"));
            btn.classList.add("selected");
        });
    });
}

function getSelectedValue(containerId) {
    const container = document.getElementById(containerId);
    const selected = container.querySelector("button.selected");
    return selected ? selected.dataset.value : null;
}

const RING_CIRCUMFERENCE = 2 * Math.PI * 46; // r=46 en el SVG de los anillos

// Colores de Chart.js según el tema activo — antes estaban fijos en los tonos
// del modo oscuro, así que en modo claro el texto de los gráficos (gris muy
// claro) quedaba invisible sobre el fondo blanco de la tarjeta.
function coloresGrafico() {
    const claro = document.documentElement.getAttribute("data-theme") === "light";
    return {
        texto: claro ? "#3A362F" : "#F5F3EF",
        grilla: claro ? "#DEDACE" : "#23262F",
        subtexto: claro ? "#746F63" : "#8A8F9C",
    };
}

function setRing(id, pct) {
    const el = document.getElementById(id);
    if (!el) return;
    const offset = RING_CIRCUMFERENCE - (Math.min(pct, 100) / 100) * RING_CIRCUMFERENCE;
    // pequeño delay para que la transición CSS se note al cargar
    requestAnimationFrame(() => {
        el.style.strokeDasharray = RING_CIRCUMFERENCE;
        el.style.strokeDashoffset = offset;
    });
}

// Íconos por tipo de comida (mismo set de trazo que el resto de la UI)
const ICONOS_COMIDA = {
    desayuno: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M1 12h2M21 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4"/></svg>',
    almuerzo: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 2v6a2 2 0 0 0 2 2v12M11 2v8M15 2c-1 1-1 3-1 5s0 4 1 5v10"/></svg>',
    merienda: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2s6 7 6 12a6 6 0 1 1-12 0c0-5 6-12 6-12z"/></svg>',
    cena: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v9M8 21h8M12 12a5 5 0 0 0 5-5V4H7v3a5 5 0 0 0 5 5z"/></svg>',
};

// ============================================
// Página: Calculadora (index.html)
// ============================================

const formCalculo = document.getElementById("form-calculo");
if (formCalculo) {
    setupSegmented("segmented-objetivo");
    precargarPerfil();
    verificarRecordatorioDiario();

    formCalculo.addEventListener("submit", async (e) => {
        e.preventDefault();

        const payload = {
            peso: document.getElementById("peso").value,
            altura: document.getElementById("altura").value,
            edad: document.getElementById("edad").value,
            sexo: document.getElementById("sexo").value,
            nivel_actividad: document.getElementById("nivel_actividad").value,
            objetivo: getSelectedValue("segmented-objetivo") || "mantener",
        };

        const resultado = await postJSON("/api/calcular", payload);

        if (resultado.error) {
            alert(resultado.error);
            return;
        }

        document.getElementById("resultado-card").style.display = "block";
        document.getElementById("res-imc").textContent = resultado.imc;
        document.getElementById("res-imc-cat").textContent = `IMC · ${resultado.categoria_imc}`;
        document.getElementById("res-calorias").textContent = `${resultado.calorias_objetivo}`;
        document.getElementById("res-agua").textContent = `${resultado.agua_litros} L`;

        const calProt = resultado.proteinas_g * 4;
        const calCarb = resultado.carbos_g * 4;
        const calGrasa = resultado.grasas_g * 9;
        const totalMacroCal = calProt + calCarb + calGrasa;

        const pctProt = Math.round((calProt / totalMacroCal) * 100);
        const pctCarb = Math.round((calCarb / totalMacroCal) * 100);
        const pctGrasa = Math.round((calGrasa / totalMacroCal) * 100);

        document.getElementById("val-proteina").textContent = resultado.proteinas_g;
        document.getElementById("val-carbos").textContent = resultado.carbos_g;
        document.getElementById("val-grasas").textContent = resultado.grasas_g;

        document.getElementById("pct-proteina").textContent = `${pctProt}% de tus calorías`;
        document.getElementById("pct-carbos").textContent = `${pctCarb}% de tus calorías`;
        document.getElementById("pct-grasas").textContent = `${pctGrasa}% de tus calorías`;

        setRing("ring-proteina", pctProt);
        setRing("ring-carbos", pctCarb);
        setRing("ring-grasas", pctGrasa);

        document.getElementById("resultado-card").scrollIntoView({ behavior: "smooth", block: "start" });
    });
}

async function precargarPerfil() {
    const data = await getJSON("/api/perfil");
    const perfil = data.perfil;
    if (!perfil) return;

    if (perfil.altura) document.getElementById("altura").value = perfil.altura;
    if (perfil.edad) document.getElementById("edad").value = perfil.edad;
    if (perfil.sexo) document.getElementById("sexo").value = perfil.sexo;
    if (perfil.nivel_actividad) document.getElementById("nivel_actividad").value = perfil.nivel_actividad;
    // El peso y el objetivo se dejan en blanco a propósito: son los datos que
    // más cambian de una vez a otra, así que se cargan frescos cada vez.
}

async function verificarRecordatorioDiario() {
    const hoy = new Date().toISOString().slice(0, 10);
    const dismissKey = `forgefit-dismiss-reminder-${hoy}`;
    if (localStorage.getItem(dismissKey)) return;

    const historial = await getJSON("/api/historial");
    if (historial.error || !Array.isArray(historial)) return;

    const yaCalculoHoy = historial.some((h) => (h.fecha || "").slice(0, 10) === hoy);
    if (yaCalculoHoy) return;

    mostrarBannerRecordatorio(dismissKey);
}

function mostrarBannerRecordatorio(dismissKey) {
    const hero = document.querySelector(".page-hero");
    if (!hero) return;

    const banner = document.createElement("div");
    banner.className = "reminder-banner";
    banner.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 9v4M12 17h.01M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/></svg>
        <span>Todavía no cargaste tu cálculo de hoy.</span>
        <button type="button" class="reminder-close" aria-label="Cerrar">✕</button>
    `;
    banner.querySelector(".reminder-close").addEventListener("click", () => {
        localStorage.setItem(dismissKey, "1");
        banner.remove();
    });
    hero.insertAdjacentElement("afterend", banner);
}

// ============================================
// Página: Rutinas (rutinas.html)
// ============================================

const formRutina = document.getElementById("form-rutina");
if (formRutina) {
    setupSegmented("segmented-objetivo-rutina");
    cargarUltimaRutina();

    formRutina.addEventListener("submit", async (e) => {
        e.preventDefault();

        const payload = {
            objetivo: getSelectedValue("segmented-objetivo-rutina") || "mantener",
            nivel: document.getElementById("nivel").value,
            dias_por_semana: document.getElementById("dias").value,
        };

        const rutina = await postJSON("/api/rutinas/generar", payload);
        if (rutina.error) {
            alert(rutina.error);
            return;
        }
        renderRutina(rutina);
    });
}

// Al entrar (o volver) a la página, recupera la última rutina generada, para
// que no "desaparezca" al navegar a otra sección y volver — antes esto no se
// hacía y el resultado solo vivía en memoria mientras durara la página.
async function cargarUltimaRutina() {
    // Muestra la rutina ACTIVA (la que el usuario eligió guardar), no
    // simplemente la última generada — así, si generó varias para comparar,
    // al volver a la página sigue viendo la que realmente eligió usar.
    const data = await getJSON("/api/rutinas/activa");
    if (data.rutina) {
        renderRutina(data.rutina);
    }
}

async function activarRutina(id) {
    const resultado = await postJSON("/api/rutinas/activar", { id });
    if (resultado.error) {
        alert(resultado.error);
        return;
    }
    cargarUltimaRutina();
}

function renderRutina(rutina) {
    const contenedor = document.getElementById("resultado-rutina");

    let botonActivar = "";
    if (rutina.activa) {
        botonActivar = `<span class="badge-activa no-print">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
            Tu rutina activa
        </span>`;
    } else if (rutina.id) {
        botonActivar = `<button type="button" class="btn-secondary no-print" style="width:auto; margin-top:0;" onclick="activarRutina(${rutina.id})">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><path d="M17 21v-8H7v8M7 3v5h8"/></svg>
            Guardar como mi rutina activa
        </button>`;
    }

    let html = `<div class="card">
        <div class="habitos-header-row">
            <h2 class="card-title" style="margin-bottom:0;">
                <span class="card-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6.5 6.5l11 11M4 9l3-3 2 2-3 3-2-2zm9 9l3-3 2 2-3 3-2-2zM2 22l4-4M18 6l4-4"/></svg></span>
                Tu rutina — ${rutina.dias_por_semana} días/semana · nivel ${rutina.nivel}
            </h2>
            <div class="no-print" style="display:flex; gap:10px; align-items:center;">
                ${botonActivar}
                <button type="button" class="btn-secondary no-print" style="width:auto; margin-top:0;" onclick="window.print()">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9V2h12v7M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2M6 14h12v8H6z"/></svg>
                    Descargar PDF
                </button>
            </div>
        </div>
        <p style="color:var(--stone); font-size:0.9rem; margin-top:-10px; margin-bottom:20px;">${rutina.descripcion}</p>`;

    rutina.plan.forEach((dia) => {
        html += `<div class="dia-plan">
            <h3><span class="dia-badge">Día ${dia.dia}</span></h3>
            <div class="grupos">${dia.grupos.map((g) => `<span class="grupo-tag">${g}</span>`).join("")}</div>`;

        dia.ejercicios.forEach((ej) => {
            const detalle = ej.grupo === "cardio" ? ej.reps : `${ej.series} × ${ej.reps} · ${ej.descanso}`;
            const botonGif = botonGifHTML(ej.nombre);
            html += `<div class="ejercicio-row">
                <span class="ej-dot"></span>
                <span class="nombre">${ej.nombre}${botonGif}</span>
                <span class="detalle">${detalle}</span>
            </div>`;
        });

        html += `</div>`;
    });

    if (rutina.volumen_semanal) {
        html += `<div class="volumen-semanal">
            <div class="volumen-titulo">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18M7 14l4-4 3 3 5-6"/></svg>
                Volumen semanal por grupo muscular
            </div>
            <div class="volumen-chips">
                ${Object.entries(rutina.volumen_semanal).map(([grupo, series]) => {
                    const nivel = series >= 10 ? "alto" : series >= 6 ? "medio" : "bajo";
                    return `<span class="volumen-chip volumen-${nivel}">${grupo}: ${series} series</span>`;
                }).join("")}
            </div>
            <p class="volumen-nota">10+ series semanales por músculo es el rango asociado a mejores resultados de hipertrofia en la evidencia científica actual.</p>
        </div>`;
    }

    if (rutina.fuente) {
        html += `<p class="fuente-cientifica">${rutina.fuente}</p>`;
    }

    html += `</div>`;
    contenedor.innerHTML = html;
    contenedor.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ============================================
// Página: Dietas (dietas.html)
// ============================================

const formDieta = document.getElementById("form-dieta");
let variacionDieta = 0;

if (formDieta) {
    cargarUltimaDieta();

    formDieta.addEventListener("submit", async (e) => {
        e.preventDefault();
        variacionDieta = 0;
        await generarYRenderDieta();
        document.getElementById("btn-otra-variante").style.display = "inline-block";
    });

    document.getElementById("btn-otra-variante").addEventListener("click", async () => {
        variacionDieta += 1;
        await generarYRenderDieta();
    });
}

// Al entrar (o volver) a la página, recupera la última dieta generada — mismo
// arreglo que en Rutinas, para que no "desaparezca" al navegar y volver.
async function cargarUltimaDieta() {
    const data = await getJSON("/api/dietas/ultima");
    if (data.dieta) {
        renderDieta(data.dieta);
        document.getElementById("btn-otra-variante").style.display = "inline-block";
    }
}

async function generarYRenderDieta() {
    const calorias = document.getElementById("calorias_objetivo").value;
    const dieta = await postJSON("/api/dietas/generar", {
        calorias_objetivo: calorias,
        variacion: variacionDieta,
    });

    if (dieta.error) {
        alert(dieta.error);
        return;
    }
    renderDieta(dieta);
}

function renderDieta(dieta) {
    const contenedor = document.getElementById("resultado-dieta");
    const nombresTipo = {
        desayuno: "Desayuno",
        almuerzo: "Almuerzo",
        merienda: "Merienda",
        cena: "Cena",
    };

    let html = `<div class="card">
        <div class="habitos-header-row">
            <h2 class="card-title" style="margin-bottom:0;">
                <span class="card-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2L3 14h7l-1 8 10-12h-7l1-8z"/></svg></span>
                Tu plan de comidas — ${dieta.totales.kcal} kcal totales
            </h2>
            <button type="button" class="btn-secondary no-print" style="width:auto; margin-top:0;" onclick="window.print()">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9V2h12v7M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2M6 14h12v8H6z"/></svg>
                Descargar PDF
            </button>
        </div>`;

    for (const [tipo, comida] of Object.entries(dieta.comidas)) {
        html += `<div class="comida-card">
            <div class="comida-icon">${ICONOS_COMIDA[tipo] || ""}</div>
            <div class="comida-info">
                <div class="tipo">${nombresTipo[tipo] || tipo}</div>
                <div class="nombre-comida">${comida.nombre}</div>
                <div class="porcion">${comida.porcion_g} g · P ${comida.proteina_g}g · C ${comida.carbos_g}g · G ${comida.grasas_g}g</div>
            </div>
            <div class="kcal">${comida.kcal}<small>kcal</small></div>
        </div>`;
    }

    html += `</div>`;
    contenedor.innerHTML = html;
    contenedor.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ============================================
// Página: Hábitos (habitos.html)
// ============================================

const listaFisico = document.getElementById("lista-habitos-fisico");
const HABITO_RING_CIRCUMFERENCE = 2 * Math.PI * 94; // r=94 en el SVG del anillo grande
let catalogoHabitos = [];
let seleccionActual = [];
let completadosHoy = [];

const MENSAJES_HABITO = [
    { min: 0, texto: "Empezá marcando tu primer hábito de hoy." },
    { min: 30, texto: "Vas arrancando bien, seguí así." },
    { min: 60, texto: "Buen ritmo hoy, ya vas por más de la mitad." },
    { min: 90, texto: "Casi perfecto, te falta muy poco." },
    { min: 100, texto: "¡Día completo! Excelente trabajo hoy." },
];

const ICONO_LOGRO = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l2.6 6.6L22 9.2l-5.4 4.7L18.2 21 12 17.3 5.8 21l1.6-7.1L2 9.2l7.4-.6L12 2z"/></svg>';

if (listaFisico) {
    inicializarPaginaHabitos();
}

async function inicializarPaginaHabitos() {
    // Estas dos lecturas son las únicas que esperan a la red: pasa una sola vez,
    // al entrar a la página. De ahí en adelante, todo se calcula en el navegador.
    const catalogoRespuesta = await getJSON("/api/habitos/catalogo");
    const estadoInicial = await getJSON("/api/habitos/hoy");

    if (estadoInicial.error || estadoInicial.aviso || !Array.isArray(catalogoRespuesta)) {
        document.getElementById("lista-habitos-fisico").innerHTML =
            `<div class="aviso-supabase">⚠️ ${estadoInicial.error || estadoInicial.aviso || "No se pudo cargar el catálogo de hábitos."}</div>`;
        return;
    }

    catalogoHabitos = catalogoRespuesta;
    seleccionActual = estadoInicial.seleccion || [];
    completadosHoy = (estadoInicial.habitos || []).filter((h) => h.completado).map((h) => h.id);

    renderHabitos(estadoInicial);
    cargarRacha();
    configurarSelectorHabitos();
}

// Réplica en JS de la lógica de habitos.armar_estado_dia, para poder actualizar
// la pantalla al instante sin esperar respuesta del servidor.
function armarEstadoLocal() {
    const sel = seleccionActual && seleccionActual.length ? seleccionActual : [];
    const completadosSet = new Set(completadosHoy);

    const habitosDelDia = catalogoHabitos
        .filter((h) => sel.includes(h.id))
        .map((h) => ({ ...h, completado: completadosSet.has(h.id) }));

    const total = habitosDelDia.length;
    const hechos = habitosDelDia.filter((h) => h.completado).length;
    const porcentaje = total ? Math.round((hechos / total) * 100) : 0;

    return { habitos: habitosDelDia, completados: hechos, total, porcentaje };
}

function renderHabitos(estado) {
    const fisicos = estado.habitos.filter((h) => h.categoria === "fisico");
    const mentales = estado.habitos.filter((h) => h.categoria === "mental");

    document.getElementById("lista-habitos-fisico").innerHTML =
        fisicos.map(habitoItemHTML).join("") || vacioCategoriaHTML();
    document.getElementById("lista-habitos-mental").innerHTML =
        mentales.map(habitoItemHTML).join("") || vacioCategoriaHTML();

    document.querySelectorAll(".habito-item").forEach((item) => {
        item.addEventListener("click", () => toggleHabito(item.dataset.id));
    });

    document.getElementById("habito-pct").textContent = `${estado.porcentaje}%`;
    document.getElementById("habito-frac").textContent = `${estado.completados} de ${estado.total} hábitos`;

    const offset = HABITO_RING_CIRCUMFERENCE - (estado.porcentaje / 100) * HABITO_RING_CIRCUMFERENCE;
    const ring = document.getElementById("habito-ring");
    requestAnimationFrame(() => {
        ring.style.strokeDasharray = HABITO_RING_CIRCUMFERENCE;
        ring.style.strokeDashoffset = offset;
    });

    const mensaje = [...MENSAJES_HABITO].reverse().find((m) => estado.porcentaje >= m.min);
    document.getElementById("habito-mensaje").textContent = mensaje.texto;
}

function vacioCategoriaHTML() {
    return `<p style="color:var(--stone); font-size:0.85rem; padding:8px 0;">No elegiste hábitos de esta categoría todavía.</p>`;
}

function habitoItemHTML(h) {
    return `<div class="habito-item ${h.completado ? "completado" : ""}" data-id="${h.id}">
        <div class="habito-check">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
        </div>
        <span class="habito-nombre">${h.nombre}</span>
    </div>`;
}

function toggleHabito(habitoId) {
    // 1) Actualizamos la pantalla al instante con lo que ya sabemos en el navegador.
    if (completadosHoy.includes(habitoId)) {
        completadosHoy = completadosHoy.filter((id) => id !== habitoId);
    } else {
        completadosHoy.push(habitoId);
    }
    renderHabitos(armarEstadoLocal());

    // 2) Guardamos en Supabase en segundo plano, sin bloquear la interfaz.
    postJSON("/api/habitos/completados", { completados: completadosHoy, seleccion: seleccionActual })
        .then(() => cargarRacha())
        .catch(() => {});
}

async function cargarRacha() {
    const data = await getJSON("/api/habitos/racha");
    if (data.error) return;

    document.getElementById("racha-numero").textContent = `${data.racha} día${data.racha === 1 ? "" : "s"}`;
    document.getElementById("racha-label").textContent = data.racha > 0
        ? "de racha activa — ¡no la cortes!"
        : "Empezá tu racha hoy";

    const desbloqueadosIds = new Set(data.logros_desbloqueados.map((l) => l.dias));

    document.getElementById("logros-grid").innerHTML = data.todos_los_logros.map((logro) => {
        const desbloqueado = desbloqueadosIds.has(logro.dias);
        return `<div class="logro-card ${desbloqueado ? "desbloqueado" : ""}">
            <div class="logro-medalla">${ICONO_LOGRO}</div>
            <div class="logro-nombre">${logro.nombre}</div>
            <div class="logro-desc">${logro.descripcion}</div>
        </div>`;
    }).join("");
}

function configurarSelectorHabitos() {
    const overlay = document.getElementById("selector-overlay");
    const btnAbrir = document.getElementById("btn-personalizar");
    const btnGuardar = document.getElementById("btn-guardar-seleccion");

    // Ya tenemos catalogoHabitos y seleccionActual cargados en memoria:
    // abrir el selector es instantáneo, no hace falta pedirle nada al servidor.
    btnAbrir.addEventListener("click", () => {
        renderSelectorLista();
        overlay.style.display = "flex";
    });

    overlay.addEventListener("click", (e) => {
        if (e.target === overlay) overlay.style.display = "none";
    });

    btnGuardar.addEventListener("click", () => {
        overlay.style.display = "none";
        renderHabitos(armarEstadoLocal());
        postJSON("/api/habitos/seleccion", { seleccion: seleccionActual }).catch(() => {});
    });
}

function renderSelectorLista() {
    const contenedor = document.getElementById("selector-lista");
    contenedor.innerHTML = catalogoHabitos.map((h) => {
        const marcado = seleccionActual.includes(h.id);
        return `<div class="selector-opcion ${marcado ? "marcado" : ""}" data-id="${h.id}">
            <div class="selector-checkbox">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
            </div>
            <span>${h.nombre}</span>
        </div>`;
    }).join("");

    contenedor.querySelectorAll(".selector-opcion").forEach((opcion) => {
        opcion.addEventListener("click", () => {
            const id = opcion.dataset.id;
            if (seleccionActual.includes(id)) {
                seleccionActual = seleccionActual.filter((x) => x !== id);
            } else {
                seleccionActual.push(id);
            }
            opcion.classList.toggle("marcado");
        });
    });
}

// ============================================
// Página: Progreso (progreso.html) — resumen, medidas y fotos
// ============================================

const formMedidas = document.getElementById("form-medidas");
if (formMedidas) {
    cargarResumenSemanal();
    cargarMedidas();
    cargarFotos();
    configurarSubidaFoto();
    inicializarAnalyticsEntrenamiento();

    formMedidas.addEventListener("submit", async (e) => {
        e.preventDefault();
        const payload = {
            cintura: document.getElementById("m-cintura").value,
            cadera: document.getElementById("m-cadera").value,
            pecho: document.getElementById("m-pecho").value,
            brazo: document.getElementById("m-brazo").value,
            pierna: document.getElementById("m-pierna").value,
        };
        const resultado = await postJSON("/api/medidas", payload);
        if (resultado.error) {
            alert(resultado.error);
            return;
        }
        formMedidas.reset();
        cargarMedidas();
    });
}

// ============================================
// Analytics de entrenamiento (dentro de Progreso)
// ============================================

let graficoProgresionActual = null;

async function inicializarAnalyticsEntrenamiento() {
    const selector = document.getElementById("selector-ejercicio-progresion");
    if (!selector) return;

    const ejercicios = await getJSON("/api/entrenamiento/ejercicios");

    if (!Array.isArray(ejercicios) || !ejercicios.length) {
        selector.innerHTML = "<option>Todavía no registraste ningún entrenamiento</option>";
        document.getElementById("volumen-semanal-real").innerHTML = empyStateHTML(
            "Sin entrenamientos registrados",
            'Registrá tus series reales en la sección "Entrenar" para ver tu progresión acá.'
        );
    } else {
        selector.innerHTML = ejercicios.map((e) => `<option value="${e}">${e}</option>`).join("");
        selector.addEventListener("change", () => cargarProgresionEjercicio(selector.value));
        cargarProgresionEjercicio(selector.value);
    }

    cargarAnalyticsGeneral();
}

async function cargarProgresionEjercicio(ejercicio) {
    const datos = await getJSON(`/api/entrenamiento/progresion?ejercicio=${encodeURIComponent(ejercicio)}`);
    const ctx = document.getElementById("grafico-progresion");
    const resumen = document.getElementById("progresion-resumen");
    if (!ctx || !Array.isArray(datos)) return;

    // Si hay muy pocos puntos, el gráfico solo muestra un punto suelto y queda
    // confuso — mostramos un resumen en texto en vez de (o además de) la curva.
    // Esto se arma ANTES de tocar Chart.js: si esa librería (que se carga desde
    // un CDN externo) tarda o no llega a cargar por una conexión lenta, el
    // resumen en texto igual se ve en vez de dejar toda la tarjeta en blanco.
    if (!datos.length) {
        ctx.style.display = "none";
        if (resumen) {
            resumen.innerHTML = empyStateHTML(
                "Sin series registradas para este ejercicio",
                'Registrá al menos una serie en "Entrenar" para empezar a ver su evolución acá.'
            );
        }
        return;
    }

    ctx.style.display = "block";
    const mejorMarca = Math.max(...datos.map((d) => d.estimado_1rm));
    const ultimo = datos[datos.length - 1];
    if (resumen) {
        if (datos.length === 1) {
            resumen.innerHTML = `
                <div class="progresion-stats">
                    <div class="progresion-stat"><span class="valor">${ultimo.estimado_1rm} kg</span><span class="label">1RM estimado (único registro)</span></div>
                </div>
                <p class="progresion-nota">Registrá este ejercicio en más días para ver la curva de progresión.</p>`;
        } else {
            resumen.innerHTML = `
                <div class="progresion-stats">
                    <div class="progresion-stat"><span class="valor">${ultimo.estimado_1rm} kg</span><span class="label">1RM estimado más reciente</span></div>
                    <div class="progresion-stat"><span class="valor">${mejorMarca} kg</span><span class="label">Mejor marca histórica</span></div>
                    <div class="progresion-stat"><span class="valor">${datos.length}</span><span class="label">días entrenados</span></div>
                </div>`;
        }
    }

    if (typeof Chart === "undefined") {
        ctx.style.display = "none";
        return;
    }

    if (graficoProgresionActual) {
        graficoProgresionActual.destroy();
    }

    const col = coloresGrafico();
    graficoProgresionActual = new Chart(ctx, {
        type: "line",
        data: {
            labels: datos.map((d) => new Date(d.fecha).toLocaleDateString("es-AR")),
            datasets: [{
                label: "1RM estimado (kg)",
                data: datos.map((d) => d.estimado_1rm),
                borderColor: "#FF5A36",
                backgroundColor: "rgba(255,90,54,0.12)",
                tension: 0.35,
                fill: true,
                pointBackgroundColor: "#FF5A36",
                pointRadius: 4,
            }],
        },
        options: {
            responsive: true,
            plugins: { legend: { labels: { color: col.texto } } },
            scales: {
                x: { ticks: { color: col.subtexto }, grid: { color: col.grilla } },
                y: { ticks: { color: col.subtexto }, grid: { color: col.grilla } },
            },
        },
    });
}

async function cargarAnalyticsGeneral() {
    const data = await getJSON("/api/entrenamiento/analytics");
    if (data.error) {
        const aviso = `<div class="aviso-supabase">⚠️ ${data.error}</div>`;
        document.getElementById("volumen-semanal-real").innerHTML = aviso;
        const heatmap = document.getElementById("calendario-heatmap");
        heatmap.style.display = "block";
        heatmap.innerHTML = aviso;
        return;
    }

    renderVolumenSemanalReal(data.volumen_semanal, data.volumen_ideal_min);
    renderCalendarioHeatmap(data.calendario);
}

function renderVolumenSemanalReal(semanas, volumenIdealMin) {
    const contenedor = document.getElementById("volumen-semanal-real");
    if (!contenedor) return;

    if (!semanas || !semanas.length) {
        contenedor.innerHTML = empyStateHTML(
            "Todavía no hay series registradas",
            "Cuando registres entrenamientos vas a ver acá si tu volumen semanal real llega al rango recomendado por la evidencia."
        );
        return;
    }

    contenedor.innerHTML = semanas.slice(0, 4).map((semana) => `
        <div class="volumen-semana-card">
            <div class="semana-label">Semana del ${new Date(semana.semana_inicio + "T00:00:00").toLocaleDateString("es-AR")}</div>
            <div class="volumen-chips">
                ${semana.grupos.map((g) => `
                    <span class="volumen-chip ${g.en_rango_ideal ? "volumen-alto" : g.series >= volumenIdealMin * 0.5 ? "volumen-medio" : "volumen-bajo"}">
                        ${g.grupo}: ${g.series} series
                    </span>
                `).join("")}
            </div>
        </div>
    `).join("");
}

const NOMBRES_MES_CORTOS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];

function renderCalendarioHeatmap(diasEntrenados) {
    const contenedor = document.getElementById("calendario-heatmap");
    if (!contenedor) return;

    const diasSet = new Set(diasEntrenados || []);
    const hoy = new Date();
    const semanas = [];

    for (let s = 11; s >= 0; s--) {
        const dias = [];
        let primerFechaSemana = null;
        for (let d = 6; d >= 0; d--) {
            const fecha = new Date(hoy);
            fecha.setDate(hoy.getDate() - (s * 7 + d));
            if (d === 6) primerFechaSemana = fecha;
            const iso = fecha.toISOString().slice(0, 10);
            dias.push({ entrenado: diasSet.has(iso), iso });
        }
        semanas.push({ dias, primerFechaSemana });
    }

    // Etiqueta el mes solo en la primera semana que lo contiene (como el
    // calendario de contribuciones de GitHub), para no amontonar texto.
    const totalEntrenados = semanas.reduce(
        (acc, semana) => acc + semana.dias.filter((d) => d.entrenado).length, 0
    );

    contenedor.style.display = "block";
    contenedor.innerHTML = `
        <div class="constancia-resumen">Entrenaste <strong>${totalEntrenados}</strong> de los últimos 84 días (12 semanas).</div>
        <div class="calendario-meses">
            ${semanas.map((semana) => `<span>${semana.primerFechaSemana.getDate() <= 7 ? NOMBRES_MES_CORTOS[semana.primerFechaSemana.getMonth()] : ""}</span>`).join("")}
        </div>
        <div class="calendario-grid">
            ${semanas.map((semana) => `
                <div class="calendario-semana">
                    ${semana.dias.map((d) => `<div class="calendario-dia ${d.entrenado ? "entrenado" : ""}" title="${d.iso}"></div>`).join("")}
                </div>
            `).join("")}
        </div>
        <div class="calendario-leyenda">
            <span class="calendario-dia"></span> No entrenaste
            <span class="calendario-dia entrenado"></span> Entrenaste
        </div>
    `;
}

async function cargarResumenSemanal() {
    const r = await getJSON("/api/resumen-semanal");
    if (r.error) {
        document.getElementById("resumen-grid").innerHTML =
            `<div class="empty-state" style="grid-column:1/-1;">
                <div class="empty-title">Conectá Supabase</div>
                <div class="empty-text">${r.error}</div>
            </div>`;
        return;
    }

    document.getElementById("resumen-rango").textContent = `(${r.rango})`;

    const cambioPesoTexto = r.cambio_peso === null
        ? "--"
        : `${r.cambio_peso > 0 ? "+" : ""}${r.cambio_peso} kg`;

    document.getElementById("resumen-grid").innerHTML = `
        <div class="resumen-item">
            <div class="resumen-valor">${r.rutinas_generadas}</div>
            <div class="resumen-label">Rutinas generadas</div>
        </div>
        <div class="resumen-item">
            <div class="resumen-valor">${cambioPesoTexto}</div>
            <div class="resumen-label">Cambio de peso</div>
        </div>
        <div class="resumen-item">
            <div class="resumen-valor">${r.dias_con_habitos}/7</div>
            <div class="resumen-label">Días activo con hábitos</div>
        </div>
        <div class="resumen-item">
            <div class="resumen-valor">${r.promedio_habitos_por_dia}</div>
            <div class="resumen-label">Hábitos promedio/día</div>
        </div>
    `;
}

async function cargarMedidas() {
    const medidas = await getJSON("/api/medidas");
    if (medidas.error || !medidas.length) {
        const ctx = document.getElementById("grafico-medidas");
        if (ctx) ctx.replaceWith(Object.assign(document.createElement("div"), {
            className: "empty-state",
            innerHTML: `<div class="empty-title">Todavía no cargaste medidas</div><div class="empty-text">Completá el formulario de arriba para empezar tu seguimiento.</div>`,
        }));
        return;
    }
    renderGraficoMedidas(medidas);
}

function renderGraficoMedidas(medidas) {
    const ordenados = [...medidas].reverse();
    const labels = ordenados.map((m) => new Date(m.fecha).toLocaleDateString("es-AR"));

    const series = [
        { campo: "cintura", label: "Cintura", color: "#FF5A36" },
        { campo: "cadera", label: "Cadera", color: "#5EEAD4" },
        { campo: "pecho", label: "Pecho", color: "#FFC857" },
        { campo: "brazo", label: "Brazo", color: "#A78BFA" },
        { campo: "pierna", label: "Pierna", color: "#60A5FA" },
    ];

    const datasets = series
        .filter((s) => ordenados.some((m) => m[s.campo] !== null && m[s.campo] !== undefined))
        .map((s) => ({
            label: s.label,
            data: ordenados.map((m) => m[s.campo]),
            borderColor: s.color,
            backgroundColor: "transparent",
            tension: 0.35,
            spanGaps: true,
            pointRadius: 3,
        }));

    const ctx = document.getElementById("grafico-medidas");
    if (!ctx || typeof Chart === "undefined") return;

    const colMed = coloresGrafico();
    new Chart(ctx, {
        type: "line",
        data: { labels, datasets },
        options: {
            responsive: true,
            plugins: { legend: { labels: { color: colMed.texto, usePointStyle: true, boxWidth: 8 } } },
            scales: {
                x: { ticks: { color: colMed.subtexto }, grid: { color: colMed.grilla } },
                y: { ticks: { color: colMed.subtexto }, grid: { color: colMed.grilla } },
            },
        },
    });
}

function configurarSubidaFoto() {
    const zona = document.getElementById("foto-upload-zone");
    const input = document.getElementById("foto-input");

    zona.addEventListener("click", () => input.click());

    input.addEventListener("change", async () => {
        const archivo = input.files[0];
        if (!archivo) return;

        const base64Comprimido = await comprimirImagen(archivo, 700);
        const resultado = await postJSON("/api/fotos", { imagen_base64: base64Comprimido });

        if (resultado.error) {
            alert(resultado.error);
            return;
        }
        input.value = "";
        cargarFotos();
    });
}

function comprimirImagen(archivo, anchoMax) {
    return new Promise((resolve, reject) => {
        const lector = new FileReader();
        lector.onload = (e) => {
            const img = new Image();
            img.onload = () => {
                const escala = Math.min(1, anchoMax / img.width);
                const canvas = document.createElement("canvas");
                canvas.width = img.width * escala;
                canvas.height = img.height * escala;
                const ctx = canvas.getContext("2d");
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                resolve(canvas.toDataURL("image/jpeg", 0.8));
            };
            img.onerror = reject;
            img.src = e.target.result;
        };
        lector.onerror = reject;
        lector.readAsDataURL(archivo);
    });
}

async function cargarFotos() {
    const fotos = await getJSON("/api/fotos");
    const galeria = document.getElementById("galeria-fotos");
    if (!galeria) return;

    if (fotos.error || !fotos.length) {
        galeria.innerHTML = "";
        return;
    }

    galeria.innerHTML = fotos.map((f) => {
        const fecha = new Date(f.fecha).toLocaleDateString("es-AR");
        return `<div class="foto-item">
            <img src="${f.imagen_base64}" alt="Foto de progreso del ${fecha}">
            <button class="foto-borrar" onclick="borrarFoto(${f.id})">✕</button>
            <div class="foto-fecha">${fecha}</div>
        </div>`;
    }).join("");
}

async function borrarFoto(id) {
    await fetch(`/api/fotos/${id}`, { method: "DELETE" });
    cargarFotos();
}

// ============================================
// Timer de descanso (reutilizable)
// ============================================

let timerIntervalo = null;

function parsearDescansoASegundos(descansoTexto) {
    // Extrae los números de textos tipo "90-120 seg" o "20-25 min" y devuelve
    // el promedio en segundos. Si no encuentra nada usable, devuelve 90 (default razonable).
    const numeros = (descansoTexto || "").match(/\d+/g);
    if (!numeros || !numeros.length) return 90;

    const promedio = numeros.reduce((a, b) => a + parseInt(b, 10), 0) / numeros.length;
    const esMinutos = /min/i.test(descansoTexto);
    return Math.round(esMinutos ? promedio * 60 : promedio);
}

function iniciarTimerDescanso(segundosTotales) {
    const contenedor = document.getElementById("timer-flotante");
    const texto = document.getElementById("timer-texto");
    if (!contenedor || !texto) return;

    clearInterval(timerIntervalo);
    let restante = segundosTotales;
    contenedor.style.display = "flex";
    actualizarTextoTimer(restante);

    timerIntervalo = setInterval(() => {
        restante -= 1;
        if (restante <= 0) {
            clearInterval(timerIntervalo);
            contenedor.style.display = "none";
            reproducirSonidoFinDescanso();
            return;
        }
        actualizarTextoTimer(restante);
    }, 1000);

    function actualizarTextoTimer(seg) {
        const min = Math.floor(seg / 60).toString().padStart(2, "0");
        const s = (seg % 60).toString().padStart(2, "0");
        texto.textContent = `${min}:${s}`;
    }

    const btnSaltar = document.getElementById("timer-saltar");
    if (btnSaltar) {
        btnSaltar.onclick = () => {
            clearInterval(timerIntervalo);
            contenedor.style.display = "none";
        };
    }
}

function reproducirSonidoFinDescanso() {
    try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.frequency.value = 880;
        gain.gain.setValueAtTime(0.15, ctx.currentTime);
        osc.start();
        osc.stop(ctx.currentTime + 0.35);
    } catch (e) {
        // Si el navegador bloquea audio sin interacción previa, no pasa nada grave.
    }
    if (navigator.vibrate) navigator.vibrate([200, 100, 200]);
}

// ============================================
// Página: Entrenar (entrenar.html)
// ============================================

const selectorDiaCard = document.getElementById("selector-dia-card");
let rutinaActualEntrenar = null;

if (selectorDiaCard) {
    inicializarPaginaEntrenar();
}

async function inicializarPaginaEntrenar() {
    // Usa la rutina ACTIVA (la que el usuario guardó), no solo "la última
    // generada" — si generó varias rutinas para comparar, acá entrena con la
    // que realmente eligió, no con la que quedó generada por accidente al final.
    const data = await getJSON("/api/rutinas/activa");

    if (data.aviso || data.error) {
        document.getElementById("sin-rutina-aviso").innerHTML =
            `<div class="aviso-supabase">⚠️ ${data.aviso || data.error}</div>`;
        return;
    }

    if (!data.rutina) {
        document.getElementById("sin-rutina-aviso").innerHTML = empyStateHTML(
            "Todavía no generaste ninguna rutina",
            'Andá a la sección "Rutinas" y generá una primero — después volvé acá para registrar tu entrenamiento real.'
        );
        return;
    }

    rutinaActualEntrenar = data.rutina;
    document.getElementById("selector-dia-card").style.display = "block";

    const contenedorDias = document.getElementById("selector-dias-entrenar");
    contenedorDias.innerHTML = rutinaActualEntrenar.plan.map((dia, i) =>
        `<button type="button" data-dia="${i}" class="${i === 0 ? "selected" : ""}">Día ${dia.dia}</button>`
    ).join("");

    contenedorDias.querySelectorAll("button").forEach((btn) => {
        btn.addEventListener("click", () => {
            contenedorDias.querySelectorAll("button").forEach((b) => b.classList.remove("selected"));
            btn.classList.add("selected");
            renderDiaEntrenar(parseInt(btn.dataset.dia, 10));
        });
    });

    renderDiaEntrenar(0);
}

function renderDiaEntrenar(indiceDia) {
    const dia = rutinaActualEntrenar.plan[indiceDia];
    const contenedor = document.getElementById("ejercicios-entrenar");

    contenedor.innerHTML = dia.ejercicios
        .filter((ej) => ej.grupo !== "cardio")
        .map((ej, idxEj) => {
            const filasSeries = Array.from({ length: ej.series }, (_, i) => {
                const idSerie = `serie-${indiceDia}-${idxEj}-${i}`;
                return `<div class="serie-input-row" id="fila-${idSerie}">
                    <span class="serie-num">${i + 1}</span>
                    <input type="number" step="0.5" placeholder="kg" id="peso-${idSerie}">
                    <input type="number" placeholder="reps" id="reps-${idSerie}">
                    <button type="button" class="btn-check-serie" data-serie-id="${idSerie}" data-ejercicio="${ej.nombre}" data-grupo="${ej.grupo}" data-numero="${i + 1}" data-descanso="${ej.descanso}">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
                    </button>
                </div>`;
            }).join("");

            return `<div class="ejercicio-registro-card">
                <h3>${ej.nombre}${botonGifHTML(ej.nombre)}</h3>
                <div class="meta">Objetivo: ${ej.series} × ${ej.reps} · descanso ${ej.descanso}</div>
                ${filasSeries}
                <div id="pr-toast-${indiceDia}-${idxEj}"></div>
            </div>`;
        }).join("");

    contenedor.querySelectorAll(".btn-check-serie").forEach((btn) => {
        btn.addEventListener("click", () => registrarSerie(btn));
    });
}

async function registrarSerie(boton) {
    const idSerie = boton.dataset.serieId;
    const fila = document.getElementById(`fila-${idSerie}`);
    const pesoInput = document.getElementById(`peso-${idSerie}`);
    const repsInput = document.getElementById(`reps-${idSerie}`);

    const peso = parseFloat(pesoInput.value);
    const reps = parseInt(repsInput.value, 10);

    if (!peso || !reps || peso <= 0 || reps <= 0) {
        pesoInput.style.borderColor = "var(--ember)";
        repsInput.style.borderColor = "var(--ember)";
        return;
    }

    boton.disabled = true;

    const resultado = await postJSON("/api/entrenamiento/registrar-serie", {
        ejercicio: boton.dataset.ejercicio,
        grupo: boton.dataset.grupo,
        serie_numero: boton.dataset.numero,
        peso,
        reps,
    });

    boton.disabled = false;

    if (resultado.error) {
        alert(resultado.error);
        return;
    }

    fila.classList.add("completada");
    pesoInput.style.borderColor = "";
    repsInput.style.borderColor = "";

    if (resultado.es_pr) {
        const contenedorEjercicio = fila.closest(".ejercicio-registro-card");
        const toastBox = contenedorEjercicio.querySelector('[id^="pr-toast-"]');
        toastBox.innerHTML = `<div class="pr-toast">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l2.6 6.6L22 9.2l-5.4 4.7L18.2 21 12 17.3 5.8 21l1.6-7.1L2 9.2l7.4-.6L12 2z"/></svg>
            ¡Nuevo récord personal en ${boton.dataset.ejercicio}!
        </div>`;
    }

    const segundos = parsearDescansoASegundos(boton.dataset.descanso);
    iniciarTimerDescanso(segundos);
}

// ============================================
// Página: Compras (compras.html)
// ============================================

const btnRegenerarLista = document.getElementById("btn-regenerar-lista");
if (btnRegenerarLista) {
    cargarListaCompras();

    btnRegenerarLista.addEventListener("click", async () => {
        const textoOriginal = btnRegenerarLista.innerHTML;
        btnRegenerarLista.disabled = true;
        btnRegenerarLista.textContent = "Generando...";

        const dietaData = await getJSON("/api/dietas/ultima");

        if (!dietaData.dieta) {
            alert('Todavía no generaste ninguna dieta. Andá a la sección "Dietas" y generá una primero.');
            btnRegenerarLista.disabled = false;
            btnRegenerarLista.innerHTML = textoOriginal;
            return;
        }

        const resultado = await postJSON("/api/compras/generar", { dieta: dietaData.dieta });
        btnRegenerarLista.disabled = false;
        btnRegenerarLista.innerHTML = textoOriginal;

        renderListaCompras(resultado.grupos || []);
    });
}

async function cargarListaCompras() {
    const data = await getJSON("/api/compras");
    if (data.error) {
        document.getElementById("lista-compras-contenido").innerHTML =
            `<div class="aviso-supabase">⚠️ ${data.error}</div>`;
        return;
    }
    renderListaCompras(data.grupos || []);
}

function renderListaCompras(grupos) {
    const contenedor = document.getElementById("lista-compras-contenido");

    if (!grupos.length) {
        contenedor.innerHTML = empyStateHTML(
            "Todavía no tenés una lista",
            'Generá una dieta primero, y después tocá "Regenerar desde tu última dieta" acá arriba.'
        );
        return;
    }

    contenedor.innerHTML = grupos.map((grupo) => `
        <div class="compras-grupo-titulo">${grupo.nombre_categoria}</div>
        ${grupo.items.map((item) => `
            <div class="compra-item ${item.comprado ? "comprado" : ""}" data-item="${item.item}">
                <div class="compra-check">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
                </div>
                <span class="compra-nombre">${item.item}</span>
            </div>
        `).join("")}
    `).join("");

    contenedor.querySelectorAll(".compra-item").forEach((el) => {
        el.addEventListener("click", async () => {
            const yaComprado = el.classList.contains("comprado");
            el.classList.toggle("comprado");
            await postJSON("/api/compras/toggle", { item: el.dataset.item, comprado: !yaComprado });
        });
    });
}

// ============================================
// Autenticación: login y registro
// ============================================

const formLogin = document.getElementById("form-login");
if (formLogin) {
    formLogin.addEventListener("submit", async (e) => {
        e.preventDefault();
        const boton = document.getElementById("btn-login");
        const errorBox = document.getElementById("login-error");
        errorBox.style.display = "none";

        const textoOriginal = boton.textContent;
        boton.disabled = true;
        boton.textContent = "Ingresando...";

        const resultado = await postJSON("/api/login", {
            email: document.getElementById("email").value,
            password: document.getElementById("password").value,
        });

        if (!resultado.ok) {
            errorBox.textContent = resultado.error || "No se pudo iniciar sesión.";
            errorBox.style.display = "block";
            boton.disabled = false;
            boton.textContent = textoOriginal;
            return;
        }

        window.location.href = "/";
    });
}

const formSignup = document.getElementById("form-signup");
if (formSignup) {
    formSignup.addEventListener("submit", async (e) => {
        e.preventDefault();
        const boton = document.getElementById("btn-signup");
        const errorBox = document.getElementById("signup-error");
        const successBox = document.getElementById("signup-success");
        errorBox.style.display = "none";
        successBox.style.display = "none";

        const textoOriginal = boton.textContent;
        boton.disabled = true;
        boton.textContent = "Creando cuenta...";

        const resultado = await postJSON("/api/signup", {
            email: document.getElementById("email").value,
            password: document.getElementById("password").value,
        });

        if (!resultado.ok) {
            errorBox.textContent = resultado.error || "No se pudo crear la cuenta.";
            errorBox.style.display = "block";
            boton.disabled = false;
            boton.textContent = textoOriginal;
            return;
        }

        if (resultado.requiere_confirmacion) {
            successBox.textContent = resultado.mensaje;
            successBox.style.display = "block";
            boton.disabled = false;
            boton.textContent = textoOriginal;
            formSignup.reset();
            return;
        }

        window.location.href = "/";
    });
}

// ============================================
// Asistente ForgeFit (chat con IA)
// ============================================

function inicializarAsistente() {
    // Solo se muestra dentro de la app (páginas con sidebar), no en login/signup.
    if (!document.querySelector(".sidebar")) return;

    const historialChat = [];

    const fab = document.createElement("button");
    fab.className = "chat-fab";
    fab.setAttribute("aria-label", "Preguntale a ForgeFit");
    fab.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`;

    const panel = document.createElement("div");
    panel.className = "chat-panel";
    panel.innerHTML = `
        <div class="chat-header">
            <span>Preguntale a ForgeFit</span>
            <button type="button" id="chat-cerrar" aria-label="Cerrar">✕</button>
        </div>
        <div class="chat-mensajes" id="chat-mensajes">
            <div class="chat-burbuja asistente">¡Hola! Preguntame lo que quieras sobre entrenamiento, nutrición o hábitos. No reemplazo a un profesional, pero te puedo orientar.</div>
        </div>
        <form class="chat-form" id="chat-form">
            <input type="text" id="chat-input" placeholder="Escribí tu pregunta..." autocomplete="off">
            <button type="submit" aria-label="Enviar">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>
            </button>
        </form>
    `;

    document.body.appendChild(fab);
    document.body.appendChild(panel);

    fab.addEventListener("click", () => panel.classList.toggle("abierto"));
    panel.querySelector("#chat-cerrar").addEventListener("click", () => panel.classList.remove("abierto"));

    const mensajesEl = panel.querySelector("#chat-mensajes");
    const formEl = panel.querySelector("#chat-form");
    const inputEl = panel.querySelector("#chat-input");

    function agregarBurbuja(texto, clase) {
        const burbuja = document.createElement("div");
        burbuja.className = `chat-burbuja ${clase}`;
        burbuja.textContent = texto;
        mensajesEl.appendChild(burbuja);
        mensajesEl.scrollTop = mensajesEl.scrollHeight;
        return burbuja;
    }

    formEl.addEventListener("submit", async (e) => {
        e.preventDefault();
        const pregunta = inputEl.value.trim();
        if (!pregunta) return;

        agregarBurbuja(pregunta, "usuario");
        historialChat.push({ rol: "usuario", texto: pregunta });
        inputEl.value = "";

        const cargando = agregarBurbuja("Pensando...", "asistente cargando");

        const resultado = await postJSON("/api/asistente", {
            pregunta,
            historial: historialChat,
        });

        cargando.remove();

        if (resultado.error) {
            agregarBurbuja(resultado.error, "asistente");
            return;
        }

        agregarBurbuja(resultado.respuesta, "asistente");
        historialChat.push({ rol: "asistente", texto: resultado.respuesta });
    });
}

inicializarAsistente();

// ============================================
// Página: Historial (historial.html)
// ============================================

const tablaHistorial = document.getElementById("tabla-historial");
if (tablaHistorial) {
    cargarHistorial();
}

async function cargarHistorial() {
    const registros = await getJSON("/api/historial");

    if (registros.error) {
        document.getElementById("aviso-container").innerHTML = `
            <div class="aviso-supabase">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 9v4M12 17h.01M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/></svg>
                ${registros.error}
            </div>`;
        document.getElementById("tabla-historial").innerHTML = empyStateHTML(
            "Conectá Supabase para ver tu historial",
            "Una vez configurado, cada cálculo que hagas va a aparecer acá."
        );
        return;
    }

    if (!registros.length) {
        document.getElementById("tabla-historial").innerHTML = empyStateHTML(
            "Todavía no tenés registros",
            "Andá a la Calculadora y cargá tus datos para empezar a ver tu evolución."
        );
        return;
    }

    renderTablaHistorial(registros);
    renderGraficoEvolucion(registros);
}

function empyStateHTML(titulo, texto) {
    return `<div class="empty-state">
        <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18M7 14l4-4 3 3 5-6"/></svg>
        <div class="empty-title">${titulo}</div>
        <div class="empty-text">${texto}</div>
    </div>`;
}

function renderTablaHistorial(registros) {
    let html = `<table>
        <thead><tr>
            <th>Fecha</th><th>Peso</th><th>IMC</th><th>Calorías</th><th>Objetivo</th><th></th>
        </tr></thead><tbody>`;

    registros.forEach((r) => {
        const fecha = new Date(r.fecha).toLocaleDateString("es-AR");
        html += `<tr>
            <td>${fecha}</td>
            <td>${r.peso} kg</td>
            <td>${r.imc}</td>
            <td>${r.calorias_objetivo} kcal</td>
            <td><span class="objetivo-pill ${r.objetivo}">${r.objetivo}</span></td>
            <td><button class="btn-delete" onclick="borrarRegistro(${r.id})">Borrar</button></td>
        </tr>`;
    });

    html += `</tbody></table>`;
    document.getElementById("tabla-historial").innerHTML = html;
}

async function borrarRegistro(id) {
    await fetch(`/api/historial/${id}`, { method: "DELETE" });
    cargarHistorial();
}

function renderGraficoEvolucion(registros) {
    const ordenados = [...registros].reverse();
    const labels = ordenados.map((r) => new Date(r.fecha).toLocaleDateString("es-AR"));
    const pesos = ordenados.map((r) => r.peso);
    const calorias = ordenados.map((r) => r.calorias_objetivo);

    const ctx = document.getElementById("grafico-evolucion");
    if (!ctx || typeof Chart === "undefined") return;
    const colEvo = coloresGrafico();

    new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Peso (kg)",
                    data: pesos,
                    borderColor: "#FF5A36",
                    backgroundColor: "rgba(255,90,54,0.12)",
                    tension: 0.35,
                    fill: true,
                    pointBackgroundColor: "#FF5A36",
                    pointRadius: 4,
                    yAxisID: "y",
                },
                {
                    label: "Calorías objetivo",
                    data: calorias,
                    borderColor: "#5EEAD4",
                    backgroundColor: "rgba(94,234,212,0.08)",
                    tension: 0.35,
                    fill: true,
                    pointBackgroundColor: "#5EEAD4",
                    pointRadius: 4,
                    yAxisID: "y1",
                },
            ],
        },
        options: {
            responsive: true,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: { labels: { color: colEvo.texto, usePointStyle: true, boxWidth: 8 } },
            },
            scales: {
                x: { ticks: { color: colEvo.subtexto }, grid: { color: colEvo.grilla } },
                y: { position: "left", ticks: { color: colEvo.subtexto }, grid: { color: colEvo.grilla } },
                y1: { position: "right", ticks: { color: colEvo.subtexto }, grid: { display: false } },
            },
        },
    });
}

// ============================================
// GIFs de ejercicios (modal)
// ============================================
// Un solo listener delegado: funciona para los botones de Rutinas y de Entrenar
// aunque se vuelvan a dibujar, sin tener que enganchar eventos uno por uno.

const ICONO_GIF = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/></svg>`;
let indiceGifs = null; // nombre del ejercicio → ruta del GIF (public/static/gifs/index.json)

async function obtenerGifEjercicio(nombre) {
    if (!indiceGifs) {
        try {
            const r = await fetch("/static/gifs/index.json");
            if (!r.ok) throw new Error("sin índice");
            indiceGifs = await r.json();
        } catch (e) {
            return { error: true }; // no se guarda: reintenta la próxima vez
        }
    }
    return { gif: indiceGifs[nombre] || null };
}

function botonGifHTML(nombre) {
    const seguro = String(nombre).replace(/&/g, "&amp;").replace(/"/g, "&quot;");
    return `<button type="button" class="btn-gif no-print" data-gif-nombre="${seguro}" title="Ver cómo se hace" aria-label="Ver cómo se hace ${seguro}">${ICONO_GIF}</button>`;
}

document.addEventListener("click", (e) => {
    const boton = e.target.closest("[data-gif-nombre]");
    if (boton) {
        e.preventDefault();
        abrirModalGif(boton.dataset.gifNombre);
    }
});

document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") cerrarModalGif();
});

function cerrarModalGif() {
    const modal = document.getElementById("modal-gif");
    if (modal) modal.remove();
}

async function abrirModalGif(nombre) {
    cerrarModalGif();

    const modal = document.createElement("div");
    modal.id = "modal-gif";
    modal.className = "modal-gif-fondo";
    modal.setAttribute("role", "dialog");
    modal.setAttribute("aria-modal", "true");

    const caja = document.createElement("div");
    caja.className = "modal-gif-caja";

    const cerrar = document.createElement("button");
    cerrar.type = "button";
    cerrar.className = "modal-gif-cerrar";
    cerrar.setAttribute("aria-label", "Cerrar");
    cerrar.textContent = "×";
    cerrar.addEventListener("click", cerrarModalGif);

    const titulo = document.createElement("h3");
    titulo.textContent = nombre;

    const cuerpo = document.createElement("div");
    cuerpo.className = "modal-gif-cuerpo";
    cuerpo.innerHTML = `<div class="modal-gif-estado"><span class="spinner-gif"></span>Buscando el GIF…</div>`;

    caja.append(cerrar, titulo, cuerpo);
    modal.appendChild(caja);
    modal.addEventListener("click", (ev) => { if (ev.target === modal) cerrarModalGif(); });
    document.body.appendChild(modal);

    const resultado = await obtenerGifEjercicio(nombre);

    if (!document.body.contains(modal)) return; // el usuario ya lo cerró

    if (resultado.gif) {
        cuerpo.innerHTML = "";
        const img = document.createElement("img");
        img.className = "modal-gif-img";
        img.alt = `Demostración de ${nombre}`;
        img.referrerPolicy = "no-referrer";
        img.addEventListener("error", () => {
            cuerpo.innerHTML = `<p class="modal-gif-vacio">No se pudo cargar el GIF.</p>`;
        });
        img.src = resultado.gif;
        const pie = document.createElement("p");
        pie.className = "modal-gif-pie";
        pie.textContent = "Posición inicial y final del movimiento";
        cuerpo.append(img, pie);
    } else {
        const msg = resultado.error
            ? "No se pudo cargar el GIF. Revisá tu conexión y probá de nuevo."
            : "Este ejercicio todavía no tiene GIF.";
        cuerpo.innerHTML = `<p class="modal-gif-vacio">${msg}</p>`;
    }
}
