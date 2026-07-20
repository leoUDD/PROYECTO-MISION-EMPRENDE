const gridSize = 12;
const words = ["IDEA", "EQUIPO", "NEGOCIO", "CREATIVIDAD", "LIDERAZGO", "VALOR", "IMPACTO", "CLIENTE"];
const gridEl = document.getElementById("grid");
const statusEl = document.getElementById("status");

function tJuego(clave, fallback = "") {
  const idioma = window.i18nJuego?.obtenerIdioma?.() || "es";
  return window.i18nJuego?.traducciones?.[idioma]?.[clave] || fallback;
}

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.substring(0, name.length + 1) === (name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

/* ── SONIDO AL ENCONTRAR PALABRA ── */
(function () {
  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  if (!AudioCtx) return;
  let ctx = null;
  function getCtx() {
    if (!ctx) ctx = new AudioCtx();
    if (ctx.state === "suspended") ctx.resume();
    return ctx;
  }
  window.sonarPalabraEncontrada = function () {
    try {
      const c = getCtx();
      const notas = [523.25, 659.25, 783.99];
      notas.forEach((freq, i) => {
        const o = c.createOscillator();
        const g = c.createGain();
        o.connect(g); g.connect(c.destination);
        o.type = "sine";
        o.frequency.setValueAtTime(freq, c.currentTime + i * 0.08);
        g.gain.setValueAtTime(0, c.currentTime + i * 0.08);
        g.gain.linearRampToValueAtTime(0.22, c.currentTime + i * 0.08 + 0.02);
        g.gain.exponentialRampToValueAtTime(0.001, c.currentTime + i * 0.08 + 0.25);
        o.start(c.currentTime + i * 0.08);
        o.stop(c.currentTime + i * 0.08 + 0.28);
      });
    } catch (_) {}
  };
})();

async function registrarPalabraEncontrada(palabra) {
  const routes = document.getElementById("routes");
  const url = routes?.dataset?.registrarPalabraUrl;
  if (!url) return;
  try {
    await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
      credentials: "same-origin",
      body: JSON.stringify({ palabra })
    });
  } catch (error) {
    console.error("No se pudo registrar palabra:", error);
  }
}

async function registrarSopaCompletada() {
  const routes = document.getElementById("routes");
  const url = routes?.dataset?.sopaCompletadaApiUrl;
  if (!url) return { ok: false };
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
      credentials: "same-origin",
      body: JSON.stringify({})
    });
    const data = await res.json().catch(() => ({}));
    return { ok: res.ok, ...data };
  } catch (error) {
    console.error("No se pudo registrar sopa completada:", error);
    return { ok: false };
  }
}

document.documentElement.style.setProperty("--cols", gridSize);
document.documentElement.style.setProperty("--rows", gridSize);

const DIRS = [
  [1, 0], [-1, 0], [0, 1], [0, -1],
  [1, 1], [-1, -1], [1, -1], [-1, 1]
];

let board = [];
let mouseDown = false;
let selection = [];
let timerInterval = null;
let syncInterval = null;
let gameEnded = false;

const routesEl = document.getElementById("routes");
let timeLeft = Number(
  routesEl?.dataset?.tiempoInicial ||
  routesEl?.dataset?.tiempo ||
  document.body?.dataset?.tiempoInicial ||
  300
);

if (Number.isNaN(timeLeft) || timeLeft <= 0) {
  timeLeft = 300;
}

// NUEVO: guarda el tiempo total inicial (no se muta) para calcular el % de la barra
const TIEMPO_TOTAL_SOPA = timeLeft;

let timerStartedByProfesor = false;
let ultimaFaseDetectada = null;

console.log("Sopa de Letras — build sincronizada • timeLeft =", timeLeft);

function createFixedBoard() {
  const gridTemplate = [
    "IDEAUDAXIHHE",
    "DOGZAREDILXC",
    "DAVXRCSNBACL",
    "GHDQTARGWUWI",
    "RNNIEQUIPOHE",
    "OESVVIZAYZFN",
    "WGNKAIIEGYKT",
    "DOCMDLTLLTIE",
    "ZCBXOROADMCR",
    "JIUTLSGREWCB",
    "VOHYJCHDMRIO",
    "IMPACTOULFCL"
  ];
  board = gridTemplate.map(row => row.split(""));
}

