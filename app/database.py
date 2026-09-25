import os
from sqlalchemy import Column, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
DATABASE_URL = "sqlite:///" + os.path.join(DATA_DIR, "fitbuddy.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    weight = Column(String(50), nullable=False)
    goal = Column(String(100), nullable=False)
    intensity = Column(String(50), nullable=False)
    original_plan = Column(Text, nullable=True)
    updated_plan = Column(Text, nullable=True)
    nutrition_tip = Column(Text, nullable=True)

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def save_user(db, user_id, username, age, weight, goal, intensity):
    user = db.query(User).filter(User.user_id == user_id).first()
    if user:
        user.username = username
        user.age = age
        user.weight = weight
        user.goal = goal
        user.intensity = intensity
    else:
        user = User(user_id=user_id, username=username, age=age, weight=weight, goal=goal, intensity=intensity)
        db.add(user)
    db.commit(); db.refresh(user); return user

def save_plan(db, user_id, original_plan, nutrition_tip):
    user = get_user(db, user_id)
    if not user: return None
    user.original_plan = original_plan
    user.updated_plan = None
    user.nutrition_tip = nutrition_tip
    db.commit(); db.refresh(user); return user

def update_plan(db, user_id, updated_plan):
    user = get_user(db, user_id)
    if not user: return None
    user.updated_plan = updated_plan
    db.commit(); db.refresh(user); return user

def get_user(db, user_id):
    return db.query(User).filter(User.user_id == user_id).first()

def get_original_plan(db, user_id):
    user = get_user(db, user_id)
    return user.original_plan if user else None

def get_all_users(db):
    return db.query(User).order_by(User.id.desc()).all()

def delete_user(db, user_id):
    user = get_user(db, user_id)
    if not user: return False
    db.delete(user); db.commit(); return True
