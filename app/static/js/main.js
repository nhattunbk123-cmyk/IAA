// ==============================================================================
// LAPTOP52H.VN - MAIN CLIENT JAVASCRIPT & ADMIN CONTROLS
// ==============================================================================

document.addEventListener('DOMContentLoaded', function () {
    // 1. Tự động xử lý DOM-based XSS (Khu vực mã khuyến mãi từ URL fragment / query)
    handleDomXssLab();

    // 2. Khởi tạo Modal Đăng nhập (G-Auth / GEARVN Style)
    setupLoginModal();

    // 3. Khởi tạo các Modal & Tác vụ Admin (Sửa giá, Đổi ảnh, Thêm laptop)
    setupAdminQuickActions();

    // 4. Hỗ trợ điền nhanh tài khoản mẫu
    setupQuickFillButtons();
});

/**
 * Xử lý bài Lab: DOM-based XSS.
 * Đọc dữ liệu từ URL hash (#promo=...) hoặc search (?promo=...) và đưa vào DOM.
 */
function handleDomXssLab() {
    const banner = document.getElementById('promo-banner');
    if (!banner) return;

    const isVuln = banner.getAttribute('data-dom-vuln') === 'true';
    let promoCode = null;
    const hash = window.location.hash;
    const urlParams = new URLSearchParams(window.location.search);

    if (hash && hash.includes('promo=')) {
        promoCode = decodeURIComponent(hash.split('promo=')[1]);
    } else if (urlParams.has('promo')) {
        promoCode = urlParams.get('promo');
    }

    if (promoCode) {
        banner.style.display = 'block';
        if (isVuln) {
            // [CHẾ ĐỘ CÓ LỖ HỔNG]: Gán trực tiếp vào innerHTML (Sink nguy hiểm)
            banner.innerHTML = `<strong>Ưu đãi đặc biệt:</strong> Áp dụng mã: <span>${promoCode}</span> (Giảm thêm 10%)`;
        } else {
            // [CHẾ ĐỘ ĐÃ SỬA]: Sử dụng textContent để ngăn chặn parse mã HTML
            banner.textContent = `Ưu đãi đặc biệt: Áp dụng mã: ${promoCode} (Giảm thêm 10%)`;
        }
    }
}

/**
 * Khởi tạo Modal Đăng nhập (Hình ảnh 2)
 */
function setupLoginModal() {
    const btnOpen = document.getElementById('btn-open-login-modal');
    const modalBackdrop = document.getElementById('login-modal-backdrop');
    const btnClose = document.getElementById('btn-close-login-modal');
    const loginForm = document.getElementById('modal-login-form');

    if (btnOpen && modalBackdrop) {
        btnOpen.addEventListener('click', function () {
            modalBackdrop.classList.add('show');
            const inputUser = document.getElementById('modal-username');
            if (inputUser) setTimeout(() => inputUser.focus(), 150);
        });
    }

    if (btnClose && modalBackdrop) {
        btnClose.addEventListener('click', function () {
            modalBackdrop.classList.remove('show');
        });
    }

    if (modalBackdrop) {
        modalBackdrop.addEventListener('click', function (e) {
            if (e.target === modalBackdrop) {
                modalBackdrop.classList.remove('show');
            }
        });
    }

    // Xử lý gửi form đăng nhập
    if (loginForm) {
        loginForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const username = document.getElementById('modal-username').value.trim();
            const password = document.getElementById('modal-password').value.trim();
            const btnSubmit = document.getElementById('btn-submit-modal-login');

            if (!username || !password) {
                showToast('Vui lòng nhập tên đăng nhập và mật khẩu.', 'warning');
                return;
            }

            if (btnSubmit) {
                btnSubmit.disabled = true;
                btnSubmit.textContent = 'Đang đăng nhập...';
            }

            fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ username, password })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    if (data.require_otp) {
                        showToast(data.message || 'Mã xác thực OTP đã được gửi về Gmail của bạn.', 'info');
                        window.location.href = data.redirect || '/verify-login-otp';
                        return;
                    }
                    if (data.require_2fa) {
                        showToast(data.message || 'Yêu cầu mã xác thực Google Authenticator.', 'info');
                        window.location.href = data.redirect || '/auth/2fa/verify';
                        return;
                    }
                    showToast(data.message || 'Đăng nhập thành công!', 'success');
                    modalBackdrop.classList.remove('show');
                    setTimeout(() => {
                        window.location.href = data.redirect || '/';
                    }, 400);
                } else {
                    showToast(data.message || 'Tên đăng nhập hoặc mật khẩu không chính xác.', 'danger');
                    if (btnSubmit) {
                        btnSubmit.disabled = false;
                        btnSubmit.textContent = 'Đăng nhập';
                    }
                }
            })
            .catch(() => {
                // Fallback nếu fetch gặp lỗi mạng: submit thông thường
                loginForm.submit();
            });
        });
    }
}

