from flask import Flask, render_template


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ingredients')
def ingredients():
    return render_template('ingredients.html') # Będziesz musiał stworzyć ten plik HTML

@app.route('/recipes')
def recipes():
    return render_template('recipes.html') # I ten

@app.route('/stats')
def stats():
    return render_template('stats.html') # I ten

@app.route('/brewing')
def brewing():
    return render_template('brewing.html') # I ten

if __name__ == '__main__':
    app.run(debug=True) # Uruchomienie aplikacji w trybie debugowania
    
    
############################################################################################
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import os # Importujemy moduł os do pracy ze ścieżkami plików

app = Flask(__name__)

# Konfiguracja bazy danych SQLite
# Użyj os.path.abspath() i os.path.dirname() aby ścieżka do bazy była zawsze względna do pliku app.py
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'inventory.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Wyłączamy śledzenie modyfikacji, bo nie jest potrzebne

db = SQLAlchemy(app)

# Definicja modelu bazy danych dla składników magazynu
# Każda klasa Pythona, która dziedziczy po db.Model, staje się tabelą w bazie danych
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True) # Nazwa, unikalna
    quantity = db.Column(db.Integer, default=0, nullable=False)   # Ilość, domyślnie 0

    def __repr__(self):
        # Reprezentacja obiektu, przydatna do debugowania
        return f'<Item {self.name}: {self.quantity}>'

# --- TRASY FLASKA ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/inventory')
def inventory():
    # Pobieramy wszystkie elementy z bazy danych, posortowane alfabetycznie
    items = Item.query.order_by(Item.name).all()
    # Przekazujemy listę elementów do szablonu inventory.html
    return render_template('inventory.html', items=items)

# Trasa do dodawania nowego elementu do magazynu (obsługa formularza POST)
@app.route('/add_item', methods=['POST'])
def add_item():
    if request.method == 'POST':
        item_name = request.form['nazwa_elementu'].strip() # Usuwamy białe znaki
        item_quantity = int(request.form['ilosc'])

        # Sprawdzamy, czy element o takiej nazwie już istnieje
        existing_item = Item.query.filter_by(name=item_name).first()
        if existing_item:
            # Jeśli istnieje, zwiększamy jego ilość
            existing_item.quantity += item_quantity
            db.session.commit()
        else:
            # Jeśli nie istnieje, tworzymy nowy element
            new_item = Item(name=item_name, quantity=item_quantity)
            db.session.add(new_item)
            db.session.commit() # Zatwierdzamy zmiany w bazie danych

    # Po dodaniu/aktualizacji przekierowujemy użytkownika z powrotem na stronę magazynu
    return redirect(url_for('inventory'))

# Trasa do aktualizacji ilości elementu (przez AJAX)
@app.route('/update_item_quantity', methods=['POST'])
def update_item_quantity():
    data = request.get_json() # Pobieramy dane JSON wysłane przez JavaScript
    item_id = data.get('id')
    change = data.get('change') # Zmiana: +1 lub -1

    item = Item.query.get(item_id) # Znajdujemy element po ID
    if item:
        item.quantity += change
        # Upewniamy się, że ilość nie spadnie poniżej zera
        if item.quantity < 0:
            item.quantity = 0
        db.session.commit()
        return jsonify(success=True, new_quantity=item.quantity) # Zwracamy odpowiedź JSON
    return jsonify(success=False, message="Item not found"), 404

# Trasa do usuwania elementu (przez AJAX)
@app.route('/delete_item', methods=['POST'])
def delete_item():
    data = request.get_json()
    item_id = data.get('id')

    item = Item.query.get(item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
        return jsonify(success=True)
    return jsonify(success=False, message="Item not found"), 404


# ---- Tutaj dodaj pozostałe trasy dla innych stron, jeśli będą -----
@app.route('/ingredients')
def ingredients():
    return render_template('ingredients.html')

@app.route('/recipes')
def recipes():
    return render_template('recipes.html')

@app.route('/stats')
def stats():
    return render_template('stats.html')

@app.route('/brewing')
def brewing():
    return render_template('brewing.html')
# ------------------------------------------------------------------

if __name__ == '__main__':
    # Tworzymy tabele w bazie danych (tylko jeśli jeszcze nie istnieją)
    with app.app_context():
        db.create_all()
    app.run(debug=True)