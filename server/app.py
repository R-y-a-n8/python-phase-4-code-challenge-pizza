#!/usr/bin/env python3
import os
from flask import Flask, request, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restful import Api, Resource
from models import db, Restaurant, RestaurantPizza, Pizza

# Set up the path for the SQLite database
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_URI = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

# Initialize database and migrate
db.init_app(app)
migrate = Migrate(app, db)

api = Api(app)

# Home route
@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

# GET /restaurants
@app.route("/restaurants", methods=["GET"])
def get_restaurants():
    restaurants = Restaurant.query.all()
    return jsonify([restaurant.to_dict() for restaurant in restaurants])

# GET /restaurants/<int:id>
@app.route("/restaurants/<int:id>", methods=["GET"])
def get_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if restaurant:
        return jsonify({
            "id": restaurant.id,
            "name": restaurant.name,
            "address": restaurant.address,
            "restaurant_pizzas": [
                {
                    "id": rp.id,
                    "price": rp.price,
                    "pizza": rp.pizza.to_dict(),
                    "restaurant": rp.restaurant.to_dict()
                } for rp in restaurant.restaurant_pizzas
            ]
        })
    else:
        return jsonify({"error": "Restaurant not found"}), 404

# DELETE /restaurants/<int:id>
@app.route("/restaurants/<int:id>", methods=["DELETE"])
def delete_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if restaurant:
        db.session.delete(restaurant)
        db.session.commit()
        return '', 204  # Empty body on successful delete
    else:
        return jsonify({"error": "Restaurant not found"}), 404

# GET /pizzas
@app.route("/pizzas", methods=["GET"])
def get_pizzas():
    pizzas = Pizza.query.all()
    return jsonify([pizza.to_dict() for pizza in pizzas])

# POST /restaurant_pizzas
@app.route("/restaurant_pizzas", methods=["POST"])
def create_restaurant_pizza():
    data = request.get_json()
    print("Received request data:", data)  # Log the incoming request data

    # Validate that the expected fields are present
    if not all(key in data for key in ["price", "pizza_id", "restaurant_id"]):
        return jsonify({"error": "Missing required fields: 'price', 'pizza_id', and 'restaurant_id'"}), 400

    price = data.get("price")
    pizza_id = data.get("pizza_id")
    restaurant_id = data.get("restaurant_id")

    # Validate price
    if not (1 <= price <= 30):
        return jsonify({"errors": ["Price must be between 1 and 30."]}), 400

    # Fetch the pizza and restaurant
    pizza = Pizza.query.get(pizza_id)
    restaurant = Restaurant.query.get(restaurant_id)

    print(f"Found pizza: {pizza}, Found restaurant: {restaurant}")  # Log if pizza and restaurant are found

    # Check if pizza and restaurant exist
    if not pizza or not restaurant:
        error_message = []
        if not pizza:
            error_message.append("Pizza not found.")
        if not restaurant:
            error_message.append("Restaurant not found.")
        return jsonify({"errors": error_message}), 404

    # Create the RestaurantPizza record
    restaurant_pizza = RestaurantPizza(price=price, pizza_id=pizza_id, restaurant_id=restaurant_id)
    db.session.add(restaurant_pizza)
    db.session.commit()

    print(f"Created restaurant_pizza: {restaurant_pizza}")  # Log the created restaurant_pizza

    # Return the newly created restaurant_pizza object
    return jsonify(restaurant_pizza.to_dict()), 201


# GET /restaurants/<int:id>/pizzas
@app.route("/restaurants/<int:id>/pizzas", methods=["GET"])
def get_pizzas_for_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if restaurant:
        restaurant_pizzas = RestaurantPizza.query.filter_by(restaurant_id=id).all()
        return jsonify({
            "restaurant_id": restaurant.id,
            "restaurant_name": restaurant.name,
            "pizzas": [
                {
                    "id": rp.pizza.id,
                    "name": rp.pizza.name,
                    "price": rp.price
                } for rp in restaurant_pizzas
            ]
        })
    else:
        return jsonify({"error": "Restaurant not found"}), 404

if __name__ == "__main__":
    app.run(port=5555, debug=True)
