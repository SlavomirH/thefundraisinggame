// Bluefox Configuration
const BLUEFOX_SUBSCRIBER_LIST_URL = 'https://api.bluefox.email/v1/subscriber-lists/6960f7e0cfa080251b241006';
const BLUEFOX_CAPTCHA_URL = 'https://api.bluefox.email/v1/captcha';

// Store captcha probes for each form
const captchaProbes = {
    'early-access': null,
    'preorder': null
};

// Scroll to preorder form
function scrollToForm() {
    document.getElementById('preorder').scrollIntoView({ behavior: 'smooth' });
}

// Generate captcha for a specific form
function loadCaptcha(formPrefix) {
    const captchaDiv = document.getElementById(`${formPrefix}-captcha-div`);

    if (!captchaDiv) {
        console.error(`Captcha div not found for: ${formPrefix}-captcha-div`);
        return;
    }

    fetch(BLUEFOX_CAPTCHA_URL)
        .then(response => response.json())
        .then(captchaData => {
            captchaDiv.innerHTML = captchaData.result.data;
            captchaProbes[formPrefix] = captchaData.result.probe;
            console.log(`Captcha loaded for ${formPrefix}`, captchaProbes[formPrefix] ? 'with probe' : 'NO PROBE');
        })
        .catch(error => {
            console.error("Error fetching CAPTCHA:", error);
            captchaDiv.innerHTML = '<p style="color: var(--color-text-muted); font-size: 0.875rem;">Failed to load captcha</p>';
        });
}

// Check rate limit (5 second cooldown)
function checkRateLimit(formPrefix) {
    const timestamp = Date.now();
    const storageKey = `signup_timestamp_${formPrefix}`;
    const previousTimestamp = localStorage.getItem(storageKey);

    if (previousTimestamp && Number(previousTimestamp) + 5000 > timestamp) {
        return true; // Rate limited
    }

    localStorage.setItem(storageKey, timestamp);
    return false;
}

// Show form state (form visible, messages hidden)
function showFormState(formPrefix) {
    const form = document.getElementById(`${formPrefix}-form`);
    const successMessage = document.getElementById(`${formPrefix}-success-message`);
    const errorMessage = document.getElementById(`${formPrefix}-error-message`);
    const backBtn = document.getElementById(`${formPrefix}-back-btn`);
    const submitBtn = document.getElementById(`${formPrefix}-submit-btn`);
    const loadingBtn = document.getElementById(`${formPrefix}-loading-btn`);
    const captchaContainer = document.getElementById(`${formPrefix}-captcha-container`);

    form.style.display = 'flex';
    successMessage.style.display = 'none';
    errorMessage.style.display = 'none';
    backBtn.style.display = 'none';
    submitBtn.style.display = 'block';
    loadingBtn.style.display = 'none';
    captchaContainer.style.display = 'block';

    // Reset form and regenerate captcha
    form.reset();
    loadCaptcha(formPrefix);
}

// Show success state
function showSuccessState(formPrefix) {
    const form = document.getElementById(`${formPrefix}-form`);
    const successMessage = document.getElementById(`${formPrefix}-success-message`);
    const errorMessage = document.getElementById(`${formPrefix}-error-message`);
    const backBtn = document.getElementById(`${formPrefix}-back-btn`);

    form.style.display = 'none';
    successMessage.style.display = 'block';
    errorMessage.style.display = 'none';
    backBtn.textContent = 'Submit Another';
    backBtn.style.display = 'block';
}

// Show error state
function showErrorState(formPrefix, errorText) {
    const form = document.getElementById(`${formPrefix}-form`);
    const successMessage = document.getElementById(`${formPrefix}-success-message`);
    const errorMessage = document.getElementById(`${formPrefix}-error-message`);
    const errorTextEl = document.getElementById(`${formPrefix}-error-text`);
    const backBtn = document.getElementById(`${formPrefix}-back-btn`);

    form.style.display = 'none';
    successMessage.style.display = 'none';
    errorMessage.style.display = 'block';
    errorTextEl.textContent = errorText || 'Oops! Something went wrong, please try again.';
    backBtn.textContent = 'Try Again';
    backBtn.style.display = 'block';
}

