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
  initAuth();
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

// 2. Mobile Menu Drawer & Toggle
function initMobileMenu() {
  const toggleBtn = document.getElementById('mobileMenuBtn');
  const drawer = document.getElementById('mobileNavDrawer');
  const backdrop = document.getElementById('mobileDrawerBackdrop');
  const closeBtn = document.getElementById('mobileDrawerCloseBtn');
  const drawerLinks = document.querySelectorAll('.mobile-nav-link, .btn-drawer-signin, .btn-drawer-cta');

  if (!toggleBtn || !drawer) return;

  function openDrawer() {
    drawer.classList.add('active');
    if (backdrop) backdrop.classList.add('active');
    document.body.style.overflow = 'hidden';
    toggleBtn.setAttribute('aria-expanded', 'true');
  }

  function closeDrawer() {
    drawer.classList.remove('active');
    if (backdrop) backdrop.classList.remove('active');
    document.body.style.overflow = '';
    toggleBtn.setAttribute('aria-expanded', 'false');
  }

  toggleBtn.addEventListener('click', () => {
    if (drawer.classList.contains('active')) {
      closeDrawer();
    } else {
      openDrawer();
    }
  });

  if (closeBtn) closeBtn.addEventListener('click', closeDrawer);
  if (backdrop) backdrop.addEventListener('click', closeDrawer);

  drawerLinks.forEach(link => {
    link.addEventListener('click', () => {
      closeDrawer();
    });
  });

  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && drawer.classList.contains('active')) {
      closeDrawer();
    }
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
        if (modalId === 'authModal' && typeof window.switchAuthTab === 'function') {
          const targetTab = trigger.getAttribute('data-auth-tab') || 'signin';
          window.switchAuthTab(targetTab);
        }
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

// =========================================================================
// 7. GOOGLE & SYSTEM AUTHENTICATION
// =========================================================================
// O'zingizning Google Cloud Console Client ID-ingizni shu yerga qo'yishingiz mumkin:
window.GOOGLE_CLIENT_ID = window.GOOGLE_CLIENT_ID || "";

