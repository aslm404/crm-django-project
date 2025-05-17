document.addEventListener('DOMContentLoaded', function() {
    const toggleBtn = document.getElementById('theme-toggle');
    const html = document.documentElement;
    const themeIcon = toggleBtn.querySelector('i');

    // Load saved theme
    if (localStorage.getItem('theme') === 'dark') {
        html.classList.add('dark-theme');
        themeIcon.classList.replace('bi-moon-stars-fill', 'bi-sun-fill');
    }

    toggleBtn.addEventListener('click', function() {
        html.classList.toggle('dark-theme');
        const isDark = html.classList.contains('dark-theme');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        themeIcon.classList.toggle('bi-moon-stars-fill', !isDark);
        themeIcon.classList.toggle('bi-sun-fill', isDark);
    });
});