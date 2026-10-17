// ARCH Realty ERP+CRM Core Client JS
document.addEventListener('DOMContentLoaded', () => {
    // Theme toggle with icon switch
    const themeToggleBtn = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    const currentTheme = localStorage.getItem('arch_theme') || 'light';
    document.documentElement.setAttribute('data-theme', currentTheme);
    updateThemeIcon(currentTheme);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', next);
            localStorage.setItem('arch_theme', next);
            updateThemeIcon(next);
        });
    }

    function updateThemeIcon(theme) {
        if (!themeIcon) return;
        if (theme === 'dark') {
            themeIcon.className = 'bi bi-sun-fill';
        } else {
            themeIcon.className = 'bi bi-moon-stars';
        }
    }

    // Sidebar toggle for mobile / responsive
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.querySelector('.app-sidebar');
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }

    // Highlight active sidebar navigation link
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar-nav li a');
    navLinks.forEach(link => {
        const linkPath = link.getAttribute('href');
        if (linkPath && currentPath === linkPath) {
            link.parentElement.classList.add('active');
        } else if (linkPath && linkPath !== '/' && currentPath.startsWith(linkPath)) {
            link.parentElement.classList.add('active');
        }
    });

    // Auto dismiss flash alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.4s ease';
            setTimeout(() => alert.remove(), 400);
        }, 5000);
    });
});

// HR Modal & Tab Helpers
window.openHrModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.style.display = 'flex';
};

window.closeHrModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.style.display = 'none';
};

window.switchProfileTab = function(tabName) {
    document.querySelectorAll('.profile-tab-item').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.profile-tab-pane').forEach(el => el.classList.remove('active'));
    
    const targetItem = document.getElementById('tab-btn-' + tabName);
    const targetPane = document.getElementById('tab-pane-' + tabName);
    if (targetItem) targetItem.classList.add('active');
    if (targetPane) targetPane.classList.add('active');
};

