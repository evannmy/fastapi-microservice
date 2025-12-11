import uvicorn
import requests
from typing import Optional
from fastapi import FastAPI, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="APPX Frontend")
templates = Jinja2Templates(directory="templates")

SERVERS = {
    "MS1": "http://localhost:5051", 
    "MS2": "http://localhost:5052", 
    "MS3": "http://localhost:5053"  
}

# --- DASHBOARD & MENU ---
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    # Logic ping server (sama seperti sebelumnya)
    server_status = {}
    for ms_name, ms_url in SERVERS.items():
        try:
            resp = requests.get(f"{ms_url}/cars", timeout=0.5)
            server_status[ms_name] = (resp.status_code == 200)
        except:
            server_status[ms_name] = False
    return templates.TemplateResponse("index.html", {"request": request, "status": server_status})

@app.get("/menu/{ms}", response_class=HTMLResponse)
def menu_view(request: Request, ms: str):
    status_server = "Offline"
    count_data = 0
    base_url = SERVERS.get(ms)
    
    # Cek koneksi (default ke dba)
    try:
        resp = requests.get(f"{base_url}/cars", timeout=1)
        if resp.status_code == 200:
            status_server = "Online"
            count_data = len(resp.json())
    except: 
        status_server = "Offline"
    
    if status_server == "Offline":
        return templates.TemplateResponse("index.html", {
            "request": request,
            "status": {"MS1": False, "MS2": False, "MS3": False},
            "error_message": f"Server {ms} sedang OFFLINE."
        })
            
    return templates.TemplateResponse("menu_microservice.html", {
        "request": request, "ms": ms, "status": status_server, "count": count_data
    })

# --- READ (PILIHAN DB) ---
@app.get("/read/{ms}", response_class=HTMLResponse)
def read_view(request: Request, ms: str, db_name: str = "dba"):
    base_url = SERVERS.get(ms)
    rows = []
    error_msg = None
    
    if base_url:
        try:
            resp = requests.get(f"{base_url}/cars", params={"db_name": db_name})
            if resp.status_code == 200: rows = resp.json()
            else: error_msg = "Gagal mengambil data."
        except: error_msg = f"Server {ms} Down."
        
    return templates.TemplateResponse("read.html", {
        "request": request, "rows": rows, "ms": ms, "error": error_msg, "current_db": db_name
    })

# --- CREATE (SUPPORT DB PILIHAN) ---
@app.get("/create/{ms}", response_class=HTMLResponse)
def create_view(request: Request, ms: str, db_name: str = "dba"):
    # Terima parameter db_name agar form tahu mau simpan ke mana
    return templates.TemplateResponse("create.html", {"request": request, "ms": ms, "current_db": db_name})

@app.post("/create/save")
def create_action(
    ms: str = Form(...), 
    db_name: str = Form(...), # Terima input db mana
    carname: str = Form(...), carbrand: str = Form(...),
    carmodel: str = Form(...), carprice: str = Form(...), 
    description: Optional[str] = Form(None)
):
    base_url = SERVERS.get(ms)
    desc = description if description else ""
    
    # Kirim query param ?db_name=... ke backend
    try: 
        requests.post(
            f"{base_url}/cars", 
            params={"db_name": db_name},
            json={"carname": carname, "carbrand": carbrand, "carmodel": carmodel, "carprice": carprice, "description": desc}
        )
    except: pass
    return RedirectResponse(url=f"/read/{ms}?db_name={db_name}", status_code=status.HTTP_303_SEE_OTHER)

# --- UPDATE (SUPPORT DB PILIHAN) ---
@app.get("/update/{ms}", response_class=HTMLResponse)
def update_list(request: Request, ms: str, db_name: str = "dba"):
    base_url = SERVERS.get(ms)
    rows = []
    try:
        resp = requests.get(f"{base_url}/cars", params={"db_name": db_name})
        if resp.status_code == 200: rows = resp.json()
    except: pass
    return templates.TemplateResponse("update_list.html", {"request": request, "rows": rows, "ms": ms, "current_db": db_name})

@app.get("/update/{ms}/{id}", response_class=HTMLResponse)
def update_form(request: Request, ms: str, id: int, db_name: str = "dba"):
    base_url = SERVERS.get(ms)
    car = None
    try:
        resp = requests.get(f"{base_url}/cars/{id}", params={"db_name": db_name})
        if resp.status_code == 200: car = resp.json()
    except: pass
    if not car: return RedirectResponse(url=f"/update/{ms}?db_name={db_name}", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("form_update.html", {"request": request, "row": car, "ms": ms, "current_db": db_name})

@app.post("/update/save")
def update_save(
    ms: str = Form(...), 
    id: int = Form(...), 
    db_name: str = Form(...), # Terima db_name
    carname: str = Form(...), carbrand: str = Form(...),
    carmodel: str = Form(...), carprice: str = Form(...), 
    description: Optional[str] = Form(None)
):
    base_url = SERVERS.get(ms)
    desc = description if description else ""
    try: 
        requests.put(
            f"{base_url}/cars/{id}", 
            params={"db_name": db_name},
            json={"id": id, "carname": carname, "carbrand": carbrand, "carmodel": carmodel, "carprice": carprice, "description": desc}
        )
    except: pass
    return RedirectResponse(url=f"/update/{ms}?db_name={db_name}", status_code=status.HTTP_303_SEE_OTHER)

# --- DELETE (SUPPORT DB PILIHAN) ---
@app.get("/delete/{ms}", response_class=HTMLResponse)
def delete_list(request: Request, ms: str, db_name: str = "dba"):
    base_url = SERVERS.get(ms)
    rows = []
    try:
        resp = requests.get(f"{base_url}/cars", params={"db_name": db_name})
        if resp.status_code == 200: rows = resp.json()
    except: pass
    return templates.TemplateResponse("delete_list.html", {"request": request, "rows": rows, "ms": ms, "current_db": db_name})

@app.get("/delete/{ms}/{id}", response_class=HTMLResponse)
def delete_action(request: Request, ms: str, id: int, db_name: str = "dba"):
    base_url = SERVERS.get(ms)
    try: 
        requests.delete(f"{base_url}/delete/{id}", params={"db_name": db_name})
    except: pass
    return RedirectResponse(url=f"/delete/{ms}?db_name={db_name}", status_code=status.HTTP_303_SEE_OTHER)

# --- SEARCH ---
@app.get("/search/{ms}", response_class=HTMLResponse)
def search_view(request: Request, ms: str, db_name: str = "dba"):
    return templates.TemplateResponse("search.html", {
        "request": request, "ms": ms, "rows": [], "keyword": "", "current_db": db_name
    })

@app.post("/search/{ms}", response_class=HTMLResponse)
def search_action(request: Request, ms: str, keyword: str = Form(...), db_name: str = Form("dba")):
    base_url = SERVERS.get(ms)
    rows = []
    try:
        resp = requests.get(f"{base_url}/search/{keyword}", params={"db_name": db_name})
        if resp.status_code == 200: rows = resp.json()
    except: pass
    return templates.TemplateResponse("search.html", {
        "request": request, "ms": ms, "rows": rows, "keyword": keyword, "current_db": db_name
    })

if __name__ == "__main__":
    uvicorn.run("frontend_app:app", host="0.0.0.0", port=5001, reload=True)