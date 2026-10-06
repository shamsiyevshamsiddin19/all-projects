"use strict";
document.addEventListener('DOMContentLoaded', () => {
    // Navigation highlighting
    const sections = document.querySelectorAll('section');
    const navLinks = document.querySelectorAll('.nav-link');
    // Throttle with requestAnimationFrame so the handler runs at most once per frame
    let navTicking = false;
    const updateActiveNav = () => {
        navTicking = false;
        let current = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            if (window.scrollY >= (sectionTop - sectionHeight / 3)) {
                current = section.getAttribute('id') || '';
            }
        });
        navLinks.forEach(link => {
            link.classList.remove('active');
            const href = link.getAttribute('href');
            if (href && href.includes(current)) {
                link.classList.add('active');
            }
        });
    };
    window.addEventListener('scroll', () => {
        if (!navTicking) {
            navTicking = true;
            requestAnimationFrame(updateActiveNav);
        }
    }, { passive: true });
    // Handle form submission via FormSubmit AJAX
    const form = document.getElementById('contactForm');
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const btn = form.querySelector('.btn');
            const originalText = btn.textContent || '';
            btn.textContent = 'SENDING...';
            const formData = new FormData(form);
            fetch("https://formsubmit.co/ajax/ad5c1a6b8cec65f29d902ec3c0012c9d", {
                method: "POST",
                headers: { 'Accept': 'application/json' },
                body: formData
            })
                .then(response => {
                    if (!response.ok) throw new Error('HTTP ' + response.status);
                    return response.json();
                })
                .then(data => {
                // FormSubmit returns { success: "true", ... } on success
                if (String(data.success) !== 'true') {
                    throw new Error(data.message || 'Submission failed');
                }
                btn.textContent = 'MESSAGE SENT!';
                btn.style.background = '#fff';
                btn.style.color = '#000';
                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.style.background = 'transparent';
                    btn.style.color = '#fff';
                    form.reset();
                }, 3000);
            })
                .catch(error => {
                btn.textContent = 'ERROR — TRY AGAIN';
                btn.style.background = 'transparent';
                btn.style.color = '#fff';
                setTimeout(() => {
                    btn.textContent = originalText;
                }, 3000);
            });
        });
    }
    // Infinite Native Momentum Marquee Setup
    const friendsCarousel = document.querySelector('.friends-carousel');
    if (friendsCarousel) {
        const cards = Array.from(friendsCarousel.children);
        if (cards.length > 0) {
            const group = document.createElement('div');
            group.className = 'marquee-group';
            cards.forEach(card => group.appendChild(card));
            const content = document.createElement('div');
            content.className = 'marquee-content';
            // We use 3 groups to allow endless scrolling in both directions safely
            content.appendChild(group.cloneNode(true));
            content.appendChild(group);
            content.appendChild(group.cloneNode(true));
            friendsCarousel.appendChild(content);
            setTimeout(() => {
                const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
                const groupWidth = content.children[0].offsetWidth;
                friendsCarousel.scrollLeft = groupWidth;
                let isHovered = false;
                let isTouching = false;
                let autoScrollSpeed = 1;
                let scrollAccumulator = friendsCarousel.scrollLeft;
                friendsCarousel.addEventListener('mouseenter', () => isHovered = true);
                friendsCarousel.addEventListener('mouseleave', () => isHovered = false);
                friendsCarousel.addEventListener('touchstart', () => isTouching = true, { passive: true });
                friendsCarousel.addEventListener('touchend', () => isTouching = false);
                function animate() {
                    if (!isHovered && !isTouching && !prefersReduced && !document.hidden) {
                        scrollAccumulator += autoScrollSpeed;
                        friendsCarousel.scrollLeft = scrollAccumulator;
                    }
                    else {
                        scrollAccumulator = friendsCarousel.scrollLeft;
                    }
                    if (friendsCarousel.scrollLeft >= groupWidth * 2) {
                        friendsCarousel.scrollLeft -= groupWidth;
                        scrollAccumulator -= groupWidth;
                    }
                    else if (friendsCarousel.scrollLeft <= 0) {
                        friendsCarousel.scrollLeft += groupWidth;
                        scrollAccumulator += groupWidth;
                    }
                    requestAnimationFrame(animate);
                }
                requestAnimationFrame(animate);
                friendsCarousel.addEventListener('scroll', () => {
                    if (friendsCarousel.scrollLeft >= groupWidth * 2) {
                        friendsCarousel.scrollLeft -= groupWidth;
                        scrollAccumulator = friendsCarousel.scrollLeft;
                    }
                    else if (friendsCarousel.scrollLeft <= 0) {
                        friendsCarousel.scrollLeft += groupWidth;
                        scrollAccumulator = friendsCarousel.scrollLeft;
                    }
                });
            }, 200);
        }
    }
    // Skill Rotators — single config-driven loop instead of 6 duplicated blocks.
    // Respects prefers-reduced-motion and pauses while the tab is hidden.
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!reduceMotion) {
        const rotators = [
            { id: 'sql-skill', items: ['PostgreSQL', 'SQLite', 'MySQL'] },
            { id: 'py-skill', items: ['Django', 'FastAPI', 'Flask'] },
            { id: 'web-skill', items: ['Node.js', 'HTML', 'CSS', 'TypeScript'] },
            { id: 'tools-skill', items: ['Docker', 'Redis', 'Celery'] },
            { id: 'cpp-skill', items: ['OOP', 'Data Structures', 'Algorithms'] },
            { id: 'git-skill', items: ['Version Control', 'CI/CD', 'GitHub Actions'] },
        ];
        rotators.forEach(({ id, items }) => {
            const el = document.getElementById(id);
            if (!el) return;
            let index = 0;
            el.style.transition = 'opacity 0.5s ease-in-out';
            setInterval(() => {
                if (document.hidden) return; // don't animate in a background tab
                el.style.opacity = '0';
                setTimeout(() => {
                    index = (index + 1) % items.length;
                    el.textContent = items[index];
                    el.style.opacity = '1';
                }, 500);
            }, 4000);
        });
    }

    // Side drawers (nav overlay + interests panel) are handled by the
    // consolidated controller further down.
});