function initAuth() {
  const authModal = document.getElementById('authModal');
  const googleChooserModal = document.getElementById('googleChooserModal');
  const tabSignInBtn = document.getElementById('tabSignInBtn');
  const tabSignUpBtn = document.getElementById('tabSignUpBtn');
  const authNameGroup = document.getElementById('authNameGroup');
  const authModalTitle = document.getElementById('authModalTitle');
  const authModalSubtitle = document.getElementById('authModalSubtitle');
  const authSubmitText = document.getElementById('authSubmitText');
  const authFooterPrompt = document.getElementById('authFooterPrompt');
  const authSwitchLink = document.getElementById('authSwitchLink');
  const authForgotLink = document.getElementById('authForgotLink');
  const authCheckboxText = document.getElementById('authCheckboxText');
  const authFullName = document.getElementById('authFullName');
  const authEmail = document.getElementById('authEmail');
  const authPassword = document.getElementById('authPassword');
  const togglePwdBtn = document.getElementById('togglePwdBtn');
  const authMainForm = document.getElementById('authMainForm');
  const googleCustomBtn = document.getElementById('googleCustomBtn');
  const userProfileNav = document.getElementById('userProfileNav');
  const userProfileBtn = document.getElementById('userProfileBtn');
  const signInBtn = document.getElementById('signInBtn');
  const navGetStartedBtn = document.getElementById('navGetStartedBtn');
  const drawerActionsGuest = document.getElementById('drawerActionsGuest');
  const drawerActionsUser = document.getElementById('drawerActionsUser');
  const authLogoutBtn = document.getElementById('authLogoutBtn');
  const drawerLogoutBtn = document.getElementById('drawerLogoutBtn');

  let currentTab = 'signin';

  // Function to switch tabs
  window.switchAuthTab = function(tab) {
    currentTab = tab;
    if (tab === 'signin') {
      if (tabSignInBtn) tabSignInBtn.classList.add('active');
      if (tabSignUpBtn) tabSignUpBtn.classList.remove('active');
      if (authNameGroup) authNameGroup.classList.add('hidden');
      if (authFullName) authFullName.removeAttribute('required');
      if (authModalTitle) authModalTitle.textContent = 'Hisobingizga kiring';
      if (authModalSubtitle) authModalSubtitle.textContent = "NexCloud bulut platformasidan to'liq foydalanish uchun tizimga kiring";
      if (authSubmitText) authSubmitText.textContent = 'Tizimga kirish';
      if (authForgotLink) authForgotLink.style.display = 'block';
      if (authCheckboxText) authCheckboxText.textContent = 'Meni eslab qolish';
      if (authFooterPrompt) authFooterPrompt.textContent = "Hisobingiz yo'qmi?";
      if (authSwitchLink) authSwitchLink.textContent = "Ro'yxatdan o'tish";
      const gLabel = document.getElementById('googleBtnLabel');
      if (gLabel) gLabel.textContent = 'Google orqali kirish';
    } else {
      if (tabSignUpBtn) tabSignUpBtn.classList.add('active');
      if (tabSignInBtn) tabSignInBtn.classList.remove('active');
      if (authNameGroup) authNameGroup.classList.remove('hidden');
      if (authFullName) authFullName.setAttribute('required', 'required');
      if (authModalTitle) authModalTitle.textContent = 'Yangi hisob yaratish';
      if (authModalSubtitle) authModalSubtitle.textContent = 'Bulutli hosting va loyihalaringizni bir daqiqada ishga tushiring';
      if (authSubmitText) authSubmitText.textContent = "Ro'yxatdan o'tish";
      if (authForgotLink) authForgotLink.style.display = 'none';
      if (authCheckboxText) authCheckboxText.textContent = 'Xizmat shartlariga roziman';
      if (authFooterPrompt) authFooterPrompt.textContent = 'Allaqachon hisobingiz bormi?';
      if (authSwitchLink) authSwitchLink.textContent = 'Kirish';
      const gLabel = document.getElementById('googleBtnLabel');
      if (gLabel) gLabel.textContent = "Google orqali ro'yxatdan o'tish";
    }
  };

  if (tabSignInBtn) tabSignInBtn.addEventListener('click', () => switchAuthTab('signin'));
  if (tabSignUpBtn) tabSignUpBtn.addEventListener('click', () => switchAuthTab('signup'));
  if (authSwitchLink) {
    authSwitchLink.addEventListener('click', () => {
      switchAuthTab(currentTab === 'signin' ? 'signup' : 'signin');
    });
  }

  // Toggle Password Visibility
  if (togglePwdBtn && authPassword) {
    togglePwdBtn.addEventListener('click', () => {
      const isPwd = authPassword.type === 'password';
      authPassword.type = isPwd ? 'text' : 'password';
      togglePwdBtn.style.color = isPwd ? '#16a34a' : '#94a3b8';
    });
  }

  // Handle Logged-In User State
  function updateAuthStateUI() {
    const savedUserJson = localStorage.getItem('nexcloud_auth_user');
    if (savedUserJson) {
      try {
        const user = JSON.parse(savedUserJson);
        if (signInBtn) signInBtn.classList.add('hidden');
        if (navGetStartedBtn) navGetStartedBtn.classList.add('hidden');
        if (userProfileNav) userProfileNav.classList.remove('hidden');

        const firstName = user.name ? user.name.split(' ')[0] : 'Foydalanuvchi';
        const initials = user.name ? user.name.split(' ').filter(Boolean).map(n => n[0]).join('').substring(0, 2).toUpperCase() : 'SS';
        
        const navAvatar = document.getElementById('userNavAvatar');
        const navName = document.getElementById('userNavName');
        const dropName = document.getElementById('userDropdownName');
        const dropEmail = document.getElementById('userDropdownEmail');
        
        if (navName) navName.textContent = firstName;
        if (dropName) dropName.textContent = user.name || user.email;
        if (dropEmail) dropEmail.textContent = user.email || '';
        if (navAvatar) {
          if (user.picture) {
            navAvatar.innerHTML = '<img src="' + user.picture + '" style="width:100%;height:100%;border-radius:50%;object-fit:cover;" alt="Avatar">';
          } else {
            navAvatar.textContent = initials;
          }
        }

        if (drawerActionsGuest) drawerActionsGuest.classList.add('hidden');
        if (drawerActionsUser) drawerActionsUser.classList.remove('hidden');
        const drawerName = document.getElementById('drawerUserName');
        const drawerEmail = document.getElementById('drawerUserEmail');
        const drawerAvatar = document.getElementById('drawerUserAvatar');
        if (drawerName) drawerName.textContent = user.name || user.email;
        if (drawerEmail) drawerEmail.textContent = user.email || '';
        if (drawerAvatar) {
          if (user.picture) {
            drawerAvatar.innerHTML = '<img src="' + user.picture + '" style="width:100%;height:100%;border-radius:50%;object-fit:cover;" alt="Avatar">';
          } else {
            drawerAvatar.textContent = initials;
          }
        }
      } catch (e) {
        console.error('Auth parse error:', e);
      }
    } else {
      if (signInBtn) signInBtn.classList.remove('hidden');
      if (navGetStartedBtn) navGetStartedBtn.classList.remove('hidden');
      if (userProfileNav) userProfileNav.classList.add('hidden');
      if (drawerActionsGuest) drawerActionsGuest.classList.remove('hidden');
      if (drawerActionsUser) drawerActionsUser.classList.add('hidden');
    }
  }

  // User Profile Dropdown Toggle
  if (userProfileBtn && userProfileNav) {
    userProfileBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      userProfileNav.classList.toggle('open');
    });

    document.addEventListener('click', (e) => {
      if (!userProfileNav.contains(e.target)) {
        userProfileNav.classList.remove('open');
      }
    });
  }

  // Logout Function
  function logoutUser() {
    localStorage.removeItem('nexcloud_auth_user');
    if (userProfileNav) userProfileNav.classList.remove('open');
    updateAuthStateUI();
    showToast('👋 Tizimdan muvaffaqiyatli chiqdingiz.');
  }

  if (authLogoutBtn) authLogoutBtn.addEventListener('click', logoutUser);
  if (drawerLogoutBtn) drawerLogoutBtn.addEventListener('click', logoutUser);

  // Successful Login Handler
  function loginSuccess(userData, source = 'Google') {
    localStorage.setItem('nexcloud_auth_user', JSON.stringify(userData));
    updateAuthStateUI();
    if (authModal) authModal.classList.remove('active');
    if (googleChooserModal) googleChooserModal.classList.remove('active');
    document.body.style.overflow = '';
    showToast(`🎉 Xush kelibsiz, ${userData.name || userData.email}! (${source} orqali ulandi)`);
  }

  // Google Login Click
  if (googleCustomBtn) {
    googleCustomBtn.addEventListener('click', () => {
      if (window.GOOGLE_CLIENT_ID && window.GOOGLE_CLIENT_ID.length > 15 && window.google && window.google.accounts) {
        try {
          google.accounts.id.prompt((notification) => {
            if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
              openGoogleChooser();
            }
          });
          return;
        } catch (err) {
          console.warn('Google GSI prompt fallback:', err);
        }
      }
      openGoogleChooser();
    });
  }

  function openGoogleChooser() {
    if (googleChooserModal) {
      googleChooserModal.classList.add('active');
      document.body.style.overflow = 'hidden';
    }
  }

  // Google Chooser Account Items click
  document.querySelectorAll('.google-acc-item[data-email]').forEach(item => {
    item.addEventListener('click', () => {
      const email = item.getAttribute('data-email');
      const name = item.getAttribute('data-name');
      loginSuccess({
        name: name,
        email: email,
        provider: 'google',
        picture: ''
      }, 'Google');
    });
  });

  const googleCustomEmailBtn = document.getElementById('googleCustomEmailBtn');
  if (googleCustomEmailBtn) {
    googleCustomEmailBtn.addEventListener('click', () => {
      const email = prompt('Google hisobingiz elektron pochtasini kiriting (masalan: siz@gmail.com):', 'shamsiyevshamsiddin19@gmail.com');
      if (email && email.includes('@')) {
        const namePart = email.split('@')[0].replace('.', ' ');
        const formattedName = namePart.charAt(0).toUpperCase() + namePart.slice(1);
        loginSuccess({
          name: formattedName,
          email: email,
          provider: 'google',
          picture: ''
        }, 'Google');
      }
    });
  }

  // Form Submit (Standard Email/Password)
  if (authMainForm) {
    authMainForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const email = authEmail ? authEmail.value : '';
      const name = authFullName && authFullName.value ? authFullName.value : email.split('@')[0];
      
      loginSuccess({
        name: name,
        email: email,
        provider: 'email',
        picture: ''
      }, currentTab === 'signin' ? 'Email' : "Ro'yxatdan o'tish");
      authMainForm.reset();
    });
  }

  // Setup Google Identity Services if Client ID exists
  if (window.GOOGLE_CLIENT_ID && window.GOOGLE_CLIENT_ID.length > 15) {
    window.addEventListener('load', () => {
      if (window.google && window.google.accounts) {
        try {
          google.accounts.id.initialize({
            client_id: window.GOOGLE_CLIENT_ID,
            callback: (response) => {
              try {
                const base64Url = response.credential.split('.')[1];
                const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
                const jsonPayload = decodeURIComponent(atob(base64).split('').map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)).join(''));
                const payload = JSON.parse(jsonPayload);
                loginSuccess({
                  name: payload.name || payload.given_name,
                  email: payload.email,
                  picture: payload.picture,
                  provider: 'google'
                }, 'Google Verified');
              } catch (jwtErr) {
                console.error('JWT decode error:', jwtErr);
              }
            }
          });

          const container = document.getElementById('g_id_signin_container');
          if (container) {
            container.style.display = 'flex';
            if (googleCustomBtn) googleCustomBtn.style.display = 'none';
            google.accounts.id.renderButton(container, {
              theme: 'outline',
              size: 'large',
              width: 380,
              text: 'continue_with',
              shape: 'rectangular',
              logo_alignment: 'left'
            });
          }
        } catch (gErr) {
          console.warn('Google GSI init err:', gErr);
        }
      }
    });
  }

  updateAuthStateUI();
}
