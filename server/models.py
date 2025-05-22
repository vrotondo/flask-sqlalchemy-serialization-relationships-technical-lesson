# server/models.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from marshmallow import Schema, fields

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)

db = SQLAlchemy(metadata=metadata)

class Animal(db.Model):
    __tablename__ = 'animals'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    species = db.Column(db.String)

    zookeeper_id = db.Column(db.Integer, db.ForeignKey('zookeepers.id'))
    enclosure_id = db.Column(db.Integer, db.ForeignKey('enclosures.id'))

    enclosure = db.relationship('Enclosure', back_populates='animals')
    zookeeper = db.relationship('Zookeeper', back_populates='animals')

    def __repr__(self):
        return f'<Animal {self.name}, a {self.species}>'

class AnimalSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.String()
    species = fields.String()
    zookeeper = fields.Nested(lambda: ZookeeperSchema(exclude=("animals",)))
    enclosure = fields.Nested(lambda: EnclosureSchema(exclude=("animals",)))

class Zookeeper(db.Model):
    __tablename__ = 'zookeepers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    birthday = db.Column(db.Date)

    animals = db.relationship('Animal', back_populates='zookeeper')

class ZookeeperSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.String()
    birthday = fields.DateTime()
    animals = fields.List(fields.Nested(AnimalSchema(exclude=("zookeeper",))))

class Enclosure(db.Model):
    __tablename__ = 'enclosures'

    id = db.Column(db.Integer, primary_key=True)
    environment = db.Column(db.String)
    open_to_visitors = db.Column(db.Boolean)

    animals = db.relationship('Animal', back_populates='enclosure')

class EnclosureSchema(Schema):
    id = fields.Int(dump_only=True)
    environment = fields.String()
    open_to_visitors = fields.Boolean()
    animals = fields.List(fields.Nested(AnimalSchema(exclude=("enclosure",))))