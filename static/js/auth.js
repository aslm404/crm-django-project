document.addEventListener('DOMContentLoaded', function() {
    // Login form validation
    const loginForm = document.querySelector('form[action="/login/"]');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            const emailInput = loginForm.querySelector('input[name="username"]');
            const passwordInput = loginForm.querySelector('input[name="password"]');
            const email = emailInput.value.trim();
            const password = passwordInput.value;

            if (!validateEmail(email)) {
                e.preventDefault();
                showError(emailInput, 'Please enter a valid email address.');
                return;
            }
            if (password.length < 1) {
                e.preventDefault();
                showError(passwordInput, 'Password is required.');
                return;
            }
        });
    }

    // Password reset form validation
    const resetForm = document.querySelector('form[action="/password_reset/"]');
    if (resetForm) {
        resetForm.addEventListener('submit', function(e) {
            const emailInput = resetForm.querySelector('input[name="email"]');
            const email = emailInput.value.trim();

            if (!validateEmail(email)) {
                e.preventDefault();
                showError(emailInput, 'Please enter a valid email address.');
            }
        });
    }

    // Password reset confirm form validation
    const confirmForm = document.querySelector('form[action*="/password-reset-confirm/"]');
    if (confirmForm) {
        confirmForm.addEventListener('submit', function(e) {
            const password1Input = confirmForm.querySelector('input[name="new_password1"]');
            const password2Input = confirmForm.querySelector('input[name="new_password2"]');
            const password1 = password1Input.value;
            const password2 = password2Input.value;

            if (password1.length < 8) {
                e.preventDefault();
                showError(password1Input, 'Password must be at least 8 characters long.');
                return;
            }
            if (password1 !== password2) {
                e.preventDefault();
                showError(password2Input, 'Passwords do not match.');
            }
        });
    }

    // Email validation
    function validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    // Show error message
    function showError(input, message) {
        const formGroup = input.closest('.form-group');
        let errorDiv = formGroup.querySelector('.error-message');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'error-message text-danger';
            formGroup.appendChild(errorDiv);
        }
        errorDiv.textContent = message;
        setTimeout(() => errorDiv.textContent = '', 3000);
    }
});