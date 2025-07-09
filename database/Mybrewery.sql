create table ingredients (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  type TEXT CHECK (type IN ('slod', 'chmiel', 'drozdze', 'dodatek')),
  quantity NUMERIC, -- np. w gramach, litrach, etc.
  unit TEXT          -- np. 'g', 'kg', 'ml'
);

create table recipe_ingredients (
  id SERIAL PRIMARY KEY,
  recipe_id INTEGER REFERENCES recipes(id) ON DELETE CASCADE,
  ingredient_id INTEGER REFERENCES ingredients(id) ON DELETE CASCADE,
  amount NUMERIC,
  unit TEXT
);

create table brew_sessions (
  id SERIAL PRIMARY KEY,
  recipe_id INTEGER REFERENCES recipes(id) ON DELETE SET NULL,
  brew_date DATE DEFAULT CURRENT_DATE,
  actual_blg NUMERIC,
  notes TEXT
);