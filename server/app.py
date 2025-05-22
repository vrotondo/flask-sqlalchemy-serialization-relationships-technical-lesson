# server/app.py
from flask import Flask, make_response
from flask_migrate import Migrate

from models import *

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

migrate = Migrate(app, db)

db.init_app(app)


@app.route('/')
def index():
    return '<h1>Zoo app</h1>'


@app.route('/animals/<int:id>')
def animal_by_id(id):
    animal = Animal.query.filter(Animal.id == id).first()

    response_body = AnimalSchema().dump(animal)

    return make_response(response_body)


@app.route('/zookeepers/<int:id>')
def zookeeper_by_id(id):
    zookeeper = Zookeeper.query.filter(Zookeeper.id == id).first()

    response_body = ZookeeperSchema().dump(zookeeper)

    return make_response(response_body)


@app.route('/enclosures/<int:id>')
def enclosure_by_id(id):
    enclosure = Enclosure.query.filter(Enclosure.id == id).first()

    response_body = EnclosureSchema().dump(enclosure)

    return make_response(response_body)


if __name__ == '__main__':
    app.run(port=5555, debug=True)