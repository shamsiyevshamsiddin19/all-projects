document.addEventListener("DOMContentLoaded", () => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const fmt = (n) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ");

    /* ---------- 1. Dynamic data (bot link + prices) ---------- */
    fetch("/api/public")
        .then(r => r.json())
        .then(data => {
            const botUsername = data.bot_username || "";
            const botLink = botUsername ? `https://t.me/${botUsername}` : "#";
            document.querySelectorAll(".cta-bot").forEach(b => b.setAttribute("href", botLink));

            const days = data.sub_days || 30;
            const perDay = (p) => `~${fmt(Math.round(p / days / 100) * 100)} so'm / kun`;
            const set = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };
            if (data.price_basic) { set("ppBasic", fmt(data.price_basic)); set("pdBasic", perDay(data.price_basic)); }
            if (data.price_premium) { set("ppPrem", fmt(data.price_premium)); set("pdPrem", perDay(data.price_premium)); }
        })
        .catch(e => console.error("public data:", e));

    /* ---------- 2. Staggered reveal ---------- */
    document.querySelectorAll("[data-stagger]").forEach(group => {
        group.querySelectorAll(".reveal, .reveal-l, .reveal-r, .reveal-scale")
            .forEach((el, i) => el.style.setProperty("--d", (i * 0.07).toFixed(2) + "s"));
    });

    const revealEls = document.querySelectorAll(".reveal, .reveal-l, .reveal-r, .reveal-scale");
    const io = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            entry.target.classList.add("visible");
            const counter = entry.target.querySelector?.(".counter");
            if (counter && !counter.dataset.done) countUp(counter);
            io.unobserve(entry.target);
        });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    revealEls.forEach(el => io.observe(el));

    function countUp(el) {
        el.dataset.done = "1";
        const target = +el.getAttribute("data-target") || 0;
        if (reduce) { el.innerText = fmt(target); return; }
        const dur = 1500, start = performance.now();
        const tick = (now) => {
            const p = Math.min((now - start) / dur, 1);
            const ease = 1 - Math.pow(1 - p, 4);
            el.innerText = fmt(Math.floor(ease * target));
            if (p < 1) requestAnimationFrame(tick);
            else el.innerText = fmt(target);
        };
        requestAnimationFrame(tick);
    }

    /* ---------- 3. Navbar on scroll ---------- */
    const nav = document.getElementById("navbar");
    if (nav) {
        const onScroll = () => nav.classList.toggle("scrolled", window.scrollY > 30);
        onScroll();
        window.addEventListener("scroll", onScroll, { passive: true });
    }

    /* ---------- 4. FAQ accordion ---------- */
    document.querySelectorAll(".faq-item").forEach(item => {
        item.addEventListener("click", () => {
            const open = item.classList.contains("active");
            document.querySelectorAll(".faq-item").forEach(f => {
                f.classList.remove("active");
                f.querySelector(".faq-a").style.maxHeight = null;
            });
            if (!open) {
                item.classList.add("active");
                const a = item.querySelector(".faq-a");
                a.style.maxHeight = a.scrollHeight + "px";
            }
        });
    });

    if (reduce) return;  // hover-effektlarni o'tkazib yuboramiz

    /* ---------- 5. Card spotlight (cursor-follow glow) ---------- */
    document.querySelectorAll(".spot").forEach(card => {
        card.addEventListener("mousemove", (e) => {
            const r = card.getBoundingClientRect();
            card.style.setProperty("--mx", (e.clientX - r.left) + "px");
            card.style.setProperty("--my", (e.clientY - r.top) + "px");
        });
    });

    /* ---------- 6. Magnetic buttons ---------- */
    document.querySelectorAll(".magnetic").forEach(btn => {
        btn.addEventListener("mousemove", (e) => {
            const r = btn.getBoundingClientRect();
            const x = e.clientX - r.left - r.width / 2;
            const y = e.clientY - r.top - r.height / 2;
            btn.style.transform = `translate(${x * 0.18}px, ${y * 0.28}px)`;
        });
        btn.addEventListener("mouseleave", () => { btn.style.transform = ""; });
    });

    /* ---------- 7. Hero player tilt ---------- */
    const tilt = document.querySelector(".tilt");
    if (tilt) {
        const wrap = tilt.closest(".hero-visual") || tilt;
        wrap.addEventListener("mousemove", (e) => {
            const r = wrap.getBoundingClientRect();
            const px = (e.clientX - r.left) / r.width - 0.5;
            const py = (e.clientY - r.top) / r.height - 0.5;
            tilt.style.transform = `perspective(900px) rotateY(${px * 7}deg) rotateX(${-py * 7}deg)`;
        });
        wrap.addEventListener("mouseleave", () => { tilt.style.transform = ""; });
    }
});
