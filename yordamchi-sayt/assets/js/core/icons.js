
// Shared icons live in one place so HTML fragments can use lightweight placeholders.
(function () {
    if (window.AppIcons) {
        return;
    }

    const icons = {
        // --- Sport kategoriyalari (har biriga alohida belgi) ---
        // Turnik: yuqoridagi ko'ndalang tayoq va unga osilgan qo'llar
        spTurnik: '<line x1="3" y1="5" x2="21" y2="5"></line><path d="M8 5v4"></path><path d="M16 5v4"></path><path d="M12 9a3 3 0 0 0-4 2.8V15"></path><path d="M12 9a3 3 0 0 1 4 2.8V15"></path><circle cx="12" cy="7.5" r="1.5"></circle>',
        // Brus: ikkita parallel tayoq
        spBrus: '<line x1="3" y1="8" x2="21" y2="8"></line><line x1="3" y1="16" x2="21" y2="16"></line><path d="M6 8v8"></path><path d="M18 8v8"></path>',
        // Ajimaniya: yerga tayanib turgan gavda
        spPush: '<line x1="2" y1="19" x2="22" y2="19"></line><path d="M5 19v-3"></path><path d="M5 16h9l5-4"></path><circle cx="20" cy="11" r="1.6"></circle><path d="M11 16v3"></path>',
        // Full body: to'liq gavda
        spBody: '<circle cx="12" cy="4" r="2"></circle><path d="M12 6v7"></path><path d="M7 9h10"></path><path d="M12 13l-3 7"></path><path d="M12 13l3 7"></path>',
        // Ko'krak: gantel (shtanga)
        spChest: '<line x1="2" y1="12" x2="22" y2="12"></line><rect x="4" y="8" width="3" height="8" rx="1"></rect><rect x="17" y="8" width="3" height="8" rx="1"></rect><rect x="8.5" y="10" width="7" height="4" rx="1"></rect>',
        // Bitseps: bukilgan qo'l
        spBiceps: '<path d="M5 19v-5a4 4 0 0 1 4-4h3"></path><path d="M12 10a4 4 0 0 1 4 4v1a3 3 0 0 1-3 3H9"></path><path d="M16 12c2-1 3-3 2.5-5"></path>',
        // Triseps: orqaga cho'zilgan qo'l
        spTriceps: '<path d="M18 5l-6 6-4 8"></path><circle cx="19" cy="4" r="1.6"></circle><path d="M12 11l4 3"></path><path d="M6 19h6"></path>',
        // Orqa: umurtqa
        spBack: '<path d="M12 3v18"></path><path d="M9 6h6"></path><path d="M9 10h6"></path><path d="M9 14h6"></path><path d="M9 18h6"></path>',
        // Yelka: yelka bo'g'imi
        spShoulder: '<circle cx="12" cy="7" r="3"></circle><path d="M6 20c0-4 2.5-7 6-7s6 3 6 7"></path><path d="M4 13l3-2"></path><path d="M20 13l-3-2"></path>',
        // Oyoq: bukilgan oyoq
        spLegs: '<path d="M9 3v7l-3 5 3 6"></path><path d="M15 3v7l3 5-3 6"></path><path d="M9 10h6"></path>',
        // Press/qorin — "olti bo'lak" tasviri
        spPress: '<rect x="7" y="3" width="10" height="18" rx="3"></rect><path d="M12 6v13"></path><path d="M7.5 9.5h9"></path><path d="M7.5 13h9"></path><path d="M7.5 16.5h9"></path>',
        // Kardio: yurak urishi
        spCardio: '<path d="M2 12h4l2-5 3 10 3-7 2 2h6"></path>',
        // Armrestling: bir-biriga tirab turgan ikki qo'l
        spArm: '<path d="M4 18l6-6"></path><path d="M20 18l-6-6"></path><path d="M10 12l4 0"></path><path d="M3 20h18"></path><circle cx="12" cy="7" r="2"></circle>',
        spFutbol: '<circle cx="12" cy="12" r="10"></circle><polygon points="12 6 16 10 14 15 10 15 8 10"></polygon><line x1="12" y1="6" x2="12" y2="2"></line><line x1="16" y1="10" x2="21" y2="8"></line><line x1="14" y1="15" x2="17" y2="20"></line><line x1="10" y1="15" x2="7" y2="20"></line><line x1="8" y1="10" x2="3" y2="8"></line>',
        spVoleybol: '<circle cx="12" cy="12" r="10"></circle><path d="M12 2c-3.3 2.6-5 6.4-5 10s1.7 7.4 5 10"></path><path d="M12 2c3.3 2.6 5 6.4 5 10s-1.7 7.4-5 10"></path><path d="M2 12h20"></path>',
        spBadminton: '<rect x="3" y="3" width="10" height="13" rx="5" transform="rotate(45 8 9.5)"></rect><line x1="15" y1="16.5" x2="20" y2="21.5"></line><line x1="12" y1="13.5" x2="18" y2="19.5"></line><circle cx="5" cy="5" r="1.5"></circle>',
        spBasketbol: '<circle cx="12" cy="12" r="10"></circle><line x1="12" y1="2" x2="12" y2="22"></line><line x1="2" y1="12" x2="22" y2="12"></line><path d="M5 5c4 3.2 4 10.8 0 14"></path><path d="M19 5c-4 3.2-4 10.8 0 14"></path>',

        archive: '<polyline points="21 8 21 21 3 21 3 8"></polyline><rect x="1" y="3" width="22" height="5"></rect><line x1="10" y1="12" x2="14" y2="12"></line>',
        book: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>',
        calendar: '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line>',
        camera: '<path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle>',
        check: '<polyline points="20 6 9 17 4 12"></polyline>',
        clock: '<circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline>',
        code: '<polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline>',
        copy: '<rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>',
        edit: '<path d="M12 20h9"></path><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"></path>',
        file: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline>',
        globe: '<circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 0 20"></path><path d="M12 2a15.3 15.3 0 0 0 0 20"></path>',
        headphones: '<path d="M3 18v-6a9 9 0 0 1 18 0v6"></path><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"></path>',
        home: '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline>',
        image: '<rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline>',
        list: '<line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line>',
        lock: '<rect x="3" y="11" width="18" height="11" rx="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path>',
        menu: '<path d="M4 7h16"></path><path d="M4 12h16"></path><path d="M4 17h16"></path>',
        message: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>',
        mic: '<path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line>',
        play: '<polygon points="5 3 19 12 5 21 5 3"></polygon>',
        plus: '<line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line>',
        refresh: '<path d="M21 12a9 9 0 0 1-15.4 6.4L3 16"></path><path d="M3 21v-5h5"></path><path d="M3 12A9 9 0 0 1 18.4 5.6L21 8"></path><path d="M21 3v5h-5"></path>',
        upload: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line>',
        download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="3" x2="12" y2="15"></line>',
        pause: '<rect x="6" y="4" width="4" height="16" rx="1"></rect><rect x="14" y="4" width="4" height="16" rx="1"></rect>',
        close: '<line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line>',
        bell: '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.7 21a2 2 0 0 1-3.4 0"></path>',
        pauseDot: '<line x1="5" y1="12" x2="11" y2="12"></line><rect x="14" y="7" width="2.5" height="10" rx="1"></rect><rect x="19" y="7" width="2.5" height="10" rx="1"></rect>',
        // Quyidagi uchtasi kodda ishlatilar, lekin aniqlanmagan edi —
        // o'sha joylarda belgi o'rniga BO'SH joy chiqardi.
        activity: '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>',
        fileText: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="8" y1="13" x2="16" y2="13"></line><line x1="8" y1="17" x2="13" y2="17"></line>',
        send: '<line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>',
        skipBack: '<polygon points="19 20 9 12 19 4 19 20"></polygon><line x1="5" y1="19" x2="5" y2="5"></line>',
        skipFwd: '<polygon points="5 4 15 12 5 20 5 4"></polygon><line x1="19" y1="5" x2="19" y2="19"></line>',
        video: '<polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>',
        volume: '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>',
        x: '<line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line>',
        arrowLeft: '<path d="M19 12H5M12 19l-7-7 7-7"></path>',
        alert: '<circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line>',
        // Lampa — savol izohini ochish tugmasi uchun
        bulb: '<path d="M9 18h6"></path><path d="M10 21h4"></path><path d="M12 3a6 6 0 0 0-3.6 10.8c.5.4.8.9.9 1.5l.1.7h5.2l.1-.7c.1-.6.4-1.1.9-1.5A6 6 0 0 0 12 3Z"></path>',
        settings: '<circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>',
        trash: '<polyline points="3 6 5 6 21 6"></polyline><path d="M19 6l-1 14H6L5 6"></path><path d="M10 11v6"></path><path d="M14 11v6"></path><path d="M9 6V4h6v2"></path>',
        // Statistika — ustunli grafik
        chart: '<line x1="3" y1="21" x2="21" y2="21"></line><rect x="5" y="11" width="3.5" height="7" rx="1"></rect><rect x="10.2" y="6" width="3.5" height="12" rx="1"></rect><rect x="15.4" y="13" width="3.5" height="5" rx="1"></rect>',
        star: '<path d="M12 2.5l2.9 5.9 6.5.95-4.7 4.58 1.11 6.47L12 17.35l-5.81 3.05 1.11-6.47-4.7-4.58 6.5-.95L12 2.5Z"></path>',
        trophy: '<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"></path><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"></path><path d="M4 22h16"></path><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"></path><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"></path><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"></path>'
    };


    /* ================= RANGLI BELGILAR =================
       Chiziqli ikonalar bir rangli — bo'limlarni bir qarashda ajratib
       bo'lmasdi. Quyida ikki qo'shimcha:
         1) `flags` — haqiqiy bayroqlar (SVG, aniq geometriya). Emoji
            ishlatilmadi: Windows'da 🇬🇧 bayroq emas, "GB" harflari chiqadi.
         2) `tile()` — brend rangidagi yumaloq plitka + ichida belgi/harf.
       Hammasi ichki SVG — tashqi CDN yo'q, shuning uchun oflayn ham ishlaydi. */

    const flags = {
        uk: '<rect width="24" height="24" rx="5" fill="#012169"/>' +
            '<path d="M0 0l24 24M24 0L0 24" stroke="#fff" stroke-width="5"/>' +
            '<path d="M0 0l24 24M24 0L0 24" stroke="#C8102E" stroke-width="3"/>' +
            '<path d="M12 0v24M0 12h24" stroke="#fff" stroke-width="8"/>' +
            '<path d="M12 0v24M0 12h24" stroke="#C8102E" stroke-width="4.5"/>',
        ru: '<rect width="24" height="8" rx="0" fill="#fff"/>' +
            '<rect y="8" width="24" height="8" fill="#0039A6"/>' +
            '<rect y="16" width="24" height="8" fill="#D52B1E"/>',
        uz: '<rect width="24" height="8" fill="#0099B5"/>' +
            '<rect y="8" width="24" height="8" fill="#fff"/>' +
            '<rect y="16" width="24" height="8" fill="#1EB53A"/>' +
            '<circle cx="5" cy="4" r="2.4" fill="#fff"/><circle cx="6.2" cy="3.4" r="2.4" fill="#0099B5"/>',
        us: '<rect width="24" height="24" fill="#fff"/>' +
            '<path d="M0 2h24M0 6h24M0 10h24M0 14h24M0 18h24M0 22h24" stroke="#B22234" stroke-width="2"/>' +
            '<rect width="11" height="12" fill="#3C3B6E"/>'
    };

    /* Bayroq — yumaloq burchakli ramka ichida */
    function flag(name, size) {
        const body = flags[name];
        if (!body) return '';
        size = Number(size || 24);
        return '<svg class="app-icon-svg" width="' + size + '" height="' + size +
               '" viewBox="0 0 24 24" aria-hidden="true">' +
               '<defs><clipPath id="fc' + name + '"><rect width="24" height="24" rx="5"/></clipPath></defs>' +
               '<g clip-path="url(#fc' + name + ')">' + body + '</g>' +
               '<rect width="24" height="24" rx="5" fill="none" stroke="rgba(0,0,0,.15)"/></svg>';
    }

    /* Brend plitkasi: rang + qisqa harf belgisi (yoki chiziqli ikona).
       Vendor logolarini xotiradan aniq chizib bo'lmaydi, shuning uchun
       rasmiy BREND RANGI + qisqa belgi — bir qarashda tanilarli va toza. */
    function tile(opts) {
        opts = opts || {};
        const size = Number(opts.size || 34);
        const c = opts.color || 'var(--accent)';
        const label = (opts.label || '?').slice(0, 3);
        const fs = label.length > 2 ? size * 0.34 : size * 0.42;
        return '<span class="brand-tile" style="width:' + size + 'px;height:' + size + 'px;' +
               'background:color-mix(in srgb,' + c + ' 18%, transparent);color:' + c + ';' +
               'font-size:' + fs.toFixed(1) + 'px">' + label + '</span>';
    }

    function svg(name, options) {
        options = options || {};
        const body = icons[name] || icons.home;
        const size = Number(options.size || 24);
        const extraClass = options.className ? ` ${options.className}` : '';
        return `<svg class="app-icon-svg${extraClass}" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${options.strokeWidth || 2}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${body}</svg>`;
    }

    function render(root) {
        const scope = root || document;
        scope.querySelectorAll('[data-icon]').forEach(node => {
            const name = node.getAttribute('data-icon');
            const size = node.getAttribute('data-icon-size');
            node.innerHTML = svg(name, { size: size || undefined });
            node.classList.add('app-icon');
        });
        // Bayroqlar: data-flag="uk|ru|uz|us"
        scope.querySelectorAll('[data-flag]').forEach(node => {
            node.innerHTML = flag(node.getAttribute('data-flag'), node.getAttribute('data-icon-size'));
            node.classList.add('app-icon');
        });
        // Brend plitkalari: data-tile="Py" data-tile-color="#3776AB"
        scope.querySelectorAll('[data-tile]').forEach(node => {
            node.innerHTML = tile({
                label: node.getAttribute('data-tile'),
                color: node.getAttribute('data-tile-color'),
                size: node.getAttribute('data-tile-size')
            });
            node.classList.add('app-icon');
        });
    }

    window.AppIcons = {
        svg,
        flag,
        tile,
        render
    };
})();
