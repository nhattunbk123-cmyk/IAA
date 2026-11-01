// ==============================================================================
// VULNSHOP LAB - LAB HUB & TOGGLES CONTROLLER
// ==============================================================================

document.addEventListener('DOMContentLoaded', function () {
    // 1. Lắng nghe sự kiện chuyển đổi trạng thái (Toggle Switch) cho từng bài lab
    setupLabToggles();

    // 2. Lắng nghe các khối Accordion (Gợi ý và Lời giải)
    setupAccordions();

    // 3. Xử lý chức năng Reset Database
    setupDatabaseReset();

    // 4. Bật/Tắt toàn bộ lab
    setupToggleAll();
});

function setupLabToggles() {
    const switches = document.querySelectorAll('.lab-toggle-checkbox');
    switches.forEach(sw => {
        sw.addEventListener('change', async function () {
            const labId = this.getAttribute('data-lab-id');
            const isVulnerable = this.checked;
            const card = document.getElementById(`lab-card-${labId}`);
            const badge = document.getElementById(`status-badge-${labId}`);

            try {
                const response = await fetch('/api/labs/toggle', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ lab_id: labId, status: isVulnerable })
                });

                const data = await response.json();
                if (data.success) {
                    showToast(data.message, isVulnerable ? 'danger' : 'success');
                    
                    // Cập nhật giao diện thẻ bài lab
                    if (card) {
                        card.classList.toggle('is-vuln', isVulnerable);
                        card.classList.toggle('is-fixed', !isVulnerable);
                    }
                    if (badge) {
                        badge.className = `badge ${isVulnerable ? 'status-badge-vuln' : 'status-badge-fixed'}`;
                        badge.textContent = isVulnerable ? '🔴 Vulnerable' : '🟢 Fixed';
                    }
                } else {
                    showToast('Lỗi: ' + data.message, 'danger');
                    this.checked = !isVulnerable; // Rollback
                }
            } catch (err) {
                showToast('Lỗi kết nối máy chủ: ' + err.message, 'danger');
                this.checked = !isVulnerable;
            }
        });
    });
}

function setupAccordions() {
    const headers = document.querySelectorAll('.accordion-header');
    headers.forEach(header => {
        header.addEventListener('click', function () {
            const content = this.nextElementSibling;
            const icon = this.querySelector('.accordion-icon');
            if (content) {
                content.classList.toggle('open');
                if (icon) {
                    icon.textContent = content.classList.contains('open') ? '▲' : '▼';
                }
            }
        });
    });
}

function setupDatabaseReset() {
    const btnOpenModal = document.getElementById('btn-reset-db-modal');
    const modal = document.getElementById('reset-db-modal');
    const btnCancel = document.getElementById('btn-reset-cancel');
    const btnConfirm = document.getElementById('btn-reset-confirm');

    if (btnOpenModal && modal) {
        btnOpenModal.addEventListener('click', () => modal.classList.add('active'));
    }
    if (btnCancel && modal) {
        btnCancel.addEventListener('click', () => modal.classList.remove('active'));
    }

    if (btnConfirm) {
        btnConfirm.addEventListener('click', async function () {
            btnConfirm.disabled = true;
            btnConfirm.textContent = 'Đang khôi phục...';

            try {
                const response = await fetch('/api/labs/reset-db', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                const res = await response.json();

                if (res.success) {
                    showToast(res.message, 'success');
                    setTimeout(() => window.location.reload(), 1200);
                } else {
                    showToast('Lỗi: ' + res.message, 'danger');
                }
            } catch (err) {
                showToast('Lỗi kết nối: ' + err.message, 'danger');
            } finally {
                btnConfirm.disabled = false;
                btnConfirm.textContent = 'Xác nhận khôi phục';
                if (modal) modal.classList.remove('active');
            }
        });
    }
}

function setupToggleAll() {
    const btnAllVuln = document.getElementById('btn-all-vuln');
    const btnAllFixed = document.getElementById('btn-all-fixed');

    if (btnAllVuln) {
        btnAllVuln.addEventListener('click', () => applyToggleAll(true));
    }
    if (btnAllFixed) {
        btnAllFixed.addEventListener('click', () => applyToggleAll(false));
    }
}

async function applyToggleAll(status) {
    try {
        const response = await fetch('/api/labs/toggle-all', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        const res = await response.json();
        if (res.success) {
            showToast(res.message, status ? 'danger' : 'success');
            setTimeout(() => window.location.reload(), 800);
        }
    } catch (err) {
        showToast('Lỗi: ' + err.message, 'danger');
    }
}
