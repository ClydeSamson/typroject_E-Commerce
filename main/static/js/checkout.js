
        document.getElementById('deliveryForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = {
                name: document.getElementById('name').value,
                street: document.getElementById('street').value,
                landmark: document.getElementById('landmark').value,
                city: document.getElementById('city').value,
                state: document.getElementById('state').value,
                pincode: document.getElementById('pincode').value,
                phone: document.getElementById('phone').value
            };

            // Send data to server
            fetch('/save_address', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    const fullAddress = `
                        <strong>${formData.name}</strong><br>
                        ${formData.street}<br>
                        ${formData.landmark ? formData.landmark + '<br>' : ''}
                        ${formData.city}, ${formData.state} - ${formData.pincode}<br>
                        Phone: ${formData.phone}
                    `;
                    
                    document.getElementById('addressValue').innerHTML = fullAddress;
                    document.getElementById('addressForm').classList.remove('active');
                    document.getElementById('addressCompleted').classList.add('active');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('There was an error saving your address. Please try again.');
            });
        });

        function editAddress() {
            document.getElementById('addressForm').classList.add('active');
            document.getElementById('addressCompleted').classList.remove('active');
        }
