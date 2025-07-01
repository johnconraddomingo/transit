// Function to toggle metric description visibility
function toggleDescription(iconElement) {
    // Find the description popup within the same metric card
    const descriptionPopup = iconElement.nextElementSibling;

    // Toggle the show-description class
    descriptionPopup.classList.toggle('show-description');

    // Update aria-label based on current state
    if (descriptionPopup.classList.contains('show-description')) {
        iconElement.setAttribute('aria-label', 'Hide description');
    } else {
        iconElement.setAttribute('aria-label', 'Show description');
    }

    // Close other open descriptions
    const allDescriptions = document.querySelectorAll('.metric-description-popup.show-description');
    allDescriptions.forEach(popup => {
        if (popup !== descriptionPopup) {
            popup.classList.remove('show-description');
            popup.previousElementSibling.setAttribute('aria-label', 'Show description');
        }
    });
}

// Close descriptions when clicking outside
document.addEventListener('click', function (event) {
    if (!event.target.classList.contains('metric-info-icon')) {
        const openDescriptions = document.querySelectorAll('.metric-description-popup.show-description');
        openDescriptions.forEach(popup => {
            popup.classList.remove('show-description');
            popup.previousElementSibling.setAttribute('aria-label', 'Show description');
        });
    }
}, true);
