(function () {
  const root = document.documentElement;
  const themeButtons = document.querySelectorAll("[data-theme-toggle]");
  const storedTheme = localStorage.getItem("theme");
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const themeIcons = {
    sun: '<svg class="theme-icon theme-icon--sun" viewBox="0 0 24 24" aria-hidden="true"><circle class="theme-icon__core" cx="12" cy="12" r="4"></circle><path class="theme-icon__rays" d="M12 2v2.2M12 19.8V22M4.93 4.93l1.56 1.56M17.51 17.51l1.56 1.56M2 12h2.2M19.8 12H22M4.93 19.07l1.56-1.56M17.51 6.49l1.56-1.56"></path></svg>',
    moon: '<svg class="theme-icon theme-icon--moon" viewBox="0 0 24 24" aria-hidden="true"><path class="theme-icon__moon" d="M20.4 14.5A8.5 8.5 0 0 1 9.5 3.6a8.5 8.5 0 1 0 10.9 10.9Z"></path></svg>'
  };

  function setTheme(theme, animate) {
    root.dataset.theme = theme;
    localStorage.setItem("theme", theme);
    themeButtons.forEach((button) => {
      const iconName = theme === "dark" ? "sun" : "moon";
      button.innerHTML = themeIcons[iconName];
      button.dataset.themeIcon = iconName;
      button.title = theme === "dark" ? "切换浅色模式" : "切换深色模式";
      button.setAttribute("aria-label", button.title);
      if (animate) {
        button.classList.remove("is-animating");
        window.requestAnimationFrame(() => button.classList.add("is-animating"));
      }
    });
  }

  setTheme(storedTheme || (prefersDark ? "dark" : "light"), false);
  themeButtons.forEach((button) => {
    button.addEventListener("animationend", () => button.classList.remove("is-animating"));
    button.addEventListener("click", () => setTheme(root.dataset.theme === "dark" ? "light" : "dark", true));
  });

  document.querySelectorAll("[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!window.confirm(form.getAttribute("data-confirm") || "确认继续？")) event.preventDefault();
    });
  });

  document.querySelectorAll("[data-file-name]").forEach((input) => {
    const target = document.querySelector(input.getAttribute("data-file-name"));
    if (!target) return;
    input.addEventListener("change", () => {
      target.textContent = input.files && input.files[0] ? input.files[0].name : "";
    });
  });

  document.querySelectorAll("[data-countdown]").forEach((element) => {
    let remaining = Number.parseInt(element.textContent, 10);
    if (!Number.isFinite(remaining)) return;
    const timer = window.setInterval(() => {
      remaining = Math.max(0, remaining - 1);
      element.textContent = String(remaining);
      if (remaining === 0) window.clearInterval(timer);
    }, 1000);
  });

  const modal = document.querySelector("[data-lightbox-modal]");
  if (!modal) return;
  const image = modal.querySelector("[data-lightbox-image]");
  const label = modal.querySelector("[data-lightbox-label]");
  const counter = modal.querySelector("[data-lightbox-counter]");
  const closeButtons = modal.querySelectorAll("[data-lightbox-close]");
  const prevButton = modal.querySelector("[data-lightbox-prev]");
  const nextButton = modal.querySelector("[data-lightbox-next]");
  const items = Array.from(document.querySelectorAll("[data-lightbox]"));
  let currentIndex = 0;

  function show(index) {
    if (!items.length) return;
    currentIndex = (index + items.length) % items.length;
    const item = items[currentIndex];
    image.src = item.dataset.lightbox;
    image.alt = item.dataset.name || "";
    label.textContent = item.dataset.name || "";
    counter.textContent = `${currentIndex + 1} / ${items.length}`;
  }
  function close() {
    modal.classList.remove("is-open");
    document.body.style.overflow = "";
    image.removeAttribute("src");
  }
  items.forEach((item, index) => item.addEventListener("click", () => { show(index); modal.classList.add("is-open"); document.body.style.overflow = "hidden"; }));
  closeButtons.forEach((button) => button.addEventListener("click", close));
  prevButton && prevButton.addEventListener("click", () => show(currentIndex - 1));
  nextButton && nextButton.addEventListener("click", () => show(currentIndex + 1));
  modal.addEventListener("click", (event) => { if (event.target === modal) close(); });
  document.addEventListener("keydown", (event) => {
    if (!modal.classList.contains("is-open")) return;
    if (event.key === "Escape") close();
    if (event.key === "ArrowLeft") show(currentIndex - 1);
    if (event.key === "ArrowRight") show(currentIndex + 1);
  });
})();
