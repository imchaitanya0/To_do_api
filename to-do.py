from flask import Flask,request,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager,jwt_required,get_jwt_identity,create_access_token
from datetime import timedelta,datetime
app=Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///to_do.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['JWT_SECRET_KEY']='tobeconfidential'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

db=SQLAlchemy(app)
jwt=JWTManager(app)

class User(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    user_name=db.Column(db.String(25),nullable=False,unique=True)
    password=db.Column(db.String(25),nullable=False)

class Task(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    title=db.Column(db.String(80),nullable=False)
    description=db.Column(db.String(100))
    done=db.Column(db.Boolean,default=False)
    priority=db.Column(db.Integer,default=1)
    due_date=db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)


with app.app_context():
    db.create_all()

@app.route('/register',methods=['POST'])
def registration():
    user_name=request.json.get("user_name",None)
    password=request.json.get('password',None)

    if not user_name or not password:
        return jsonify({'msg':'request not accepted'}),400
    if User.query.filter_by(user_name=user_name).first():
        return jsonify({'msg':'user_name is already existed'}),400
    new_user=User(user_name=user_name,password=password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'msg':'you are registered'})

@app.route('/login',methods=['POST'])
def login():
    user_name=request.json.get('user_name',None)
    password=request.json.get('password',None)

    user=User.query.filter_by(user_name=user_name,password=password).first()

    if not user:
        return jsonify({'msg':'username or password is incorrect'}),400
    
    access_token=create_access_token(identity=user_name)

    return jsonify(access_token=access_token)

@app.route('/tasks',methods=['GET'])
@jwt_required()

def get_tasks():
    curr_user=get_jwt_identity()

    user=User.query.filter_by(user_name=curr_user).first()
    tasks=Task.query.filter_by(user_id=user.id).all()
    return jsonify([{
        'id':task.id,
        'title':task.title,
        'description':task.description,
        'done': task.done,
        'priority': task.priority,
        'due_date': task.due_date.isoformat() if task.due_date else None
    }for task in tasks]),200

@app.route('/tasks',methods=['POST'])
@jwt_required()
def add_tasks():
    curr_user=get_jwt_identity()

    user=User.query.filter_by(user_name=curr_user).first()
    title = request.json.get('title')
    description = request.json.get('description')
    priority = request.json.get('priority', 1)
    due_date = request.json.get('due_date')

    if not title:
        return jsonify({'msg':'title must be included'}),400
    
    due_date=datetime.fromisoformat(due_date) if due_date else None
    new_task=Task(title=title,description=description,priority=priority,due_date=due_date,user_id=user.id)
    db.session.add(new_task)
    db.session.commit()
    return jsonify({
        'id':new_task.id,
        'title':new_task.title,
        'description':new_task.description,
        'done':new_task.done,
        'priority':new_task.priority,
        'due_date':new_task.due_date.isoformat() if new_task.due_date else None
    }),200

@app.route('/tasks/<int:task_id>',methods=['PUT'])
@jwt_required()
def update_tasks(task_id):
    curr_user=get_jwt_identity()
    user=User.query.filter_by(user_name=curr_user).first()
    task=Task.query.filter_by(id=task_id,user_id=user.id).first()

    if not task:
        return jsonify({'msg':'not found'}),404
    
    task.title=request.json.get('title',task.title)
    task.description=request.json.get('description',task.description)
    task.done=request.json.get('done',task.done)
    task.priority=request.json.get('priority',task.priority)
    due_date=request.json.get('due_date')
    task.due_date=datetime.fromisoformat(due_date) if due_date else task.due_date
    db.session.commit()

    return jsonify({
        'id':task.id,
        'title':task.title,
        'description':task.description,
        'done':task.done,
        'priority':task.priority,
        'due_date':task.due_date.isoformat() if task.due_date else None
    }),200

@app.route('/tasks/<int:task_id>',methods=['DELETE'])
@jwt_required()
def delete_tasks(task_id):
    curr_user=get_jwt_identity()
    user=User.query.filter_by(user_name=curr_user).first()
    task=Task.query.filter_by(id=task_id,user_id=user.id).first()

    if not task:
        return jsonify({'msg':'not found'}),404
    
    db.session.delete(task)
    db.session.commit()
    return jsonify({'msg':'deleted successfully'}),200

if __name__=='__main__':
    app.run(debug=True)