// === Typewriter effect ===
(function () {
    const el = document.getElementById('typewriter');
    if (!el) return;
    const words = ['BACKEND DEVELOPER', 'PYTHON ENGINEER', 'API BUILDER', 'DJANGO / FASTAPI'];
    let wi = 0, ci = 0, deleting = false;
    function tick() {
        const word = words[wi];
        if (!deleting) {
            el.textContent = word.slice(0, ci + 1);
            ci++;
            if (ci === word.length) { deleting = true; setTimeout(tick, 1800); return; }
        } else {
            el.textContent = word.slice(0, ci - 1);
            ci--;
            if (ci === 0) { deleting = false; wi = (wi + 1) % words.length; }
        }
        setTimeout(tick, deleting ? 50 : 95);
    }
    tick();
})();

// === Stat counter animation ===
(function () {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const statEls = document.querySelectorAll('.stat h3');
    if (!statEls.length) return;
    const parsed = Array.from(statEls).map(el => {
        const raw = el.textContent.trim();
        const num = parseFloat(raw);
        const suffix = raw.replace(/[\d.]/g, '');
        return { el, num, suffix };
    });
    let done = false;
    const obs = new IntersectionObserver(entries => {
        if (done || !entries.some(e => e.isIntersecting)) return;
        done = true;
        parsed.forEach(({ el, num, suffix }) => {
            const start = performance.now();
            const dur = 1400;
            (function tick(now) {
                const t = Math.min((now - start) / dur, 1);
                const ease = 1 - Math.pow(1 - t, 3);
                el.textContent = Math.floor(ease * num) + suffix;
                if (t < 1) requestAnimationFrame(tick);
            })(start);
        });
        obs.disconnect();
    }, { threshold: 0.6 });
    statEls.forEach(el => obs.observe(el));
})();

