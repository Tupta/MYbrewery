document.addEventListener('DOMContentLoaded', function() {
    const listaMagazynu = document.getElementById('lista-magazynu');

    // Obsługa zwiększania/zmniejszania ilości
    listaMagazynu.addEventListener('click', async function(event) {
        let button = event.target;
        if (button.classList.contains('increase-btn') || button.classList.contains('decrease-btn')) {
            const itemRow = button.closest('.item-row');
            const itemId = itemRow.dataset.itemId;
            const currentQuantitySpan = itemRow.querySelector('.current-quantity');
            let currentQuantity = parseInt(currentQuantitySpan.textContent);
            let change = 0;

            if (button.classList.contains('increase-btn')) {
                change = 1;
            } else if (button.classList.contains('decrease-btn')) {
                change = -1;
            }

            // Zapobiegnij spadnięciu poniżej zera na froncie, jeśli zmieniamy na -1
            if (currentQuantity + change < 0) {
                return; // Nie rób nic, jeśli próba zmniejszenia poniżej 0
            }

            try {
                const response = await fetch('/update_item_quantity', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ id: itemId, change: change })
                });
                const data = await response.json();

                if (data.success) {
                    currentQuantitySpan.textContent = data.new_quantity; // Aktualizuj ilość na stronie
                } else {
                    console.error('Błąd aktualizacji ilości:', data.message);
                    alert('Nie udało się zaktualizować ilości: ' + data.message);
                }
            } catch (error) {
                console.error('Błąd komunikacji z serwerem:', error);
                alert('Wystąpił błąd podczas komunikacji z serwerem.');
            }
        }

        // Obsługa usuwania elementu
        if (button.classList.contains('delete-btn')) {
            const itemRow = button.closest('.item-row');
            const itemId = itemRow.dataset.itemId;

            if (confirm('Czy na pewno chcesz usunąć ten składnik z magazynu?')) {
                try {
                    const response = await fetch('/delete_item', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ id: itemId })
                    });
                    const data = await response.json();

                    if (data.success) {
                        itemRow.remove(); // Usuń cały wiersz elementu z DOM
                    } else {
                        console.error('Błąd usuwania elementu:', data.message);
                        alert('Nie udało się usunąć elementu: ' + data.message);
                    }
                } catch (error) {
                    console.error('Błąd komunikacji z serwerem podczas usuwania:', error);
                    alert('Wystąpił błąd podczas usuwania elementu.');
                }
            }
        }
    });

    // Obsługa dynamicznego dodawania elementu po wysłaniu formularza
    // Przechwytywanie submit formularza, aby użyć AJAX
    const addItemForm = document.getElementById('add-item-form');
    if (addItemForm) {
        addItemForm.addEventListener('submit', async function(event) {
            event.preventDefault(); // Zapobiegamy domyślnej akcji wysłania formularza (przeładowania strony)

            const formData = new FormData(this); // Zbierz dane z formularza
            const itemName = formData.get('nazwa_elementu').trim();
            const itemQuantity = parseInt(formData.get('ilosc'));

            if (!itemName) {
                alert('Nazwa składnika nie może być pusta.');
                return;
            }

            try {
                // Wysyłamy dane do Flask'a tradycyjnie, ale potem odświeżamy listę dynamicznie
                const response = await fetch(this.action, {
                    method: 'POST',
                    body: formData // FormData jest automatycznie obsługiwana przez Flask
                });

                // Sprawdzamy czy odpowiedź jest OK, wtedy możemy odświeżyć listę.
                // Flask redirectuje nas na /inventory, więc tutaj po prostu przeładujemy stronę.
                // Aby to było prawdziwie dynamiczne, Flask musiałby zwracać JSON z nowym elementem
                // i wtedy JavaScript by go dodawał. Na razie zostawimy proste przekierowanie.
                if (response.redirected) {
                    window.location.href = response.url; // Przekieruj przeglądarkę
                } else {
                    // W bardziej zaawansowanym AJAX, tutaj byśmy parsowali JSON i dodawali element
                    // dynamicznie do listy bez przeładowania.
                    alert('Składnik dodany lub zaktualizowany! Odśwież stronę, aby zobaczyć zmiany.');
                    // LUB: Pobierz i wyświetl całą listę na nowo, bez przeładowania.
                    // const updatedItemsResponse = await fetch('/inventory');
                    // const updatedItemsHtml = await updatedItemsResponse.text();
                    // listaMagazynu.innerHTML = updatedItemsHtml; // To wymagałoby, aby /inventory zwracało tylko fragment HTML
                }
                this.reset(); // Wyczyść formularz po wysłaniu
            } catch (error) {
                console.error('Błąd podczas dodawania składnika:', error);
                alert('Wystąpił błąd podczas dodawania składnika.');
            }
        });
    }
});