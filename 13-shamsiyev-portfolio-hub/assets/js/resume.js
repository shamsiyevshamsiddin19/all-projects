"use strict";

document.addEventListener('DOMContentLoaded', () => {
    const langSwitcher = document.getElementById('langSwitcher');
    if (!langSwitcher) return;

    const langBtns = langSwitcher.querySelectorAll('.lang-btn');
    const allEn = document.querySelectorAll('.lang-en');
    const allRu = document.querySelectorAll('.lang-ru');
    const allUz = document.querySelectorAll('.lang-uz');

    const elementsMap = {
        'en': allEn,
        'ru': allRu,
        'uz': allUz
    };

    function setLanguage(lang) {
        // Update switcher UI
        langSwitcher.setAttribute('data-active', lang);
        langBtns.forEach(btn => {
            if (btn.getAttribute('data-lang') === lang) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // Update content visibility
        for (const [key, elements] of Object.entries(elementsMap)) {
            elements.forEach(el => {
                if (key === lang) {
                    el.style.display = 'inline';
                } else {
                    el.style.display = 'none';
                }
            });
        }

        // Save preference
        localStorage.setItem('preferredLang', lang);
    }

    // Initialize from localStorage or default to 'en'
    const savedLang = localStorage.getItem('preferredLang') || 'en';
    setLanguage(savedLang);

    // Add click listeners
    langBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const selectedLang = btn.getAttribute('data-lang');
            setLanguage(selectedLang);
        });
    });
});
