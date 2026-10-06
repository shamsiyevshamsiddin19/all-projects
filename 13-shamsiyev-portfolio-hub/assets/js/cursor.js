"use strict";
// === Rolls-Royce-style trailing ring cursor — shared across every page ===
// A thin ring follows the pointer with easing (the signature lag). It keeps a
// fixed size and fills with the accent gradient on press (.cursor-down). The
// native cursor is only hidden once this is confirmed running (.cursor-ready),
// so a JS failure safely falls back to the OS cursor. Desktop + motion-safe.
(function () {
    if (!window.matchMedia) return;
    if (!matchMedia('(hover: hover) and (pointer: fine)').matches) return;
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const ring = document.querySelector('.cursor-ring');
    if (!ring) return;

    document.body.classList.add('cursor-ready');

    let mx = window.innerWidth / 2, my = window.innerHeight / 2; // pointer target
    let rx = mx, ry = my;                                        // eased ring position
    let seen = false;

    window.addEventListener('mousemove', (e) => {
        mx = e.clientX; my = e.clientY;
        if (!seen) { seen = true; document.body.classList.add('cursor-active'); }
    }, { passive: true });

    document.addEventListener('mouseleave', () => document.body.classList.remove('cursor-active'));
    document.addEventListener('mouseenter', () => document.body.classList.add('cursor-active'));
    document.addEventListener('mousedown', () => document.body.classList.add('cursor-down'));
    document.addEventListener('mouseup', () => document.body.classList.remove('cursor-down'));

    (function loop() {
        rx += (mx - rx) * 0.18;   // easing — the signature trailing lag
        ry += (my - ry) * 0.18;
        ring.style.transform = `translate3d(${rx}px, ${ry}px, 0)`;
        requestAnimationFrame(loop);
    })();
})();
