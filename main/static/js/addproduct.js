// static/js/add-product.js
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Dropzone
    Dropzone.autoDiscover = false;
    
    new Dropzone("#productImages", {
        url: "/upload-image",
        acceptedFiles: "image/*",
        addRemoveLinks: true,
        maxFiles: 5,
        init: function() {
            this.on("success", function(file, response) {
                // Add the uploaded file to the form data
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'product_images[]';
                input.value = response.filename;
                document.getElementById('addProductForm').appendChild(input);
            });
        }
    });

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
});

// Step navigation functions
function nextStep(step) {
    // Hide current step
    document.querySelectorAll('.step-content').forEach(content => {
        content.classList.add('d-none');
    });
    
    // Show next step
    document.getElementById(`step${step}`).classList.remove('d-none');
    
    // Update indicators
    document.querySelectorAll('.step').forEach(stepEl => {
        stepEl.classList.remove('active');
    });
    document.getElementById(`step${step}-indicator`).classList.add('active');
    
    // Mark previous steps as completed
    for(let i = 1; i < step; i++) {
        document.getElementById(`step${i}-indicator`).classList.add('completed');
    }
}

function prevStep(step) {
    document.querySelectorAll('.step-content').forEach(content => {
        content.classList.add('d-none');
    });
    document.getElementById(`step${step}`).classList.remove('d-none');
    
    // Update indicators
    document.querySelectorAll('.step').forEach(stepEl => {
        stepEl.classList.remove('active');
    });
    document.getElementById(`step${step}-indicator`).classList.add('active');
}

function toggleColor(element) {
    element.classList.toggle('selected');
    updateColorInputs();
}

function updateColorInputs() {
    const selectedColors = Array.from(document.querySelectorAll('.color-circle.selected'))
        .map(circle => getComputedStyle(circle).backgroundColor);
    
    // Remove existing color inputs
    document.querySelectorAll('input[name="colors[]"]').forEach(input => input.remove());
    
    // Add new color inputs
    selectedColors.forEach(color => {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'colors[]';
        input.value = color;
        document.getElementById('addProductForm').appendChild(input);
    });
}