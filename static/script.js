document.addEventListener("DOMContentLoaded", function () {
  const startBtn = document.getElementById("startBtn");
  const pauseBtn = document.getElementById("pauseBtn");

  // Standard Metrics
  const volVal = document.getElementById("vol-val");
  const distVal = document.getElementById("dist-val");
  const accVal = document.getElementById("acc-val");
  const timeVal = document.getElementById("time-val");

  // Cards
  const cardOpen = document.getElementById("card-open");
  const cardPinch = document.getElementById("card-pinch");
  const cardClosed = document.getElementById("card-closed");

  // WINDOWS 11 OVERLAY ELEMENTS
  const overlay = document.getElementById("volume-overlay");
  const overlayFill = document.getElementById("overlay-fill"); // The blue bar
  const overlayThumb = document.getElementById("overlay-thumb"); // The round dot
  const overlayIcon = document.getElementById("overlay-icon");
  const overlayText = document.getElementById("overlay-text"); // The number (30 -> 100)

  let overlayTimeout;

  function sendCommand(command) {
    fetch(`/${command}`, { method: "POST" })
      .then((response) => response.json())
      .then((data) => console.log(data.status));
  }

  startBtn.addEventListener("click", () => sendCommand("start"));
  pauseBtn.addEventListener("click", () => sendCommand("pause"));

  function showOverlay() {
    if (overlay.classList.contains("hidden")) {
      overlay.classList.remove("hidden");
    }
    if (overlayTimeout) {
      clearTimeout(overlayTimeout);
      overlayTimeout = null;
    }
  }

  function hideOverlayDelayed() {
    if (!overlayTimeout && !overlay.classList.contains("hidden")) {
      overlayTimeout = setTimeout(() => {
        overlay.classList.add("hidden");
        overlayTimeout = null;
      }, 1000);
    }
  }

  function updateUI(data) {
    // 1. Update Standard Metrics
    volVal.innerText = data.current_volume + "%";
    distVal.innerText = data.finger_distance_mm + "mm";
    accVal.innerText = data.accuracy + "%";
    timeVal.innerText = data.response_time_ms + "ms";

    // 2. Card Logic
    [cardOpen, cardPinch, cardClosed].forEach((card) => {
      card.classList.remove("active-card");
      card.querySelector(".status").innerText = "Inactive";
      card.querySelector(".status").classList.replace("active", "inactive");
    });

    let activeCard = null;
    if (data.current_gesture === "Open Hand") activeCard = cardOpen;
    else if (data.current_gesture === "Pinch") activeCard = cardPinch;
    else if (data.current_gesture === "Closed") activeCard = cardClosed;

    if (activeCard && data.is_running) {
      activeCard.classList.add("active-card");
      activeCard.querySelector(".status").innerText = "Active";
      activeCard
        .querySelector(".status")
        .classList.replace("inactive", "active");
    }

    // 3. WINDOWS 11 OVERLAY LOGIC
    if (!data.is_running) {
      overlay.classList.add("hidden");
      return;
    }

    if (data.current_gesture === "Pinch") {
      // --- VOLUME CHANGING MODE ---
      showOverlay();
      overlay.classList.remove("muted");

      // LOGGING: Check your console (F12) to see if this prints changing numbers!
      // console.log("Volume moving:", data.current_volume);

      // A. UPDATE NUMBER (0-100)
      overlayText.innerText = data.current_volume;

      // B. UPDATE BAR WIDTH (0%-100%)
      overlayFill.style.width = data.current_volume + "%";

      // C. UPDATE DOT POSITION
      overlayThumb.style.left = data.current_volume + "%";

      // D. UPDATE ICON
      if (data.current_volume === 0)
        overlayIcon.className = "fas fa-volume-mute";
      else if (data.current_volume < 50)
        overlayIcon.className = "fas fa-volume-down";
      else overlayIcon.className = "fas fa-volume-up";
    } else if (data.current_gesture === "Closed") {
      // --- MUTE MODE ---
      showOverlay();
      overlay.classList.add("muted");

      overlayIcon.className = "fas fa-volume-xmark";
      overlayText.innerText = "0";
      overlayFill.style.width = "0%";
      overlayThumb.style.left = "0%";
    } else {
      // --- IDLE MODE ---
      hideOverlayDelayed();
    }
  }

  setInterval(() => {
    fetch("/get_data")
      .then((response) => response.json())
      .then((data) => updateUI(data));
  }, 50); // Faster updates (50ms) for smoother animation

  sendCommand("pause");
});
