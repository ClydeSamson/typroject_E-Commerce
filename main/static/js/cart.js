
function updateQuantity(cartId, action) {
    fetch(`/update_cart/${cartId}/${action}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Refresh the page to show updated cart
            location.reload();
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error updating cart:', error);
    });
}

function removeItem(cartId) {
    if (confirm('Are you sure you want to remove this item?')) {
        fetch(`/remove_from_cart/${cartId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Refresh the page to show updated cart
                location.reload();
            } else {
                alert(data.message);
            }
        })
        .catch(error => {
            console.error('Error removing item:', error);
        });
    }
}