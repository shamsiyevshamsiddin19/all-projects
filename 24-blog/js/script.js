/**
 * ========================================================
 * HAGUE — EDITORIAL MAGAZINE JAVASCRIPT
 * FastAPI Backend & PostgreSQL Database Integration
 * ========================================================
 */

document.addEventListener('DOMContentLoaded', () => {
  'use strict';

  // 1. API Configuration & State
  const isLocalFile = window.location.protocol === 'file:';
  const isLocalHost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  const API_BASE = isLocalFile 
    ? 'http://127.0.0.1:8000' 
    : (window.location.port === '8000' ? '' : (isLocalHost && window.location.port !== '80' && window.location.port !== '' ? 'http://127.0.0.1:8000' : ''));

  let currentUser = null;
  let authToken = localStorage.getItem('blog_access_token') || null;
  let activePostId = null;
  let allApiPosts = [];
  let allCategories = [];

  // DOM Elements
  const articleCards = document.querySelectorAll('.article-card');
  const articleModalEl = document.getElementById('articleModal');
  const modalArticleTitle = document.getElementById('modalArticleTitle');
  const modalArticleCategory = document.getElementById('modalArticleCategory');
  const modalArticleDate = document.getElementById('modalArticleDate');
  const modalArticleAuthor = document.getElementById('modalArticleAuthor');
  const modalArticleImg = document.getElementById('modalArticleImg');
  const modalArticleContent = document.getElementById('modalArticleContent');
  const modalReadingTime = document.getElementById('modalReadingTime');
  const likeBtn = document.getElementById('likeBtn');
  const likeCount = document.getElementById('likeCount');
  const bookmarkBtn = document.getElementById('bookmarkBtn');
  const shareBtn = document.getElementById('shareBtn');

  // Comments Elements
  const modalCommentsCount = document.getElementById('modalCommentsCount');
  const modalCommentsList = document.getElementById('modalCommentsList');
  const addCommentForm = document.getElementById('addCommentForm');
  const commentInput = document.getElementById('commentInput');
  const commentUserHint = document.getElementById('commentUserHint');

  // Search Elements
  const liveSearchInput = document.getElementById('liveSearchInput');
  const searchResults = document.getElementById('searchResults');

  // Header & Auth Elements
  const backendStatusBadge = document.getElementById('backendStatusBadge');
  const headerWritePostBtn = document.getElementById('headerWritePostBtn');
  const authHeaderContainer = document.getElementById('authHeaderContainer');
  const loginTriggerBtn = document.getElementById('loginTriggerBtn');

  // Auth Modal & Forms
  const authModalEl = document.getElementById('authModal');
  const loginForm = document.getElementById('loginForm');
  const registerForm = document.getElementById('registerForm');
  const loginAlert = document.getElementById('loginAlert');
  const registerAlert = document.getElementById('registerAlert');

  // Create Post Modal & Form
  const createPostModalEl = document.getElementById('createPostModal');
  const createPostForm = document.getElementById('createPostForm');
  const postCategorySelect = document.getElementById('postCategorySelect');
  const createPostAlert = document.getElementById('createPostAlert');

  // Newsletter Forms
  const subscribeForm = document.getElementById('subscribeForm');
  const newsletterCalloutForm = document.getElementById('newsletterCalloutForm');

  // Bootstrap Modal Instances
  let articleModal = articleModalEl && window.bootstrap ? new bootstrap.Modal(articleModalEl) : null;
  let authModal = authModalEl && window.bootstrap ? new bootstrap.Modal(authModalEl) : null;
  let createPostModal = createPostModalEl && window.bootstrap ? new bootstrap.Modal(createPostModalEl) : null;

  // ========================================================
  // 2. BACKEND HEALTH CHECK & AUTH INITIALIZATION
  // ========================================================
  async function checkBackendHealth() {
    try {
      const res = await fetch(`${API_BASE}/api/health`);
      if (res.ok) {
        if (backendStatusBadge) {
          backendStatusBadge.className = 'badge bg-success-subtle text-success border border-success-subtle d-inline-flex align-items-center gap-1 py-1 px-2';
          backendStatusBadge.innerHTML = '<i class="bi bi-circle-fill text-success" style="font-size:0.45rem;"></i> <span class="small fw-semibold">FastAPI & PostgreSQL (Ulangan)</span>';
        }
        await loadInitialBackendData();
      } else {
        throw new Error('API unreachable');
      }
    } catch {
      if (backendStatusBadge) {
        backendStatusBadge.className = 'badge bg-warning-subtle text-warning border border-warning-subtle d-inline-flex align-items-center gap-1 py-1 px-2';
        backendStatusBadge.innerHTML = '<i class="bi bi-circle-fill text-warning" style="font-size:0.45rem;"></i> <span class="small fw-semibold">Lokal Rejim (FastAPI kutilyapti)</span>';
      }
    }
  }

  async function loadInitialBackendData() {
    await Promise.all([
      fetchUserProfile(),
      fetchCategories(),
      fetchPosts()
    ]);
  }

  // ========================================================
  // 3. AUTHENTICATION (Register, Login, Profile, Logout)
  // ========================================================
  async function fetchUserProfile() {
    if (!authToken) {
      renderAuthHeader(null);
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/auth/me`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      if (res.ok) {
        currentUser = await res.json();
        renderAuthHeader(currentUser);
      } else {
        // Token muddati o'tgan bo'lsa
        logout();
      }
    } catch {
      renderAuthHeader(null);
    }
  }

  function renderAuthHeader(user) {
    if (!authHeaderContainer) return;
    if (user) {
      authHeaderContainer.innerHTML = `
        <div class="dropdown">
          <button class="btn btn-outline-dark btn-sm dropdown-toggle rounded-1 fw-semibold d-flex align-items-center gap-1" 
                  type="button" data-bs-toggle="dropdown" aria-expanded="false">
            <i class="bi bi-person-check-fill text-success"></i>
            <span>${user.username}</span>
          </button>
          <ul class="dropdown-menu dropdown-menu-end shadow-sm border-0 rounded-1">
            <li class="dropdown-header small text-secondary">${user.email}</li>
            <li><hr class="dropdown-divider"></li>
            <li><a class="dropdown-item small" href="#" id="myPostsLink"><i class="bi bi-file-earmark-text me-2"></i>Mening maqolalarim</a></li>
            <li><button class="dropdown-item small text-danger" id="logoutActionBtn"><i class="bi bi-box-arrow-right me-2"></i>Chiqish</button></li>
          </ul>
        </div>
      `;

      document.getElementById('logoutActionBtn')?.addEventListener('click', (e) => {
        e.preventDefault();
        logout();
      });

      document.getElementById('myPostsLink')?.addEventListener('click', (e) => {
        e.preventDefault();
        filterMyPosts();
      });

      if (commentUserHint) {
        commentUserHint.innerHTML = `<span class="text-success"><i class="bi bi-check-circle-fill me-1"></i><strong>${user.username}</strong> nomidan izoh</span>`;
      }
    } else {
      authHeaderContainer.innerHTML = `
        <button class="btn btn-primary btn-sm px-3 py-1 rounded-1 fw-semibold text-white shadow-sm d-flex align-items-center gap-1" 
                id="loginTriggerBtn"
                type="button">
          <i class="bi bi-person-fill"></i>
          <span>Kirish</span>
        </button>
      `;
      document.getElementById('loginTriggerBtn')?.addEventListener('click', () => {
        if (authModal) authModal.show();
      });

      if (commentUserHint) {
        commentUserHint.textContent = "Izoh qoldirish uchun tizimga kiring";
      }
    }
  }

  function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('blog_access_token');
    renderAuthHeader(null);
    showToast("Tizimdan muvaffaqiyatli chiqildi.");
  }

  // Login Form submit
  loginForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const emailOrUser = document.getElementById('loginEmail')?.value.trim();
    const password = document.getElementById('loginPassword')?.value;
    if (loginAlert) loginAlert.classList.add('d-none');

    try {
      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: emailOrUser, password: password })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Login yoki parol noto'g'ri");
      }

      authToken = data.access_token;
      currentUser = data.user;
      localStorage.setItem('blog_access_token', authToken);
      renderAuthHeader(currentUser);
      if (authModal) authModal.hide();
      loginForm.reset();
      showToast(`Xush kelibsiz, ${currentUser.username}!`);
      
      // Agar maqola modali ochiq bo'lsa, izohlarni yangilash
      if (activePostId) {
        loadCommentsForPost(activePostId);
      }
    } catch (err) {
      if (loginAlert) {
        loginAlert.textContent = err.message;
        loginAlert.classList.remove('d-none');
      }
    }
  });

  // Register Form submit
  registerForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('regUsername')?.value.trim();
    const email = document.getElementById('regEmail')?.value.trim();
    const password = document.getElementById('regPassword')?.value;
    if (registerAlert) registerAlert.classList.add('d-none');

    try {
      const res = await fetch(`${API_BASE}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Ro'yxatdan o'tishda xatolik yuz berdi");
      }

      authToken = data.access_token;
      currentUser = data.user;
      localStorage.setItem('blog_access_token', authToken);
      renderAuthHeader(currentUser);
      if (authModal) authModal.hide();
      registerForm.reset();
      showToast(`Tabriklaymiz, ${currentUser.username}! Hisob muvaffaqiyatli yaratildi.`);
    } catch (err) {
      if (registerAlert) {
        registerAlert.textContent = err.message;
        registerAlert.classList.remove('d-none');
      }
    }
  });

  // Trigger login modal button
  loginTriggerBtn?.addEventListener('click', () => {
    if (authModal) authModal.show();
  });

  // ========================================================
  // 4. CATEGORIES LOADING & SELECTION
  // ========================================================
  async function fetchCategories() {
    try {
      const res = await fetch(`${API_BASE}/api/categories`);
      if (res.ok) {
        allCategories = await res.json();
        populateCategoryDropdown(allCategories);
        attachCategoryFilters();
      }
    } catch (err) {
      console.warn("Could not load categories from backend:", err);
    }
  }

  function populateCategoryDropdown(cats) {
    if (!postCategorySelect) return;
    postCategorySelect.innerHTML = '<option value="">Kategoriyani tanlang...</option>' + 
      cats.map(c => `<option value="${c.id}">${c.name} (${c.post_count || 0} maqola)</option>`).join('');
  }

  function attachCategoryFilters() {
    // Navbar category links
    const categoryLinks = document.querySelectorAll('.main-navbar .nav-link, .main-navbar .dropdown-item');
    categoryLinks.forEach(link => {
      const text = link.innerText.trim();
      const matchedCat = allCategories.find(c => c.name.toLowerCase() === text.toLowerCase());
      if (matchedCat) {
        link.addEventListener('click', (e) => {
          e.preventDefault();
          fetchPosts({ category_id: matchedCat.id });
          showToast(`Kategoriya bo'yicha filter: ${matchedCat.name}`);
        });
      }
    });
  }

  // ========================================================
  // 5. POSTS FETCHING & INTEGRATION
  // ========================================================
  async function fetchPosts(params = {}) {
    try {
      let url = `${API_BASE}/api/posts?limit=30`;
      if (params.category_id) url += `&category_id=${params.category_id}`;
      if (params.search) url += `&search=${encodeURIComponent(params.search)}`;
      if (params.owner_id) url += `&owner_id=${params.owner_id}`;

      const res = await fetch(url);
      if (res.ok) {
        allApiPosts = await res.json();
        enrichCardsWithApiData(allApiPosts);
      }
    } catch (err) {
      console.warn("Could not fetch posts from backend:", err);
    }
  }

  function enrichCardsWithApiData(posts) {
    if (!posts || posts.length === 0) return;

    // Har bir kartaga mos API post ma'lumotlarini bog'lash
    articleCards.forEach((card, index) => {
      const apiPost = posts[index % posts.length];
      if (apiPost) {
        card.dataset.apiId = apiPost.id;
        card.dataset.title = apiPost.title;
        card.dataset.category = apiPost.category?.name || card.dataset.category || 'ARTICLE';
        card.dataset.author = apiPost.owner?.username || card.dataset.author || 'Author';
        card.dataset.content = apiPost.content;
        card.dataset.commentsCount = apiPost.comments_count || 0;

        // Kartadagi sarlavha va kategoriyani ham yangilash
        const titleEl = card.querySelector('.article-title');
        if (titleEl && index < posts.length) {
          titleEl.textContent = apiPost.title;
        }
        const badgeEl = card.querySelector('.badge');
        if (badgeEl && apiPost.category?.name) {
          badgeEl.textContent = apiPost.category.name;
        }
      }
    });
  }

  async function filterMyPosts() {
    if (!currentUser) return;
    try {
      const res = await fetch(`${API_BASE}/api/users/me/posts`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      if (res.ok) {
        const myPosts = await res.json();
        showToast(`Sizning maqolalaringiz: ${myPosts.length} ta`);
        if (myPosts.length > 0) {
          enrichCardsWithApiData(myPosts);
          window.scrollTo({ top: document.getElementById('hero-section')?.offsetTop || 0, behavior: 'smooth' });
        } else {
          showToast("Hali hech qanday maqola yozmagansiz. Yangi maqola yarating!");
        }
      }
    } catch (err) {
      showToast("Maqolalarni yuklashda xatolik yuz berdi");
    }
  }

  // ========================================================
  // 6. CREATE NEW POST (Maqola Yaratish)
  // ========================================================
  headerWritePostBtn?.addEventListener('click', () => {
    if (!currentUser) {
      showToast("Maqola yozish uchun avval tizimga kiring");
      if (authModal) authModal.show();
      return;
    }
    if (createPostModal) {
      if (createPostAlert) createPostAlert.classList.add('d-none');
      createPostModal.show();
    }
  });

  createPostForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!authToken) {
      showToast("Iltimos, avval tizimga kiring");
      if (authModal) authModal.show();
      return;
    }

    const title = document.getElementById('postTitleInput')?.value.trim();
    const categoryId = document.getElementById('postCategorySelect')?.value;
    const rating = parseInt(document.getElementById('postRatingInput')?.value || '5', 10);
    const content = document.getElementById('postContentInput')?.value.trim();

    if (createPostAlert) createPostAlert.classList.add('d-none');

    const payload = {
      title,
      content,
      category_id: categoryId ? parseInt(categoryId, 10) : null,
      rating: rating,
      published: true
    };

    try {
      const res = await fetch(`${API_BASE}/api/posts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Maqola yaratishda xatolik");
      }

      if (createPostModal) createPostModal.hide();
      createPostForm.reset();
      showToast("Maqolangiz muvaffaqiyatli PostgreSQL bazasiga saqlandi!");
      
      // Postlar ro'yxatini qayta yuklash
      await fetchPosts();
    } catch (err) {
      if (createPostAlert) {
        createPostAlert.textContent = err.message;
        createPostAlert.classList.remove('d-none');
      }
    }
  });

  // ========================================================
  // 7. ARTICLE MODAL & COMMENTS SYSTEM
  // ========================================================
  articleCards.forEach(card => {
    card.addEventListener('click', async (e) => {
      if (e.target.tagName.toLowerCase() === 'a') {
        e.preventDefault();
      }

      const id = card.dataset.id || 'article';
      const apiId = card.dataset.apiId ? parseInt(card.dataset.apiId, 10) : null;
      activePostId = apiId;

      const title = card.dataset.title || card.querySelector('.article-title')?.innerText || 'Article Title';
      const category = card.dataset.category || 'NEWS';
      const date = card.dataset.date || 'January 8, 2025';
      const author = card.dataset.author || 'Editorial Staff';
      const img = card.dataset.img || card.querySelector('img')?.src;
      const content = card.dataset.content || 'Content for this article is being updated by the editorial team.';

      if (modalArticleTitle) modalArticleTitle.textContent = title;
      if (modalArticleCategory) modalArticleCategory.textContent = category;
      if (modalArticleDate) modalArticleDate.textContent = date;
      if (modalArticleAuthor) modalArticleAuthor.textContent = author;
      if (modalArticleImg && img) {
        modalArticleImg.src = img;
        modalArticleImg.alt = title;
      }

      const words = content.split(/\s+/).length;
      const readingMinutes = Math.max(2, Math.ceil(words / 40));
      if (modalReadingTime) modalReadingTime.textContent = `${readingMinutes} min read`;

      if (modalArticleContent) {
        modalArticleContent.innerHTML = `
          <p class="lead text-dark fw-normal">${content}</p>
          <blockquote class="p-3 my-4 bg-light border-start border-4 border-primary font-serif fst-italic">
            "Fikr va axborot erkinligi jamiyat taraqqiyotining asosiy poydevoridir."
          </blockquote>
          <p class="text-secondary">Ushbu maqola HAGUE tahririyati tomonidan mustaqil tarzda tayyorlangan va PostgreSQL ma'lumotlar bazasida arxivlangan.</p>
        `;
      }

      // Like holatini tiklash
      const savedLikes = parseInt(localStorage.getItem(`hague_like_${id}`) || '42', 10);
      if (likeCount) likeCount.textContent = savedLikes;
      if (likeBtn) {
        likeBtn.dataset.currentId = id;
        const isLiked = localStorage.getItem(`hague_is_liked_${id}`) === 'true';
        likeBtn.classList.toggle('btn-danger', isLiked);
        likeBtn.classList.toggle('btn-outline-secondary', !isLiked);
        likeBtn.querySelector('i').className = isLiked ? 'bi bi-heart-fill me-1 text-white' : 'bi bi-heart me-1';
      }

      // Bookmark
      if (bookmarkBtn) {
        bookmarkBtn.dataset.currentId = id;
        const isBookmarked = localStorage.getItem(`hague_bookmarked_${id}`) === 'true';
        bookmarkBtn.classList.toggle('btn-primary', isBookmarked);
        bookmarkBtn.classList.toggle('btn-outline-secondary', !isBookmarked);
        bookmarkBtn.innerHTML = isBookmarked 
          ? '<i class="bi bi-bookmark-fill me-1 text-white"></i> Bookmarked' 
          : '<i class="bi bi-bookmark me-1"></i> Bookmark';
      }

      // Load comments for active post
      if (apiId) {
        loadCommentsForPost(apiId);
      } else {
        renderCommentsList([]);
      }

      if (articleModal) {
        articleModal.show();
      }
    });
  });

  async function loadCommentsForPost(postId) {
    if (!modalCommentsList) return;
    modalCommentsList.innerHTML = '<div class="text-center py-2 text-secondary small"><i class="bi bi-hourglass-split me-1"></i>Izohlar yuklanmoqda...</div>';

    try {
      const res = await fetch(`${API_BASE}/api/posts/${postId}/comments`);
      if (res.ok) {
        const comments = await res.json();
        renderCommentsList(comments);
        if (modalCommentsCount) modalCommentsCount.textContent = comments.length;
      } else {
        renderCommentsList([]);
      }
    } catch {
      renderCommentsList([]);
    }
  }

  function renderCommentsList(comments) {
    if (!modalCommentsList) return;
    if (modalCommentsCount) modalCommentsCount.textContent = comments ? comments.length : 0;

    if (!comments || comments.length === 0) {
      modalCommentsList.innerHTML = `
        <div class="text-center py-4 bg-light rounded text-secondary small">
          <i class="bi bi-chat-square-dots fs-3 d-block mb-1 text-muted"></i>
          Hali hech qanday izoh qoldirilmagan. Birinchi bo'lib fikr bildiring!
        </div>
      `;
      return;
    }

    modalCommentsList.innerHTML = comments.map(c => {
      const authorName = c.author?.username || 'Foydalanuvchi';
      const isMyComment = currentUser && currentUser.id === c.user_id;
      const dateFormatted = new Date(c.created_at).toLocaleDateString('uz-UZ', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });

      return `
        <div class="comment-card p-3 rounded border bg-white shadow-2xs" id="comment-${c.id}">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <div class="d-flex align-items-center gap-2">
              <span class="badge bg-secondary-subtle text-dark fw-bold rounded-circle p-2" style="width:28px;height:28px;display:inline-flex;align-items:center;justify-content:center;">
                ${authorName.charAt(0).toUpperCase()}
              </span>
              <strong class="small text-dark">${authorName}</strong>
              <small class="text-secondary">• ${dateFormatted}</small>
            </div>
            ${isMyComment ? `
              <button class="btn btn-outline-danger btn-sm border-0 py-0 px-2 delete-comment-btn" data-comment-id="${c.id}" title="O'chirish">
                <i class="bi bi-trash3"></i>
              </button>
            ` : ''}
          </div>
          <p class="mb-0 text-secondary small lh-base">${escapeHtml(c.content)}</p>
        </div>
      `;
    }).join('');

    // Attach delete comment handlers
    modalCommentsList.querySelectorAll('.delete-comment-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const cId = btn.dataset.commentId;
        if (!confirm("Haqiqatan ham bu izohni o'chirmoqchimisiz?")) return;
        await deleteComment(cId);
      });
    });
  }

  // Add Comment Form submit
  addCommentForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!currentUser || !authToken) {
      showToast("Izoh qoldirish uchun tizimga kiring!");
      if (authModal) authModal.show();
      return;
    }

    if (!activePostId) {
      showToast("Maqola aniqlanmadi.");
      return;
    }

    const text = commentInput?.value.trim();
    if (!text) return;

    try {
      const res = await fetch(`${API_BASE}/api/posts/${activePostId}/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ content: text })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Izoh qo'shishda xatolik yuz berdi");
      }

      if (commentInput) commentInput.value = '';
      showToast("Izohingiz muvaffaqiyatli saqlandi!");
      await loadCommentsForPost(activePostId);
    } catch (err) {
      showToast(err.message);
    }
  });

  async function deleteComment(commentId) {
    try {
      const res = await fetch(`${API_BASE}/api/comments/${commentId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      if (res.ok) {
        showToast("Izoh o'chirildi.");
        if (activePostId) await loadCommentsForPost(activePostId);
      } else {
        showToast("Izohni o'chirish huquqi yo'q");
      }
    } catch {
      showToast("Xatolik yuz berdi");
    }
  }

  // Helper function to escape HTML
  function escapeHtml(text) {
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
  }

  // ========================================================
  // 8. LIKE, BOOKMARK, SHARE HANDLERS
  // ========================================================
  likeBtn?.addEventListener('click', () => {
    const id = likeBtn.dataset.currentId;
    if (!id) return;

    let count = parseInt(likeCount?.textContent || '42', 10);
    const isLiked = localStorage.getItem(`hague_is_liked_${id}`) === 'true';

    if (isLiked) {
      count -= 1;
      localStorage.setItem(`hague_is_liked_${id}`, 'false');
      likeBtn.classList.remove('btn-danger');
      likeBtn.classList.add('btn-outline-secondary');
      likeBtn.querySelector('i').className = 'bi bi-heart me-1';
    } else {
      count += 1;
      localStorage.setItem(`hague_is_liked_${id}`, 'true');
      likeBtn.classList.add('btn-danger');
      likeBtn.classList.remove('btn-outline-secondary');
      likeBtn.querySelector('i').className = 'bi bi-heart-fill me-1 text-white';
    }

    if (likeCount) likeCount.textContent = count;
    localStorage.setItem(`hague_like_${id}`, String(count));
  });

  bookmarkBtn?.addEventListener('click', () => {
    const id = bookmarkBtn.dataset.currentId;
    if (!id) return;

    const isBookmarked = localStorage.getItem(`hague_bookmarked_${id}`) === 'true';
    if (isBookmarked) {
      localStorage.setItem(`hague_bookmarked_${id}`, 'false');
      bookmarkBtn.classList.remove('btn-primary');
      bookmarkBtn.classList.add('btn-outline-secondary');
      bookmarkBtn.innerHTML = '<i class="bi bi-bookmark me-1"></i> Bookmark';
      showToast("Maqola xatcho'plardan olib tashlandi.");
    } else {
      localStorage.setItem(`hague_bookmarked_${id}`, 'true');
      bookmarkBtn.classList.add('btn-primary');
      bookmarkBtn.classList.remove('btn-outline-secondary');
      bookmarkBtn.innerHTML = '<i class="bi bi-bookmark-fill me-1 text-white"></i> Bookmarked';
      showToast("Maqola muvaffaqiyatli saqlab qo'yildi!");
    }
  });

  shareBtn?.addEventListener('click', () => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(window.location.href);
      showToast("Maqola havolasi nusxalandi!");
    } else {
      showToast("Maqola havolasi tayyor.");
    }
  });

  // ========================================================
  // 9. LIVE SEARCH FILTER (FastAPI & PostgreSQL)
  // ========================================================
  let searchDebounceTimer = null;
  liveSearchInput?.addEventListener('input', (e) => {
    const query = e.target.value.trim();
    if (!searchResults) return;

    clearTimeout(searchDebounceTimer);

    if (!query) {
      searchResults.innerHTML = '<span class="text-secondary small">Start typing to search through all published stories...</span>';
      return;
    }

    searchDebounceTimer = setTimeout(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/posts?search=${encodeURIComponent(query)}`);
        if (res.ok) {
          const apiMatches = await res.json();
          if (apiMatches.length === 0) {
            searchResults.innerHTML = `<span class="text-danger small">No articles found matching "${query}". Try "AI", "business", or "prose".</span>`;
            return;
          }

          searchResults.innerHTML = apiMatches.map(m => `
            <div class="search-item p-2 rounded border bg-light d-flex align-items-center justify-content-between" style="cursor: pointer;" data-api-id="${m.id}">
              <div>
                <span class="badge bg-primary-subtle text-primary text-uppercase me-1" style="font-size: 0.65rem;">${m.category?.name || 'EDITORIAL'}</span>
                <strong class="font-serif small text-dark d-block mt-1">${m.title}</strong>
                <small class="text-secondary">${m.owner?.username ? 'By ' + m.owner.username : ''} • ${m.comments_count || 0} izoh</small>
              </div>
              <i class="bi bi-chevron-right text-secondary"></i>
            </div>
          `).join('');

          searchResults.querySelectorAll('.search-item').forEach(item => {
            item.addEventListener('click', () => {
              const apiId = parseInt(item.dataset.apiId, 10);
              const found = apiMatches.find(p => p.id === apiId);
              
              const searchModalEl = document.getElementById('searchModal');
              if (searchModalEl && window.bootstrap) {
                bootstrap.Modal.getInstance(searchModalEl)?.hide();
              }

              if (found) {
                activePostId = found.id;
                if (modalArticleTitle) modalArticleTitle.textContent = found.title;
                if (modalArticleCategory) modalArticleCategory.textContent = found.category?.name || 'EDITORIAL';
                if (modalArticleDate) modalArticleDate.textContent = new Date(found.created_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
                if (modalArticleAuthor) modalArticleAuthor.textContent = found.owner?.username || 'Editorial Team';
                if (modalArticleContent) {
                  modalArticleContent.innerHTML = `<p class="lead text-dark fw-normal">${found.content}</p>`;
                }
                loadCommentsForPost(found.id);
                if (articleModal) articleModal.show();
              }
            });
          });
        }
      } catch {
        // Fallback to local cards
        searchResults.innerHTML = `<span class="text-secondary small">Local search: "${query}"</span>`;
      }
    }, 250);
  });

  // ========================================================
  // 10. NEWSLETTER FORMS
  // ========================================================
  subscribeForm?.addEventListener('submit', (e) => {
    e.preventDefault();
    const email = document.getElementById('subscriberEmail')?.value.trim();
    if (email) {
      localStorage.setItem('hague_subscriber', email);
      const subscribeModalEl = document.getElementById('subscribeModal');
      if (subscribeModalEl && window.bootstrap) {
        bootstrap.Modal.getInstance(subscribeModalEl)?.hide();
      }
      showToast("Thank you! You are now subscribed to HAGUE Digital.");
    }
  });

  newsletterCalloutForm?.addEventListener('submit', (e) => {
    e.preventDefault();
    const email = document.getElementById('newsletterEmailInput')?.value.trim();
    if (email) {
      localStorage.setItem('hague_subscriber', email);
      document.getElementById('newsletterEmailInput').value = '';
      showToast("Thank you! Welcome to HAGUE Morning Digest.");
    }
  });

  // ========================================================
  // 11. TOAST NOTIFICATION UTILITY
  // ========================================================
  function showToast(message) {
    const existing = document.querySelector('.hague-toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'hague-toast alert alert-dark shadow-lg d-flex align-items-center gap-2 position-fixed bottom-0 end-0 m-4 py-3 px-4 rounded-2 border-0';
    toast.style.zIndex = '9999';
    toast.style.backgroundColor = '#111111';
    toast.style.color = '#FFFFFF';
    toast.innerHTML = `
      <i class="bi bi-check-circle-fill text-success fs-5"></i>
      <span class="small fw-semibold">${message}</span>
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
      toast.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(15px)';
      setTimeout(() => toast.remove(), 450);
    }, 3200);
  }

  // Run initial backend connection
  checkBackendHealth();
  console.log('HAGUE Editorial Blog connected to FastAPI & PostgreSQL.');
});
