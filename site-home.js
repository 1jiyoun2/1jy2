(() => {
  if (document.querySelector(".site-home-button")) return;

  const homeUrl = location.hostname.endsWith("github.io") ? "/1jy2/" : "/";
  const link = document.createElement("a");
  link.className = "site-home-button";
  link.href = homeUrl;
  link.setAttribute("aria-label", "메인으로 이동");
  link.textContent = "⌂ Home";

  const style = document.createElement("style");
  style.textContent = `
    .site-home-button {
      position: fixed;
      right: 18px;
      bottom: 18px;
      z-index: 9999;
      display: inline-flex;
      align-items: center;
      min-height: 34px;
      padding: 6px 11px;
      border: 1px solid #cfd4dc;
      background: rgba(255,255,255,.96);
      color: #334155 !important;
      font: 600 12px/1.2 "Malgun Gothic", Arial, sans-serif;
      text-decoration: none !important;
      box-shadow: 0 2px 8px rgba(15,23,42,.08);
    }
    .site-home-button:hover {
      background: #f7f8fa;
      border-color: #aeb5bf;
    }
    @media (max-width: 640px) {
      .site-home-button {
        right: 12px;
        bottom: 12px;
      }
    }
  `;

  document.head.appendChild(style);
  document.body.appendChild(link);
})();