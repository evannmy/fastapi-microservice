import uvicorn
from fastapi import FastAPI, Depends, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel, Field, Session, create_engine, select, col
from typing import Optional, List

# ==========================================
# 1. KONFIGURASI DATABASE (SQLModel)
# ==========================================

# Definisi Model Tabel (Car)
class Car(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    carname: str
    carbrand: str
    carmodel: str
    carprice: str
    description: str

# Setup SQLite Database
# File database.db akan otomatis dibuat saat aplikasi dijalankan
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# echo=False agar terminal tidak penuh dengan log SQL
engine = create_engine(sqlite_url, echo=False)

def create_db_and_tables():
    """Membuat tabel otomatis jika belum ada."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Dependency untuk mendapatkan sesi database."""
    with Session(engine) as session:
        yield session

# ==========================================
# 2. KONFIGURASI APP & TEMPLATES
# ==========================================

app = FastAPI(title="Car CRUDS FastAPI")

# Menyiapkan folder templates untuk file HTML
# Pastikan Anda sudah membuat folder bernama 'templates' di samping file ini
templates = Jinja2Templates(directory="templates")

# Event yang dijalankan saat aplikasi mulai (Startup) untuk buat DB
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# ==========================================
# 3. ROUTE FRONTEND (CRUDS LOGIC)
# ==========================================

# --- A. READ (HOME PAGE) ---
@app.get("/", response_class=HTMLResponse)
def read_view(request: Request, session: Session = Depends(get_session)):
    # Ambil semua data mobil dari DB
    cars = session.exec(select(Car)).all()
    # Kirim ke index.html
    return templates.TemplateResponse("index.html", {"request": request, "rows": cars})


# --- B. CREATE (TAMBAH DATA) ---
@app.get("/create", response_class=HTMLResponse)
def create_view(request: Request):
    # Tampilkan form tambah data
    return templates.TemplateResponse("create.html", {"request": request})

@app.post("/create")
def create_action(
    carname: str = Form(...), 
    carbrand: str = Form(...),
    carmodel: str = Form(...), 
    carprice: str = Form(...),
    description: str = Form(...), 
    session: Session = Depends(get_session)
):
    # Simpan data baru ke DB
    new_car = Car(
        carname=carname, 
        carbrand=carbrand, 
        carmodel=carmodel, 
        carprice=carprice, 
        description=description
    )
    session.add(new_car)
    session.commit()
    # Redirect kembali ke Home
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


# --- C. UPDATE (EDIT DATA) ---

# 1. Halaman List Update (Menampilkan daftar untuk dipilih)
@app.get("/update", response_class=HTMLResponse)
def update_list_view(request: Request, session: Session = Depends(get_session)):
    cars = session.exec(select(Car)).all()
    return templates.TemplateResponse("update_list.html", {"request": request, "rows": cars})

# 2. Halaman Form Edit (Formulir Pengisian data spesifik)
@app.get("/update/{car_id}", response_class=HTMLResponse)
def update_form_view(request: Request, car_id: int, session: Session = Depends(get_session)):
    # Cari mobil berdasarkan ID
    car = session.get(Car, car_id)
    if not car:
        # Jika tidak ketemu, kembalikan ke list update
        return RedirectResponse(url="/update", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("form_update.html", {"request": request, "row": car})

# 3. Aksi Simpan Perubahan (POST)
@app.post("/update/save")
def update_action(
    id: int = Form(...), 
    carname: str = Form(...), 
    carbrand: str = Form(...),
    carmodel: str = Form(...), 
    carprice: str = Form(...),
    description: str = Form(...), 
    session: Session = Depends(get_session)
):
    # Cari data lama di DB
    car_db = session.get(Car, id)
    if car_db:
        # Update field dengan data baru
        car_db.carname = carname
        car_db.carbrand = carbrand
        car_db.carmodel = carmodel
        car_db.carprice = carprice
        car_db.description = description
        
        session.add(car_db)
        session.commit()
        
    return RedirectResponse(url="/update", status_code=status.HTTP_303_SEE_OTHER)


# --- D. DELETE (HAPUS DATA) ---

# 1. Halaman List Delete
@app.get("/delete", response_class=HTMLResponse)
def delete_list_view(request: Request, session: Session = Depends(get_session)):
    cars = session.exec(select(Car)).all()
    return templates.TemplateResponse("delete_list.html", {"request": request, "rows": cars})

# 2. Aksi Hapus (Dipanggil via Link/Button)
@app.get("/delete/action/{car_id}")
def delete_action(car_id: int, session: Session = Depends(get_session)):
    car = session.get(Car, car_id)
    if car:
        session.delete(car)
        session.commit()
    return RedirectResponse(url="/delete", status_code=status.HTTP_303_SEE_OTHER)


# --- E. SEARCH (CARI DATA) ---

# 1. Tampilan Awal Search (Form Kosong)
@app.get("/search", response_class=HTMLResponse)
def search_view(request: Request):
    return templates.TemplateResponse("search.html", {"request": request, "rows": [], "keyword": ""})

# 2. Hasil Pencarian (POST dari Form)
@app.post("/search", response_class=HTMLResponse)
def search_action(
    request: Request, 
    keyword: str = Form(...), 
    session: Session = Depends(get_session)
):
    # Query SQL LIKE / CONTAINS
    # Mencari kecocokan di Nama, Brand, atau Model
    statement = select(Car).where(
        col(Car.carname).contains(keyword) | 
        col(Car.carbrand).contains(keyword) | 
        col(Car.carmodel).contains(keyword)
    )
    results = session.exec(statement).all()
    
    return templates.TemplateResponse("search.html", {
        "request": request, 
        "rows": results, 
        "keyword": keyword
    })


# ==========================================
# 4. ENTRY POINT
# ==========================================
if __name__ == "__main__":
    # Menjalankan server uvicorn
    # Akses di browser: http://localhost:8000
    print("Server berjalan di http://localhost:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)