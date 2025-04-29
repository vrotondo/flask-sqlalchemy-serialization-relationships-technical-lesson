# Technical Lesson: Serialization and Relationships

## Introduction

We saw in a prior lesson how to use Marshmallow to convert a
SQLAlchemy model into a dictionary. In this lesson, we'll serialize models that
have relationships. We'll use serialization rules to include or exclude
attributes to avoid issues with nested models and infinite recursion.

## Scenario

You have been hired as a backend engineer at a zoo management company. The existing 
backend API allows users to retrieve information about animals, enclosures, and 
zookeepers. However, users increasingly request detailed data that shows relationships 
— for example, which animals are in a specific enclosure, or which zookeeper cares for 
which animals.

Unfortunately, the current API returns only simple flat data, without showing any relational 
connections. Moreover, attempts to serialize relationships have caused performance issues, 
including infinite recursion errors.

You have been tasked with refactoring the serialization logic using Marshmallow to properly 
serialize models and their relationships, ensuring users can retrieve structured data without 
errors.

## Tools & Resources

- [GitHub Repo](https://github.com/learn-co-curriculum/flask-sqlalchemy-serialization-relationships-technical-lesson)
- [Marshmallow: Nesting](https://marshmallow.readthedocs.io/en/stable/nesting.html)

## Setup

This lesson is a code-along, so fork and clone the repo.

Run `pipenv install` to install the dependencies and `pipenv shell` to enter
your virtual environment before running your code.

```console
$ pipenv install
$ pipenv shell
```

Change into the `server` directory and configure the `FLASK_APP` and
`FLASK_RUN_PORT` environment variables:

```console
$ cd server
$ export FLASK_APP=app.py
$ export FLASK_RUN_PORT=5555
```

## Instructions

### Task 1: Define the Problem

In real-world applications, data often has complex relationships — one-to-many, 
many-to-many, and so forth. Simply serializing each model individually is not 
enough: users expect a complete picture that includes related data. However, 
naively serializing these relationships can cause:

* Recursion errors (infinite loops between objects)
* Performance bottlenecks (overly deep nested data)
* Difficulty maintaining API responses (users receiving too much or too little data)

The problem is how to serialize models and their relationships cleanly using Marshmallow, 
without creating recursion or overwhelming API consumers with unnecessary nesting.

### Task 2: Determine the Design

* Schemas for Each Model: 
  * Create a Marshmallow Schema for each model (Animal, Zookeeper, Enclosure).
* Nested Fields for Relationships: 
  * Use fields.Nested and fields.List(fields.Nested) to include relationships cleanly.
* Use lambda for Forward References: 
  * To avoid circular dependency issues when nesting, define nested schemas lazily with lambda: SchemaName.
* Control Nesting with exclude:
  * To prevent infinite recursion, use the exclude parameter to omit nested fields that would otherwise cause loops.
* Update endpoints to use marshmallow schemas.

### Task 3: Develop, Test, and Refine the Code

#### Step 1: Create and Seed the Database

```bash
flask db init
flask db migrate -m 'initial migration'
flask db upgrade head
python seed.py
```

Updating the code to serialize the data will not impact the database schema; we
won't need to touch Flask-Migrate again in this lesson.

#### Step 2: Set Up Schemas

Navigate to `models.py` and you'll notice the import at the top:

```py
# models.py
from marshmallow import Schema, fields
```

Our models are already defined, but we need to add a Schema for each model.

```python
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

# Create AnimalSchema, inheritting from Schema
class AnimalSchema(Schema):
    pass

class Zookeeper(db.Model):
    __tablename__ = 'zookeepers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    birthday = db.Column(db.Date)

    animals = db.relationship('Animal', back_populates='zookeeper')

# Create ZookeeperSchema, inheritting from Schema
class ZookeeperSchema(Schema):
    pass

class Enclosure(db.Model):
    __tablename__ = 'enclosures'

    id = db.Column(db.Integer, primary_key=True)
    environment = db.Column(db.String)
    open_to_visitors = db.Column(db.Boolean)

    animals = db.relationship('Animal', back_populates='enclosure')

# Create EnclosureSchema, inheritting from Schema
class EnclosureSchema(Schema):
    pass
```

#### Step 3: Add Columns to Schemas

Next, recall how to serialize database columns. We need to add these to each Schema.

For the `AnimalSchema`, we'll add `id`, `name`, and `species`.

```python
class AnimalSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.String()
    species = fields.String()
```

For the `ZookeeperSchema`, we'll add `id`, `name`, and `birthday`.

```python
class ZookeeperSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()
    birthday = fields.String()
    birthday = fields.DateTime()
```

And finally, for `EnclosureSchema`, we'll add `id`, `environment`, and `open_to_visitors`.

```python
class EnclosureSchema(Schema):
    id = fields.Int(dump_only=True)
    environment = fields.String()
    open_to_visitors = fields.Boolean()
```

#### Step 4: Serialize Relationships in Schemas

##### `Nested` fields in Marshmallow

To use relationships with serializtion in marshmallow, we can use the `Nested` field.

For the `AnimalSchema`, we'll add both zookeeper and enclosure.

```python
class AnimalSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.String()
    species = fields.String()

    zookeeper = fields.Nested(ZookeeperSchema)
    enclosure = fields.Nested(EnclosureSchema)
```

For the `ZookeeperSchema`, we'll add animals as a list.

```python
class ZookeeperSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()
    birthday = fields.String()
    birthday = fields.DateTime()

    animals = fields.List(fields.Nested(AnimalSchema))
```

And finally, for `EnclosureSchema`, we'll also add animals as a list.

```python
class EnclosureSchema(Schema):
    id = fields.Int(dump_only=True)
    environment = fields.String()
    open_to_visitors = fields.Boolean()

    animals = fields.List(fields.Nested(AnimalSchema))
```

Now, if you try hopping into `flask shell`, you should see an error:

```bash
NameError: name 'ZookeeperSchema' is not defined
```

This error comes up because we used ZookeeperSchema (and EnclosureSchema) in
the AnimalSchema before we defined them. Now, all Schemas use each other, so 
there is no order we can define them in to avoid this. Instead, we need to use 
a `lambda` for these definitions, which Marshmallow allows. Let's fix our 
`AnimalSchema`:

```python
class AnimalSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.String()
    species = fields.String()

    zookeeper = fields.Nested(lambda: ZookeeperSchema)
    enclosure = fields.Nested(lambda: EnclosureSchema)
```

Now, you can run `flask shell` and should no longer see that error immediately.

```bash
flask shell
>>> from models import *
>>> a1 = Animal.query.first()
>>> AnimalSchema().dump(a1)
.....
.....
....
RecursionError: maximum recursion depth exceeded in comparison
```

Uh oh, we have another error! Recursion depth is a common issue we run into when
serialization with relationships. What's happening here? You can imagine our program
trying to call something like:

```
animal
  attributes
  zookeeper
  enclosure
```

then:

```
animal
  attributes
  zookeeper
    attributes
    animals
  enclosure
    attributes
    animals
```

then:

```
animal
  attributes
  zookeeper
    attributes
    animals
      attributes
      zookeper
      enclosure
  enclosure
    attributes
    animals
      attributes
      zookeeper
      enclosure
```

And on and on. It will continue nesting animals, zookeepers, and enclosures unless
we do somethine about it.

##### Recursion Depth

Sometimes, the process of serialization can get very complex, especially if the
data we're working with has many layers of nested structures or relationships.

Recursion depth refers to how deeply we traverse the nested relationships within
data structures when we serialize them. If the structures are very deeply
nested, a complete serialization process can require a lot of memory and
computational resources, which can slow down the program or even cause it to
crash.

For example, imagine you have a data structure representing a family tree, with
each person having parents, grandparents, and so on. If we try to serialize this
structure and we don't set a limit on the recursion depth, the program might
keep going deeper and deeper into the family tree, creating more and more data
to process, until it runs out of memory or crashes.

To avoid this problem, we can exclude or include fields when pulling relationships.

##### `exclude` and `include`

We saw these in the previous serialize lesson, to specify if we want to leave out
any fields or only include a couple of columns. This option is crucial when 
serializing relationships however. Let's update our Schemas to avoid recursion.

Starting with AnimalSchema, we need to exclude animals from both zookeeper and
enclosure fields. Note that if you exclude the comma after animals, you will see an
error that exclude requires a list of strings as an argument.

```py
class AnimalSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.String()
    species = fields.String()
    zookeeper = fields.Nested(lambda: ZookeeperSchema(exclude=("animals",)))
    enclosure = fields.Nested(lambda: EnclosureSchema(exclude=("animals",)))
```

Next, lets exclude zookeeper from animals in Zookeeper Schema:

```py
class ZookeeperSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()
    birthday = fields.DateTime()
    animals = fields.List(fields.Nested(AnimalSchema(exclude=("zookeeper", "enclosure"))))
```

And finally, update EnclosureSchema:

```py
class EnclosureSchema(Schema):
    id = fields.Int(dump_only=True)
    environment = fields.String()
    open_to_visitors = fields.Boolean()
    animals = fields.List(fields.Nested(AnimalSchema(exclude=("enclosure",))))
```

Save your changes and navigate back to the Flask shell. Let's try converting our
record to a dictionary again (your result will differ):

```bash
>>> from models import *
>>> z1 = Zookeeper.query.first()
>>> ZookeeperSchema().dump(z1)
# => {'id': 1, 'name': 'Christine Johnson', 'birthday': '2000-12-30', 'animals': [{'id': 3, 'name': 'Crystal', 'species': 'Ostrich', 'enclosure': {'id': 1, 'environment': 'Cage', 'open_to_visitors': False}}, {'id': 137, 'name': 'Larry', 'species': 'Tiger', 'enclosure': {'id': 16, 'environment': 'Cage', 'open_to_visitors': False}}, {'id': 143, 'name': 'Amy', 'species': 'Bear', 'enclosure': {'id': 18, 'environment': 'Trees', 'open_to_visitors': False}}, {'id': 150, 'name': 'Mitchell', 'species': 'Elephant', 'enclosure': {'id': 7, 'environment': 'Cave', 'open_to_visitors': False}}, {'id': 171, 'name': 'Lee', 'species': 'Ostrich', 'enclosure': {'id': 16, 'environment': 'Cage', 'open_to_visitors': False}}, {'id': 187, 'name': 'Julia', 'species': 'Snake', 'enclosure': {'id': 24, 'environment': 'Cage', 'open_to_visitors': True}}, {'id': 190, 'name': 'Sierra', 'species': 'Bear', 'enclosure': {'id': 18, 'environment': 'Trees', 'open_to_visitors': False}}]}
```

Just like that, we have a dictionary representation of a Python SQLAlchemy
object. This will be much easier for other applications to use!

#### Step 5: Test Relationships in Flask Shell

Let's head back to the Flask shell and give these a shot:

```bash
$ from models import *
$ z1 = Zookeeper.query.first()
$ z1
# => <Zookeeper 1>
$ ZookeeperSchema().dump(z1)
# => {'id': 1, 'name': 'Christine Johnson', 'birthday': '2000-12-30', 'animals': [{'id': 3, 'name': 'Crystal', 'species': 'Ostrich', 'enclosure': {'id': 1, 'environment': 'Cage', 'open_to_visitors': False}}, {'id': 137, 'name': 'Larry', 'species': 'Tiger', 'enclosure': {'id': 16, 'environment': 'Cage', 'open_to_visitors': False}}, {'id': 143, 'name': 'Amy', 'species': 'Bear', 'enclosure': {'id': 18, 'environment': 'Trees', 'open_to_visitors': False}}, {'id': 150, 'name': 'Mitchell', 'species': 'Elephant', 'enclosure': {'id': 7, 'environment': 'Cave', 'open_to_visitors': False}}, {'id': 171, 'name': 'Lee', 'species': 'Ostrich', 'enclosure': {'id': 16, 'environment': 'Cage', 'open_to_visitors': False}}, {'id': 187, 'name': 'Julia', 'species': 'Snake', 'enclosure': {'id': 24, 'environment': 'Cage', 'open_to_visitors': True}}, {'id': 190, 'name': 'Sierra', 'species': 'Bear', 'enclosure': {'id': 18, 'environment': 'Trees', 'open_to_visitors': False}}]}
$ ZookeeperSchema(only=("name",)).dump(z1)
# => {'name': 'Christine Johnson'}
$ a1 = Animal.query.first()
$ a1
# => <Animal Melanie, a Snake>
$ AnimalSchema().dump(a1)
# => {'id': 1, 'name': 'Melanie', 'species': 'Snake', 'zookeeper': {'id': 16, 'name': 'Tanya Brown', 'birthday': '1984-12-19'}, 'enclosure': {'id': 22, 'environment': 'Cage', 'open_to_visitors': True}}
```

> Note, the a1 print out is different from z1 since the Animal class has a defined custom `__repr__` method while Zookeeper does not.

#### Step 6: Update Endpoints in `app.py`

Finally, we can update our endpoints in `app.py` to use our serialization.

Delete or comment out the response_body code for each route, and add a line to set `response_body`
for each route to use the `dump` method.

```python
@app.route('/animals/<int:id>')
def animal_by_id(id):
    animal = Animal.query.filter(Animal.id == id).first()
    # response_body = f''
    # response_body += f'<ul>ID: {animal.id}</ul>'
    # response_body += f'<ul>Name: {animal.name}</ul>'
    # response_body += f'<ul>Species: {animal.species}</ul>'
    # response_body += f'<ul>Zookeeper: {animal.zookeeper.name}</ul>'
    # response_body += f'<ul>Enclosure: {animal.enclosure.environment}</ul>'

    response_body = AnimalSchema().dump(animal)

    return make_response(response_body)


@app.route('/zookeepers/<int:id>')
def zookeeper_by_id(id):
    zookeeper = Zookeeper.query.filter(Zookeeper.id == id).first()
    # response_body = f''
    # response_body += f'<ul>ID: {zookeeper.id}</ul>'
    # response_body += f'<ul>Name: {zookeeper.name}</ul>'
    # response_body += f'<ul>Birthday: {zookeeper.birthday}</ul>'

    # for animal in zookeeper.animals:
    #     response_body += f'<ul>Animal: {animal.name}</ul>'

    response_body = ZookeeperSchema().dump(zookeeper)

    return make_response(response_body)


@app.route('/enclosures/<int:id>')
def enclosure_by_id(id):
    enclosure = Enclosure.query.filter(Enclosure.id == id).first()
    # response_body = f''
    # response_body += f'<ul>ID: {enclosure.id}</ul>'
    # response_body += f'<ul>Environment: {enclosure.environment}</ul>'
    # response_body += f'<ul>Open to Visitors: {enclosure.open_to_visitors}</ul>'

    # for animal in enclosure.animals:
    #     response_body += f'<ul>Animal: {animal.name}</ul>'

    response_body = EnclosureSchema().dump(enclosure)

    return make_response(response_body)
```

Use `flask run` to look at each endpoint in the browser.

#### Step 7: Verify your Code

Solution Code:

```py
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
    name = fields.Str()
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
```

```py
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
```

#### Step 8: Commit and Push Git History

* Commit and push your code:

```bash
git add .
git commit -m "final solution"
git push
```

* If you created a separate feature branch, remember to open a PR on main and merge.

### Task 4: Document and Maintain

Best Practice documentation steps:
* Add comments to the code to explain purpose and logic, clarifying intent and functionality of your code to other developers.
* Update README text to reflect the functionality of the application following https://makeareadme.com. 
  * Add screenshot of completed work included in Markdown in README.
* Delete any stale branches on GitHub
* Remove unnecessary/commented out code
* If needed, update git ignore to remove sensitive data

## Conclusion

SQLAlchemy-Serializer is a helpful tool that helps programmers turn complex
database information into simpler, portable formats. It makes it easier to share
this data with other programs or systems. For instance, if you have a list of
friends on Facebook, SQLAlchemy-Serializer can help you turn that data into a
format that another website or app can understand.

However, when we serialize data, it can sometimes become too complex and cause
problems. To prevent this, programmers need to set limits on how deep the data
can go. For example, imagine a list of animals with each animal having
offspring, and each of those offspring having their own offspring. The list
could go on forever! SQLAlchemy-Serializer helps programmers manage this issue
by providing tools such as `serialize_rules` and the `rules` and `only`
arguments to the `to_dict()` method to handle these kinds of situations.

By using SQLAlchemy-Serializer, programmers can create faster and more efficient
programs that can easily share data with others.

## Considerations

### Recursion Management
Always guard against infinite loops by selectively excluding fields in nested 
serialization.

### Selective Serialization: 
Only serialize the fields that matter for the client request, avoiding unnecessary 
payload size.

### Performance Impacts: 
Serializing deeply nested or large collections can slow down API responses 
significantly — use pagination, which we'll discuss in a later course, or 
filtering if needed.

### Future-Proofing: 
New models or relationships may require updates to existing schemas. Design 
your schema relationships to be modular and easily extendable.

### Security Concerns: 
If sensitive fields exist (like user passwords in other apps), ensure they 
are excluded from serialization with dump_only or exclude.

