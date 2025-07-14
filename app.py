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

# Definicja modelu bazy danych dla składników magazynu (Twoje Items)
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True) # Nazwa, unikalna
    quantity = db.Column(db.Integer, default=0, nullable=False)   # Ilość, domyślnie 0
    # Możesz dodać pole na jednostkę, np. unit = db.Column(db.String(20), default='g')

    def __repr__(self):
        # Reprezentacja obiektu, przydatna do debugowania
        return f'<Item {self.name}: {self.quantity}>'

# Definicja modelu dla przepisów
class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    instructions = db.Column(db.Text) # Dodatkowe pole na opis/instrukcje
    
    # Definiowanie relacji z RecipeIngredient (tabela pośrednia)
    # 'RecipeIngredient' to nazwa klasy, backref='recipe' tworzy dostęp z RecipeIngredient do Recipe
    # lazy='dynamic' pozwala na filtrowanie i sortowanie powiązanych obiektów
    ingredients_association = db.relationship('RecipeIngredient', backref='recipe', lazy='dynamic')

    def __repr__(self):
        return f'<Recipe {self.name}>'

# Definicja modelu dla składników w przepisie (tabela łącząca wiele do wielu)
class RecipeIngredient(db.Model):
    # Klucze główne składają się z dwóch kluczy obcych
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False) # Ilość danego składnika w tym przepisie
    unit = db.Column(db.String(20), default='g') # Jednostka (np. "g", "ml", "szt")

    # Dodatkowe relacje, aby łatwo dostać się do obiektu Recipe i Item z RecipeIngredient
    # 'item' pozwala na dostęp do obiektu Item z RecipeIngredient (np. recipe_ingredient.item.name)
    item = db.relationship('Item', backref='recipe_associations') 

    def __repr__(self):
        return f'<RecipeIngredient RecipeID: {self.recipe_id}, ItemID: {self.item_id}, Qty: {self.quantity} {self.unit}>'


# --- TRASY FLASKA ---

@app.route('/')
def index():
    """Trasa dla strony głównej."""
    return render_template('index.html')

@app.route('/ingredients')
def ingredients():
    """Trasa dla strony Magazynu/Składników. Wyświetla listę wszystkich składników."""
    # Pobieramy wszystkie elementy z bazy danych, posortowane alfabetycznie
    items = Item.query.order_by(Item.name).all()
    # Przekazujemy listę elementów do szablonu ingredients.html (zamiast inventory.html)
    return render_template('ingredients.html', items=items)

@app.route('/add_item', methods=['POST'])
def add_item():
    """Trasa do dodawania nowego elementu do magazynu (obsługa formularza POST)."""
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

    # Po dodaniu/aktualizacji przekierowujemy użytkownika z powrotem na stronę składników
    return redirect(url_for('ingredients'))

@app.route('/update_item_quantity', methods=['POST'])
def update_item_quantity():
    """Trasa do aktualizacji ilości elementu (przez AJAX)."""
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

@app.route('/delete_item', methods=['POST'])
def delete_item():
    """Trasa do usuwania elementu (przez AJAX)."""
    data = request.get_json()
    item_id = data.get('id')

    item = Item.query.get(item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
        return jsonify(success=True)
    return jsonify(success=False, message="Item not found"), 404

# Trasa dla strony przepisów
@app.route('/recipes')
def recipes():
    """Trasa dla strony przepisów."""
    # Tutaj w przyszłości będziesz pobierać przepisy z bazy danych
    return render_template('recipes.html')

# Trasa dla strony statystyk
@app.route('/stats')
def stats():
    """Trasa dla strony statystyk."""
    return render_template('stats.html')

# Trasa dla strony warzenia
@app.route('/brewing')
def brewing():
    """Trasa dla strony warzenia."""
    return render_template('brewing.html')

if __name__ == '__main__':
    # Tworzymy tabele w bazie danych (tylko jeśli jeszcze nie istnieją)
    with app.app_context():
        db.create_all()
    app.run(debug=True)

