from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./calorie_tracker.db")

# Railway Postgres gives a URL starting with "postgres://", SQLAlchemy needs "postgresql://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
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
    calories = Column(Float)          # total kcal (fixed) OR kcal per 100 g
    per100g = Column(Boolean, default=False)  # True = calories are per 100 g

class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, index=True)
    tg_id = Column(Integer, index=True)
    food_name = Column(String)
    calories = Column(Float)
    date = Column(Date, default=datetime.date.today)