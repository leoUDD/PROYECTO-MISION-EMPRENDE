(function () {
  document.addEventListener("DOMContentLoaded", () => {
    const box = document.getElementById("textoGuardado");
    const timerEl = document.getElementById("timer");
    const alarm = document.getElementById("alarmAudio");
    let ultimoSegundo = null;
    let alarmaDisparada = false;
    let finLocal = null;
    let intervaloLocal = null;

    function actualizarTextoPropio(texto) {
      if (!box) return;

      if (texto && texto.trim()) {
        box.textContent = texto;
      } else {
        box.innerHTML = '<p class="subtitle">No se encontró texto guardado. Vuelve a la etapa anterior y escribe tu pitch.</p>';
      }
    }

    function reproducirAlarmaSuave() {
      if (!alarm) return;
      try {
        alarm.currentTime = 0;
        alarm.play();
      } catch (_) {}
    }

    function pintarTimer(valor) {
        const min = String(Math.floor(valor / 60)).padStart(2, "0");
        const sec = String(valor % 60).padStart(2, "0");

        timerEl.textContent = `${min}:${sec}`;
        timerEl.dataset.seconds = valor;

        if (ultimoSegundo !== null && valor > 0) {
          alarmaDisparada = false;
        }

        if (valor === 0 && !alarmaDisparada && ultimoSegundo !== 0) {
          reproducirAlarmaSuave();
          alarmaDisparada = true;
        }

        ultimoSegundo = valor;
    }

    function segundosLocales() {
      return Math.max(0, Math.ceil((finLocal - performance.now()) / 1000));
    }

    window.presentarPitchUI = {
      actualizarPitchPropio(texto) {
        actualizarTextoPropio(texto);
      },

      /* Las consultas pueden llegar tarde o desordenadas: pintar cada respuesta
         hacía retroceder el reloj. Mientras corre, se cuenta contra una hora de
         término local y solo se corrige un desfase real con el servidor. */
      actualizarTimer(segundos, corriendo = false) {
        if (!timerEl) return;

        const valor = Math.max(0, Number(segundos || 0));

        if (!corriendo) {
          clearInterval(intervaloLocal);
          intervaloLocal = null;
          finLocal = null;
          pintarTimer(valor);
          return;
        }

        const ahora = performance.now();
        const desfase = finLocal === null ? Infinity : Math.abs(valor - (finLocal - ahora) / 1000);

        if (desfase > 2) {
          finLocal = ahora + valor * 1000;
        }

        if (!intervaloLocal) {
          intervaloLocal = setInterval(() => pintarTimer(segundosLocales()), 200);
        }

        pintarTimer(segundosLocales());
      }
    };

    if (timerEl) {
      const inicial = Math.max(0, Number(timerEl.dataset.seconds || 90));
      window.presentarPitchUI.actualizarTimer(inicial);
    }
  });
})();

/* La ruta de mision corre el contenedor: el timer se centra sobre el, no sobre la ventana. */
(function () {
  const main = document.querySelector("main.pitch-container");
  if (!main) return;

  function centrarTimer() {
    const caja = main.getBoundingClientRect();
    document.body.style.setProperty("--presentar-main-center-x", `${caja.left + caja.width / 2}px`);
  }

  centrarTimer();
  window.addEventListener("resize", centrarTimer, { passive: true });
  if ("ResizeObserver" in window) new ResizeObserver(centrarTimer).observe(main);
})();
