import uvicorn
import requests
from typing import Optional
from fastapi import FastAPI, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="APPX Frontend - Microservices Client")
templates = Jinja2Templates(directory="templates")

# Konfigurasi Alamat Microservice
SERVERS = {
    "MS1": "http://localhost:5051", 
    "MS2": "http://localhost:5052", 
    "MS3": "http://localhost:5053"  
}

# --- 1. DASHBOARD UTAMA (Dengan Pengecekan Status) ---
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    # Dictionary untuk menyimpan status: True (Online) atau False (Offline)
    server_status = {}
    
    # Loop cek setiap server
    for ms_name, ms_url in SERVERS.items():
        try:
            # Ping dengan timeout cepat (0.5 detik) agar dashboard tidak loading lama
            resp = requests.get(f"{ms_url}/cars", timeout=0.5)
            if resp.status_code == 200:
                server_status[ms_name] = True
            else:
                server_status[ms_name] = False
        except:
            server_status[ms_name] = False

    # Kirim data 'server_status' ke HTML
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "status": server_status
    })

# --- 2. MENU MICROSERVICE ---
@app.get("/menu/{ms}", response_class=HTMLResponse)
def menu_view(request: Request, ms: str):
    status_server = "Offline"
    count_data = 0
    base_url = SERVERS.get(ms)
    
    # Proteksi tambahan: Jika diakses paksa lewat URL saat offline
    is_online = False
    
    if base_url:
        try:
            resp = requests.get(f"{base_url}/cars", timeout=1)
            if resp.status_code == 200:
                status_server = "Online"
                count_data = len(resp.json())
                is_online = True
        except:
            status_server = "Offline"
    
    # Jika offline, jangan tampilkan menu, tapi kembali ke dashboard atau tampilkan error
    if not is_online:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "status": {"MS1": False, "MS2": False, "MS3": False}, # Dummy status agar tidak error render
            "error_message": f"Maaf, Server {ms} sedang OFFLINE dan tidak dapat diakses."
        })
            
    return templates.TemplateResponse("menu_microservice.html", {
        "request": request, 
        "ms": ms, 
        "status": status_server,
        "count": count_data
    })

# --- 3. OPERASI CRUDS ---

# READ
@app.get("/read/{ms}", response_class=HTMLResponse)
def read_view(request: Request, ms: str):
    base_url = SERVERS.get(ms)
    rows = []
    error_msg = None
    if base_url:
        try:
            resp = requests.get(f"{base_url}/cars")
            if resp.status_code == 200: rows = resp.json()
            else: error_msg = "Gagal mengambil data."
        except: error_msg = f"Server {ms} Down."
    return templates.TemplateResponse("read.html", {"request": request, "rows": rows, "ms": ms, "error": error_msg})

# CREATE
@app.get("/create/{ms}", response_class=HTMLResponse)
def create_view(request: Request, ms: str):
    return templates.TemplateResponse("create.html", {"request": request, "ms": ms})

@app.post("/create/save")
def create_action(
    ms: str = Form(...), 
    carname: str = Form(...), 
    carbrand: str = Form(...),
    carmodel: str = Form(...), 
    carprice: str = Form(...), 
    description: Optional[str] = Form(None)
):
    base_url = SERVERS.get(ms)
    desc_value = description if description else ""
    
    data = {
        "carname": carname, "carbrand": carbrand, 
        "carmodel": carmodel, "carprice": carprice, 
        "description": desc_value
    }
    try: requests.post(f"{base_url}/cars", json=data)
    except: pass
    return RedirectResponse(url=f"/read/{ms}", status_code=status.HTTP_303_SEE_OTHER)

# UPDATE
@app.get("/update/{ms}", response_class=HTMLResponse)
def update_list(request: Request, ms: str):
    base_url = SERVERS.get(ms)
    rows = []
    try:
        resp = requests.get(f"{base_url}/cars")
        if resp.status_code == 200: rows = resp.json()
    except: pass
    return templates.TemplateResponse("update_list.html", {"request": request, "rows": rows, "ms": ms})

@app.get("/update/{ms}/{id}", response_class=HTMLResponse)
def update_form(request: Request, ms: str, id: int):
    base_url = SERVERS.get(ms)
    car = None
    try:
        resp = requests.get(f"{base_url}/cars/{id}")
        if resp.status_code == 200: car = resp.json()
    except: pass
    if not car: return RedirectResponse(url=f"/update/{ms}", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("form_update.html", {"request": request, "row": car, "ms": ms})

@app.post("/update/save")
def update_save(
    ms: str = Form(...), id: int = Form(...), 
    carname: str = Form(...), carbrand: str = Form(...),
    carmodel: str = Form(...), carprice: str = Form(...), 
    description: Optional[str] = Form(None)
):
    base_url = SERVERS.get(ms)
    desc_value = description if description else ""
    data = {
        "id": id, "carname": carname, "carbrand": carbrand, 
        "carmodel": carmodel, "carprice": carprice, "description": desc_value
    }
    try: requests.put(f"{base_url}/cars/{id}", json=data)
    except: pass
    return RedirectResponse(url=f"/update/{ms}", status_code=status.HTTP_303_SEE_OTHER)

# DELETE
@app.get("/delete/{ms}", response_class=HTMLResponse)
def delete_list(request: Request, ms: str):
    base_url = SERVERS.get(ms)
    rows = []
    try:
        resp = requests.get(f"{base_url}/cars")
        if resp.status_code == 200: rows = resp.json()
    except: pass
    return templates.TemplateResponse("delete_list.html", {"request": request, "rows": rows, "ms": ms})

@app.get("/delete/{ms}/{id}")
def delete_action(ms: str, id: int):
    base_url = SERVERS.get(ms)
    try: requests.delete(f"{base_url}/delete/{id}")
    except: pass
    return RedirectResponse(url=f"/delete/{ms}", status_code=status.HTTP_303_SEE_OTHER)

# SEARCH
@app.get("/search/{ms}", response_class=HTMLResponse)
def search_view(request: Request, ms: str):
    return templates.TemplateResponse("search.html", {"request": request, "ms": ms, "rows": [], "keyword": ""})

@app.post("/search/{ms}", response_class=HTMLResponse)
def search_action(request: Request, ms: str, keyword: str = Form(...)):
    base_url = SERVERS.get(ms)
    rows = []
    try:
        resp = requests.get(f"{base_url}/search/{keyword}")
        if resp.status_code == 200: rows = resp.json()
    except: pass
    return templates.TemplateResponse("search.html", {"request": request, "ms": ms, "rows": rows, "keyword": keyword})

if __name__ == "__main__":
    uvicorn.run("frontend_app:app", host="0.0.0.0", port=5000, reload=True)