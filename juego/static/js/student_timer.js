/* ============================================================
   MISION EMPRENDE — TIMER ALUMNO / OPCION B
   - Grande al entrar.
   - Compacto al hacer scroll.
   - Detecta 60s / 30s para estados warning/danger.
   - No controla el conteo: solo observa el texto que ya actualiza
     el JS existente de cada actividad.
   ============================================================ */

(function () {
  "use strict";

  const DEFAULT_COMPACT_AFTER = 48;

  function parseTimer(text) {
    if (!text) return null;

    const clean = String(text).trim();

    // mm:ss o hh:mm:ss
    const match = clean.match(/(\d{1,2}):(\d{2})(?::(\d{2}))?/);
    if (!match) return null;

    if (match[3] !== undefined) {
      return (
        Number(match[1]) * 3600 +
        Number(match[2]) * 60 +
        Number(match[3])
      );
    }

    return Number(match[1]) * 60 + Number(match[2]);
  }

  function initStudentTimer(host) {
    if (!host || host.dataset.timerInitialized === "true") return;

    const value =
      host.querySelector(".student-timer-value") ||
      host.querySelector(
        "#timer, #timerTematica, #timerEvaluacion, [role='timer'] strong"
      );

    if (!value) return;

    host.dataset.timerInitialized = "true";

    const compactAfter = Math.max(
      0,
      Number(host.dataset.compactAfter || DEFAULT_COMPACT_AFTER)
    );

    let ticking = false;

    function updateCompactState() {
      const shouldCompact = window.scrollY > compactAfter;

      host.classList.toggle("is-compact", shouldCompact);
      ticking = false;
    }

    function requestCompactUpdate() {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(updateCompactState);
    }

    function updateTimeState() {
      const seconds = parseTimer(value.textContent);

      host.classList.remove("is-warning", "is-danger");

      if (seconds === null || seconds <= 0) return;

      if (seconds <= 30) {
        host.classList.add("is-danger");
      } else if (seconds <= 60) {
        host.classList.add("is-warning");
      }
    }

    window.addEventListener("scroll", requestCompactUpdate, {
      passive: true
    });

    window.addEventListener("resize", requestCompactUpdate, {
      passive: true
    });

    const observer = new MutationObserver(updateTimeState);

    observer.observe(value, {
      childList: true,
      characterData: true,
      subtree: true
    });

    updateCompactState();
    updateTimeState();
  }

  function initAllStudentTimers() {
    document
      .querySelectorAll("[data-student-timer]")
      .forEach(initStudentTimer);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAllStudentTimers);
  } else {
    initAllStudentTimers();
  }
})();

/* ============================================================
   TIMER GLOBAL FINAL — ALINEACION AL MAIN

   - centra el timer respecto al <main> real
   - reserva solo el espacio vertical necesario
   - recalcula en resize/orientation
   - Bubble Map usa html como único scroll root
   ============================================================ */
(function () {
  const GLOBAL_TIMER_MARKER = "student-global-timer-layout";

  let resizeObserver = null;
  let rafId = null;

  function obtenerHost() {
    return (
      document.querySelector("body > .student-timer-host") ||
      document.querySelector(".student-timer-host")
    );
  }

  function obtenerMain() {
    return (
      document.querySelector("body > main") ||
      document.querySelector("main")
    );
  }

  function px(value) {
    const n = Number.parseFloat(value);
    return Number.isFinite(n) ? n : 0;
  }

  function limpiarMargenCalculado(main) {
    if (!main) return;

    if (main.dataset.studentTimerMarginManaged === "1") {
      main.style.removeProperty("margin-top");
      delete main.dataset.studentTimerMarginManaged;
    }
  }

  function alinearTimer() {
    rafId = null;

    const body = document.body;
    const host = obtenerHost();
    const main = obtenerMain();

    if (!body || !host || !main) return;

    body.classList.add(GLOBAL_TIMER_MARKER);

    if (body.classList.contains("bubblemap-page")) {
      document.documentElement.classList.add("bubblemap-scroll-root");
    } else {
      document.documentElement.classList.remove("bubblemap-scroll-root");
    }

    /*
     * Primero quitamos SOLO el margen que este script haya calculado,
     * para medir el layout natural actual.
     */
    limpiarMargenCalculado(main);

    const mainRect = main.getBoundingClientRect();

    const mainCenterX =
      mainRect.left + mainRect.width / 2;

    body.style.setProperty(
      "--student-main-center-x",
      `${mainCenterX}px`
    );

    body.style.setProperty(
      "--student-main-width",
      `${Math.max(0, mainRect.width)}px`
    );

    /*
     * Esperamos un frame para que el host ya haya tomado
     * position:fixed + center-x y podamos medir su altura real.
     */
    requestAnimationFrame(() => {
      const currentHost = obtenerHost();
      const currentMain = obtenerMain();

      if (!currentHost || !currentMain) return;

      const timerRect =
        currentHost.getBoundingClientRect();

      const newMainRect =
        currentMain.getBoundingClientRect();

      const styles =
        getComputedStyle(body);

      const gap =
        px(styles.getPropertyValue("--student-timer-gap")) || 12;

      const desiredMainTop =
        timerRect.bottom + gap;

      /*
       * Solo agregamos espacio si el main chocaría con el timer.
       * No imponemos un margen gigante a páginas que ya tienen
       * suficiente aire superior.
       */
      const missing =
        Math.max(
          0,
          desiredMainTop - newMainRect.top
        );

      if (missing > 0.5) {
        const currentMargin =
          px(getComputedStyle(currentMain).marginTop);

        currentMain.style.setProperty(
          "margin-top",
          `${currentMargin + missing}px`,
          "important"
        );

        currentMain.dataset.studentTimerMarginManaged = "1";
      }
    });
  }

  function programarAlineacion() {
    if (rafId !== null) {
      cancelAnimationFrame(rafId);
    }

    rafId =
      requestAnimationFrame(alinearTimer);
  }

  function observarMain() {
    const main = obtenerMain();

    if (!main || typeof ResizeObserver === "undefined") {
      return;
    }

    resizeObserver?.disconnect();

    resizeObserver =
      new ResizeObserver(() => {
        programarAlineacion();
      });

    resizeObserver.observe(main);
  }

  function iniciar() {
    if (!obtenerHost() || !obtenerMain()) return;

    alinearTimer();
    observarMain();

    setTimeout(programarAlineacion, 80);
    setTimeout(programarAlineacion, 250);
    setTimeout(programarAlineacion, 600);
  }

  if (document.readyState === "loading") {
    document.addEventListener(
      "DOMContentLoaded",
      iniciar,
      { once: true }
    );
  } else {
    iniciar();
  }

  window.addEventListener(
    "resize",
    programarAlineacion,
    { passive: true }
  );

  window.addEventListener(
    "orientationchange",
    () => {
      setTimeout(() => {
        programarAlineacion();
        observarMain();
      }, 160);
    },
    { passive: true }
  );

  /*
   * Si una vista cambia contenido/idioma y el main modifica su ancho,
   * volvemos a centrar.
   */
  window.addEventListener(
    "idiomaJuegoCambiado",
    () => setTimeout(programarAlineacion, 40)
  );
})();
