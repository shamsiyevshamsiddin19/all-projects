/**
 * ========================================================
 * HAGUE — EDITORIAL MAGAZINE JAVASCRIPT
 * Bootstrap 5.3 Interactive Features & Modals
 * ========================================================
 */

document.addEventListener('DOMContentLoaded', () => {
  'use strict';

  // 1. DOM Elements
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

  // Search Elements
  const liveSearchInput = document.getElementById('liveSearchInput');
  const searchResults = document.getElementById('searchResults');

  // Forms
  const subscribeForm = document.getElementById('subscribeForm');
  const newsletterCalloutForm = document.getElementById('newsletterCalloutForm');

  // Bootstrap Modal Instance
  let articleModal = null;
  if (articleModalEl && window.bootstrap) {
    articleModal = new bootstrap.Modal(articleModalEl);
  }

  // ========================================================
  // 2. ARTICLE READING MODAL (Interaktiv maqolani o'qish)
  // ========================================================
  articleCards.forEach(card => {
    card.addEventListener('click', (e) => {
      // Agar ichki havola bosilgan bo'lsa sahifa sakramasligi uchun
      if (e.target.tagName.toLowerCase() === 'a') {
        e.preventDefault();
      }

      const id = card.dataset.id || 'article';
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

      // Hisoblangan o'qish vaqti
      const words = content.split(/\s+/).length;
      const readingMinutes = Math.max(2, Math.ceil(words / 40));
      if (modalReadingTime) modalReadingTime.textContent = `${readingMinutes} min read`;

      // Maqola tanasi
      if (modalArticleContent) {
        modalArticleContent.innerHTML = `
          <p class="lead text-dark fw-normal">${content}</p>
          <p>Morbi in sem quis dui placerat ornare. Pellentesque odio nisi, euismod in, pharetra a, ultricies in, diam. Sed arcu. Cras consequat. Praesent dapibus, neque id cursus faucibus, tortor neque egestas augue, eu vulputate magna eros eu erat. Aliquam erat volutpat.</p>
          <blockquote>"Investigative journalism is not just about chronicling events; it is about providing the civic foundation upon which informed citizens act."</blockquote>
          <p>Nam dui mi, tincidunt quis, accumsan porttitor, facilisis luctus, metus. Phasellus ultrices nulla quis nibh. Quisque a lectus. Donec consectetuer ligula vulputate sem tristique cursus. Nam nulla quam, gravida non, commodo a, sodales sit amet, nisi.</p>
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

      // Bookmark holatini tekshirish
      if (bookmarkBtn) {
        bookmarkBtn.dataset.currentId = id;
        const isBookmarked = localStorage.getItem(`hague_bookmarked_${id}`) === 'true';
        bookmarkBtn.classList.toggle('btn-primary', isBookmarked);
        bookmarkBtn.classList.toggle('btn-outline-secondary', !isBookmarked);
        bookmarkBtn.innerHTML = isBookmarked 
          ? '<i class="bi bi-bookmark-fill me-1 text-white"></i> Bookmarked' 
          : '<i class="bi bi-bookmark me-1"></i> Bookmark';
      }

      if (articleModal) {
        articleModal.show();
      }
    });
  });

  // Like tugmasi
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

  // Bookmark tugmasi
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

  // Share tugmasi
  shareBtn?.addEventListener('click', () => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(window.location.href);
      showToast("Maqola havolasi nusxalandi!");
    } else {
      showToast("Maqola havolasi tayyor.");
    }
  });

  // ========================================================
  // 3. LIVE SEARCH FILTER (Jonli qidiruv modali)
  // ========================================================
  const allArticlesData = [];
  articleCards.forEach(card => {
    allArticlesData.push({
      id: card.dataset.id,
      title: card.dataset.title || card.querySelector('.article-title')?.innerText || '',
      category: card.dataset.category || '',
      date: card.dataset.date || '',
      cardElement: card
    });
  });

  liveSearchInput?.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase().trim();
    if (!searchResults) return;

    if (!query) {
      searchResults.innerHTML = '<span class="text-secondary small">Start typing to search through all published stories...</span>';
      return;
    }

    const matches = allArticlesData.filter(item => 
      item.title.toLowerCase().includes(query) || 
      item.category.toLowerCase().includes(query)
    );

    if (matches.length === 0) {
      searchResults.innerHTML = `<span class="text-danger small">No articles found matching "${query}". Try "travel", "business", or "truth".</span>`;
      return;
    }

    searchResults.innerHTML = matches.map(m => `
      <div class="search-item p-2 rounded border bg-light d-flex align-items-center justify-content-between" style="cursor: pointer;" data-target-id="${m.id}">
        <div>
          <span class="badge bg-primary-subtle text-primary text-uppercase me-1" style="font-size: 0.65rem;">${m.category}</span>
          <strong class="font-serif small text-dark d-block mt-1">${m.title}</strong>
        </div>
        <i class="bi bi-chevron-right text-secondary"></i>
      </div>
    `).join('');

    searchResults.querySelectorAll('.search-item').forEach(item => {
      item.addEventListener('click', () => {
        const targetId = item.dataset.targetId;
        const matchingCard = document.querySelector(`.article-card[data-id="${targetId}"]`);
        
        // Modalni yopish
        const searchModalEl = document.getElementById('searchModal');
        if (searchModalEl && window.bootstrap) {
          bootstrap.Modal.getInstance(searchModalEl)?.hide();
        }

        if (matchingCard) {
          matchingCard.click();
        }
      });
    });
  });

  // ========================================================
  // 4. NEWSLETTER FORMLARI
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
  // 5. YORDAMCHI TOAST BILDIRISHNOMA
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
      <i class="bi bi-check-circle-fill text-primary fs-5"></i>
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

  console.log('HAGUE Editorial Blog (Bootstrap 5.3) successfully loaded.');
});
