document.addEventListener("DOMContentLoaded", () => {
  const fullscreenBtn = document.getElementById("fullscreen-toggle");
  let controlOverlay = document.getElementById("controls");
  let hideTimeout;

  function enterFullscreen() {
    const elem = document.documentElement;
    if (elem.requestFullscreen) {
      elem.requestFullscreen();
    } else if (elem.webkitRequestFullscreen) { /* Safari */
      elem.webkitRequestFullscreen();
    } else if (elem.msRequestFullscreen) { /* IE11 */
      elem.msRequestFullscreen();
    }
  }

  function exitFullscreen() {
    if (document.exitFullscreen) {
      document.exitFullscreen();
    } else if (document.webkitExitFullscreen) {
      document.webkitExitFullscreen();
    } else if (document.msExitFullscreen) {
      document.msExitFullscreen();
    }
  }

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      enterFullscreen();
    } else {
      exitFullscreen();
    }
  }

  function hideControls() {
    if (controlOverlay) controlOverlay.style.opacity = "0";
  }

  function showControls() {
    if (controlOverlay) controlOverlay.style.opacity = "1";
    clearTimeout(hideTimeout);
    hideTimeout = setTimeout(hideControls, 2500);
  }

  // Hook up fullscreen toggle button
  if (fullscreenBtn) {
    fullscreenBtn.addEventListener("click", toggleFullscreen);
  }

  // Exit fullscreen on ESC
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") exitFullscreen();
  });

  // Exit fullscreen on click
  document.addEventListener("click", () => {
    if (document.fullscreenElement) exitFullscreen();
  });

  // Auto-hide controls after inactivity
  document.addEventListener("mousemove", showControls);
});