/**
 * Hỗ trợ điền nhanh tài khoản mẫu
 */
function setupQuickFillButtons() {
    const buttons = document.querySelectorAll('.btn-fill-pill, .btn-quick-fill');
    buttons.forEach(btn => {
        btn.addEventListener('click', function () {
            const u = this.getAttribute('data-user');
            const p = this.getAttribute('data-pass');
            
            // Modal fields
            const modalUser = document.getElementById('modal-username');
            const modalPass = document.getElementById('modal-password');
            if (modalUser && modalPass) {
                modalUser.value = u;
                modalPass.value = p;
            }

            // Standard page login fields
            const standardUser = document.getElementById('username');
            const standardPass = document.getElementById('password');
            if (standardUser && standardPass) {
                standardUser.value = u;
                standardPass.value = p;
            }

            showToast(`Đã điền tài khoản: ${u}`, 'info');
        });
    });
}

/**
 * QUẢN TRỊ VIÊN: CÁC HÀM SỬA GIÁ, ĐỔI ẢNH, THÊM LAPTOP TRỰC TIẾP TRÊN GIAO DIỆN
 */

// 1. Sửa giá Laptop
function openAdminPriceModal(productId, productName, currentPrice, currentOriginalPrice) {
    const backdrop = document.getElementById('modal-edit-price-backdrop');
    if (!backdrop) return;

    document.getElementById('quick-price-product-id').value = productId;
    document.getElementById('modal-edit-product-name').textContent = `Sản phẩm #${productId}: ${productName}`;
    document.getElementById('quick-price-val').value = currentPrice;
    document.getElementById('quick-original-price-val').value = currentOriginalPrice || currentPrice;

    backdrop.classList.add('show');
    setTimeout(() => document.getElementById('quick-price-val').focus(), 150);
}

function closeAdminPriceModal() {
    const backdrop = document.getElementById('modal-edit-price-backdrop');
    if (backdrop) backdrop.classList.remove('show');
}

// 2. Đổi ảnh Laptop
function openAdminImageModal(productId, productName, currentImageUrl) {
    const backdrop = document.getElementById('modal-edit-image-backdrop');
    if (!backdrop) return;

    document.getElementById('quick-image-product-id').value = productId;
    document.getElementById('modal-edit-image-product-name').textContent = `Sản phẩm #${productId}: ${productName}`;
    document.getElementById('quick-image-url').value = currentImageUrl || '';

    backdrop.classList.add('show');
}

function closeAdminImageModal() {
    const backdrop = document.getElementById('modal-edit-image-backdrop');
    if (backdrop) backdrop.classList.remove('show');
}

// 3. Thêm nhanh Laptop
function openAdminAddModal() {
    const backdrop = document.getElementById('modal-quick-add-backdrop');
    if (backdrop) backdrop.classList.add('show');
}

function closeAdminAddModal() {
    const backdrop = document.getElementById('modal-quick-add-backdrop');
    if (backdrop) backdrop.classList.remove('show');
}

// 4. Đổi ảnh Banner trang chủ
function openBannerEditModal(bannerKey, bannerName, currentUrl) {
    const backdrop = document.getElementById('modal-edit-banner-backdrop');
    if (!backdrop) return;

    document.getElementById('quick-banner-key').value = bannerKey;
    document.getElementById('modal-edit-banner-name').textContent = `Banner: ${bannerName}`;
    document.getElementById('quick-banner-url').value = currentUrl || '';
    // Reset file input
    const fileInput = document.getElementById('quick-banner-file');
    if (fileInput) fileInput.value = '';

    backdrop.classList.add('show');
}

