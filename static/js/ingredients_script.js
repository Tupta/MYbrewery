document.addEventListener('DOMContentLoaded', function() {
    // Referencja do formularza dodawania składnika
    const addItemForm = document.getElementById('dodaj-element-form');
    
    // Funkcja do obsługi wysyłania formularza dodawania składnika
    addItemForm.addEventListener('submit', async function(event) {
        event.preventDefault(); // ZATRZYMUJEMY domyślne zachowanie formularza (czyli przeładowanie strony)

        const formData = new FormData(this); // Zbierz wszystkie dane z formularza
        
        const itemName = formData.get('nazwa_elementu').trim();
        let itemQuantity = parseInt(formData.get('ilosc'));
        const itemType = formData.get('type'); 
        const itemUnit = formData.get('unit');
        
        // Pobierz wartość klikniętego przycisku submit
        const formAction = event.submitter.value;

        if (!itemName) {
            alert('Nazwa składnika nie może być pusta.');
            return;
        }
        
        // Jeśli akcja to 'subtract', zmień ilość na ujemną
        if (formAction === 'subtract') {
            // Upewnij się, że ilość jest dodatnia, a potem zmień na ujemną
            itemQuantity = -Math.abs(itemQuantity);
        }

        // Utwórz obiekt z danymi do wysłania
        const dataToSend = {
            nazwa_elementu: itemName,
            ilosc: itemQuantity,
            type: itemType,
            unit: itemUnit
        };

        try {
            // Użyjemy action z formularza, czyli /add_item
            const response = await fetch(this.action, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json' // TEN NAGŁÓWEK JEST KLUCZOWY!
                },
                body: JSON.stringify(dataToSend) // KONWERSJA NA JSON!
            });

            // Oczekujemy odpowiedzi w postaci JSON, nawet jeśli jest pusta
            const result = await response.json();

            if (response.ok && result.success) {
                alert('Składnik ' + (formAction === 'add' ? 'dodany/zaktualizowany' : 'zaktualizowany') + ' pomyślnie!');
                window.location.reload(); // Proste odświeżenie strony po pomyślnej operacji
            } else {
                console.error('Błąd podczas operacji na składniku:', result.message);
                alert('Nie udało się wykonać operacji na składniku: ' + result.message);
            }
        } catch (error) {
            console.error('Błąd komunikacji z serwerem:', error);
            alert('Wystąpił błąd podczas komunikacji z serwerem.');
        }
    });

    // Funkcje do przycisków +/- w formularzu dodawania
    window.zwiekszIlosc = function() {
        const iloscInput = document.getElementById('ilosc');
        iloscInput.value = parseInt(iloscInput.value) + 1;
    };

    window.zmniejszIlosc = function() {
        const iloscInput = document.getElementById('ilosc');
        if (parseInt(iloscInput.value) > 0) {
            iloscInput.value = parseInt(iloscInput.value) - 1;
        }
    };
});