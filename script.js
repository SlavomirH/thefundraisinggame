// Bluefox Configuration
const BLUEFOX_SUBSCRIBER_LIST_URL = 'https://api.bluefox.email/v1/subscriber-lists/6960f7e0cfa080251b241006';

// Scroll to preorder form
function scrollToForm() {
    document.getElementById('preorder').scrollIntoView({ behavior: 'smooth' });
}

// Bluefox API Integration
async function subscribeToBluefox(email) {
    try {
        const response = await fetch(BLUEFOX_SUBSCRIBER_LIST_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Failed to subscribe');
        }

        return {
            success: true,
            message: 'Successfully subscribed to the list!'
        };
    } catch (error) {
        console.error('Bluefox subscription error:', error);
        return {
            success: false,
            message: error.message || 'Failed to subscribe. Please try again.'
        };
    }
}

// Show message helper
function showMessage(elementId, message, type) {
    const messageElement = document.getElementById(elementId);
    messageElement.textContent = message;
    messageElement.className = `form-message ${type}`;
    messageElement.style.display = 'block';

    // Hide message after 5 seconds
    setTimeout(() => {
        messageElement.style.display = 'none';
    }, 5000);
}

// Hero Form Handler
const heroForm = document.getElementById('hero-form');
heroForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const emailInput = document.getElementById('hero-email');
    const submitButton = heroForm.querySelector('button[type="submit"]');
    const originalButtonText = submitButton.textContent;

    // Disable button and show loading state
    submitButton.disabled = true;
    submitButton.textContent = '...';

    const result = await subscribeToBluefox(emailInput.value);

    // Show message
    showMessage('hero-message', result.message, result.success ? 'success' : 'error');

    // Reset form if successful
    if (result.success) {
        emailInput.value = '';
    }

    // Re-enable button
    submitButton.disabled = false;
    submitButton.textContent = originalButtonText;
});

// Preorder Form Handler
const preorderForm = document.getElementById('preorder-form');
preorderForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const emailInput = document.getElementById('preorder-email');
    const submitButton = preorderForm.querySelector('button[type="submit"]');
    const originalButtonText = submitButton.textContent;

    // Disable button and show loading state
    submitButton.disabled = true;
    submitButton.textContent = 'Joining the VIP List...';

    const result = await subscribeToBluefox(emailInput.value);

    // Show message
    const message = result.success
        ? "Success! You've been added to our exclusive preorder list. We'll notify you when the book is ready!"
        : "Oops! Something went wrong. Please try again or contact us directly.";
    showMessage('preorder-message', message, result.success ? 'success' : 'error');

    // Reset form if successful
    if (result.success) {
        emailInput.value = '';
        document.getElementById('marketing-consent').checked = false;
    }

    // Re-enable button
    submitButton.disabled = false;
    submitButton.textContent = originalButtonText;
});

// Log initialization
console.log('%cVC Dating Secrets - Landing Page', 'font-size: 20px; font-weight: bold; color: #ef4444;');
console.log('%cBluefox Integration: Ready', 'color: green;');
