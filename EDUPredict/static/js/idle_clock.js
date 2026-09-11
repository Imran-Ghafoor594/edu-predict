(function () {
  const IDLE_TIMEOUT = 10 * 5000; // 10 seconds (test ke liye, baad mein 2 * 60 * 1000 karna)
  let idleTimer = null;
  let clockInterval = null;
  let spikesCreated = false;

  // ── Google Font ──
  if (!document.querySelector('link[href*="Comfortaa"]')) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "https://fonts.googleapis.com/css2?family=Comfortaa:wght@300;400;500;600;700&display=swap";
    document.head.appendChild(link);
  }

  // ── All CSS inline ──
  const style = document.createElement("style");
  style.textContent = `
    #idle-overlay {
      display: none;
      position: fixed;
      inset: 0;
      z-index: 9999;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      gap: 30px;
      font-family: "Comfortaa", sans-serif;

      /* ✅ FIX 1: Gradient seedha overlay pe lagao */
      background: radial-gradient(ellipse at center, #302b63 0%, #0f0c29 70%, #000000 100%);
    }

    #idle-overlay.active {
      display: flex;
    }

    /* ✅ FIX 2: shakeX animation define karo */
    @keyframes shakeX {
      0%, 100% { transform: translateX(0); }
      15%       { transform: translateX(-8px); }
      30%       { transform: translateX(8px); }
      45%       { transform: translateX(-6px); }
      60%       { transform: translateX(6px); }
      75%       { transform: translateX(-4px); }
      90%       { transform: translateX(4px); }
    }

    /* Subtle background pulse */
    @keyframes pulseBG {
      0%   { background-size: 100%; }
      100% { background-size: 110%; }
    }

    .idle-clock {
      --clock-size: 360px;
      width: var(--clock-size);
      height: var(--clock-size);
      position: relative;
      color: white;
    }

    .idle-spike {
      position: absolute;
      width: 8px;
      height: 1px;
      background: #fff9;
      transform-origin: 50% 50%;
      inset: 0;
      margin: auto;
      transform: rotate(var(--rotate)) translateX(var(--dail-size));
    }

    .idle-spike:nth-child(5n + 1) {
      box-shadow: -7px 0 #fff9;
      width: 12px;
    }

    .idle-spike:nth-child(5n + 1)::after {
      content: attr(data-i);
      position: absolute;
      right: 22px;
      top: -10px;
      font-size: 10px;
      transition: 1s linear;
      transform: rotate(calc(var(--dRotate) - var(--rotate)));
    }

    .idle-seconds {
      --dRotate: 0deg;
      --dail-size: calc((var(--clock-size) / 2) - 10px);
      position: absolute;
      inset: 0;
      transition: 1s linear;
      transform: rotate(calc(-1 * var(--dRotate)));
    }

    .idle-minutes {
      --dRotate: 0deg;
      --dail-size: calc((var(--clock-size) / 2) - 65px);
      position: absolute;
      inset: 0;
      transition: 1s linear;
      transform: rotate(calc(-1 * var(--dRotate)));
    }

    .idle-hour {
      font-size: 70px;
      font-weight: 900;
      position: absolute;
      left: 50%;
      top: 50%;
      transform: translate(-50%, -50%);
      margin-left: -40px;
    }

    .idle-minute-label {
      z-index: 10;
      font-size: 36px;
      font-weight: 900;
      position: absolute;
      background: rgba(0, 0, 0, 0.55);
      right: 75px;
      top: 50%;
      transform: translateY(-50%);
      padding: 4px;
    }

    .idle-minute-label::after {
      content: "";
      position: absolute;
      border: 2px solid #29ff08;
      border-right: none;
      height: 55px;
      left: -10px;
      top: 50%;
      border-radius: 40px 0 0 40px;
      width: 155px;
      transform: translateY(-50%);
      pointer-events: none;
    }

    #idle-message {
      color: #ffffff66;
      font-size: 14px;
      letter-spacing: 2px;
    }

    #idle-continue-btn {
      background: transparent;
      border: 2px solid #29ff08;
      color: #29ff08;
      font-family: "Comfortaa", sans-serif;
      font-size: 18px;
      padding: 12px 40px;
      border-radius: 50px;
      cursor: pointer;
      letter-spacing: 2px;
      transition: all 0.3s ease;
    }

    /* ✅ FIX 3: shakeX hover working */
    #idle-continue-btn:hover {
      animation: shakeX 0.55s;
      border-color: #29ff08;
      background: rgba(41, 255, 8, 0.1);
    }
  `;
  document.head.appendChild(style);

  // ── HTML Overlay ──
  const overlay = document.createElement("div");
  overlay.id = "idle-overlay";
  overlay.innerHTML = `
    <div class="idle-clock">
      <div class="idle-seconds"></div>
      <div class="idle-minutes"></div>
      <span class="idle-hour">00 min</span>
      <span class="idle-minute-label">00 sec</span>
    </div>
    <p id="idle-message">You've been away...</p>
    <button id="idle-continue-btn">&#9654; Continue</button>
  `;
  document.body.appendChild(overlay);

  // ── Create 60 spikes ──
  function createSpikes() {
    if (spikesCreated) return;
    const sDiv = overlay.querySelector(".idle-seconds");
    const mDiv = overlay.querySelector(".idle-minutes");
    for (let i = 0; i < 60; i++) {
      const s = document.createElement("i");
      const m = document.createElement("i");
      s.className = "idle-spike";
      m.className = "idle-spike";
      s.style.setProperty("--rotate", `${i * 6}deg`);
      m.style.setProperty("--rotate", `${i * 6}deg`);
      s.setAttribute("data-i", i);
      m.setAttribute("data-i", i);
      sDiv.append(s);
      mDiv.append(m);
    }
    spikesCreated = true;
  }

  // ── Clock tick ──
  function updateClock() {
    const now = new Date();
    const s = now.getSeconds();
    const m = now.getMinutes();
    const h = now.getHours();
    overlay.querySelector(".idle-hour").textContent = h.toString().padStart(2, "0");
    overlay.querySelector(".idle-minute-label").textContent = m.toString().padStart(2, "0");
    overlay.querySelector(".idle-seconds").style.setProperty("--dRotate", `${s * 6}deg`);
    overlay.querySelector(".idle-minutes").style.setProperty("--dRotate", `${m * 6}deg`);
  }

  // ── Show / Hide ──
  function showIdleScreen() {
    createSpikes();
    overlay.classList.add("active");
    updateClock();
    clockInterval = setInterval(updateClock, 1000);
  }

  function hideIdleScreen() {
    overlay.classList.remove("active");
    clearInterval(clockInterval);
  }

  // ── Reset timer on any activity ──
  function resetIdleTimer() {
    clearTimeout(idleTimer);
    if (overlay.classList.contains("active")) return;
    idleTimer = setTimeout(showIdleScreen, IDLE_TIMEOUT);
  }

  // ── Continue button ──
  document.getElementById("idle-continue-btn").addEventListener("click", () => {
    hideIdleScreen();
    resetIdleTimer();
  });

  // ── Activity listeners ──
  ["mousemove", "mousedown", "keydown", "touchstart", "scroll"].forEach(
    (e) => document.addEventListener(e, resetIdleTimer)
  );

  // ── Start ──
  resetIdleTimer();
})();