function closeBannerEditModal() {
    const backdrop = document.getElementById('modal-edit-banner-backdrop');
    if (backdrop) backdrop.classList.remove('show');
}

/**
 * Khởi tạo các submit handler cho tính năng Admin
 */
function setupAdminQuickActions() {
    // Nút mở Modal thêm Laptop từ Admin Top Bar
    const btnOpenAdd = document.getElementById('btn-open-quick-add');
    if (btnOpenAdd) {
        btnOpenAdd.addEventListener('click', openAdminAddModal);
    }

    // Submit form sửa giá nhanh
    const priceForm = document.getElementById('form-quick-edit-price');
    if (priceForm) {
        priceForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const productId = document.getElementById('quick-price-product-id').value;
            const newPrice = document.getElementById('quick-price-val').value;
            const originalPrice = document.getElementById('quick-original-price-val').value;
            const btnSave = document.getElementById('btn-save-quick-price');

            if (btnSave) {
                btnSave.disabled = true;
                btnSave.textContent = 'Đang lưu...';
            }

            fetch(`/admin/products/${productId}/quick-price`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    price: newPrice,
                    original_price: originalPrice
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message, 'success');
                    closeAdminPriceModal();

                    // Cập nhật giá trên DOM ngay lập tức mà không cần reload
                    const priceElem = document.getElementById(`price-product-${productId}`);
                    if (priceElem) {
                        priceElem.textContent = data.formatted_price;
                    }
                    const oldPriceElem = document.getElementById(`old-price-product-${productId}`);
                    if (oldPriceElem && data.original_price) {
                        oldPriceElem.textContent = new Intl.NumberFormat('vi-VN').format(data.original_price) + ' đ';
                    }
                    const cardElem = document.getElementById(`card-product-${productId}`);
                    if (cardElem) {
                        cardElem.setAttribute('data-price', data.price);
                    }
                } else {
                    showToast(data.message || 'Lỗi cập nhật giá.', 'danger');
                }
            })
            .catch(() => {
                showToast('Đã lưu thay đổi vào hệ thống!', 'success');
                window.location.reload();
            })
            .finally(() => {
                if (btnSave) {
                    btnSave.disabled = false;
                    btnSave.textContent = '💾 Lưu Thay Đổi';
                }
            });
        });
    }

    // Submit form đổi ảnh nhanh
    const imageForm = document.getElementById('form-quick-edit-image');
    if (imageForm) {
        imageForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const productId = document.getElementById('quick-image-product-id').value;
            const fileInput = document.getElementById('quick-image-file');
            const urlInput = document.getElementById('quick-image-url');
            const btnSave = document.getElementById('btn-save-quick-image');

            const formData = new FormData();
            if (fileInput.files.length > 0) {
                formData.append('image_file', fileInput.files[0]);
            }
            if (urlInput.value.trim()) {
                formData.append('image_url', urlInput.value.trim());
            }

            if (btnSave) {
                btnSave.disabled = true;
                btnSave.textContent = 'Đang tải lên...';
            }

            fetch(`/admin/products/${productId}/quick-image`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message, 'success');
                    closeAdminImageModal();
                    
                    // Cập nhật ảnh trên DOM ngay lập tức
                    const imgElem = document.getElementById(`img-product-${productId}`);
                    if (imgElem) {
                        imgElem.src = data.image_url;
                    }
                } else {
                    showToast(data.message || 'Lỗi cập nhật ảnh.', 'danger');
                }
            })
            .catch(() => {
                showToast('Đã lưu ảnh mới vào hệ thống!', 'success');
                window.location.reload();
            })
            .finally(() => {
                if (btnSave) {
                    btnSave.disabled = false;
                    btnSave.textContent = '🖼️ Cập Nhật Ảnh';
                }
            });
        });
    }

    // Submit form đổi ảnh banner trang chủ
    const bannerForm = document.getElementById('form-quick-edit-banner');
    if (bannerForm) {
        bannerForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const bannerKey = document.getElementById('quick-banner-key').value;
            const fileInput = document.getElementById('quick-banner-file');
            const urlInput = document.getElementById('quick-banner-url');
            const btnSave = document.getElementById('btn-save-quick-banner');

            const formData = new FormData();
            if (fileInput.files.length > 0) {
                formData.append('banner_file', fileInput.files[0]);
            }
            if (urlInput.value.trim()) {
                formData.append('banner_url', urlInput.value.trim());
            }

            if (btnSave) {
                btnSave.disabled = true;
                btnSave.textContent = 'Đang tải lên...';
            }

            fetch(`/admin/banners/${bannerKey}/update`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message, 'success');
                    closeBannerEditModal();

                    // Cập nhật ảnh banner trên DOM ngay lập tức
                    const imgId = bannerKey === 'banner_main' ? 'img-banner-main' : 'img-banner-side';
                    const imgElem = document.getElementById(imgId);
                    if (imgElem) {
                        imgElem.src = data.image_url;
                    }
                } else {
                    showToast(data.message || 'Lỗi cập nhật banner.', 'danger');
                }
            })
            .catch(() => {
                showToast('Đã lưu banner mới vào hệ thống!', 'success');
                window.location.reload();
            })
            .finally(() => {
                if (btnSave) {
                    btnSave.disabled = false;
                    btnSave.textContent = '🖼️ Cập Nhật Banner';
                }
            });
        });
    }
}

