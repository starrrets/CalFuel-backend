from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

DATABASE_URL = "sqlite:///./calorie_tracker.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    tg_id = Column(Integer, unique=True, index=True)
    gender = Column(String)
    age = Column(Integer)
    height = Column(Float)
    weight = Column(Float)
    activity = Column(Float)
    goal_type = Column(String, default="maintain")
    goal_percent = Column(Float, default=0)
    units = Column(String, default="metric")
    daily_norm = Column(Float, default=2000)
    language = Column(String, default="ru")   # ← новое поле для языка бота

class Food(Base):
    __tablename__ = "foods"
    id = Column(Integer, primary_key=True, index=True)
    tg_id = Column(Integer, index=True)
    name = Column(String, index=True)
    calories = Column(Float)
    proteins = Column(Float, default=0)
    fats = Column(Float, default=0)
    carbs = Column(Float, default=0)

class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, index=True)
    tg_id = Column(Integer, index=True)
    food_name = Column(String)
    calories = Column(Float)
    date = Column(Date, default=datetime.date.today)