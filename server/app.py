import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db, Restaurant, RestaurantPizza, Pizza

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_URI = os.getenv("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

db.init_app(app)
migrate = Migrate(app, db)

# Create tables and add sample data if they don't exist
with app.app_context():
    db.create_all()
    # Add sample data if database is empty
    if not Pizza.query.first():
        pizza1 = Pizza(name="Cheese", ingredients="Dough, Tomato Sauce, Cheese")
        pizza2 = Pizza(name="Pepperoni", ingredients="Dough, Tomato Sauce, Cheese, Pepperoni")
        restaurant1 = Restaurant(name="Pizza Palace", address="123 Main St")
        restaurant2 = Restaurant(name="Italian Bistro", address="456 Oak Ave")
        db.session.add_all([pizza1, pizza2, restaurant1, restaurant2])
        db.session.commit()

@app.route("/")
def index():
    return "<h1>Pizza Restaurant API</h1>"

@app.route("/restaurants", methods=["GET"])
def get_restaurants():
    restaurants = Restaurant.query.all()
    return jsonify([{
        "id": r.id,
        "name": r.name,
        "address": r.address
    } for r in restaurants])

@app.route("/restaurants/<int:id>", methods=["GET"])
def get_restaurant(id):
    restaurant = db.session.get(Restaurant, id)
    if restaurant:
        # Get associated pizzas through restaurant_pizzas
        restaurant_pizzas = [{
            "id": rp.pizza.id,
            "name": rp.pizza.name,
            "ingredients": rp.pizza.ingredients
        } for rp in restaurant.restaurant_pizzas]
        return jsonify({
            "id": restaurant.id,
            "name": restaurant.name,
            "address": restaurant.address,
            "restaurant_pizzas": restaurant_pizzas  # Changed from "pizzas" to "restaurant_pizzas"
        })
    return jsonify({"error": "Restaurant not found"}), 404

@app.route("/restaurants/<int:id>", methods=["DELETE"])
def delete_restaurant(id):
    restaurant = db.session.get(Restaurant, id)
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404
    
    # Delete associated restaurant_pizzas first
    RestaurantPizza.query.filter_by(restaurant_id=id).delete()
    db.session.delete(restaurant)
    db.session.commit()
    return '', 204

@app.route("/pizzas", methods=["GET"])
def get_pizzas():
    pizzas = Pizza.query.all()
    return jsonify([{
        "id": p.id,
        "name": p.name,
        "ingredients": p.ingredients
    } for p in pizzas])

@app.route("/restaurant_pizzas", methods=["GET", "POST"])
def handle_restaurant_pizzas():
    if request.method == "GET":
        # Return all restaurant_pizza relationships
        restaurant_pizzas = RestaurantPizza.query.all()
        return jsonify([{
            "id": rp.id,
            "price": rp.price,
            "pizza_id": rp.pizza_id,
            "restaurant_id": rp.restaurant_id,
            "pizza": {
                "id": rp.pizza.id,
                "name": rp.pizza.name,
                "ingredients": rp.pizza.ingredients
            },
            "restaurant": {
                "id": rp.restaurant.id,
                "name": rp.restaurant.name,
                "address": rp.restaurant.address
            }
        } for rp in restaurant_pizzas])
    
    elif request.method == "POST":
        # Create new restaurant_pizza
        data = request.get_json()

        required_fields = ["price", "pizza_id", "restaurant_id"]
        if not all(field in data for field in required_fields):
            return jsonify({"errors": ["validation errors"]}), 400

        try:
            price = int(data["price"])
            if not 1 <= price <= 30:
                return jsonify({"errors": ["validation errors"]}), 400

            pizza = db.session.get(Pizza, data["pizza_id"])
            restaurant = db.session.get(Restaurant, data["restaurant_id"])

            if not pizza or not restaurant:
                errors = []
                if not pizza:
                    errors.append("Pizza not found")
                if not restaurant:
                    errors.append("Restaurant not found")
                return jsonify({"errors": errors}), 404

            restaurant_pizza = RestaurantPizza(
                price=price,
                pizza_id=data["pizza_id"],
                restaurant_id=data["restaurant_id"]
            )

            db.session.add(restaurant_pizza)
            db.session.commit()

            return jsonify({
                "id": restaurant_pizza.id,
                "price": restaurant_pizza.price,
                "pizza_id": pizza.id,
                "restaurant_id": restaurant.id,
                "pizza": {
                    "id": pizza.id,
                    "name": pizza.name,
                    "ingredients": pizza.ingredients
                },
                "restaurant": {
                    "id": restaurant.id,
                    "name": restaurant.name,
                    "address": restaurant.address
                }
            }), 201

        except ValueError:
            return jsonify({"errors": ["validation errors"]}), 400
        except Exception as e:
            return jsonify({"errors": [str(e)]}), 400

if __name__ == "__main__":
    app.run(port=5555, debug=True)