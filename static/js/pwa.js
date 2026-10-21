(() => {
  if ("serviceWorker" in navigator && window.isSecureContext) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/service-worker.js", { scope: "/" }).catch((error) => {
        console.error("تعذّر تفعيل وضع PWA.", error);
      });
    });
  }

  const isStandalone = window.matchMedia("(display-mode: standalone)").matches || navigator.standalone === true;
  const isAppleMobile = /iphone|ipad|ipod/i.test(navigator.userAgent)
    || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  let installPrompt = null;
  let installBar;

  const connectionNotice = document.createElement("div");
  connectionNotice.className = "pwa-connection-notice";
  connectionNotice.setAttribute("role", "status");
  connectionNotice.setAttribute("aria-live", "polite");
  connectionNotice.textContent = "أنت غير متصل بالإنترنت";
  document.body.append(connectionNotice);

  function updateConnectionStatus() {
    connectionNotice.hidden = navigator.onLine;
  }

  window.addEventListener("online", updateConnectionStatus);
  window.addEventListener("offline", updateConnectionStatus);
  updateConnectionStatus();

  if (isStandalone) return;

  function createInstallBar(label) {
    installBar = document.createElement("aside");
    installBar.className = "pwa-install-bar";
    installBar.setAttribute("aria-label", "تثبيت تطبيق Copra");
    installBar.innerHTML = '<img src="/static/images/copra-icon-192.png" alt="" width="40" height="40"><span></span><button type="button"></button>';
    installBar.querySelector("span").textContent = label;
    installBar.querySelector("button").textContent = isAppleMobile ? "طريقة التثبيت" : "تثبيت";
    installBar.querySelector("button").addEventListener("click", async () => {
      if (isAppleMobile) {
        showAppleInstallHelp();
        return;
      }
      if (!installPrompt) return;
      await installPrompt.prompt();
      await installPrompt.userChoice;
      installPrompt = null;
      installBar?.remove();
      installBar = undefined;
    });
    document.body.append(installBar);
  }

  function showAppleInstallHelp() {
    let help = document.querySelector(".pwa-install-help");
    if (!help) {
      help = document.createElement("div");
      help.className = "pwa-install-help";
      help.setAttribute("role", "dialog");
      help.setAttribute("aria-modal", "true");
      help.setAttribute("aria-labelledby", "pwa-help-title");
      help.innerHTML = '<div><button class="pwa-help-close" type="button" aria-label="إغلاق">×</button><h2 id="pwa-help-title">أضف Copra إلى الشاشة الرئيسية</h2><p>من Safari اضغط زر المشاركة <span aria-hidden="true">□↑</span>، ثم اختر <strong>إضافة إلى الشاشة الرئيسية</strong>.</p></div>';
      help.querySelector("button").addEventListener("click", () => help.remove());
      help.addEventListener("click", (event) => {
        if (event.target === help) help.remove();
      });
      document.body.append(help);
    }
  }

  if (isAppleMobile) {
    createInstallBar("ثبّت Copra على هاتفك");
  } else {
    window.addEventListener("beforeinstallprompt", (event) => {
      event.preventDefault();
      installPrompt = event;
      createInstallBar("ثبّت Copra على هاتفك");
    });
  }

  window.addEventListener("appinstalled", () => {
    installBar?.remove();
    installBar = undefined;
    installPrompt = null;
  });
})();
