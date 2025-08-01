from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from flask_migrate import Migrate 


app = Flask(__name__)

# Konfiguracja bazy danych SQLite
# os.path.abspath() i os.path.dirname() aby ścieżka do bazy była zawsze względna do pliku app.py
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'inventory.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Wyłączamy śledzenie modyfikacji, bo nie jest potrzebne

db = SQLAlchemy(app)

migrate = Migrate(app, db)

# Definicja modelu bazy danych dla składników magazynu 
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True) # Nazwa, unikalna
    quantity = db.Column(db.Integer, default=0, nullable=False)   # Ilość, domyślnie 0
    unit = db.Column(db.String(20), default='g') # Jednostka, domyślnie gram
    type = db.Column(db.String(50), default='słód')   # rodzaj do rozbicia tabeli na mniejsze tabele na stronie

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
    """Trasa dla strony Magazynu/Składników. Renderuje szablon."""
    # Dane są teraz pobierane przez JavaScript za pomocą /ingredients_data
    return render_template('ingredients.html')

@app.route('/ingredients_data')
def ingredients_data():
    """Trasa API do zwracania danych składników w JSON, podzielonych na kategorie."""
    all_items = Item.query.order_by(Item.name).all()
    
    # Tworzymy słownik, który będzie przechowywał listy składników dla każdej kategorii
    categorized_items = {
        'slody': [],
        'chmiele': [],
        'drozdze': [],
        'inne': []
    }

    for item in all_items:
        # Konwertujemy obiekt Item na słownik, aby można go było zserializować do JSON
        item_data = {
            'id': item.id,
            'name': item.name,
            'quantity': item.quantity,
            'unit': item.unit,
            'type': item.type
        }
        # Dodajemy element do odpowiedniej kategorii, domyślnie 'inne' jeśli typ nie pasuje
        # Upewnij się, że typy w bazie danych (np. 'slod', 'chmiel') odpowiadają kluczom w categorized_items
        categorized_items.get(item.type, categorized_items['inne']).append(item_data)
    
    return jsonify(categorized_items) # Zwracamy dane jako JSON


@app.route('/add_item', methods=['POST'])
def add_item():
    """Trasa do dodawania/odejmowania elementu z magazynu (obsługa danych JSON z AJAX)."""
    data = request.get_json()
    item_name = data.get('nazwa_elementu').strip()
    item_quantity = int(data.get('ilosc'))
    item_type = data.get('type')
    item_unit = data.get('unit')

    if not item_name:
        return jsonify(success=False, message="Nazwa składnika nie może być pusta."), 400

    existing_item = Item.query.filter_by(name=item_name).first()

    # Uproszczona logika oparta na znaku item_quantity
    if existing_item:
        existing_item.quantity += item_quantity
        if existing_item.quantity < 0:
            existing_item.quantity = 0
        # Jeśli ilość jest dodawana, uaktualniamy też typ i jednostkę
        if item_quantity > 0:
            existing_item.unit = item_unit
            existing_item.type = item_type
        db.session.commit()
        return jsonify(success=True, message="Ilość składnika zaktualizowana.")
    else: # Nowy składnik, dodajemy go tylko jeśli ilość jest dodatnia
        if item_quantity > 0:
            new_item = Item(name=item_name, quantity=item_quantity, type=item_type, unit=item_unit)
            db.session.add(new_item)
            db.session.commit()
            return jsonify(success=True, message="Składnik dodany pomyślnie.")
        else:
            return jsonify(success=False, message="Nie można odjąć ilości, gdy składnik nie istnieje."), 404

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
