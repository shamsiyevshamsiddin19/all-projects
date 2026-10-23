/**
 * Foldex Veb-Admin Panel Asosiy Mantiqi (app.js)
 * Standart: Sof JavaScript (Vanilla JS), to'liq reaktiv SPA,
 * Drag-and-Drop, XMLHttpRequest yuklash indikatori, modallar va navigatsiya.
 */

document.addEventListener("DOMContentLoaded", async () => {
    // 1. Tizimga kirish huquqini tekshirish (auth.js orqali)
    const isAuthed = await window.Auth.checkAuth();
    if (!isAuthed) return;

    // 2. Ilova holati (State)
    const state = {
        currentFolderId: null,
        currentFolderName: "Bosh sahifa",
        activeFilter: "all",
        searchQuery: "",
        viewMode: localStorage.getItem("foldex_view_mode") || "grid",
        subfolders: [],
        files: [],
        treeData: [],
        allFlatFolders: [],
        // Ko'p tanlash: tanlangan fayl id lari va Shift uchun oxirgi bosilgan indeks
        selected: new Set(),
        lastClickedIndex: null,
        // Saralash (brauzerda eslab qolinadi)
        sortBy: localStorage.getItem("foldex_sort_by") || "name",
        sortDir: localStorage.getItem("foldex_sort_dir") || "asc"
    };

    // 3. DOM Elementlari
    const elements = {
        sidebar: document.getElementById("sidebar"),
        openSidebarBtn: document.getElementById("openSidebarBtn"),
        closeSidebarBtn: document.getElementById("closeSidebarBtn"),
        logoutBtn: document.getElementById("logoutBtn"),
        searchInput: document.getElementById("searchInput"),
        clearSearchBtn: document.getElementById("clearSearchBtn"),
        viewGridBtn: document.getElementById("viewGridBtn"),
        viewListBtn: document.getElementById("viewListBtn"),
        breadcrumbsNav: document.getElementById("breadcrumbsNav"),
        foldersSection: document.getElementById("foldersSection"),
        foldersGrid: document.getElementById("foldersGrid"),
        subfoldersBadge: document.getElementById("subfoldersBadge"),
        filesSection: document.getElementById("filesSection"),
        filesContainer: document.getElementById("filesContainer"),
        filesBadge: document.getElementById("filesBadge"),
        emptyState: document.getElementById("emptyState"),
        folderTreeContainer: document.getElementById("folderTreeContainer"),
        treeRefreshBtn: document.getElementById("treeRefreshBtn"),
        dropZoneArea: document.getElementById("dropZoneArea"),
        dropOverlay: document.getElementById("dropOverlay"),
        storagePercentText: document.getElementById("storagePercentText"),
        storageProgressBar: document.getElementById("storageProgressBar"),
        storageUsedText: document.getElementById("storageUsedText"),
        storageTotalText: document.getElementById("storageTotalText"),
        countAll: document.getElementById("countAll"),
        countDocs: document.getElementById("countDocs"),
        countPhotos: document.getElementById("countPhotos"),
        countVideos: document.getElementById("countVideos"),
        countAudio: document.getElementById("countAudio"),
        countArchives: document.getElementById("countArchives"),
        toastContainer: document.getElementById("toastContainer")
    };

    // 4. Toast Xabarnoma chiqarish funksiyasi
    function showToast(message, type = "success") {
        const toast = document.createElement("div");
        toast.className = `toast ${type}`;

        const iconMap = {
            success: "fa-circle-check text-emerald",
            error: "fa-circle-xmark text-rose",
            info: "fa-circle-info text-sky"
        };

        toast.innerHTML = `
            <i class="fa-solid ${iconMap[type] || iconMap.info}"></i>
            <span>${message}</span>
        `;

        elements.toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = "0";
            toast.style.transform = "translateX(50px)";
            toast.style.transition = "all 0.3s ease";
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    }

    // 5. Fayl formatlari uchun mos ikonka va ranglarni aniqlash
    function getFileIcon(type, filename) {
        const ext = filename.split('.').pop().toLowerCase();
        switch (type) {
            case "photo":
                return '<i class="fa-solid fa-file-image text-emerald"></i>';
            case "video":
                return '<i class="fa-solid fa-file-video text-rose"></i>';
            case "audio":
                return '<i class="fa-solid fa-file-audio text-amber"></i>';
            case "archive":
                return '<i class="fa-solid fa-file-zipper text-purple"></i>';
            case "code":
                return '<i class="fa-solid fa-file-code text-sky"></i>';
            case "document":
                if (ext === "pdf") return '<i class="fa-solid fa-file-pdf text-rose"></i>';
                if (["doc", "docx"].includes(ext)) return '<i class="fa-solid fa-file-word text-sky"></i>';
                if (["xls", "xlsx"].includes(ext)) return '<i class="fa-solid fa-file-excel text-emerald"></i>';
                if (["ppt", "pptx"].includes(ext)) return '<i class="fa-solid fa-file-powerpoint text-amber"></i>';
                return '<i class="fa-solid fa-file-lines text-indigo"></i>';
            default:
                return '<i class="fa-solid fa-file text-muted"></i>';
        }
    }

    // 6. Xotira va Statistika ma'lumotlarini yuklash
    async function loadDashboardStats() {
        try {
            const resp = await fetch("/api/stats/dashboard");
            if (!resp.ok) return;
            const data = await resp.json();

            elements.storagePercentText.innerText = `${data.storage_used_percent}%`;
            elements.storageProgressBar.style.width = `${data.storage_used_percent}%`;
            elements.storageUsedText.innerText = data.total_size_formatted;
            elements.storageTotalText.innerText = data.storage_limit_formatted;

            elements.countAll.innerText = data.total_files;
            elements.countDocs.innerText = data.categories.document || 0;
            elements.countPhotos.innerText = data.categories.photo || 0;
            elements.countVideos.innerText = data.categories.video || 0;
            elements.countAudio.innerText = data.categories.audio || 0;
            elements.countArchives.innerText = data.categories.archive || 0;
        } catch (e) {
            console.error("Dashboard stats error:", e);
        }
    }

    // 7. Papkalar daraxtini (Sidebar Folder Tree) yuklash va chizish
    async function loadFolderTree() {
        try {
            const resp = await fetch("/api/folders/tree");
            if (!resp.ok) return;
            const tree = await resp.json();
            state.treeData = tree;

            function buildTreeHtml(nodes) {
                if (!nodes || nodes.length === 0) return "";
                let html = '<div class="tree-children">';
                for (const node of nodes) {
                    const isActive = state.currentFolderId === node.id ? "active" : "";
                    html += `
                        <div class="tree-node">
                            <div class="tree-node-content ${isActive}" data-id="${node.id}">
                                <span>${node.icon || "📁"}</span>
                                <span>${node.name}</span>
                            </div>
                            ${buildTreeHtml(node.children)}
                        </div>
                    `;
                }
                html += '</div>';
                return html;
            }

            let rootHtml = `
                <div class="tree-node">
                    <div class="tree-node-content ${state.currentFolderId === null ? "active" : ""}" data-id="root">
                        <span>🏠</span>
                        <span>Bosh sahifa</span>
                    </div>
                </div>
            `;

            for (const node of tree) {
                const isActive = state.currentFolderId === node.id ? "active" : "";
                rootHtml += `
                    <div class="tree-node">
                        <div class="tree-node-content ${isActive}" data-id="${node.id}">
                            <span>${node.icon || "📁"}</span>
                            <span>${node.name}</span>
                        </div>
                        ${buildTreeHtml(node.children)}
                    </div>
                `;
            }

            elements.folderTreeContainer.innerHTML = rootHtml;

            // Daraxt elementlarini bosish voqeasi
            elements.folderTreeContainer.querySelectorAll(".tree-node-content").forEach(el => {
                el.addEventListener("click", () => {
                    const idAttr = el.getAttribute("data-id");
                    const targetId = idAttr === "root" ? null : parseInt(idAttr);
                    navigateToFolder(targetId);
                    if (window.innerWidth <= 768) {
                        elements.sidebar.classList.remove("open");
                    }
                });
            });

        } catch (e) {
            console.error("Folder tree load error:", e);
        }
    }

    // 8. Joriy papkani yuklash (Load Folder Contents)
    async function navigateToFolder(folderId) {
        state.currentFolderId = folderId;

        // Qidiruvni tozalash
        if (state.searchQuery) {
            elements.searchInput.value = "";
            state.searchQuery = "";
            elements.clearSearchBtn.style.display = "none";
        }

        try {
            let breadcrumbs = [];
            let subfolders = [];

            if (folderId === null) {
                // Ildiz papka
                const [crumbsResp, subResp] = await Promise.all([
                    fetch("/api/folders/breadcrumbs/root"),
                    fetch("/api/folders/")
                ]);
                breadcrumbs = await crumbsResp.json();
                subfolders = await subResp.json();
                state.currentFolderName = "Bosh sahifa";
            } else {
                // Muayyan papka
                const folderResp = await fetch(`/api/folders/${folderId}`);
                if (!folderResp.ok) {
                    showToast("Papka topilmadi!", "error");
                    return navigateToFolder(null);
                }
                const detail = await folderResp.json();
                breadcrumbs = detail.breadcrumbs;
                subfolders = detail.subfolders;
                state.currentFolderName = detail.folder.name;
            }

            state.subfolders = subfolders;
            renderBreadcrumbs(breadcrumbs);
            renderFolders(subfolders);

            // Shu papkadagi fayllarni yuklash
            await loadFiles(folderId);

            // Daraxtni ham sinxron yangilash
            loadFolderTree();

        } catch (e) {
            showToast("Ma'lumotlarni yuklashda xatolik!", "error");
        }
    }

    // 9. Breadcrumbs zanjirini chizish
    function renderBreadcrumbs(crumbs) {
        elements.breadcrumbsNav.innerHTML = "";
        crumbs.forEach((crumb, index) => {
            const item = document.createElement("div");
            item.className = `breadcrumb-item ${index === crumbs.length - 1 ? "active" : ""}`;
            item.innerHTML = `<span>${crumb.icon || "📁"}</span> <span>${crumb.name}</span>`;

            item.addEventListener("click", () => {
                navigateToFolder(crumb.id);
            });

            elements.breadcrumbsNav.appendChild(item);

            if (index < crumbs.length - 1) {
                const sep = document.createElement("span");
                sep.className = "breadcrumb-separator";
                sep.innerHTML = '<i class="fa-solid fa-chevron-right"></i>';
                elements.breadcrumbsNav.appendChild(sep);
            }
        });
    }

    // 10. Papkalar kartalarini chizish
    function renderFolders(folders) {
        elements.subfoldersBadge.innerText = `${folders.length} ta`;
        elements.foldersGrid.innerHTML = "";

        if (folders.length === 0) {
            elements.foldersSection.style.display = "none";
            return;
        }

        elements.foldersSection.style.display = "block";

        folders.forEach(folder => {
            const card = document.createElement("div");
            card.className = "folder-card";

            card.innerHTML = `
                <div class="folder-card-icon">${folder.icon || "📁"}</div>
                <div class="folder-card-info">
                    <div class="folder-card-name" title="${folder.name}">${folder.name}</div>
                    <div class="folder-card-meta">${folder.files_count} ta fayl</div>
                </div>
                <div class="card-actions-dropdown">
                    <button class="dropdown-trigger" title="Amallar"><i class="fa-solid fa-ellipsis-vertical"></i></button>
                    <div class="dropdown-menu">
                        <button class="dropdown-item rename-folder-btn" data-id="${folder.id}" data-name="${folder.name}">
                            <i class="fa-solid fa-pen"></i> Qayta nomlash
                        </button>
                        <button class="dropdown-item move-folder-btn" data-id="${folder.id}" data-name="${folder.name}">
                            <i class="fa-solid fa-arrow-right-arrow-left"></i> Ko'chirish
                        </button>
                        <button class="dropdown-item danger delete-folder-btn" data-id="${folder.id}" data-name="${folder.name}">
                            <i class="fa-solid fa-trash"></i> O'chirish
                        </button>
                    </div>
                </div>
            `;

            // Papkaga kirish
            card.addEventListener("click", (e) => {
                if (e.target.closest(".card-actions-dropdown")) return;
                navigateToFolder(folder.id);
            });

            // Dropdown amallar menyusi
            const trigger = card.querySelector(".dropdown-trigger");
            const menu = card.querySelector(".dropdown-menu");

            trigger.addEventListener("click", (e) => {
                e.stopPropagation();
                const willShow = !menu.classList.contains("show");
                document.querySelectorAll(".dropdown-menu.show").forEach(m => {
                    m.classList.remove("show");
                    const p = m.closest(".folder-card, .file-card");
                    if (p) p.classList.remove("menu-open");
                });
                if (willShow) {
                    menu.classList.add("show");
                    card.classList.add("menu-open");
                }
            });

            // Rename
            card.querySelector(".rename-folder-btn").addEventListener("click", (e) => {
                e.stopPropagation();
                menu.classList.remove("show");
                openRenameModal(folder.id, "folder", folder.name);
            });

            // Move
            card.querySelector(".move-folder-btn").addEventListener("click", (e) => {
                e.stopPropagation();
                menu.classList.remove("show");
                openMoveModal(folder.id, "folder", folder.name);
            });

            // Delete
            card.querySelector(".delete-folder-btn").addEventListener("click", (e) => {
                e.stopPropagation();
                menu.classList.remove("show");
                openDeleteModal(folder.id, "folder", folder.name);
            });

            // O'ng tugma menyusi
            card.addEventListener("contextmenu", (e) => {
                e.preventDefault();
                openContextMenu(e.clientX, e.clientY, "folder", folder);
            });

            // Fayllarni shu papkaga sudrab tashlash
            card.addEventListener("dragover", (e) => {
                if (!e.dataTransfer.types.includes("application/x-foldex-files")) return;
                e.preventDefault();
                e.dataTransfer.dropEffect = "move";
                card.classList.add("drop-target");
            });
            card.addEventListener("dragleave", () => card.classList.remove("drop-target"));
            card.addEventListener("drop", async (e) => {
                card.classList.remove("drop-target");
                const raw = e.dataTransfer.getData("application/x-foldex-files");
                if (!raw) return;
                e.preventDefault();
                let ids = [];
                try { ids = JSON.parse(raw); } catch (_) { return; }
                await moveFiles(ids, folder.id, folder.name);
            });

            elements.foldersGrid.appendChild(card);
        });
    }

    // 11. Fayllarni yuklash (Filtirlar va qidiruv bilan)
    async function loadFiles(folderId) {
        let url = `/api/files/?`;
        if (folderId !== null) {
            url += `folder_id=${folderId}&`;
        }
        if (state.activeFilter && state.activeFilter !== "all") {
            url += `file_type=${state.activeFilter}&`;
        }
        if (state.searchQuery) {
            url += `search=${encodeURIComponent(state.searchQuery)}&`;
        }

        try {
            const resp = await fetch(url);
            if (!resp.ok) return;
            const data = await resp.json();
            state.files = sortFiles(data.items);
            // Boshqa papkaga o'tilganda eski tanlov qolib ketmasin
            state.selected.clear();
            state.lastClickedIndex = null;
            renderFiles(state.files);
            updateSelectionBar();
            loadDashboardStats();
        } catch (e) {
            console.error("Files load error:", e);
        }
    }

    // 12. Fayllar kartalari/ro'yxatini chizish
    function renderFiles(files) {
        elements.filesBadge.innerText = `${files.length} ta`;
        elements.filesContainer.innerHTML = "";

        if (files.length === 0 && state.subfolders.length === 0) {
            elements.emptyState.style.display = "block";
            elements.filesSection.style.display = "block";
            return;
        }

        elements.emptyState.style.display = "none";
        elements.filesSection.style.display = "block";

        files.forEach((file, index) => {
            const card = document.createElement("div");
            card.className = "file-card" + (state.selected.has(file.id) ? " selected" : "");
            card.dataset.fileId = file.id;
            card.dataset.index = index;
            card.draggable = true;

            const iconHtml = getFileIcon(file.file_type, file.name);
            const tgBadge = file.is_synced_with_telegram
                ? '<span class="tg-badge" title="Telegramda tezkor ulashishga tayyor"><i class="fa-brands fa-telegram"></i> Telegram</span>'
                : '';

            card.innerHTML = `
                <label class="file-select-box" title="Tanlash">
                    <input type="checkbox" class="file-select-cb" ${state.selected.has(file.id) ? "checked" : ""}>
                </label>
                <div class="file-card-preview">
                    ${iconHtml}
                </div>
                <div class="file-card-details">
                    <div class="file-card-name" title="${file.name}">${file.name}</div>
                    <div class="file-card-footer">
                        <span>${file.formatted_size}</span>
                        ${tgBadge}
                    </div>
                </div>
                <div class="card-actions-dropdown">
                    <button class="dropdown-trigger" title="Amallar"><i class="fa-solid fa-ellipsis-vertical"></i></button>
                    <div class="dropdown-menu">
                        <button class="dropdown-item preview-file-btn">
                            <i class="fa-solid fa-eye"></i> Ko'rish
                        </button>
                        <a href="/api/files/${file.id}/download" class="dropdown-item" download>
                            <i class="fa-solid fa-download"></i> Yuklab olish
                        </a>
                        <button class="dropdown-item copylink-file-btn">
                            <i class="fa-solid fa-link"></i> Havolani nusxalash
                        </button>
                        <button class="dropdown-item telegram-file-btn">
                            <i class="fa-brands fa-telegram"></i> Telegramga yuborish
                        </button>
                        <button class="dropdown-item rename-file-btn" data-id="${file.id}" data-name="${file.name}">
                            <i class="fa-solid fa-pen"></i> Qayta nomlash
                        </button>
                        <button class="dropdown-item move-file-btn" data-id="${file.id}" data-name="${file.name}">
                            <i class="fa-solid fa-arrow-right-arrow-left"></i> Ko'chirish
                        </button>
                        <button class="dropdown-item danger delete-file-btn" data-id="${file.id}" data-name="${file.name}">
                            <i class="fa-solid fa-trash"></i> O'chirish
                        </button>
                    </div>
                </div>
            `;

            // Dropdown trigger
            const trigger = card.querySelector(".dropdown-trigger");
            const menu = card.querySelector(".dropdown-menu");

            trigger.addEventListener("click", (e) => {
                e.stopPropagation();
                const willShow = !menu.classList.contains("show");
                document.querySelectorAll(".dropdown-menu.show").forEach(m => {
                    m.classList.remove("show");
                    const p = m.closest(".folder-card, .file-card");
                    if (p) p.classList.remove("menu-open");
                });
                if (willShow) {
                    menu.classList.add("show");
                    card.classList.add("menu-open");
                }
            });

            // Rename
            card.querySelector(".rename-file-btn").addEventListener("click", (e) => {
                e.stopPropagation();
                menu.classList.remove("show");
                openRenameModal(file.id, "file", file.name);
            });

            // Move
            card.querySelector(".move-file-btn").addEventListener("click", (e) => {
                e.stopPropagation();
                menu.classList.remove("show");
                openMoveModal(file.id, "file", file.name);
            });

            // Delete
            card.querySelector(".delete-file-btn").addEventListener("click", (e) => {
                e.stopPropagation();
                menu.classList.remove("show");
                openDeleteModal(file.id, "file", file.name);
            });

            // Ko'rish / havola / Telegram
            card.querySelector(".preview-file-btn").addEventListener("click", (e) => {
                e.stopPropagation();
                menu.classList.remove("show");
                openPreview(file);
            });
            card.querySelector(".copylink-file-btn").addEventListener("click", (e) => {
                e.stopPropagation();
                menu.classList.remove("show");
                copyFileLink(file);
            });
            card.querySelector(".telegram-file-btn").addEventListener("click", (e) => {
                e.stopPropagation();
                menu.classList.remove("show");
                sendToTelegram([file.id]);
            });

            // Tanlash: katakcha, oddiy bosish, Ctrl/Cmd va Shift bilan bosish
            const cb = card.querySelector(".file-select-cb");
            cb.addEventListener("click", (e) => {
                e.stopPropagation();
                toggleSelect(file.id, index, { force: cb.checked });
            });

            card.addEventListener("click", (e) => {
                if (e.target.closest(".card-actions-dropdown") || e.target.closest(".file-select-box")) return;
                if (e.shiftKey) {
                    selectRange(index);
                } else if (e.ctrlKey || e.metaKey) {
                    toggleSelect(file.id, index);
                } else {
                    // Oddiy bosish: faqat shu faylni tanlaydi
                    state.selected.clear();
                    toggleSelect(file.id, index, { force: true });
                }
            });

            // Ikki marta bosish — ko'rish oynasi
            card.addEventListener("dblclick", (e) => {
                if (e.target.closest(".card-actions-dropdown")) return;
                openPreview(file);
            });

            // O'ng tugma menyusi
            card.addEventListener("contextmenu", (e) => {
                e.preventDefault();
                if (!state.selected.has(file.id)) {
                    state.selected.clear();
                    toggleSelect(file.id, index, { force: true });
                }
                openContextMenu(e.clientX, e.clientY, "file", file);
            });

            // Sudrab papkaga tashlash
            card.addEventListener("dragstart", (e) => {
                if (!state.selected.has(file.id)) {
                    state.selected.clear();
                    toggleSelect(file.id, index, { force: true });
                }
                e.dataTransfer.setData("application/x-foldex-files",
                    JSON.stringify([...state.selected]));
                e.dataTransfer.effectAllowed = "move";
                card.classList.add("dragging");
            });
            card.addEventListener("dragend", () => card.classList.remove("dragging"));

            elements.filesContainer.appendChild(card);
        });
    }

    // 13. Qidiruv boshqaruvi (Debounce bilan)
    let searchTimeout = null;
    elements.searchInput.addEventListener("input", (e) => {
        const query = e.target.value.trim();
        elements.clearSearchBtn.style.display = query ? "block" : "none";

        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            state.searchQuery = query;
            loadFiles(state.currentFolderId);
        }, 300);
    });

    elements.clearSearchBtn.addEventListener("click", () => {
        elements.searchInput.value = "";
        elements.clearSearchBtn.style.display = "none";
        state.searchQuery = "";
        loadFiles(state.currentFolderId);
    });

    // 14. Toifalar filtri (Sidebar Quick Navigation)
    document.querySelectorAll(".nav-item[data-type]").forEach(item => {
        item.addEventListener("click", () => {
            document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
            item.classList.add("active");
            state.activeFilter = item.getAttribute("data-type");
            loadFiles(state.currentFolderId);

            if (window.innerWidth <= 768) {
                elements.sidebar.classList.remove("open");
            }
        });
    });

    // 15. Ko'rinish rejimini almashtirish (Grid / List)
    function setViewMode(mode) {
        state.viewMode = mode;
        localStorage.setItem("foldex_view_mode", mode);
        if (mode === "grid") {
            elements.filesContainer.classList.remove("list-mode");
            elements.filesContainer.classList.add("grid-mode");
            elements.viewGridBtn.classList.add("active");
            elements.viewListBtn.classList.remove("active");
        } else {
            elements.filesContainer.classList.remove("grid-mode");
            elements.filesContainer.classList.add("list-mode");
            elements.viewListBtn.classList.add("active");
            elements.viewGridBtn.classList.remove("active");
        }
    }

    elements.viewGridBtn.addEventListener("click", () => setViewMode("grid"));
    elements.viewListBtn.addEventListener("click", () => setViewMode("list"));
    setViewMode(state.viewMode);

    // 16. Boshqaruv tugmalari va Sidebar ochish/yopish
    const sidebarBackdrop = document.getElementById("sidebarBackdrop");
    elements.openSidebarBtn.addEventListener("click", () => {
        elements.sidebar.classList.add("open");
        if (sidebarBackdrop) sidebarBackdrop.classList.add("active");
    });
    const closeMobileSidebar = () => {
        elements.sidebar.classList.remove("open");
        if (sidebarBackdrop) sidebarBackdrop.classList.remove("active");
    };
    elements.closeSidebarBtn.addEventListener("click", closeMobileSidebar);
    if (sidebarBackdrop) sidebarBackdrop.addEventListener("click", closeMobileSidebar);

    elements.logoutBtn.addEventListener("click", () => window.Auth.logout());
    elements.treeRefreshBtn.addEventListener("click", () => loadFolderTree());

    // Sahifaning boshqa joyiga bosilganda ochiq dropdown menyularni yopish
    document.addEventListener("click", () => {
        document.querySelectorAll(".dropdown-menu.show").forEach(m => m.classList.remove("show"));
        document.querySelectorAll(".menu-open").forEach(c => c.classList.remove("menu-open"));
    });

    // =========================================================================
    // 17. MODALLAR BOSHQARUVI
    // =========================================================================
    function openModal(modalId) {
        document.getElementById(modalId).classList.add("show");
    }

    function closeModal(modalId) {
        document.getElementById(modalId).classList.remove("show");
    }

    document.querySelectorAll(".close-modal-btn, .modal-backdrop").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".modal.show").forEach(m => m.classList.remove("show"));
        });
    });

    // A) Yangi papka ochish
    const newFolderModal = document.getElementById("newFolderModal");
    const newFolderForm = document.getElementById("newFolderForm");
    const openNewFolderModalBtn = document.getElementById("openNewFolderModalBtn");

    openNewFolderModalBtn.addEventListener("click", () => {
        document.getElementById("folderNameInput").value = "";
        document.getElementById("folderDescInput").value = "";
        openModal("newFolderModal");
    });

    // Emoji tanlash
    document.querySelectorAll(".emoji-item").forEach(item => {
        item.addEventListener("click", () => {
            document.getElementById("folderIconInput").value = item.innerText;
        });
    });

    newFolderForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const name = document.getElementById("folderNameInput").value.trim();
        const icon = document.getElementById("folderIconInput").value.trim() || "📁";
        const desc = document.getElementById("folderDescInput").value.trim();

        if (!name) return;

        try {
            const resp = await fetch("/api/folders/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    name: name,
                    parent_id: state.currentFolderId,
                    icon: icon,
                    description: desc
                })
            });

            if (resp.ok) {
                closeModal("newFolderModal");
                showToast(`«${name}» papkasi muvaffaqiyatli yaratildi!`);
                navigateToFolder(state.currentFolderId);
            } else {
                const err = await resp.json();
                showToast(err.detail || "Papka yaratishda xatolik!", "error");
            }
        } catch (err) {
            showToast("Tarmoq xatosi!", "error");
        }
    });

    // B) Fayllarni yuklash (Drag & Drop va Multi-upload)
    const uploadModal = document.getElementById("uploadModal");
    const uploadForm = document.getElementById("uploadForm");
    const fileInput = document.getElementById("fileInput");
    const browseFilesBtn = document.getElementById("browseFilesBtn");
    const openUploadModalBtn = document.getElementById("openUploadModalBtn");
    const emptyUploadBtn = document.getElementById("emptyUploadBtn");
    const selectedFilesList = document.getElementById("selectedFilesList");
    const filesPreviewScroll = document.getElementById("filesPreviewScroll");
    const selectedCountBadge = document.getElementById("selectedCountBadge");
    const uploadProgressContainer = document.getElementById("uploadProgressContainer");
    const uploadProgressBar = document.getElementById("uploadProgressBar");
    const uploadStatusText = document.getElementById("uploadStatusText");
    const uploadPercentText = document.getElementById("uploadPercentText");

    let queuedFiles = [];

    function triggerUploadModal() {
        queuedFiles = [];
        fileInput.value = "";
        selectedFilesList.style.display = "none";
        uploadProgressContainer.style.display = "none";
        uploadProgressBar.style.width = "0%";
        openModal("uploadModal");
    }

    openUploadModalBtn.addEventListener("click", triggerUploadModal);
    emptyUploadBtn.addEventListener("click", triggerUploadModal);
    browseFilesBtn.addEventListener("click", () => fileInput.click());

    fileInput.addEventListener("change", (e) => {
        handleFilesSelected(Array.from(e.target.files));
    });

    function handleFilesSelected(files) {
        if (!files || files.length === 0) return;
        queuedFiles = files;
        selectedCountBadge.innerText = `${files.length} ta`;
        filesPreviewScroll.innerHTML = "";

        files.forEach(file => {
            const sizeStr = (file.size / 1024).toFixed(1) + " KB";
            const item = document.createElement("div");
            item.className = "preview-file-item";
            item.innerHTML = `
                <span><i class="fa-solid fa-file"></i> ${file.name}</span>
                <span class="text-faint">${sizeStr}</span>
            `;
            filesPreviewScroll.appendChild(item);
        });

        selectedFilesList.style.display = "block";
    }

    // Modal ichida Drag & Drop
    const modalDropzone = document.getElementById("modalDropzone");
    modalDropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        modalDropzone.classList.add("dragover");
    });
    modalDropzone.addEventListener("dragleave", () => {
        modalDropzone.classList.remove("dragover");
    });
    modalDropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        modalDropzone.classList.remove("dragover");
        if (e.dataTransfer.files) {
            handleFilesSelected(Array.from(e.dataTransfer.files));
        }
    });

    // Butun oynaga (DropZoneArea) fayl tashlash
    window.addEventListener("dragenter", (e) => {
        e.preventDefault();
        elements.dropOverlay.classList.add("active");
    });
    elements.dropOverlay.addEventListener("dragover", (e) => e.preventDefault());
    elements.dropOverlay.addEventListener("dragleave", (e) => {
        if (e.relatedTarget === null) {
            elements.dropOverlay.classList.remove("active");
        }
    });
    elements.dropOverlay.addEventListener("drop", (e) => {
        e.preventDefault();
        elements.dropOverlay.classList.remove("active");
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            triggerUploadModal();
            handleFilesSelected(Array.from(e.dataTransfer.files));
        }
    });

    // XMLHttpRequest orqali oqimli va foizli (0% -> 100%) yuklash
    uploadForm.addEventListener("submit", (e) => {
        e.preventDefault();
        if (queuedFiles.length === 0) {
            return showToast("Hech qanday fayl tanlanmagan!", "error");
        }

        const formData = new FormData();
        queuedFiles.forEach(file => {
            formData.append("files", file);
        });
        if (state.currentFolderId !== null) {
            formData.append("folder_id", state.currentFolderId);
        }

        uploadProgressContainer.style.display = "block";
        uploadProgressBar.style.width = "0%";
        uploadPercentText.innerText = "0%";
        uploadStatusText.innerText = `${queuedFiles.length} ta fayl yuklanmoqda...`;

        const xhr = new XMLHttpRequest();
        xhr.open("POST", "/api/files/upload", true);

        xhr.upload.onprogress = (evt) => {
            if (evt.lengthComputable) {
                const percent = Math.round((evt.loaded / evt.total) * 100);
                uploadProgressBar.style.width = `${percent}%`;
                uploadPercentText.innerText = `${percent}%`;
                if (percent === 100) {
                    uploadStatusText.innerText = "Serverda saqlanmoqda va qayta ishlanmoqda...";
                }
            }
        };

        xhr.onload = () => {
            if (xhr.status === 201) {
                closeModal("uploadModal");
                showToast(`✅ ${queuedFiles.length} ta fayl muvaffaqiyatli yuklandi!`);
                loadFiles(state.currentFolderId);
            } else {
                try {
                    const err = JSON.parse(xhr.responseText);
                    showToast(err.detail || "Yuklashda xatolik!", "error");
                } catch (_) {
                    showToast("Server xatosi!", "error");
                }
            }
        };

        xhr.onerror = () => {
            showToast("Tarmoq xatosi yuz berdi!", "error");
        };

        xhr.send(formData);
    });

    // C) Qayta nomlash (Rename)
    function openRenameModal(id, type, currentName) {
        document.getElementById("renameItemId").value = id;
        document.getElementById("renameItemType").value = type;
        document.getElementById("renameInput").value = currentName;
        openModal("renameModal");
    }

    document.getElementById("renameForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const id = document.getElementById("renameItemId").value;
        const type = document.getElementById("renameItemType").value;
        const newName = document.getElementById("renameInput").value.trim();

        if (!newName) return;

        try {
            const url = type === "folder" ? `/api/folders/${id}` : `/api/files/${id}`;
            const resp = await fetch(url, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name: newName })
            });

            if (resp.ok) {
                closeModal("renameModal");
                showToast("Nom muvaffaqiyatli o'zgartirildi!");
                if (type === "folder") {
                    navigateToFolder(state.currentFolderId);
                } else {
                    loadFiles(state.currentFolderId);
                }
            } else {
                const err = await resp.json();
                showToast(err.detail || "Xatolik yuz berdi!", "error");
            }
        } catch (_) {
            showToast("Tarmoq xatosi!", "error");
        }
    });

    // D) Boshqa papkaga ko'chirish (Move)
    async function openMoveModal(id, type, itemName) {
        document.getElementById("moveItemId").value = id;
        document.getElementById("moveItemType").value = type;
        document.getElementById("moveItemDescription").innerText = `«${itemName}» elementini qaysi papkaga ko'chirmoqchisiz?`;

        const select = document.getElementById("moveTargetFolderSelect");
        select.innerHTML = '<option value="">🏠 Bosh sahifa (Ildiz katalog)</option>';

        // Barcha mavjud papkalar ro'yxatini olish
        try {
            const resp = await fetch("/api/folders/");
            const folders = await resp.json();
            folders.forEach(f => {
                // Papka o'zini o'ziga ko'chira olmasligi uchun
                if (type === "folder" && parseInt(id) === f.id) return;
                select.innerHTML += `<option value="${f.id}">${f.icon || "📁"} ${f.name}</option>`;
            });
        } catch (_) {}

        openModal("moveModal");
    }

    document.getElementById("moveForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const id = document.getElementById("moveItemId").value;
        const type = document.getElementById("moveItemType").value;
        const targetVal = document.getElementById("moveTargetFolderSelect").value;
        const targetFolderId = targetVal ? parseInt(targetVal) : null;

        // Ommaviy ko'chirish: tanlangan barcha fayllar
        if (type === "bulk") {
            const sel = document.getElementById("moveTargetFolderSelect");
            const targetName = targetFolderId
                ? sel.options[sel.selectedIndex].text.replace(/^\S+\s/, "")
                : null;
            closeModal("moveModal");
            await moveFiles([...state.selected], targetFolderId, targetName);
            return;
        }

        try {
            const url = type === "folder" ? `/api/folders/${id}` : `/api/files/${id}`;
            const body = type === "folder" ? { parent_id: targetFolderId } : { folder_id: targetFolderId };

            const resp = await fetch(url, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body)
            });

            if (resp.ok) {
                closeModal("moveModal");
                showToast("Muvaffaqiyatli ko'chirildi!");
                navigateToFolder(state.currentFolderId);
            } else {
                const err = await resp.json();
                showToast(err.detail || "Ko'chirishda xatolik!", "error");
            }
        } catch (_) {
            showToast("Tarmoq xatosi!", "error");
        }
    });

    // E) O'chirish (Delete)
    let pendingDelete = null;
    function openDeleteModal(id, type, name) {
        pendingDelete = { id, type };
        document.getElementById("deleteModalMessage").innerHTML = `<b>«${name}»</b> ${type === 'folder' ? 'papkasini' : 'faylini'} butunlay o'chirib tashlamoqchimisiz?`;
        document.getElementById("deleteFolderWarning").style.display = type === "folder" ? "block" : "none";
        openModal("deleteModal");
    }

    document.getElementById("confirmDeleteBtn").addEventListener("click", async () => {
        if (!pendingDelete) return;
        const { id, type } = pendingDelete;

        try {
            const url = type === "folder" ? `/api/folders/${id}` : `/api/files/${id}`;
            const resp = await fetch(url, { method: "DELETE" });

            if (resp.ok) {
                closeModal("deleteModal");
                showToast("Muvaffaqiyatli o'chirildi!");
                if (type === "folder") {
                    navigateToFolder(state.currentFolderId);
                } else {
                    loadFiles(state.currentFolderId);
                }
            } else {
                const err = await resp.json();
                showToast(err.detail || "O'chirishda xatolik!", "error");
            }
        } catch (_) {
            showToast("Tarmoq xatosi!", "error");
        }
    });

    // =========================================================================
    // 18. SARALASH (nom / hajm / sana / tur)
    // =========================================================================
    const SORT_LABELS = {
        name: "Nomi bo'yicha",
        size: "Hajmi bo'yicha",
        date: "Sanasi bo'yicha",
        type: "Turi bo'yicha"
    };

    function sortFiles(files) {
        const dir = state.sortDir === "desc" ? -1 : 1;
        const arr = [...(files || [])];
        arr.sort((a, b) => {
            let r = 0;
            switch (state.sortBy) {
                case "size": r = (a.file_size || 0) - (b.file_size || 0); break;
                case "date": r = String(a.created_at).localeCompare(String(b.created_at)); break;
                case "type": r = String(a.file_type).localeCompare(String(b.file_type)); break;
                default: r = a.name.localeCompare(b.name, "ru", { numeric: true });
            }
            // Teng bo'lsa nom bo'yicha barqaror tartib
            if (r === 0) r = a.name.localeCompare(b.name, "ru", { numeric: true });
            return r * dir;
        });
        return arr;
    }

    function buildSortControl() {
        const header = elements.filesSection.querySelector(".section-header");
        if (!header || header.querySelector(".sort-control")) return;

        const wrap = document.createElement("div");
        wrap.className = "sort-control";
        wrap.innerHTML = `
            <select class="sort-select" title="Saralash">
                ${Object.entries(SORT_LABELS).map(([k, v]) =>
                    `<option value="${k}" ${state.sortBy === k ? "selected" : ""}>${v}</option>`).join("")}
            </select>
            <button class="sort-dir-btn" title="Yo'nalishni almashtirish">
                <i class="fa-solid ${state.sortDir === "asc" ? "fa-arrow-up-short-wide" : "fa-arrow-down-wide-short"}"></i>
            </button>
        `;

        wrap.querySelector(".sort-select").addEventListener("change", (e) => {
            state.sortBy = e.target.value;
            localStorage.setItem("foldex_sort_by", state.sortBy);
            state.files = sortFiles(state.files);
            renderFiles(state.files);
        });

        wrap.querySelector(".sort-dir-btn").addEventListener("click", (e) => {
            state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
            localStorage.setItem("foldex_sort_dir", state.sortDir);
            e.currentTarget.innerHTML =
                `<i class="fa-solid ${state.sortDir === "asc" ? "fa-arrow-up-short-wide" : "fa-arrow-down-wide-short"}"></i>`;
            state.files = sortFiles(state.files);
            renderFiles(state.files);
        });

        header.appendChild(wrap);
    }

    // =========================================================================
    // 19. KO'P TANLASH VA OMMAVIY AMALLAR
    // =========================================================================
    function toggleSelect(fileId, index, opts = {}) {
        const want = opts.force !== undefined ? opts.force : !state.selected.has(fileId);
        if (want) state.selected.add(fileId); else state.selected.delete(fileId);
        state.lastClickedIndex = index;
        refreshSelectionUI();
    }

    function selectRange(index) {
        if (state.lastClickedIndex === null) return toggleSelect(state.files[index].id, index, { force: true });
        const [a, b] = [state.lastClickedIndex, index].sort((x, y) => x - y);
        for (let i = a; i <= b; i++) {
            if (state.files[i]) state.selected.add(state.files[i].id);
        }
        refreshSelectionUI();
    }

    function selectAllFiles() {
        state.files.forEach(f => state.selected.add(f.id));
        refreshSelectionUI();
    }

    function clearSelection() {
        state.selected.clear();
        state.lastClickedIndex = null;
        refreshSelectionUI();
    }

    /** Qayta chizmasdan faqat tanlov ko'rinishini yangilaydi (tez va silliq) */
    function refreshSelectionUI() {
        elements.filesContainer.querySelectorAll(".file-card").forEach(card => {
            const id = parseInt(card.dataset.fileId);
            const on = state.selected.has(id);
            card.classList.toggle("selected", on);
            const cb = card.querySelector(".file-select-cb");
            if (cb) cb.checked = on;
        });
        updateSelectionBar();
    }

    function getSelectionBar() {
        let bar = document.getElementById("selectionBar");
        if (bar) return bar;

        bar = document.createElement("div");
        bar.id = "selectionBar";
        bar.className = "selection-bar";
        bar.innerHTML = `
            <span class="sel-count"><b id="selCountNum">0</b> ta tanlandi</span>
            <div class="sel-actions">
                <button class="sel-btn" id="selDownloadBtn"><i class="fa-solid fa-download"></i> Yuklab olish</button>
                <button class="sel-btn" id="selTelegramBtn"><i class="fa-brands fa-telegram"></i> Telegramga</button>
                <button class="sel-btn" id="selMoveBtn"><i class="fa-solid fa-arrow-right-arrow-left"></i> Ko'chirish</button>
                <button class="sel-btn danger" id="selDeleteBtn"><i class="fa-solid fa-trash"></i> O'chirish</button>
                <button class="sel-btn ghost" id="selClearBtn"><i class="fa-solid fa-xmark"></i> Bekor</button>
            </div>
        `;
        document.body.appendChild(bar);

        bar.querySelector("#selClearBtn").addEventListener("click", clearSelection);
        bar.querySelector("#selDeleteBtn").addEventListener("click", bulkDelete);
        bar.querySelector("#selMoveBtn").addEventListener("click", openBulkMoveModal);
        bar.querySelector("#selDownloadBtn").addEventListener("click", bulkDownload);
        bar.querySelector("#selTelegramBtn").addEventListener("click", () => sendToTelegram([...state.selected]));
        return bar;
    }

    function updateSelectionBar() {
        const bar = getSelectionBar();
        const n = state.selected.size;
        bar.querySelector("#selCountNum").innerText = n;
        bar.classList.toggle("show", n > 0);
    }

    async function bulkDelete() {
        const ids = [...state.selected];
        if (ids.length === 0) return;
        if (!confirm(`${ids.length} ta faylni butunlay o'chirmoqchimisiz? Bu amalni qaytarib bo'lmaydi.`)) return;

        let ok = 0, fail = 0;
        for (const id of ids) {
            try {
                const resp = await fetch(`/api/files/${id}`, { method: "DELETE" });
                resp.ok ? ok++ : fail++;
            } catch (_) { fail++; }
        }
        clearSelection();
        showToast(fail ? `${ok} ta o'chirildi, ${fail} tasida xatolik` : `${ok} ta fayl o'chirildi`,
                  fail ? "error" : "success");
        loadFiles(state.currentFolderId);
    }

    /** Fayllarni boshqa papkaga ko'chiradi (sudrab tashlash va ommaviy ko'chirish uchun) */
    async function moveFiles(ids, targetFolderId, targetName) {
        if (!ids || ids.length === 0) return;
        let ok = 0, fail = 0;
        for (const id of ids) {
            try {
                const resp = await fetch(`/api/files/${id}`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ folder_id: targetFolderId })
                });
                resp.ok ? ok++ : fail++;
            } catch (_) { fail++; }
        }
        clearSelection();
        const where = targetName ? `«${targetName}» papkasiga` : "Bosh sahifaga";
        showToast(fail ? `${ok} ta ko'chirildi, ${fail} tasida xatolik` : `${ok} ta fayl ${where} ko'chirildi`,
                  fail ? "error" : "success");
        navigateToFolder(state.currentFolderId);
    }

    async function openBulkMoveModal() {
        if (state.selected.size === 0) return;
        document.getElementById("moveItemType").value = "bulk";
        document.getElementById("moveItemId").value = "";
        document.getElementById("moveItemDescription").innerText =
            `${state.selected.size} ta faylni qaysi papkaga ko'chirmoqchisiz?`;

        const select = document.getElementById("moveTargetFolderSelect");
        select.innerHTML = '<option value="">🏠 Bosh sahifa (Ildiz katalog)</option>';
        try {
            const resp = await fetch("/api/folders/");
            const folders = await resp.json();
            folders.forEach(f => {
                select.innerHTML += `<option value="${f.id}">${f.icon || "📁"} ${f.name}</option>`;
            });
        } catch (_) {}
        openModal("moveModal");
    }

    function bulkDownload() {
        const ids = [...state.selected];
        if (ids.length === 0) return;
        // Brauzer ketma-ket yuklashni bloklamasligi uchun kichik oraliq bilan
        ids.forEach((id, i) => {
            setTimeout(() => {
                const a = document.createElement("a");
                a.href = `/api/files/${id}/download`;
                a.download = "";
                document.body.appendChild(a);
                a.click();
                a.remove();
            }, i * 400);
        });
        showToast(`${ids.length} ta fayl yuklab olinmoqda...`, "info");
    }

    async function sendToTelegram(ids) {
        if (!ids || ids.length === 0) return;
        showToast(`${ids.length} ta fayl Telegramga jo'natilmoqda...`, "info");
        let ok = 0, fail = 0;
        for (const id of ids) {
            try {
                const resp = await fetch(`/api/files/${id}/send-telegram`, { method: "POST" });
                resp.ok ? ok++ : fail++;
            } catch (_) { fail++; }
        }
        showToast(fail ? `${ok} ta jo'natildi, ${fail} tasida xatolik` : `${ok} ta fayl Telegramga jo'natildi`,
                  fail ? "error" : "success");
        if (ok) loadFiles(state.currentFolderId);
    }

    async function copyFileLink(file) {
        const url = `${location.origin}/api/files/${file.id}/download`;
        try {
            await navigator.clipboard.writeText(url);
            showToast("Havola nusxalandi");
        } catch (_) {
            // clipboard API ishlamasa (HTTP yoki ruxsat yo'q) — zaxira usul
            const ta = document.createElement("textarea");
            ta.value = url;
            document.body.appendChild(ta);
            ta.select();
            try { document.execCommand("copy"); showToast("Havola nusxalandi"); }
            catch (_) { showToast("Nusxalab bo'lmadi", "error"); }
            ta.remove();
        }
    }

    // =========================================================================
    // 20. FAYLNI KO'RISH OYNASI (PDF, rasm, video, audio)
    // =========================================================================
    function getPreviewModal() {
        let modal = document.getElementById("previewModal");
        if (modal) return modal;

        modal = document.createElement("div");
        modal.id = "previewModal";
        modal.className = "modal preview-modal";
        modal.innerHTML = `
            <div class="modal-backdrop"></div>
            <div class="modal-dialog preview-dialog">
                <div class="modal-header">
                    <h3 id="previewTitle">Ko'rish</h3>
                    <div class="preview-head-actions">
                        <a id="previewDownload" class="text-btn" download><i class="fa-solid fa-download"></i></a>
                        <button class="close-modal-btn"><i class="fa-solid fa-xmark"></i></button>
                    </div>
                </div>
                <div class="modal-body preview-body" id="previewBody"></div>
            </div>
        `;
        document.body.appendChild(modal);
        modal.querySelector(".close-modal-btn").addEventListener("click", closePreview);
        modal.querySelector(".modal-backdrop").addEventListener("click", closePreview);
        return modal;
    }

    function openPreview(file) {
        const modal = getPreviewModal();
        const body = modal.querySelector("#previewBody");
        modal.querySelector("#previewTitle").innerText = file.name;
        modal.querySelector("#previewDownload").href = `/api/files/${file.id}/download`;

        // inline=1 — brauzer faylni yuklab olmasdan o'zida ochadi
        const src = `/api/files/${file.id}/download?inline=1`;
        const ext = (file.name.split(".").pop() || "").toLowerCase();

        if (file.file_type === "photo") {
            body.innerHTML = `<img src="${src}" alt="${file.name}" class="preview-img">`;
        } else if (file.file_type === "video") {
            body.innerHTML = `<video src="${src}" controls class="preview-video"></video>`;
        } else if (file.file_type === "audio") {
            body.innerHTML = `<audio src="${src}" controls class="preview-audio"></audio>`;
        } else if (ext === "pdf") {
            body.innerHTML = `<iframe src="${src}" class="preview-frame" title="${file.name}"></iframe>`;
        } else if (["txt", "md", "json", "csv", "log", "xml", "yml", "yaml"].includes(ext)) {
            body.innerHTML = `<iframe src="${src}" class="preview-frame" title="${file.name}"></iframe>`;
        } else {
            body.innerHTML = `
                <div class="preview-unsupported">
                    <i class="fa-solid fa-file-circle-question"></i>
                    <p>Bu turdagi faylni brauzerda ko'rib bo'lmaydi.</p>
                    <a class="btn-primary" href="/api/files/${file.id}/download" download>
                        <i class="fa-solid fa-download"></i> Yuklab olish
                    </a>
                </div>`;
        }
        modal.classList.add("show");
    }

    function closePreview() {
        const modal = document.getElementById("previewModal");
        if (!modal) return;
        modal.classList.remove("show");
        // Video/audio fonda ijro etilib qolmasligi uchun tozalaymiz
        modal.querySelector("#previewBody").innerHTML = "";
    }

    // =========================================================================
    // 21. O'NG TUGMA (KONTEKST) MENYUSI
    // =========================================================================
    function closeContextMenu() {
        const m = document.getElementById("ctxMenu");
        if (m) m.remove();
    }

    function openContextMenu(x, y, type, item) {
        closeContextMenu();
        const menu = document.createElement("div");
        menu.id = "ctxMenu";
        menu.className = "ctx-menu";

        const many = type === "file" && state.selected.size > 1;
        const rows = type === "folder"
            ? [
                ["fa-folder-open", "Ochish", () => navigateToFolder(item.id)],
                ["fa-pen", "Qayta nomlash", () => openRenameModal(item.id, "folder", item.name)],
                ["fa-arrow-right-arrow-left", "Ko'chirish", () => openMoveModal(item.id, "folder", item.name)],
                ["fa-trash", "O'chirish", () => openDeleteModal(item.id, "folder", item.name), true]
              ]
            : many
            ? [
                ["fa-download", `Yuklab olish (${state.selected.size})`, bulkDownload],
                ["fa-telegram", `Telegramga (${state.selected.size})`, () => sendToTelegram([...state.selected])],
                ["fa-arrow-right-arrow-left", `Ko'chirish (${state.selected.size})`, openBulkMoveModal],
                ["fa-trash", `O'chirish (${state.selected.size})`, bulkDelete, true]
              ]
            : [
                ["fa-eye", "Ko'rish", () => openPreview(item)],
                ["fa-download", "Yuklab olish", () => bulkDownload()],
                ["fa-link", "Havolani nusxalash", () => copyFileLink(item)],
                ["fa-telegram", "Telegramga yuborish", () => sendToTelegram([item.id])],
                ["fa-pen", "Qayta nomlash", () => openRenameModal(item.id, "file", item.name)],
                ["fa-arrow-right-arrow-left", "Ko'chirish", () => openMoveModal(item.id, "file", item.name)],
                ["fa-trash", "O'chirish", () => openDeleteModal(item.id, "file", item.name), true]
              ];

        rows.forEach(([icon, label, fn, danger]) => {
            const b = document.createElement("button");
            b.className = "ctx-item" + (danger ? " danger" : "");
            const fam = icon === "fa-telegram" ? "fa-brands" : "fa-solid";
            b.innerHTML = `<i class="${fam} ${icon}"></i> ${label}`;
            b.addEventListener("click", () => { closeContextMenu(); fn(); });
            menu.appendChild(b);
        });

        document.body.appendChild(menu);
        // Ekran chetidan chiqib ketmasligi uchun joyini to'g'rilaymiz
        const r = menu.getBoundingClientRect();
        menu.style.left = Math.min(x, window.innerWidth - r.width - 8) + "px";
        menu.style.top = Math.min(y, window.innerHeight - r.height - 8) + "px";
    }

    document.addEventListener("click", closeContextMenu);
    document.addEventListener("scroll", closeContextMenu, true);

    // Bo'sh joyga o'ng tugma bosilsa menyuni yopamiz
    elements.filesContainer.addEventListener("contextmenu", (e) => {
        if (!e.target.closest(".file-card")) closeContextMenu();
    });

    // =========================================================================
    // 22. KLAVIATURA QISQA YO'LLARI
    // =========================================================================
    document.addEventListener("keydown", (e) => {
        const typing = ["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName);
        const modalOpen = document.querySelector(".modal.show");

        if (e.key === "Escape") {
            if (document.getElementById("ctxMenu")) return closeContextMenu();
            if (modalOpen) {
                document.querySelectorAll(".modal.show").forEach(m => m.classList.remove("show"));
                closePreview();
                return;
            }
            if (state.selected.size) clearSelection();
            return;
        }

        if (typing || modalOpen) return;

        // Ctrl/Cmd + A — hammasini tanlash
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "a") {
            e.preventDefault();
            selectAllFiles();
            return;
        }
        // Delete — tanlanganlarni o'chirish
        if (e.key === "Delete" && state.selected.size) {
            e.preventDefault();
            bulkDelete();
            return;
        }
        // F2 — bitta tanlangan faylni qayta nomlash
        if (e.key === "F2" && state.selected.size === 1) {
            e.preventDefault();
            const id = [...state.selected][0];
            const f = state.files.find(x => x.id === id);
            if (f) openRenameModal(f.id, "file", f.name);
            return;
        }
        // Enter yoki probel — ko'rish oynasi
        if ((e.key === "Enter" || e.key === " ") && state.selected.size === 1) {
            e.preventDefault();
            const id = [...state.selected][0];
            const f = state.files.find(x => x.id === id);
            if (f) openPreview(f);
        }
    });

    // =========================================================================
    // 23. BOSHLANG'ICH YUKLANISH
    // =========================================================================
    buildSortControl();
    navigateToFolder(null);
    loadDashboardStats();
});