function fillRandom() {
  const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  for (let r = 0; r < gridSize; r++) {
    for (let c = 0; c < gridSize; c++) {
      if (board[r][c] === "X" || board[r][c] === undefined) {
        board[r][c] = letters[Math.floor(Math.random() * letters.length)];
      }
    }
  }
}

function render() {
  if (!gridEl) return;
  gridEl.innerHTML = "";
  for (let r = 0; r < gridSize; r++) {
    for (let c = 0; c < gridSize; c++) {
      const cell = document.createElement("div");
      cell.className = "cell";
      cell.textContent = board[r][c];
      cell.dataset.r = r;
      cell.dataset.c = c;
      cell.addEventListener("mousedown", (e) => { e.preventDefault(); handleDown(e); });
      cell.addEventListener("mouseover", (e) => { e.preventDefault(); handleOver(e); });
      cell.addEventListener("mouseup", (e) => { e.preventDefault(); handleUp(e); });
      cell.addEventListener("touchstart", (e) => { e.preventDefault(); handleDown(convertTouch(e)); }, { passive: false });
      cell.addEventListener("touchmove", (e) => { e.preventDefault(); handleOver(convertTouch(e)); }, { passive: false });
      cell.addEventListener("touchend", (e) => { e.preventDefault(); handleUp(e); }, { passive: false });
      gridEl.appendChild(cell);
    }
  }
  gridEl.addEventListener("dragstart", (e) => e.preventDefault());
  document.addEventListener("mouseup", cancelDragOutside);
  document.addEventListener("touchend", cancelDragOutside, { passive: false });
}

function convertTouch(e) {
  const t = e.touches && e.touches[0] ? e.touches[0] : (e.changedTouches ? e.changedTouches[0] : null);
  if (!t) return e;
  const el = document.elementFromPoint(t.clientX, t.clientY);
  return { currentTarget: el, button: 0 };
}

function handleDown(e) {
  if (e.button !== 0) return;
  if (!e.currentTarget || !e.currentTarget.dataset) return;
  if (gameEnded) return;
  mouseDown = true;
  clearTempSelection();
  addToSelection(e.currentTarget);
}

function handleOver(e) {
  if (!mouseDown || gameEnded) return;
  if (!e.currentTarget || !e.currentTarget.dataset) return;
  addToSelection(e.currentTarget, true);
}

function handleUp() {
  if (!mouseDown) return;
  mouseDown = false;
  checkSelection();
}

function cancelDragOutside() {
  if (!mouseDown) return;
  mouseDown = false;
  checkSelection();
}

function addToSelection(el, validateLine = false) {
  if (!el || !el.dataset) return;
  const r = parseInt(el.dataset.r, 10);
  const c = parseInt(el.dataset.c, 10);
  if (Number.isNaN(r) || Number.isNaN(c)) return;
  if (selection.some(s => s.r === r && s.c === c)) return;
  if (validateLine && selection.length >= 1) {
    const r0 = selection[0].r;
    const c0 = selection[0].c;
    const dr = r - r0;
    const dc = c - c0;
    const gcd = (a, b) => b ? gcd(b, a % b) : Math.abs(a);
    const g = gcd(Math.abs(dr), Math.abs(dc)) || 1;
    const udr = dr / g;
    const udc = dc / g;
    const isValidDir = DIRS.some(([dx, dy]) => dx === udc && dy === udr);
    if (!isValidDir) return;
  }
  el.classList.add("selected");
  selection.push({ r, c, el });
}

function clearTempSelection() {
  selection.forEach(s => s.el && s.el.classList.remove("selected"));
  selection = [];
}

function textFromSelection() {
  if (selection.length <= 1) {
    return selection.map(s => board[s.r][s.c]).join("");
  }
  const s0 = selection[0];
  const s1 = selection[1];
  const dr = Math.sign(s1.r - s0.r);
  const dc = Math.sign(s1.c - s0.c);
  selection.sort((a, b) =>
    ((a.r - s0.r) * dr + (a.c - s0.c) * dc) -
    ((b.r - s0.r) * dr + (b.c - s0.c) * dc)
  );
  return selection.map(s => board[s.r][s.c]).join("");
}

