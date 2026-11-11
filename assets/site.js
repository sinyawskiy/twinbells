(function () {
  "use strict";

  var LANG_KEY = "twinbells.lang";
  var LANGS = ["ru", "en", "es", "cn"];
  var HTML_LANG = { ru: "ru", en: "en", es: "es", cn: "zh-CN" };

  var UI = {
    ru: {
      privacy: "Политика конфиденциальности",
      description: "Описание приложения",
      descriptionFull: "Полное описание приложения",
      toc: "Содержание",
      backToTop: "Наверх",
      footerNote: "Данные остаются на устройстве.",
      skip: "К содержанию",
      exercises: "Упражнения",
      programs: "Программы",
      tbf: "TBF"
    },
    en: {
      privacy: "Privacy policy",
      description: "App description",
      descriptionFull: "Full app description",
      toc: "Contents",
      backToTop: "Back to top",
      footerNote: "Your data stays on your device.",
      skip: "Skip to content",
      exercises: "Exercises",
      programs: "Programs",
      tbf: "TBF"
    },
    es: {
      privacy: "Política de privacidad",
      description: "Descripción de la aplicación",
      descriptionFull: "Descripción completa de la aplicación",
      toc: "Contenido",
      backToTop: "Volver arriba",
      footerNote: "Tus datos permanecen en tu dispositivo.",
      skip: "Ir al contenido",
      exercises: "Ejercicios",
      programs: "Programas",
      tbf: "TBF"
    },
    cn: {
      privacy: "隐私政策",
      description: "应用说明",
      descriptionFull: "应用完整说明",
      toc: "目录",
      backToTop: "返回顶部",
      footerNote: "数据保存在您的设备上。",
      skip: "跳到正文",
      exercises: "动作",
      programs: "训练计划",
      tbf: "TBF"
    }
  };

  var sections = Array.prototype.slice.call(document.querySelectorAll(".lang-content"));
  var buttons = Array.prototype.slice.call(document.querySelectorAll(".lang-btn"));
  var current = "ru";

  function normalize(value) {
    if (!value) return null;
    var v = String(value).toLowerCase();
    if (v.indexOf("ru") === 0) return "ru";
    if (v.indexOf("en") === 0) return "en";
    if (v.indexOf("es") === 0) return "es";
    if (v.indexOf("zh") === 0 || v.indexOf("cn") === 0) return "cn";
    return null;
  }

  function fromHash() {
    var match = window.location.hash.match(/^#(ru|en|es|cn)-/);
    return match ? match[1] : null;
  }

  function fromUrl() {
    return normalize(new URLSearchParams(window.location.search).get("lang"));
  }

  function fromStorage() {
    try {
      return normalize(window.localStorage.getItem(LANG_KEY));
    } catch (error) {
      return null;
    }
  }

  function fromBrowser() {
    var list = navigator.languages && navigator.languages.length
      ? navigator.languages
      : [navigator.language || ""];
    for (var index = 0; index < list.length; index += 1) {
      var match = normalize(list[index]);
      if (match) return match;
    }
    return null;
  }

  function activeSection(lang) {
    for (var index = 0; index < sections.length; index += 1) {
      if (sections[index].getAttribute("data-lang") === lang) return sections[index];
    }
    return null;
  }

  function buildToc(section) {
    var desktop = document.getElementById("toc-desktop");
    var mobile = document.getElementById("toc-mobile");
    if (desktop) desktop.replaceChildren();
    if (mobile) mobile.replaceChildren();
    if (!section || (!desktop && !mobile)) return;

    var headings = Array.prototype.slice.call(
      section.querySelectorAll("h2[id], h3[id]")
    );

    function fill(target) {
      if (!target) return;
      var list = document.createElement("ul");
      headings.forEach(function (heading) {
        var item = document.createElement("li");
        if (heading.tagName === "H3") item.className = "toc-sub";
        var link = document.createElement("a");
        link.href = "#" + heading.id;
        link.setAttribute("data-target", heading.id);
        link.textContent = heading.textContent.trim();
        link.addEventListener("click", function () {
          var details = document.getElementById("toc-mobile-details");
          if (details) details.open = false;
        });
        item.appendChild(link);
        list.appendChild(item);
      });
      target.appendChild(list);
    }

    fill(desktop);
    fill(mobile);
  }

  var tocFrame = null;

  function updateActiveToc() {
    if (tocFrame !== null) return;
    tocFrame = window.requestAnimationFrame(function () {
      tocFrame = null;
      var section = activeSection(current);
      if (!section) return;
      var header = document.querySelector(".site-header");
      var offset = (header ? header.getBoundingClientRect().height : 0) + 36;
      var headings = Array.prototype.slice.call(
        section.querySelectorAll("h2[id], h3[id]")
      );
      var active = headings.length ? headings[0] : null;
      headings.forEach(function (heading) {
        if (heading.getBoundingClientRect().top <= offset) active = heading;
      });
      var links = document.querySelectorAll(
        "#toc-desktop a[data-target], #toc-mobile a[data-target]"
      );
      Array.prototype.forEach.call(links, function (link) {
        link.classList.toggle(
          "active",
          Boolean(active) && link.getAttribute("data-target") === active.id
        );
      });
    });
  }

  function apply(lang, options) {
    options = options || {};
    if (LANGS.indexOf(lang) === -1) lang = "ru";
    current = lang;

    document.documentElement.lang = HTML_LANG[lang];
    document.body.setAttribute("data-lang", lang);

    sections.forEach(function (section) {
      section.hidden = section.getAttribute("data-lang") !== lang;
    });

    buttons.forEach(function (button) {
      var pressed = button.getAttribute("data-lang") === lang;
      button.setAttribute("aria-pressed", pressed ? "true" : "false");
    });

    var strings = UI[lang];
    Array.prototype.forEach.call(document.querySelectorAll("[data-ui]"), function (node) {
      var value = strings[node.getAttribute("data-ui")];
      if (value) node.textContent = value;
    });

    Array.prototype.forEach.call(document.querySelectorAll("[data-page-link]"), function (link) {
      link.href = link.getAttribute("data-page-link") + ".html?lang=" + lang;
    });

    var section = activeSection(lang);
    if (section) {
      if (section.getAttribute("data-title")) {
        document.title = section.getAttribute("data-title");
      }
      var meta = document.querySelector('meta[name="description"]');
      if (meta && section.getAttribute("data-meta")) {
        meta.setAttribute("content", section.getAttribute("data-meta"));
      }
    }

    buildToc(section);

    try {
      window.localStorage.setItem(LANG_KEY, lang);
    } catch (error) {
      /* Storage can be unavailable in private mode; language still works. */
    }

    if (options.updateUrl !== false) {
      var url = new URL(window.location.href);
      url.searchParams.set("lang", lang);
      if (options.keepHash !== true) {
        url.hash = section ? section.id : "";
      }
      window.history.replaceState(null, "", url);
    }

    if (options.scrollToTop) {
      window.scrollTo({ top: 0, behavior: "auto" });
    } else if (options.scrollToHash && window.location.hash) {
      window.requestAnimationFrame(function () {
        var target = document.getElementById(window.location.hash.slice(1));
        var container = target ? target.closest(".lang-content") : null;
        if (target && (!container || !container.hidden)) {
          target.scrollIntoView({ block: "start" });
        }
      });
    }

    updateActiveToc();
  }

  current = fromUrl() || fromHash() || fromStorage() || fromBrowser() || "ru";
  if (LANGS.indexOf(current) === -1) current = "ru";

  buttons.forEach(function (button) {
    button.addEventListener("click", function () {
      var lang = button.getAttribute("data-lang");
      if (lang === current) return;
      apply(lang, { scrollToTop: true });
    });
  });

  Array.prototype.forEach.call(document.querySelectorAll("[data-scroll-top]"), function (control) {
    control.addEventListener("click", function (event) {
      event.preventDefault();
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  });

  Array.prototype.forEach.call(document.querySelectorAll("[data-current-year]"), function (node) {
    node.textContent = String(new Date().getFullYear());
  });

  // Каталог открывает TBF-файл в приложении; без JS ссылка остаётся на файл.
  Array.prototype.forEach.call(document.querySelectorAll("[data-tbf-open]"), function (link) {
    try {
      var file = new URL(link.getAttribute("data-tbf-open"), window.location.href).href;
      link.href = "twinbells://import?url=" + encodeURIComponent(file);
      link.setAttribute("rel", "nofollow");
    } catch (error) {
      // Оставляем обычную ссылку на файл.
    }
  });

  window.addEventListener("scroll", updateActiveToc, { passive: true });
  window.addEventListener("resize", updateActiveToc);
  window.addEventListener("hashchange", function () {
    var hashLang = fromHash();
    if (hashLang && hashLang !== current) {
      apply(hashLang, { updateUrl: false });
    }
    updateActiveToc();
  });

  apply(current, {
    updateUrl: true,
    keepHash: true,
    scrollToHash: Boolean(window.location.hash)
  });
})();
