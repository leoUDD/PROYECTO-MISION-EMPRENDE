/* Escapa texto escrito por usuarios antes de insertarlo con innerHTML.
   Sin esto, el nombre de un equipo puede ejecutar código en otras pantallas. */
window.escaparHtml = function (texto) {
  return String(texto ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
};
