// Czekamy, aż cały dokument HTML zostanie załadowany
document.addEventListener('DOMContentLoaded', function() {

    // --- FUNKCJE POMOCNICZE DLA UI ---
    
    // Funkcja do dynamicznego tworzenia i wyświetlania komunikatu
    function showMessage(message, isSuccess = true) {
        const messageContainer = document.getElementById('message-container');
        // Usuwamy stary komunikat, jeśli istnieje
        while (messageContainer.firstChild) {
            messageContainer.removeChild(messageContainer.firstChild);
        }
        
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${isSuccess ? 'success' : 'danger'} alert-dismissible fade show`;
        alertDiv.role = 'alert';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        messageContainer.appendChild(alertDiv);
    }
    
    // --- GŁÓWNA LOGIKA APLIKACJI ---

    // Funkcja do pobierania danych z API i dynamicznego renderowania tabel
    async function fetchAndRenderIngredients() {
        try {
            // Pobieramy dane z naszego API Flask
            const response = await fetch('/ingredients_data');
            if (!response.ok) {
                throw new Error('Problem z pobieraniem danych z serwera.');
            }
            const data = await response.json();
            
            // Renderujemy tabele dla każdej kategorii
            renderTable('slody', data.slody, 'Słód');
            renderTable('chmiele', data.chmiele, 'Chmiel');
            renderTable('drozdze', data.drozdze, 'Drożdże');
            renderTable('inne', data.inne, 'Inne');
            
            // Po załadowaniu danych, dodajemy słuchacze zdarzeń do przycisków
            addEventListenersToButtons();

        } catch (error) {
            console.error('Błąd:', error);
            showMessage('Wystąpił błąd podczas ładowania danych.', false);
        }
    }
    
    // Funkcja do generowania HTML tabeli
    function createTableHTML(items) {
        if (items.length === 0) {
            return '<p class="text-muted">Brak składników w tej kategorii.</p>';
        }
    
        let tableHTML = `
            <table class="table table-hover align-middle">
                <thead>
                    <tr>
                        <th scope="col">Nazwa</th>
                        <th scope="col" class="text-center">Ilość</th>
                        <th scope="col">Jednostka</th>
                        <th scope="col">Akcje</th>
                    </tr>
                </thead>
                <tbody>
        `;
    
        items.forEach(item => {
            tableHTML += `
                <tr data-item-id="${item.id}">
                    <td>${item.name}</td>
                    <td class="text-center">
                        <div class="d-flex align-items-center justify-content-center">
                            <button class="btn btn-sm btn-outline-secondary quantity-btn decrease-btn" data-item-id="${item.id}">-</button>
                            <span class="current-quantity mx-2">${item.quantity}</span>
                            <button class="btn btn-sm btn-outline-secondary quantity-btn increase-btn" data-item-id="${item.id}">+</button>
                        </div>
                    </td>
                    <td>${item.unit}</td>
                    <td>
                        <button class="btn btn-danger btn-sm delete-btn" data-item-id="${item.id}">Usuń</button>
                    </td>
                </tr>
            `;
        });
    
        tableHTML += `
                </tbody>
            </table>
        `;
        return tableHTML;
    }
    
    // Funkcja do renderowania tabeli w odpowiednim kontenerze
    function renderTable(containerId, items) {
        const container = document.getElementById(containerId + '-container');
        if (container) {
            container.innerHTML = createTableHTML(items);
        }
    }
    
    // --- OBSŁUGA ZDARZEŃ ---
    
    // Obsługa formularza dodawania składnika
    const addItemForm = document.getElementById('addItemForm');
    addItemForm.addEventListener('submit', async function(event) {
        event.preventDefault(); // Zapobiegamy domyślnej akcji (przeładowaniu strony)
        
        const form = event.target;
        const formData = {
            nazwa_elementu: form.itemName.value,
            ilosc: parseInt(form.itemQuantity.value),
            type: form.itemType.value,
            unit: form.itemUnit.value
        };

        try {
            const response = await fetch('/add_item', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData),
            });
            const result = await response.json();
            
            if (result.success) {
                showMessage(result.message);
                form.reset(); // Czyścimy formularz
                fetchAndRenderIngredients(); // Odświeżamy tabele po sukcesie
            } else {
                showMessage(result.message, false);
            }
        } catch (error) {
            console.error('Błąd:', error);
            showMessage('Wystąpił błąd podczas dodawania składnika.', false);
        }
    });

    // Funkcja do dodawania słuchaczy do przycisków po ich wyrenderowaniu
    function addEventListenersToButtons() {
        const tableContainer = document.querySelector('.container'); // Główny kontener na tabele
        tableContainer.addEventListener('click', async function(event) {
            const target = event.target;

            // Obsługa przycisków +/-
            if (target.classList.contains('quantity-btn')) {
                const itemId = target.dataset.itemId;
                const change = target.classList.contains('increase-btn') ? 1 : -1;

                try {
                    const response = await fetch('/update_item_quantity', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ id: itemId, change: change }),
                    });
                    const result = await response.json();
                    
                    if (result.success) {
                        // Aktualizujemy tylko ilość, bez przeładowania całej strony
                        const quantitySpan = target.parentElement.querySelector('.current-quantity');
                        quantitySpan.textContent = result.new_quantity;
                    } else {
                        showMessage(result.message, false);
                    }
                } catch (error) {
                    console.error('Błąd:', error);
                    showMessage('Wystąpił błąd podczas aktualizacji ilości.', false);
                }
            }

            // Obsługa przycisku "Usuń"
            if (target.classList.contains('delete-btn')) {
                const itemId = target.dataset.itemId;
                if (confirm('Czy na pewno chcesz usunąć ten składnik?')) {
                    try {
                        const response = await fetch('/delete_item', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ id: itemId }),
                        });
                        const result = await response.json();
                        
                        if (result.success) {
                            showMessage('Składnik został usunięty.');
                            // Usuwamy cały wiersz z tabeli
                            const row = target.closest('tr');
                            row.remove();
                        } else {
                            showMessage(result.message, false);
                        }
                    } catch (error) {
                        console.error('Błąd:', error);
                        showMessage('Wystąpił błąd podczas usuwania składnika.', false);
                    }
                }
            }
        });
    }

    // Pierwsze uruchomienie pobierania danych, aby załadować tabele po wejściu na stronę
    fetchAndRenderIngredients();
});
