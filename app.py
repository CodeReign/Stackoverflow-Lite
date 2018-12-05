#import request to request data and jsonify for returning information

import os
import jwt
import datetime
from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy 
#import uuid #for generating random public id
from werkzeug.security import generate_password_hash, check_password_hash #the passwords should not be in plain text in the db
from functools import wraps #for creating a decorator for the token


app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisissecret'
SQLALCHEMY_ECHO = False
SQLALCHEMY_TRACK_MODIFICATIONS = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/StackOverFlow_Lite'
db = SQLAlchemy(app)
db.create_all()

def token_required(f): 
    @wraps(f)
    def decorated(*args, **kwargs):#this is the inner decorated function that parses the positional arguments and the keyword args
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message' : 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.query.filter_by(username = data['username']).first()
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        return f(current_user, *args, **kwargs)

        return decorated

class User(db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key = True)
    #public_id = db.Column(db.String(50), unique = True) #for hiding the exact number of users. This will be random
    username = db.Column(db.String(80), unique = True)
    email = db.Column(db.String(120), unique = True)
    password = db.Column(db.String(120), unique=True)

    def __init__(self, username, email, password):
        #self.public_id = public_id
        self.username = username
        self.email = email
        self.password = password 

    def __repr__(self):
        return '<User %r>' % self.username

class Question(db.Model):

    __tablename__ = "questions"

    questions_id = db.Column(db.Integer, primary_key = True)
    question = db.Column(db.String, unique = False)
    user_id = db.Column(db.Integer(50))

    def __init__(self, question, user_id):
        self.question = question
        self.user_id = user_id

    def __repr__(self):
        return '<Question %r>' % self.question

class Answer(db.Model):

    __tablename__ = 'answers'

    answers_id = db.Column(db.Integer, primary_key = True)
    answer = db.Column(db.String, unique = False)

    def __init__(self, answer):
        self.answer = answer

    def __repr__(self):
        return '<Answer %r>' % self.answer

#register a user. Question== Should i add the GET method in this endpoint
@app.route('/register', methods = ["POST"])
@token_required
def register(current_user):
    data = request.get_json()

    hashed_password = generate_password_hash(data['password'], method = 'sha256')
    user = User(username=data['name'], email=data['email'], password=hashed_password)
    #now save new user to the database
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'Your account has been successfully created!'})

#login a user
@app.route('/login', methods = ["POST"])
@token_required
def login(current_user):
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        #token = jwt.encode({'user' : auth.username, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
        #return jsonify({'token': token.decode('UTF-8')}) #decode the token to be a regular string
        return make_response('Could not verify!', 401, {'WWW-Authentication' : 'Basic realm = "Login Required"'} )

    user = User.query.filter_by(name =auth.username).first()

    if not user:
        return make_response('Could not verify!', 401, {'WWW-Authentication': 'Basic realm = "Login Required"'})

    if check_password_hash(user.password, auth.password):
        token = jwt.encode({'username': user.username, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30), app.config['SECRET_KEY']})
            
        return jsonify({'token': token.decode('UTF-8')})

    return make_response('Could not verify!', 401, {'WWW-Authentication' : 'Basic realm = "Login Required"'} )

        

#fetch all questions
@app.route('/questions', methods=["GET"])
@token_required
def get_all_questions(current_user, user_id):
    all_questions = Question.query.all()

    output = []

    for question in all_questions:
        question_data = {}
        question_data['id'] = question.id
        question_data['text'] = question.text 
        output.append(question_data)            
        
    return jsonify({'all_questions': output})

#fetch a specific question
@app.route('/questions/<questions_id>', methods = ["GET"])
@token_required
def get_one_question(current_user, questions_id):
    question = Question.query.filter_by(questions_id).first()

    if not question:
        return jsonify({'message' : 'Question not found'})
    
    question_data = {}
    question_data['id'] = question.id
    question_data['text'] = question.text 
    return ''

#user post a question
@app.route('/questions', methods=["POST"])
@token_required
def post_a_question(current_user, user_id):
    data = request.get_json()

    new_question = Question(question=data['text'], user_id= '' ) #i need to use the id of user asking question given at registration
    db.session.add(new_question)
    db.session.commit()


    return jsonify({'message': 'Your question has been posted!'})

#delete a question
@app.route('/questions/<questions_id>', methods=["DELETE"])
@token_required
def delete_a_question(current_user, questions_id):
    question = Question.query.filter_by(id = questions_id, user_id = '')

    if not question:
        reurn jsonify({'message': 'Question not found'})

    db.session.delete(question)
    db.session.commit()

    return jsonify({'message' : 'Question has been deleted'})

#post an answer to a question
@app.route('/questions/<questions_id>/answers', methods=["POST"])
@token_required
def answer_a_question(current_user, questions_id):
    data = request.get_json()
    answer = Question.query.filter_by(id = questions_id)
    answer = Question.(question = data['text'])
    db.session.add(answer)
    db.session.commit()

    return jsonify('message' : 'Your answer has been posted successfully!')

#Mark an answer as accepted or update an answer
@app.route('/questions/<questions_id>/answers/<answers_id>', methods = ["PUT"])
@token_required
def accept_answer(current_user):

    return ''


if __name__ =='__main__':
    
    app.run(debug = True)