async function checkSelection() {
  if (selection.length === 0 || gameEnded) return;
  const str = textFromSelection();
  const rev = [...str].reverse().join("");
  const candidates = words.filter(w => !isWordFound(w));
  const match = candidates.find(w => w === str || w === rev);
  if (match) {
    selection.forEach(s => {
      if (!s.el) return;
      s.el.classList.remove("selected");
      s.el.classList.add("found");
      s.el.style.pointerEvents = "none";
    });
    markWordAsFound(match);
    if (typeof window.sonarPalabraEncontrada === "function") {
      window.sonarPalabraEncontrada();
    }
    await registrarPalabraEncontrada(match);
    clearTempSelection();
    updateStatus();
    if (allFound()) {
      endGame(true);
    }
  } else {
    clearTempSelection();
  }
}

function getWordListItem(word) {
  let li = document.querySelector(`#word-list li[data-word="${word}"]`);
  if (li) return li;
  const items = document.querySelectorAll("#word-list li");
  for (const item of items) {
    if (item.textContent.trim().toUpperCase() === word) return item;
  }
  return null;
}

function isWordFound(word) {
  const li = getWordListItem(word);
  return li ? li.classList.contains("found") : false;
}

function markWordAsFound(word) {
  const li = getWordListItem(word);
  if (li) li.classList.add("found");
}

function updateStatus() {
  if (!statusEl) return;
  const total = words.length;
  const items = document.querySelectorAll("#word-list li.found");
  const found = items ? items.length : 0;
  statusEl.textContent = `${found}/${total} ${tJuego("sopa_estado_encontradas", "encontradas")}`;
}

function allFound() {
  const list = document.querySelectorAll("#word-list li");
  if (!list.length) return false;
  return [...list].every(li => li.classList.contains("found"));
}

function bloquearJuego() {
  const grid = document.getElementById("grid");
  if (grid) {
    grid.style.pointerEvents = "none";
    grid.style.opacity = "0.4";
  }
}

function mostrarEsperandoProfesor() {
  const timerContainer = document.getElementById("timer-container");
  if (timerContainer) {
    timerContainer.classList.remove("blur-target-bloqueado", "timer-esperando");
    timerContainer.classList.add("blur-target-activo");
  }
  const titulo = document.getElementById("tituloSopa");
  const subtitulo = document.getElementById("subtituloSopa");
  const wordsBox = document.getElementById("wordsBox");
  const grid = document.getElementById("grid");
  [titulo, subtitulo, wordsBox, grid].forEach(el => {
    if (!el) return;
    el.classList.remove("blur-target-activo");
    el.classList.add("blur-target-bloqueado");
  });
}

function endGame(won, alarmAudio = null) {
  if (gameEnded) return;
  gameEnded = true;
  bloquearJuego();

  if (typeof window.musicaSopa?.detener === "function") {
    window.musicaSopa.detener();
  }

  if (alarmAudio && !won) {
    try {
      alarmAudio.pause();
      alarmAudio.currentTime = 0;
    } catch (_) {}
  }
  if (!won) {
    pauseTimerLocally();
  }
  if (won) {
    setTimeout(showWinModal, 200);
  } else {
    setTimeout(showTimeUpModal, 0);
  }
}

async function showWinModal() {
  if (!gameEnded) return;

  const modal = document.getElementById("winModal");
  const title = document.getElementById("winTitle");
  // ── Sin botón OK — solo mostramos el modal con texto de espera ──
  const esperaEl = document.getElementById("winEspera");

  if (!modal || !title) return;

  const resultado = await registrarSopaCompletada();

  if (resultado?.primer_equipo) {
    title.textContent = tJuego("sopa_win_primer_titulo", "¡Ganaste! Fuiste el primer equipo");
  } else {
    title.textContent = tJuego("sopa_win_otro_titulo", "¡Buen trabajo!");
  }

  // Texto de espera
  if (esperaEl) {
    esperaEl.textContent = tJuego("sopa_win_espera", "Esperando a los demás escuadrones...");
  }

  modal.style.display = "flex";
  modal.setAttribute("aria-hidden", "false");

  const victoryAudio = document.getElementById("victory-sound");
  if (victoryAudio) {
    try {
      victoryAudio.currentTime = 0;
      victoryAudio.play();
    } catch (_) {}
  }
  // Sin btn.onclick — no hay botón OK
}

