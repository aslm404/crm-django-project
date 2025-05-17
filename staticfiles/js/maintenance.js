document.addEventListener('DOMContentLoaded', function() {
    // Auto-refresh every 30 seconds
    setInterval(function() {
        fetch('/', { method: 'HEAD' })
            .then(response => {
                if (response.ok) {
                    window.location.href = '/dashboard/';
                }
            })
            .catch(error => console.log('Maintenance check failed:', error));
    }, 30000);
});