// Show loading state
function showLoadingState(formPrefix) {
    const submitBtn = document.getElementById(`${formPrefix}-submit-btn`);
    const loadingBtn = document.getElementById(`${formPrefix}-loading-btn`);

    submitBtn.style.display = 'none';
    loadingBtn.style.display = 'block';
}

// Hide loading state
function hideLoadingState(formPrefix) {
    const submitBtn = document.getElementById(`${formPrefix}-submit-btn`);
    const loadingBtn = document.getElementById(`${formPrefix}-loading-btn`);

    submitBtn.style.display = 'block';
    loadingBtn.style.display = 'none';
}

// Form submit handler
async function handleFormSubmit(event, formPrefix) {
    event.preventDefault();

    // Check rate limit
    if (checkRateLimit(formPrefix)) {
        showErrorState(formPrefix, 'Too many signups, please try again in a little while.');
        return;
    }

    showLoadingState(formPrefix);

    const form = event.target;
    const formData = new FormData(form);

    // Build data object
    const data = {};
    formData.forEach((value, key) => {
        if (key === 'marketing') {
            data[key] = true;
        } else {
            data[key] = value;
        }
    });

    // Add captcha probe
    data.captchaProbe = captchaProbes[formPrefix];

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            showSuccessState(formPrefix);
        } else {
            const errorData = await response.json();
            let errorMessage = 'Oops! Something went wrong, please try again.';

            if (response.status === 401) {
                errorMessage = 'Domain not whitelisted. Please contact support.';
            } else if (errorData.error && errorData.error.message) {
                errorMessage = errorData.error.message;
            }

            showErrorState(formPrefix, errorMessage);
        }
    } catch (error) {
        console.error('Form submission error:', error);

        if (error.message === 'Failed to fetch') {
            showErrorState(formPrefix, 'Network error. Please check your connection and try again.');
        } else {
            showErrorState(formPrefix, error.message || 'An unexpected error occurred.');
        }

        // Clear rate limit on network error
        localStorage.removeItem(`signup_timestamp_${formPrefix}`);
    }
}

// Initialize forms
function initializeForms() {
    // Early Access Form
    const earlyAccessForm = document.getElementById('early-access-form');
    if (earlyAccessForm) {
        // Generate initial captcha
        loadCaptcha('early-access');

        // Form submit handler
        earlyAccessForm.addEventListener('submit', (e) => handleFormSubmit(e, 'early-access'));

        // Refresh captcha button
        const refreshBtn = document.getElementById('early-access-refresh-captcha');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => loadCaptcha('early-access'));
        }

        // Back button handler
        const backBtn = document.getElementById('early-access-back-btn');
        if (backBtn) {
            backBtn.addEventListener('click', () => showFormState('early-access'));
        }
    }

    // Preorder Form
    const preorderForm = document.getElementById('preorder-form');
    if (preorderForm) {
        // Generate initial captcha
        loadCaptcha('preorder');

        // Form submit handler
        preorderForm.addEventListener('submit', (e) => handleFormSubmit(e, 'preorder'));

        // Refresh captcha button
        const refreshBtn = document.getElementById('preorder-refresh-captcha');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => loadCaptcha('preorder'));
        }

        // Back button handler
        const backBtn = document.getElementById('preorder-back-btn');
        if (backBtn) {
            backBtn.addEventListener('click', () => showFormState('preorder'));
        }
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', initializeForms);

// Log initialization
console.log('%cVC Dating Secrets - Landing Page', 'font-size: 20px; font-weight: bold; color: #ef4444;');
console.log('%cBluefox Integration: Ready with Captcha', 'color: green;');