function showTimeUpModal() {
  if (!gameEnded) return;
  const modal = document.getElementById("timeModal");
  const btn = document.getElementById("btnRetry");
  if (!modal || !btn) return;
  modal.style.display = "flex";
  modal.setAttribute("aria-hidden", "false");
  btn.onclick = () => {
    modal.style.display = "none";
    modal.setAttribute("aria-hidden", "true");
    mostrarEsperandoProfesor();
    revisarEstadoProfesor();
  };
}

function renderTimer() {
  const timerEl = document.getElementById("timer");
  if (!timerEl) return;
  const tiempoSeguro = Math.max(0, Number(timeLeft) || 0);
  const min = Math.floor(tiempoSeguro / 60);
  const sec = tiempoSeguro % 60;
  timerEl.textContent = `${min.toString().padStart(2, "0")}:${sec.toString().padStart(2, "0")}`;
  if (tiempoSeguro <= 10) {
    timerEl.classList.add("low-time");
  } else {
    timerEl.classList.remove("low-time");
  }

  // NUEVO: actualizar la barra de tiempo (si existe en el HTML; si no, no hace nada)
  const fillEl = document.getElementById("timer-bar-fill");
  if (fillEl) {
    const pct = TIEMPO_TOTAL_SOPA > 0
      ? Math.max(0, Math.min(100, (tiempoSeguro / TIEMPO_TOTAL_SOPA) * 100))
      : 0;
    fillEl.style.width = pct + "%";
    fillEl.classList.toggle("low-time", tiempoSeguro <= 10);
  }
}

function pauseTimerLocally() {
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
}

function startTimer() {
  const alarmAudio = document.getElementById("alarm-audio");
  if (timerInterval) return;
  renderTimer();
  timerInterval = setInterval(() => {
    timeLeft--;
    renderTimer();
    if (timeLeft <= 0) {
      pauseTimerLocally();
      endGame(false, alarmAudio);
    }
  }, 1000);
}

/* ============================================================================
   DIMENSIONADO DEL TABLERO
   Este bloque escribe --cell-size INLINE en <html>, así que manda por sobre
   cualquier valor de estilo_sopadeletras.css. Todo el tamaño del tablero se
   decide acá.

   Reglas:
   · CELDA_MIN / CELDA_MAX acotan el resultado (antes: 22 / 60 → el tablero
     quedaba pegado al piso en laptops de ~700px de alto).
   · SCROLL_PERMITIDO deja que el tablero sea más alto que el viewport en una
     cantidad controlada; la página ya scrolleaba por el alto de la cabecera +
     lista de palabras, así que se aprovecha ese margen en vez de encoger.
   · Se mide por ID (#tituloSopa, #subtituloSopa, #wordsBox). El querySelector("p")
     anterior tomaba el primer <p> del documento — podía ser el de la tarjeta de
     inicio de fase o el del diálogo, inflando headerH y achicando la celda.
   ========================================================================== */
