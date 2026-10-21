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
        allFlatFolders: []
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
                // Boshqa ochiq menyularni yopish
                document.querySelectorAll(".dropdown-menu.show").forEach(m => m !== menu && m.classList.remove("show"));
                menu.classList.toggle("show");
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
            state.files = data.items;
            renderFiles(data.items);
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

        files.forEach(file => {
            const card = document.createElement("div");
            card.className = "file-card";

            const iconHtml = getFileIcon(file.file_type, file.name);
            const tgBadge = file.is_synced_with_telegram
                ? '<span class="tg-badge" title="Telegramda tezkor ulashishga tayyor"><i class="fa-brands fa-telegram"></i> Telegram</span>'
                : '';

            card.innerHTML = `
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
                        <a href="/api/files/${file.id}/download" class="dropdown-item" download>
                            <i class="fa-solid fa-download"></i> Yuklab olish
                        </a>
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
                document.querySelectorAll(".dropdown-menu.show").forEach(m => m !== menu && m.classList.remove("show"));
                menu.classList.toggle("show");
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
    elements.openSidebarBtn.addEventListener("click", () => elements.sidebar.classList.add("open"));
    elements.closeSidebarBtn.addEventListener("click", () => elements.sidebar.classList.remove("open"));
    elements.logoutBtn.addEventListener("click", () => window.Auth.logout());
    elements.treeRefreshBtn.addEventListener("click", () => loadFolderTree());

    // Sahifaning boshqa joyiga bosilganda ochiq dropdown menyularni yopish
    document.addEventListener("click", () => {
        document.querySelectorAll(".dropdown-menu.show").forEach(m => m.classList.remove("show"));
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
    // 18. BOSHLANG'ICH YUKLANISH
    // =========================================================================
    navigateToFolder(null);
    loadDashboardStats();
});