// === Scroll-reveal animations (added) ===
document.addEventListener('DOMContentLoaded', () => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    if (!('IntersectionObserver' in window)) return;

    const selectors = [
        '.about-image', '.about-text',
        '.skills-container > h2', '.skill-card',
        '.portfolio-info', '.project-card',
        '.network-grid > .network-card', '.carousel-wrapper',
        '.blog-card',
        '.contact-info', '.contact-form'
    ];

    const els = [];
    selectors.forEach(sel => document.querySelectorAll(sel).forEach(el => {
        if (!el.classList.contains('reveal')) { el.classList.add('reveal'); els.push(el); }
    }));

    // Stagger cards within their grids
    document.querySelectorAll('.skills-grid, .project-grid, .blog-grid, .network-grid').forEach(grid => {
        Array.from(grid.children).forEach((child, idx) => {
            if (child.classList.contains('reveal')) child.style.transitionDelay = (idx * 0.09).toFixed(2) + 's';
        });
    });

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            const el = entry.target;
            el.classList.add('visible');
            observer.unobserve(el);
            // After the reveal finishes, strip the helper classes so each
            // element returns to its natural CSS (hover transitions intact).
            setTimeout(() => {
                el.classList.remove('reveal', 'visible');
                el.style.transitionDelay = '';
                el.style.willChange = '';
            }, 1500);
        });
    }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });

    els.forEach(el => observer.observe(el));
});

// === Mobile nav drawer (hamburger) ===
document.addEventListener('DOMContentLoaded', () => {
    const nav = document.querySelector('.nav');
    const toggle = document.querySelector('.nav-toggle');
    if (!nav || !toggle) return;

    const isNavOpen = () => nav.classList.contains('open');
    const setOpen = (open) => {
        nav.classList.toggle('open', open);
        toggle.classList.toggle('open', open);
        toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
        document.body.classList.toggle('drawer-open', open);
    };

    // Kept for the swipe handler below.
    window.__drawers = { closeAll: () => setOpen(false), openNav: () => setOpen(true), isNavOpen, isPanelOpen: () => false };

    toggle.addEventListener('click', () => setOpen(!isNavOpen()));
    nav.querySelectorAll('.nav-link').forEach((link) => link.addEventListener('click', () => setOpen(false)));
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && isNavOpen()) setOpen(false); });
    window.addEventListener('resize', () => { if (window.innerWidth > 800) setOpen(false); });
});

// === Swipe to DISMISS an open drawer (never to open — that fired accidentally
//     during normal scrolling and clashed with the browser back-gesture) ===
document.addEventListener('DOMContentLoaded', () => {
    let touchStartX = 0;
    const swipeThreshold = 60; // minimum px distance for a swipe

    document.addEventListener('touchstart', e => {
        touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });

    document.addEventListener('touchend', e => {
        const D = window.__drawers;
        if (!D || !(D.isPanelOpen() || D.isNavOpen())) return; // only act while a drawer is open
        const dx = e.changedTouches[0].screenX - touchStartX;
        if (Math.abs(dx) < swipeThreshold) return;
        // Left panel dismissed by swiping left; full-screen nav dismissed by swiping right.
        if (D.isPanelOpen() && dx < 0) D.closeAll();
        else if (D.isNavOpen() && dx > 0) D.closeAll();
    }, { passive: true });
});

// === Footer: keep the copyright year current ===
(function () {
    var y = document.getElementById('footerYear');
    if (y) y.textContent = new Date().getFullYear();
})();

// === Hero title: shrink to fit so any language/script never overflows ===
// The name is shown at a huge viewport-relative size; different scripts
// (e.g. Cyrillic capitals) can render wider than Latin at the same
// font-size, so measure the actual rendered width and scale down if needed.
(function () {
    const el = document.querySelector('.main-title');
    if (!el) return;

    function fit() {
        el.style.fontSize = ''; // reset to the CSS-defined (vw-based) size first
        const container = el.closest('.hero-content') || el.parentElement;
        if (!container) return;
        const maxWidth = container.clientWidth;
        const natural = parseFloat(getComputedStyle(el).fontSize);
        const width = el.scrollWidth;
        if (width > maxWidth && width > 0 && natural > 0) {
            el.style.fontSize = (natural * (maxWidth / width)) + 'px';
        }
    }

    window.fitHeroTitle = fit;
    document.addEventListener('DOMContentLoaded', fit);
    window.addEventListener('load', fit);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(fit);
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(fit, 120);
    });
})();

