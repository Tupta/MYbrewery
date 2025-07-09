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