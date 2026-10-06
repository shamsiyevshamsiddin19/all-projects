/**
 * NexCloud Platform - Modern Interactive Logic
 * High-performance, accessible, and reactive UI interactions
 */

document.addEventListener('DOMContentLoaded', () => {
  initNavbarScroll();
  initMobileMenu();
  initMetricCounters();
  initModals();
  initFormsAndToasts();
  initSmoothScroll();
});

// 1. Sticky Navbar shadow on scroll
function initNavbarScroll() {
  const navbar = document.querySelector('.main-navbar');
  if (!navbar) return;

  window.addEventListener('scroll', () => {
    if (window.scrollY > 20) {
      navbar.style.boxShadow = '0 10px 25px -5px rgba(15, 23, 42, 0.08)';
      navbar.style.borderBottomColor = 'transparent';
    } else {
      navbar.style.boxShadow = 'none';
      navbar.style.borderBottomColor = 'var(--color-border-light)';
    }
  });
}

// 2. Mobile Menu Toggle
function initMobileMenu() {
  const toggleBtn = document.querySelector('.mobile-menu-toggle');
  const navMenu = document.querySelector('.nav-menu');
  if (!toggleBtn || !navMenu) return;

  toggleBtn.addEventListener('click', () => {
    const isOpen = navMenu.classList.toggle('mobile-open');
    toggleBtn.setAttribute('aria-expanded', isOpen);
  });
}

// 3. Animated Metric Counters
function initMetricCounters() {
  const counters = document.querySelectorAll('.metric-number');
  if (!counters.length) return;

  let animated = false;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting && !animated) {
        animated = true;
        counters.forEach(counter => {
          const target = counter.getAttribute('data-target');
          if (!target) return;
          animateValue(counter, target);
        });
      }
    });
  }, { threshold: 0.3 });

  const metricsSection = document.querySelector('.metrics-row-grid');
  if (metricsSection) {
    observer.observe(metricsSection);
  }
}

function animateValue(obj, targetStr) {
  let isPercentage = targetStr.includes('%');
  let isPlus = targetStr.includes('+');
  let isK = targetStr.includes('K');
  let isSlash = targetStr.includes('/');

  if (isSlash) {
    obj.textContent = targetStr; // e.g. 24/7
    return;
  }

  let num = parseFloat(targetStr.replace(/[^0-9.]/g, ''));
  let start = 0;
  let duration = 1600;
  let startTime = null;

  function step(timestamp) {
    if (!startTime) startTime = timestamp;
    let progress = Math.min((timestamp - startTime) / duration, 1);
    let current = progress * num;

    if (isPercentage) {
      obj.textContent = (current).toFixed(1) + '%';
    } else if (isK) {
      obj.textContent = Math.floor(current) + 'K+';
    } else if (isPlus) {
      obj.textContent = Math.floor(current) + '+';
    } else {
      obj.textContent = Math.floor(current);
    }

    if (progress < 1) {
      window.requestAnimationFrame(step);
    } else {
      obj.textContent = targetStr;
    }
  }
  window.requestAnimationFrame(step);
}

// 4. Modal Windows (Video, Contact, Search)
function initModals() {
  const modals = document.querySelectorAll('.modal-backdrop');
  const closeBtns = document.querySelectorAll('.modal-close-btn');

  // Open triggers
  document.querySelectorAll('[data-open-modal]').forEach(trigger => {
    trigger.addEventListener('click', (e) => {
      e.preventDefault();
      const modalId = trigger.getAttribute('data-open-modal');
      const modal = document.getElementById(modalId);
      if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
      }
    });
  });

  // Close triggers
  closeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      modals.forEach(m => m.classList.remove('active'));
      document.body.style.overflow = '';
    });
  });

  // Close on outside click
  modals.forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
      }
    });
  });

  // Keyboard shortcut (Escape & Cmd+K)
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      modals.forEach(m => m.classList.remove('active'));
      document.body.style.overflow = '';
    }
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      const searchModal = document.getElementById('searchModal');
      if (searchModal) {
        searchModal.classList.toggle('active');
        document.body.style.overflow = searchModal.classList.contains('active') ? 'hidden' : '';
      }
    }
  });
}

// 5. Form Submissions and Toast Notifications
function initFormsAndToasts() {
  const newsletterForm = document.getElementById('newsletterForm');
  if (newsletterForm) {
    newsletterForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const input = newsletterForm.querySelector('input[type="email"]');
      if (input && input.value) {
        showToast(`🎉 Rahmat! ${input.value} muvaffaqiyatli obuna qilindi.`);
        input.value = '';
      }
    });
  }

  const contactForm = document.getElementById('contactModalForm');
  if (contactForm) {
    contactForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const name = contactForm.querySelector('#contactName')?.value || 'Hurmatli mijoz';
      const contactModal = document.getElementById('contactModal');
      if (contactModal) contactModal.classList.remove('active');
      document.body.style.overflow = '';
      showToast(`✅ Rahmat, ${name}! Sizning so'rovingiz qabul qilindi. Tez orada mutaxassis bog'lanadi.`);
      contactForm.reset();
    });
  }
}

function showToast(message) {
  let toast = document.querySelector('.toast-notification');
  if (!toast) {
    toast = document.createElement('div');
    toast.className = 'toast-notification';
    document.body.appendChild(toast);
  }
  toast.innerHTML = `<span>${message}</span>`;
  toast.classList.add('show');

  setTimeout(() => {
    toast.classList.remove('show');
  }, 4000);
}

// 6. Smooth Scroll for hash links
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href');
      if (targetId && targetId !== '#') {
        const targetElement = document.querySelector(targetId);
        if (targetElement) {
          e.preventDefault();
          targetElement.scrollIntoView({ behavior: 'smooth' });
        }
      }
    });
  });
}