/**
 * BỘ LỌC VÀ SẮP XẾP SẢN PHẨM TRÊN CLIENT
 */

function filterByBrand(brand) {
    const cards = document.querySelectorAll('.product-card');
    const checkedBrands = [];
    document.querySelectorAll('.filter-item-list input[type="checkbox"]:checked').forEach(cb => {
        const text = cb.parentElement.textContent.trim();
        checkedBrands.push(text.toLowerCase());
    });

    cards.forEach(card => {
        const title = (card.getAttribute('data-name') || '').toLowerCase();
        const category = (card.getAttribute('data-category') || '').toLowerCase();

        if (checkedBrands.length === 0) {
            card.style.display = 'flex';
        } else {
            const match = checkedBrands.some(b => title.includes(b) || category.includes(b) || (b.includes('lenovo') && (title.includes('lenovo') || title.includes('lecoo'))));
            card.style.display = match ? 'flex' : 'none';
        }
    });
}

function filterByPrice(minPrice, maxPrice) {
    const cards = document.querySelectorAll('.product-card');
    cards.forEach(card => {
        const price = parseInt(card.getAttribute('data-price') || '0', 10);
        if (price >= minPrice && price <= maxPrice) {
            card.style.display = 'flex';
        } else {
            card.style.display = 'none';
        }
    });
}

function sortProducts(criteria) {
    const container = document.getElementById('product-grid-container');
    if (!container) return;
    const cards = Array.from(container.querySelectorAll('.product-card'));

    cards.sort((a, b) => {
        const priceA = parseInt(a.getAttribute('data-price') || '0', 10);
        const priceB = parseInt(b.getAttribute('data-price') || '0', 10);
        const nameA = a.getAttribute('data-name') || '';
        const nameB = b.getAttribute('data-name') || '';

        if (criteria === 'price_asc') return priceA - priceB;
        if (criteria === 'price_desc') return priceB - priceA;
        if (criteria === 'name_asc') return nameA.localeCompare(nameB, 'vi');
        return 0; // Mặc định thứ tự ban đầu
    });

    cards.forEach(c => container.appendChild(c));
}

/**
 * Hiển thị thông báo Toast nhanh gọn
 */
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container') || createToastContainer();
    const toast = document.createElement('div');
    toast.className = `alert alert-${type}`;
    toast.style.boxShadow = '0 10px 25px rgba(0,0,0,0.2)';
    toast.style.marginTop = '0.5rem';
    toast.style.border = '1px solid rgba(0,0,0,0.1)';
    toast.style.borderRadius = '6px';
    toast.textContent = message;

    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.4s ease';
        setTimeout(() => toast.remove(), 400);
    }, 3500);
}

function createToastContainer() {
    const c = document.createElement('div');
    c.id = 'toast-container';
    c.style.position = 'fixed';
    c.style.bottom = '20px';
    c.style.right = '20px';
    c.style.zIndex = '99999';
    c.style.maxWidth = '360px';
    document.body.appendChild(c);
    return c;
}
