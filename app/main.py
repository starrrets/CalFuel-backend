from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
import datetime
from sqlalchemy.orm import Session
from .database import SessionLocal, User, Food, Log, engine, Base

app = FastAPI(title="Calorie Tracker Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ProfileCreate(BaseModel):
    tg_id: int
    gender: str
    age: int
    height: float
    weight: float
    activity: float
    goal_type: str
    goal_percent: float = 0
    units: str = "metric"


class FoodCreate(BaseModel):
    tg_id: int
    name: str
    calories: float
    per100g: bool = False


class LogCreate(BaseModel):
    tg_id: int
    food_name: str
    calories: float


def calculate_daily_norm(gender: str, age: int, height: float, weight: float,
                         activity: float, goal_type: str, goal_percent: float) -> float:
    if gender == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    tdee = bmr * activity
    if goal_type == "deficit":
        return tdee * (1 - goal_percent / 100)
    elif goal_type == "surplus":
        return tdee * (1 + goal_percent / 100)
    return tdee


@app.get("/api/profile/{tg_id}")
def get_profile(tg_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == tg_id).first()
    if not user:
        return {"daily_norm": 2000, "units": "metric"}
    return {
        "daily_norm": user.daily_norm,
        "units": user.units or "metric",
        "height": user.height,
        "weight": user.weight,
        "gender": user.gender,
        "age": user.age,
        "activity": user.activity,
        "goal_type": user.goal_type,
        "goal_percent": user.goal_percent,
        "language": user.language or "ru",
    }


@app.post("/api/profile")
def save_profile(profile: ProfileCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == profile.tg_id).first()
    if not user:
        user = User(tg_id=profile.tg_id)
        db.add(user)

    user.gender = profile.gender
    user.age = profile.age
    user.height = profile.height
    user.weight = profile.weight
    user.activity = profile.activity
    user.goal_type = profile.goal_type
    user.goal_percent = profile.goal_percent
    user.units = profile.units
    user.daily_norm = calculate_daily_norm(
        profile.gender, profile.age, profile.height,
        profile.weight, profile.activity, profile.goal_type, profile.goal_percent,
    )

    db.commit()
    db.refresh(user)
    return {"daily_norm": user.daily_norm, "units": user.units}


@app.get("/api/foods/{tg_id}")
def get_foods(tg_id: int, db: Session = Depends(get_db)):
    foods = db.query(Food).filter(Food.tg_id == tg_id).all()
    return [
        {"id": f.id, "name": f.name, "calories": f.calories, "per100g": bool(f.per100g)}
        for f in foods
    ]


@app.post("/api/foods")
def add_food(food: FoodCreate, db: Session = Depends(get_db)):
    new_food = Food(
        tg_id=food.tg_id,
        name=food.name,
        calories=food.calories,
        per100g=food.per100g,
    )
    db.add(new_food)
    db.commit()
    db.refresh(new_food)
    return {"id": new_food.id}


@app.delete("/api/foods/{food_id}")
def delete_food(food_id: int, db: Session = Depends(get_db)):
    food = db.query(Food).filter(Food.id == food_id).first()
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")
    db.delete(food)
    db.commit()
    return {"message": "Food deleted"}


@app.post("/api/log")
def add_log(log: LogCreate, db: Session = Depends(get_db)):
    new_log = Log(
        tg_id=log.tg_id,
        food_name=log.food_name,
        calories=log.calories,
        date=datetime.date.today(),
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return {"id": new_log.id, "message": "Log added"}


@app.get("/api/logs/today/{tg_id}")
def get_today_logs(tg_id: int, db: Session = Depends(get_db)):
    today = datetime.date.today()
    logs = db.query(Log).filter(Log.tg_id == tg_id, Log.date == today).all()
    total = sum(l.calories for l in logs)
    return {
        "total_today": total,
        "logs": [{"id": l.id, "food_name": l.food_name, "calories": l.calories} for l in logs],
    }


@app.get("/api/logs/day/{tg_id}/{date_str}")
def get_day_logs(tg_id: int, date_str: str, db: Session = Depends(get_db)):
    try:
        day = datetime.date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format, use YYYY-MM-DD")
    logs = db.query(Log).filter(Log.tg_id == tg_id, Log.date == day).all()
    total = sum(l.calories for l in logs)
    return {
        "date": date_str,
        "total": total,
        "logs": [{"id": l.id, "food_name": l.food_name, "calories": l.calories} for l in logs],
    }


@app.get("/api/history/{tg_id}")
def get_history(tg_id: int, db: Session = Depends(get_db)):
    cutoff = datetime.date.today() - datetime.timedelta(days=29)
    logs = db.query(Log).filter(Log.tg_id == tg_id, Log.date >= cutoff).all()
    result: Dict[str, float] = {}
    for log in logs:
        date_str = log.date.isoformat()
        result[date_str] = result.get(date_str, 0) + log.calories
    return result


@app.delete("/api/log/{log_id}")
def delete_log(log_id: int, db: Session = Depends(get_db)):
    log = db.query(Log).filter(Log.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    db.delete(log)
    db.commit()
    return {"message": "Log deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