(function makeGridResponsive() {
  const root = document.documentElement;

  const CELDA_MIN = 26;
  const CELDA_MAX = 80;
  const SCROLL_PERMITIDO = 140;
  const MARGENES_V = 48;   // márgenes verticales entre h1, subtítulo, timer y grid

  let rafPendiente = null;

  function altoVisible(el) {
    // offsetParent null ⇒ display:none (no ocupa alto real)
    return el && el.offsetParent !== null ? el.offsetHeight : 0;
  }

  function adjustGrid() {
    const container = document.querySelector(".game-container");
    if (!container) return;

    const cols = gridSize;
    const rows = gridSize;
    const gap = window.innerWidth <= 700 ? 3 : 4;

    const titleEl = document.getElementById("tituloSopa") || container.querySelector("h1");
    const subEl = document.getElementById("subtituloSopa");
    const timerBox = document.getElementById("timer-container");
    const wordsBox = document.getElementById("wordsBox") || document.querySelector(".words");

    const cs = getComputedStyle(container);
    const bodyCS = getComputedStyle(document.body);

    // ── Presupuesto horizontal ──
    const innerW = container.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
    const maxWidth = Math.min(innerW, window.innerWidth * 0.94);

    // ── Presupuesto vertical ──
    const bodyVPadding = parseFloat(bodyCS.paddingTop) + parseFloat(bodyCS.paddingBottom);
    const containerVPadding = parseFloat(cs.paddingTop) + parseFloat(cs.paddingBottom);
    const headerH = altoVisible(titleEl) + altoVisible(subEl) + altoVisible(timerBox);
    const wordsH = altoVisible(wordsBox);

    const presupuestoH = window.innerHeight - bodyVPadding + SCROLL_PERMITIDO;
    const availableH = presupuestoH - headerH - wordsH - containerVPadding - MARGENES_V;

    const cellByWidth = (maxWidth - (cols - 1) * gap - 2 * gap) / cols;
    const cellByHeight = (availableH - (rows - 1) * gap - 2 * gap) / rows;

    const cell = Math.floor(Math.min(cellByWidth, cellByHeight));
    const finalSize = Math.max(CELDA_MIN, Math.min(cell, CELDA_MAX));

    root.style.setProperty("--cell-size", finalSize + "px");
    root.style.setProperty("--cols", cols);
    root.style.setProperty("--rows", rows);
    root.style.setProperty("--gap", gap + "px");
  }

  function pedirAjuste() {
    if (rafPendiente) return;
    rafPendiente = requestAnimationFrame(() => {
      rafPendiente = null;
      adjustGrid();
    });
  }

  // Se expone para poder recalcular después de render() y de cambiar idioma:
  // el alto de la lista de palabras (chips) cambia y con él el del tablero.
  window.ajustarGridSopa = pedirAjuste;

  window.addEventListener("resize", pedirAjuste);
  window.addEventListener("orientationchange", pedirAjuste);
  window.addEventListener("load", pedirAjuste);

  // Share Tech Mono cambia el alto de los chips al cargar → recalcular.
  if (document.fonts?.ready) {
    document.fonts.ready.then(pedirAjuste).catch(() => {});
  }

  adjustGrid();
})();

function obtenerSesionId() {
  const routes = document.getElementById("routes");
  const sesionId =
    routes?.dataset?.sesionId ||
    document.body?.dataset?.sesionId ||
    document.documentElement?.dataset?.sesionId;
  return sesionId;
}

function procesarEstadoSesion(data) {
  if (!data) return;
  const faseActual = data.faseActual;
  ultimaFaseDetectada = faseActual;
  if (faseActual && faseActual !== "f1_sopa") {
    if (data.rutaAlumno && window.location.pathname !== data.rutaAlumno) {
      window.location.href = data.rutaAlumno;
    }
    return;
  }
  if (gameEnded) return;
  const backendSeconds = Number(data.segundosRestantes);
  if (!Number.isNaN(backendSeconds) && backendSeconds >= 0) {
    timeLeft = backendSeconds;
    renderTimer();
  }
  if (!timerStartedByProfesor && data.timerCorriendo && data.inicioFaseHabilitado) {
    timerStartedByProfesor = true;
    startTimer();
    return;
  }
  if (timerStartedByProfesor && !data.timerCorriendo) {
    pauseTimerLocally();
    timerStartedByProfesor = false;
  }
}

async function revisarEstadoProfesor() {
  try {
    const sesionId = obtenerSesionId();
    if (!sesionId) return;
    const res = await fetch(`/sesion/${sesionId}/estado/`, {
      credentials: "same-origin",
      cache: "no-store"
    });
    if (!res.ok) return;
    const data = await res.json();
    procesarEstadoSesion(data);
  } catch (error) {
    console.error("Error sincronizando sopa:", error);
  }
}

window.addEventListener("idiomaJuegoCambiado", () => {
  updateStatus();
  window.ajustarGridSopa?.();
});

(function init() {
  createFixedBoard();
  fillRandom();
  render();
  updateStatus();
  renderTimer();
  window.ajustarGridSopa?.();
  revisarEstadoProfesor();
  syncInterval = setInterval(revisarEstadoProfesor, 1500);
})();