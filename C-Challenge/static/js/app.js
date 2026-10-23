/*
 * Núcleo S.A. - cliente web interno
 * build staging v2.3.1
 */
(function () {
  "use strict";

  // Config heredada del entorno dev. TODO: mover a variables de entorno
  // antes de pasar a producción (ticket NUC-412).
  const CONFIG = {
    api: "/api",
    JWT_SECRET: "dev-secret-123",       // clave de firma (dev)
    JWT_ALG: "HS256",
    session_cookie: "token",
    debug: false,
  };

  function ping() {
    try {
      fetch(CONFIG.api + "/health").catch(function () {});
    } catch (e) {}
  }

  document.addEventListener("DOMContentLoaded", ping);

  window.__NUCLEO__ = CONFIG;
})();
