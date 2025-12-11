import uvicorn
from fastapi import FastAPI, HTTPException, Query
from sqlmodel import SQLModel, Field, Session, create_engine, select, col
from typing import Optional, List

# --- KONFIGURASI HYBRID (DB-A & DB-B FULL ACCESS) ---
PORT = 5052
DB_FILE_A = "DB-A.db"
DB_FILE_B = "DB-B.db" 

engine_a = create_engine(f"sqlite:///{DB_FILE_A}")
engine_b = create_engine(f"sqlite:///{DB_FILE_B}")

class TBCarsWeb(SQLModel, table=True):
    __tablename__ = "tbcarsweb"
    __table_args__ = {"extend_existing": True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    carname: str
    carbrand: str
    carmodel: str
    carprice: str
    description: Optional[str] = None

app = FastAPI(title="Hybrid MS (DB-A & DB-B Full Access)")

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine_a)
    SQLModel.metadata.create_all(engine_b)

# --- HELPER MEMILIH DATABASE ---
def get_session(db_name: str):
    if db_name == 'dbb':
        return Session(engine_b)
    return Session(engine_a)

# --- READ & SEARCH ---
@app.get("/cars", response_model=List[TBCarsWeb])
def get_cars(db_name: str = Query("dba")): 
    with get_session(db_name) as session:
        return session.exec(select(TBCarsWeb)).all()

@app.get("/search/{query}")
def search_car(query: str, db_name: str = Query("dba")):
    with get_session(db_name) as session:
        statement = select(TBCarsWeb).where(
            col(TBCarsWeb.carname).contains(query) | 
            col(TBCarsWeb.carbrand).contains(query) | 
            col(TBCarsWeb.carmodel).contains(query)
        )
        return session.exec(statement).all()

@app.get("/cars/{car_id}", response_model=TBCarsWeb)
def get_car(car_id: int, db_name: str = Query("dba")):
    with get_session(db_name) as session:
        car = session.get(TBCarsWeb, car_id)
        if not car: raise HTTPException(404, "Not Found")
        return car

# --- CREATE, UPDATE, DELETE (SEKARANG BISA UNTUK KEDUA DB) ---

@app.post("/cars")
def create_car(car: TBCarsWeb, db_name: str = Query("dba")):
    # Gunakan session sesuai db_name yang dikirim
    with get_session(db_name) as session:
        session.add(car)
        session.commit()
        session.refresh(car)
        return car

@app.put("/cars/{car_id}")
def update_car(car_id: int, car_data: TBCarsWeb, db_name: str = Query("dba")):
    with get_session(db_name) as session:
        car = session.get(TBCarsWeb, car_id)
        if not car: raise HTTPException(404, "Not Found")
        car.sqlmodel_update(car_data.dict(exclude_unset=True))
        session.add(car)
        session.commit()
        session.refresh(car)
        return {"status": "success", "data": car}

@app.delete("/delete/{car_id}")
def delete_car(car_id: int, db_name: str = Query("dba")):
    with get_session(db_name) as session:
        car = session.get(TBCarsWeb, car_id)
        if not car: raise HTTPException(404, "Not Found")
        session.delete(car)
        session.commit()
        return {"status": "success"}

if __name__ == "__main__":
    print(f"Hybrid MS Running on Port {PORT}")
    uvicorn.run("ms2:app", host="0.0.0.0", port=PORT, reload=True)