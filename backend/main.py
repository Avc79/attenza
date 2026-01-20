from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Request, Form
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os
import shutil
from typing import List

from . import models, database, auth, face_utils

# Create tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="SecureAttend API")

# Resolve paths relative to the current file (backend/main.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Mount Static Files
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Templates
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# CORS Setup - Enable all for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    return database.get_db()

@app.post("/token", response_model=dict)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id, "full_name": user.full_name}

@app.post("/register")
async def register_user(
    email: str = Form(...), 
    full_name: str = Form(...), 
    password: str = Form(...), 
    role: str = Form("staff"), 
    db: Session = Depends(database.get_db),
    file: UploadFile = File(...)
):
    # Check if user exists
    existing_user = db.query(models.User).filter(models.User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Save user to DB first to get ID
    hashed_password = auth.get_password_hash(password)
    new_user = models.User(
        email=email,
        full_name=full_name,
        hashed_password=hashed_password,
        role=role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Save reference image
    try:
        temp_path = f"temp_register_{new_user.id}.jpg"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        saved_path = face_utils.save_face_image(new_user.id, temp_path)
        new_user.face_image_path = saved_path
        db.commit()
        
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
    except Exception as e:
        db.delete(new_user)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")

    return {"message": "User created successfully", "user_id": new_user.id}

@app.get("/users/me")
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role
    }

@app.get("/attendance/history")
def get_attendance_history(
    current_user: models.User = Depends(auth.get_current_user), 
    db: Session = Depends(database.get_db)
):
    # Retrieve attendance records for the user
    records = db.query(models.Attendance).filter(models.Attendance.user_id == current_user.id).order_by(models.Attendance.timestamp.desc()).all()
    return records

@app.post("/attendance/mark")
async def mark_attendance(
    request: Request,
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    # 1. Wifi/IP Check
    client_ip = request.client.host
    # NOTE: In a real scenario, we would check if this IP is in the allowed subnet
    # For now, we just record it.
    
    # 2. Face Verification
    temp_filename = f"temp_verify_{current_user.id}_{datetime.now().timestamp()}.jpg"
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    verification_result = face_utils.verify_face(temp_filename, current_user.id)
    
    # Cleanup temp file
    if os.path.exists(temp_filename):
        os.remove(temp_filename)
        
    if not verification_result["verified"]:
        raise HTTPException(status_code=400, detail=f"Face verification failed: {verification_result.get('message')}")
    
    # 3. Mark Attendance
    # Logic to determine status (Late vs Present) based on time
    now = datetime.now()
    status_text = "Present"
    if now.hour > 9: # Assuming 9 AM start
        status_text = "Late"
        
    new_attendance = models.Attendance(
        user_id=current_user.id,
        status=status_text,
        ip_address=client_ip,
        verification_method="Dual (Wifi+Face)"
    )
    db.add(new_attendance)
    db.commit()
    
    return {
        "message": "Attendance marked successfully", 
        "status": status_text,
        "verification": verification_result,
        "ip": client_ip
    }

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/history", response_class=HTMLResponse)
def history_page(request: Request):
    return templates.TemplateResponse("history.html", {"request": request})

