import uvicorn
from fastapi import FastAPI, HTTPException
from sqlmodel import SQLModel, Field, Session, create_engine, select, col
from typing import Optional, List

# --- KONFIGURASI UNTUK MS3 ---
PORT = 5053         # BEDA PORT
DB_FILE = "DB-B.db" # BEDA DATABASE (SITE B)

sqlite_url = f"sqlite:///{DB_FILE}"
engine = create_engine(sqlite_url)

# ... (SISANYA SAMA PERSIS DENGAN KODE MS1/MS2 DI ATAS) ...
# Salin class TBCarsWeb sampai baris if __name__ == "__main__" dari ms1.py

class TBCarsWeb(SQLModel, table=True):
    __tablename__ = "tbcarsweb"
    __table_args__ = {"extend_existing": True} 
    
    id: Optional[int] = Field(default=None, primary_key=True)
    carname: str
    carbrand: str
    carmodel: str
    carprice: str
    description: Optional[str] = None

app = FastAPI(title="MS3 Service")

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.get("/cars", response_model=List[TBCarsWeb])
def get_cars():
    with Session(engine) as session:
        return session.exec(select(TBCarsWeb)).all()

@app.post("/cars", response_model=TBCarsWeb)
def create_car(car: TBCarsWeb):
    with Session(engine) as session:
        session.add(car)
        session.commit()
        session.refresh(car)
        return car

@app.get("/cars/{car_id}", response_model=TBCarsWeb)
def get_car(car_id: int):
    with Session(engine) as session:
        car = session.get(TBCarsWeb, car_id)
        if not car: raise HTTPException(404, "Not Found")
        return car

@app.put("/cars/{car_id}")
def update_car(car_id: int, car_data: TBCarsWeb):
    with Session(engine) as session:
        car = session.get(TBCarsWeb, car_id)
        if not car: raise HTTPException(404, "Not Found")
        car.sqlmodel_update(car_data.dict(exclude_unset=True))
        session.add(car)
        session.commit()
        session.refresh(car)
        return {"status": "success", "data": car}

@app.delete("/delete/{car_id}")
def delete_car(car_id: int):
    with Session(engine) as session:
        car = session.get(TBCarsWeb, car_id)
        if not car: raise HTTPException(404, "Not Found")
        session.delete(car)
        session.commit()
        return {"status": "success"}

@app.get("/search/{query}")
def search_car(query: str):
    with Session(engine) as session:
        statement = select(TBCarsWeb).where(
            col(TBCarsWeb.carname).contains(query) | 
            col(TBCarsWeb.carbrand).contains(query) | 
            col(TBCarsWeb.carmodel).contains(query)
        )
        return session.exec(statement).all()

if __name__ == "__main__":
    print(f"MS3 Running on Port {PORT} connected to {DB_FILE}")
    uvicorn.run("ms3:app", host="0.0.0.0", port=PORT, reload=True)