// === Cursor spotlight glow (desktop, motion-safe) ===
(function () {
    if (!window.matchMedia) return;
    if (matchMedia('(hover: none), (pointer: coarse)').matches) return;
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const glow = document.querySelector('.cursor-glow');
    if (!glow) return;
    let x = 0, y = 0, queued = false;
    const apply = () => {
        glow.style.setProperty('--cx', x + 'px');
        glow.style.setProperty('--cy', y + 'px');
        queued = false;
    };
    window.addEventListener('mousemove', (e) => {
        x = e.clientX; y = e.clientY;
        document.body.classList.add('cursor-active');
        if (!queued) { queued = true; requestAnimationFrame(apply); }
    }, { passive: true });
    document.addEventListener('mouseleave', () => document.body.classList.remove('cursor-active'));
})();

// The trailing ring cursor now lives in assets/js/cursor.js so every page
// (home, CV, resume) can share it. It is loaded separately on each page.

// === Premium pointer interactions: scroll progress, 3D tilt + spotlight, magnetic ===
(function () {
    // Scroll progress bar (always on, cheap)
    const bar = document.querySelector('.scroll-progress');
    if (bar) {
        let queued = false;
        const upd = () => {
            queued = false;
            const h = document.documentElement.scrollHeight - window.innerHeight;
            bar.style.setProperty('--sp', h > 0 ? (window.scrollY / h).toFixed(4) : '0');
        };
        window.addEventListener('scroll', () => { if (!queued) { queued = true; requestAnimationFrame(upd); } }, { passive: true });
        window.addEventListener('resize', upd, { passive: true });
        upd();
    }

    // Pointer-driven effects only on precise pointers, and never with reduced motion
    if (!window.matchMedia) return;
    if (!matchMedia('(hover: hover) and (pointer: fine)').matches) return;
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    // 3D tilt + cursor spotlight on grid cards (not the transformed deck cards)
    document.querySelectorAll('.skill-card, .network-grid .network-card').forEach((el) => {
        el.classList.add('tilt', 'spot');
        let raf = false, ev = null;
        el.addEventListener('mousemove', (e) => {
            ev = e; if (raf) return; raf = true;
            requestAnimationFrame(() => {
                raf = false;
                const r = el.getBoundingClientRect();
                const px = (ev.clientX - r.left) / r.width;
                const py = (ev.clientY - r.top) / r.height;
                const rx = (0.5 - py) * 9;
                const ry = (px - 0.5) * 11;
                el.style.transform = `perspective(720px) rotateX(${rx.toFixed(2)}deg) rotateY(${ry.toFixed(2)}deg) translateY(-6px)`;
                el.style.setProperty('--mx', (px * 100).toFixed(1) + '%');
                el.style.setProperty('--my', (py * 100).toFixed(1) + '%');
            });
        });
        el.addEventListener('mouseleave', () => { el.style.transform = ''; });
    });

    // Magnetic hero buttons
    document.querySelectorAll('.hero .btn').forEach((btn) => {
        btn.style.transition = 'transform 0.2s cubic-bezier(0.22, 0.61, 0.36, 1)';
        btn.addEventListener('mousemove', (e) => {
            const r = btn.getBoundingClientRect();
            const mx = e.clientX - r.left - r.width / 2;
            const my = e.clientY - r.top - r.height / 2;
            btn.style.transform = `translate(${(mx * 0.25).toFixed(1)}px, ${(my * 0.4).toFixed(1)}px)`;
        });
        btn.addEventListener('mouseleave', () => { btn.style.transform = ''; });
    });
})();

// === Preloader: hide as soon as the page is ready (JS removes it entirely) ===
(function () {
    const p = document.querySelector('.preloader');
    if (!p) return;
    let gone = false;
    const hide = () => {
        if (gone) return; gone = true;
        p.classList.add('done');
        setTimeout(() => { if (p.parentNode) p.parentNode.removeChild(p); }, 650);
    };
    if (document.readyState === 'complete') { setTimeout(hide, 300); }
    else { window.addEventListener('load', () => setTimeout(hide, 300)); }
    setTimeout(hide, 3500); // absolute safety — never let it linger
})();
