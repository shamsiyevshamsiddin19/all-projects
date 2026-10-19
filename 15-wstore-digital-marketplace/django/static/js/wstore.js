/**
 * wstore.uz — Frontend JavaScript Engine
 * Fully featured client logic: Theme, Currency, Live Search, Mobile Drawers, Wishlist AJAX
 */

(function () {
  "use strict";

  // -------------------------------------------------------------------------
  // 1. Currency Conversion & Formatting
  // -------------------------------------------------------------------------
  const serverRate = parseFloat(
    (document.documentElement.dataset.uzsRate || "").replace(",", ".")
  );

  const RATES = {
    USD: 1,
    UZS: Number.isFinite(serverRate) && serverRate > 0 ? serverRate : 12600,
    RUB: 90,
    EUR: 0.92,
  };

  const CURRENCY_META = {
    USD: { code: "USD", suffix: "USD", decimals: 0 },
    UZS: { code: "UZS", suffix: "so'm", decimals: 0 },
    RUB: { code: "RUB", suffix: "RUB", decimals: 0 },
    EUR: { code: "EUR", suffix: "EUR", decimals: 0 },
  };

  function formatPrice(usd, currency) {
    const meta = CURRENCY_META[currency] || CURRENCY_META.USD;
    const rate = RATES[currency] || 1;
    const val = usd * rate;
    const rounded =
      meta.decimals > 0
        ? val.toFixed(meta.decimals)
        : String(Math.round(val));
    const parts = rounded.split(".");
    const spaced = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, " ");
    const num = parts[1] ? spaced + "." + parts[1] : spaced;
    return num + " " + meta.suffix;
  }

  function getSavedCurrency() {
    const c = localStorage.getItem("cur");
    return c && RATES[c] ? c : "USD";
  }

  function applyCurrency(currency) {
    localStorage.setItem("cur", currency);

    // Update currency buttons
    document.querySelectorAll(".currency-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.curr === currency);
    });

    // Update all elements with data-usd attribute
    document.querySelectorAll("[data-usd]").forEach((el) => {
      const usd = parseFloat(el.getAttribute("data-usd"));
      if (!isNaN(usd)) {
        el.textContent = formatPrice(usd, currency);
      }
    });

    // Update price range filter labels dynamically
    document.querySelectorAll(".price-range-label").forEach((el) => {
      const min = parseFloat(el.getAttribute("data-min"));
      const max = parseFloat(el.getAttribute("data-max"));
      if (!isNaN(min) && !isNaN(max)) {
        if (max >= 999999) {
          el.textContent = `${formatPrice(min, currency)} +`;
        } else {
          el.textContent = `${formatPrice(min, currency)} – ${formatPrice(max, currency)}`;
        }
      }
    });
  }

  window.setCurrency = function (curr) {
    applyCurrency(curr);
  };

  // -------------------------------------------------------------------------
  // 2. Theme Toggle (Dark / Light)
  // -------------------------------------------------------------------------
  function getSavedTheme() {
    const match = document.cookie.match(/(?:^|; )theme=([^;]*)/);
    const cookieTheme = match ? decodeURIComponent(match[1]) : null;
    return cookieTheme || localStorage.getItem("theme") || "dark";
  }

  function applyTheme(theme) {
    if (theme === "light") {
      document.documentElement.setAttribute("data-theme", "light");
    } else {
      document.documentElement.removeAttribute("data-theme");
    }
    localStorage.setItem("theme", theme);
    document.cookie = `theme=${theme}; path=/; max-age=31536000; SameSite=Lax`;

    const sun = document.getElementById("themeSunIcon");
    const moon = document.getElementById("themeMoonIcon");
    if (sun && moon) {
      if (theme === "light") {
        sun.style.display = "none";
        moon.style.display = "block";
      } else {
        sun.style.display = "block";
        moon.style.display = "none";
      }
    }
  }

  window.toggleTheme = function () {
    const current = getSavedTheme();
    const next = current === "light" ? "dark" : "light";
    applyTheme(next);
  };

  // -------------------------------------------------------------------------
  // 3. Wishlist AJAX Toggle
  // -------------------------------------------------------------------------
  window.toggleWishlist = async function (e, productId) {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }

    const csrfEl = document.querySelector("[name=csrfmiddlewaretoken]");
    const csrfToken = csrfEl ? csrfEl.value : "";

    // Find corresponding button(s)
    const btns = document.querySelectorAll(`[data-product-id="${productId}"]`);

    try {
      const res = await fetch(`/wishlist/toggle/${productId}/`, {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken,
          "X-Requested-With": "XMLHttpRequest",
        },
      });

      if (res.status === 401 || res.redirected || res.url.includes("/login")) {
        window.location.href = `/auth/login/?next=${encodeURIComponent(
          window.location.pathname
        )}`;
        return;
      }

      const data = await res.json();
      if (data && typeof data.wishlisted !== "undefined") {
        btns.forEach((btn) => {
          btn.classList.toggle("wishlisted", data.wishlisted);
          btn.classList.toggle("active", data.wishlisted);
          const icon = btn.querySelector("i, svg");
          if (icon) {
            if (data.wishlisted) {
              icon.classList.add("fill-current", "text-red-500");
              icon.style.fill = "#ef4444";
              icon.style.color = "#ef4444";
            } else {
              icon.classList.remove("fill-current", "text-red-500");
              icon.style.fill = "none";
              icon.style.color = "";
            }
          }
        });
      }
    } catch (err) {
      console.error("Wishlist error:", err);
    }
  };

  // -------------------------------------------------------------------------
  // 4. Slider Scroller
  // -------------------------------------------------------------------------
  window.scrollSlider = function (sliderId, dir) {
    const el = document.getElementById(sliderId);
    if (el) {
      el.scrollLeft += dir * (el.clientWidth * 0.75);
    }
  };

  // -------------------------------------------------------------------------
  // 5. DOM Initialization
  // -------------------------------------------------------------------------
  document.addEventListener("DOMContentLoaded", () => {
    // 5.1 Initialize Lucide Icons
    if (window.lucide && typeof window.lucide.createIcons === "function") {
      window.lucide.createIcons();
    }

    // 5.2 Apply Theme
    const activeTheme = getSavedTheme();
    applyTheme(activeTheme);

    const themeToggleBtn = document.getElementById("themeToggleBtn");
    if (themeToggleBtn) {
      themeToggleBtn.addEventListener("click", window.toggleTheme);
    }

    // 5.3 Apply Currency
    const activeCur = getSavedCurrency();
    applyCurrency(activeCur);

    document.querySelectorAll(".currency-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const curr = btn.getAttribute("data-curr");
        if (curr) applyCurrency(curr);
      });
    });

    // 5.4 Lang Dropdown
    const langBtn = document.getElementById("langSelectBtn");
    const langDropdown = document.getElementById("langDropdown");
    if (langBtn && langDropdown) {
      langBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        langDropdown.classList.toggle("show");
      });
      // Tanlash tugmalari endi forma yuboradi (set_language) — bu yerda
      // faqat ro'yxat ichiga bosilganda u yopilib qolmasligini ta'minlaymiz.
      langDropdown.addEventListener("click", (e) => e.stopPropagation());
    }

    // 5.5 Account Menu Dropdown
    const accountBtn = document.getElementById("accountMenuBtn");
    const accountDropdown = document.getElementById("accountDropdownMenu");
    if (accountBtn && accountDropdown) {
      accountBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        accountDropdown.classList.toggle("show");
      });
    }

    // Click outside to close dropdowns
    document.addEventListener("click", () => {
      if (langDropdown) langDropdown.classList.remove("show");
      if (accountDropdown) accountDropdown.classList.remove("show");
      const deskDrop = document.getElementById("desktopSearchDropdown");
      const mobDrop = document.getElementById("mobileSearchDropdown");
      if (deskDrop) deskDrop.style.display = "none";
      if (mobDrop) mobDrop.style.display = "none";
    });

    // 5.6 Mobile Navigation Slide-Over Drawer
    const mobileMenuToggle = document.getElementById("mobileMenuToggle");
    const mobileDrawerWrap = document.getElementById("mobileDrawerWrap");
    const mobileDrawerBackdrop = document.getElementById("mobileDrawerBackdrop");
    const mobileDrawerPanel = document.getElementById("mobileDrawerPanel");
    const mobileDrawerClose = document.getElementById("mobileDrawerClose");

    function openMobileDrawer() {
      if (!mobileDrawerWrap || !mobileDrawerPanel || !mobileDrawerBackdrop) return;
      mobileDrawerWrap.style.display = "block";
      setTimeout(() => {
        mobileDrawerBackdrop.classList.remove("opacity-0");
        mobileDrawerBackdrop.classList.add("opacity-100");
        mobileDrawerPanel.classList.remove("translate-x-full");
        mobileDrawerPanel.classList.add("translate-x-0");
      }, 10);
    }

    function closeMobileDrawer() {
      if (!mobileDrawerWrap || !mobileDrawerPanel || !mobileDrawerBackdrop) return;
      mobileDrawerBackdrop.classList.remove("opacity-100");
      mobileDrawerBackdrop.classList.add("opacity-0");
      mobileDrawerPanel.classList.remove("translate-x-0");
      mobileDrawerPanel.classList.add("translate-x-full");
      setTimeout(() => {
        mobileDrawerWrap.style.display = "none";
      }, 300);
    }

    if (mobileMenuToggle) mobileMenuToggle.addEventListener("click", openMobileDrawer);
    if (mobileDrawerClose) mobileDrawerClose.addEventListener("click", closeMobileDrawer);
    if (mobileDrawerBackdrop) mobileDrawerBackdrop.addEventListener("click", closeMobileDrawer);

    // 5.7 Mobile Filter Bottom Sheet
    const openMobileFilterBtn = document.getElementById("openMobileFilterBtn");
    const mobileFilterModal = document.getElementById("mobileFilterModal");
    const mobileFilterBackdrop = document.getElementById("mobileFilterBackdrop");
    const mobileFilterSheet = document.getElementById("mobileFilterSheet");
    const closeMobileFilterBtn = document.getElementById("closeMobileFilterBtn");
    const mobileFilterBody = document.getElementById("mobileFilterBody");
    const catalogFilterForm = document.getElementById("catalogFilterForm");

    function openMobileFilter() {
      if (!mobileFilterModal || !mobileFilterSheet) return;
      // Copy sidebar form to mobile sheet if empty
      if (mobileFilterBody && catalogFilterForm && mobileFilterBody.children.length === 0) {
        const clone = catalogFilterForm.cloneNode(true);
        // Klondagi id'lar asl forma bilan takrorlanmasin — aks holda
        // document.getElementById doim desktop nusxasini topadi.
        clone.querySelectorAll("[id]").forEach((el) => {
          el.id = el.id + "__mobile";
        });
        clone.id = "mobileCatalogFilterForm";
        mobileFilterBody.appendChild(clone);
      }

      mobileFilterModal.style.display = "block";
      setTimeout(() => {
        if (mobileFilterBackdrop) {
          mobileFilterBackdrop.classList.remove("opacity-0");
          mobileFilterBackdrop.classList.add("opacity-100");
        }
        mobileFilterSheet.classList.remove("translate-y-full");
        mobileFilterSheet.classList.add("translate-y-0");
      }, 10);
    }

    function closeMobileFilter() {
      if (!mobileFilterModal || !mobileFilterSheet) return;
      if (mobileFilterBackdrop) {
        mobileFilterBackdrop.classList.remove("opacity-100");
        mobileFilterBackdrop.classList.add("opacity-0");
      }
      mobileFilterSheet.classList.remove("translate-y-0");
      mobileFilterSheet.classList.add("translate-y-full");
      setTimeout(() => {
        mobileFilterModal.style.display = "none";
      }, 300);
    }

    // Mobil varaqdagi "Ko'rsatish" tugmasi KLON formani yuborishi kerak,
    // aks holda foydalanuvchi belgilagan katakchalar hisobga olinmaydi.
    window.submitCatalogFilter = function () {
      const form =
        document.getElementById("mobileCatalogFilterForm") ||
        document.getElementById("catalogFilterForm");
      if (form) form.submit();
    };

    if (openMobileFilterBtn) openMobileFilterBtn.addEventListener("click", openMobileFilter);
    if (closeMobileFilterBtn) closeMobileFilterBtn.addEventListener("click", closeMobileFilter);
    if (mobileFilterBackdrop) mobileFilterBackdrop.addEventListener("click", closeMobileFilter);

    // 5.8 Instant Live Client Autocomplete
    const searchIndexScript = document.getElementById("searchIndexData");
    let searchIndex = [];
    if (searchIndexScript) {
      try {
        searchIndex = JSON.parse(searchIndexScript.textContent);
      } catch (e) {
        console.error("Failed to parse searchIndex", e);
      }
    }

    function setupSearchAutocomplete(inputId, dropdownId) {
      const input = document.getElementById(inputId);
      const dropdown = document.getElementById(dropdownId);
      if (!input || !dropdown) return;

      input.addEventListener("input", () => {
        const q = input.value.trim().toLowerCase();
        if (!q) {
          dropdown.style.display = "none";
          dropdown.innerHTML = "";
          return;
        }

        const matches = searchIndex.filter((item) => {
          const title = (item.title || "").toLowerCase();
          const tech = Array.isArray(item.tech) ? item.tech.join(" ").toLowerCase() : "";
          const cat = (item.category || "").toLowerCase();
          return title.includes(q) || tech.includes(q) || cat.includes(q);
        });

        if (matches.length === 0) {
          dropdown.innerHTML = `<div class="p-3 text-center text-xs text-muted">Ushbu so'rov bo'yicha mahsulot topilmadi.</div>`;
          dropdown.style.display = "block";
          return;
        }

        const html = matches.slice(0, 5).map((item) => {
          const techBadges = Array.isArray(item.tech)
            ? item.tech.slice(0, 3).join(", ")
            : "";
          return `
            <a href="/product/${item.slug}/" class="search-suggestion-item">
              <div class="h-10 w-10 shrink-0 overflow-hidden rounded bg-surface-2">
                <img src="${item.cover_url || ''}" alt="" class="h-full w-full object-cover">
              </div>
              <div class="min-w-0 flex-1">
                <div class="truncate text-sm font-medium text-fg">${item.title}</div>
                <div class="truncate text-xs text-muted">${techBadges || item.category || ''}</div>
              </div>
            </a>
          `;
        }).join("");

        dropdown.innerHTML = html;
        dropdown.style.display = "block";
      });

      // Press Enter to submit search
      input.addEventListener("keydown", (e) => {
        if (e.key !== "Enter") return;
        // Mavjud filtrlarni saqlab, faqat `q` ni yangilaymiz
        const params = new URLSearchParams(window.location.search);
        const value = input.value.trim();
        if (value) {
          params.set("q", value);
        } else {
          params.delete("q");
        }
        params.delete("page");
        const qs = params.toString();
        window.location.href = qs ? `/?${qs}` : "/";
      });
    }

    setupSearchAutocomplete("desktopSearchInput", "desktopSearchDropdown");
    setupSearchAutocomplete("mobileSearchInput", "mobileSearchDropdown");

    // 5.9 Slayder chetidagi solishtirish maskasi — oxirigacha surilganda
    //     o'ng chetdagi xiralashish kerak emas, boshida esa kerak.
    document.querySelectorAll(".highlight-scroller").forEach((sc) => {
      const sync = () => {
        const atEnd = sc.scrollLeft + sc.clientWidth >= sc.scrollWidth - 2;
        const noOverflow = sc.scrollWidth <= sc.clientWidth + 2;
        sc.classList.toggle("at-end", atEnd || noOverflow);
      };
      sc.addEventListener("scroll", sync, { passive: true });
      window.addEventListener("resize", sync);
      sync();
    });

    // 5.10 Copy-to-clipboard handler
    document.querySelectorAll("[data-copy]").forEach((el) => {
      el.addEventListener("click", () => {
        const text = el.dataset.copy;
        navigator.clipboard.writeText(text).then(() => {
          const orig = el.innerHTML;
          el.innerHTML = "<span>Nusxa olindi! ✅</span>";
          setTimeout(() => {
            el.innerHTML = orig;
            if (window.lucide) window.lucide.createIcons();
          }, 2000);
        });
      });
    });

  });
})();
