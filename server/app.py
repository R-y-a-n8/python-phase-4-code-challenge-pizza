import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db, Restaurant, RestaurantPizza, Pizza

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_URI = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

db.init_app(app)
migrate = Migrate(app, db)

@app.route("/")
def index():
    return "<h1>Pizza Restaurant API</h1>"

@app.route("/restaurants", methods=["GET"])
def get_restaurants():
    restaurants = Restaurant.query.all()
    return jsonify([restaurant.to_dict() for restaurant in restaurants])

@app.route("/restaurants/<int:id>", methods=["GET"])
def get_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if restaurant:
        return jsonify(restaurant.to_dict(include_pizzas=True))
    return jsonify({"error": "Restaurant not found"}), 404

@app.route("/restaurants/<int:id>", methods=["DELETE"])
def delete_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404
    
    db.session.delete(restaurant)
    db.session.commit()
    return '', 204

@app.route("/pizzas", methods=["GET"])
def get_pizzas():
    pizzas = Pizza.query.all()
    return jsonify([pizza.to_dict() for pizza in pizzas])

@app.route("/restaurant_pizzas", methods=["POST"])
def create_restaurant_pizza():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ["price", "pizza_id", "restaurant_id"]
    if not all(field in data for field in required_fields):
        return jsonify({"errors": ["Missing required fields"]}), 400
    
    try:
        # Validate price
        price = int(data["price"])
        if not 1 <= price <= 30:
            return jsonify({"errors": ["Price must be between 1 and 30"]}), 400
        
        # Check if pizza and restaurant exist
        pizza = Pizza.query.get(data["pizza_id"])
        restaurant = Restaurant.query.get(data["restaurant_id"])
        
        if not pizza or not restaurant:
            errors = []
            if not pizza:
                errors.append("Pizza not found")
            if not restaurant:
                errors.append("Restaurant not found")
            return jsonify({"errors": errors}), 404
        
        # Create new RestaurantPizza
        restaurant_pizza = RestaurantPizza(
            price=price,
            pizza_id=data["pizza_id"],
            restaurant_id=data["restaurant_id"]
        )
        
        db.session.add(restaurant_pizza)
        db.session.commit()
        
        # Return the created RestaurantPizza with associated data
        return jsonify({
            "id": restaurant_pizza.id,
            "price": restaurant_pizza.price,
            "pizza": pizza.to_dict(),
            "restaurant": restaurant.to_dict()
        }), 201
    
    except ValueError:
        return jsonify({"errors": ["Invalid price value"]}), 400
    except Exception as e:
        return jsonify({"errors": ["Validation error"]}), 400

if __name__ == "__main__":
    app.run(port=5555, debug=True)