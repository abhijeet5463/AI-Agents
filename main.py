from fastapi import FastAPI
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
import requests
import json
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

OLLAMA_URL = "http://localhost:11434/api/chat"   # Ollama server
MODEL_NAME = "llama3.1:8b"                       # Change this anytime

# Secret settings and password hashing logic
SECRET_KEY = "your_secret_key_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

fake_users_db = {}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Argon2 has no 72-byte limit
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    # Argon2 handles long passwords natively
    return pwd_context.hash(password)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication payload")
        user = fake_users_db.get(username)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")


def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

class ChatMessage(BaseModel):
    text: str

# Register endpoint
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from fastapi import status

from fastapi import Form

from fastapi import Response


from fastapi import Form

@app.post("/register")
def register(username: str = Form(...), password: str = Form(...)):
    # Argon2: no 72-byte limit; accept full password

    if username in fake_users_db:
        raise HTTPException(status_code=400, detail="User already registered")
    
    fake_users_db[username] = {
        "username": username,
        "hashed_password": get_password_hash(password)
    }
    return {"msg": "Registration successful!"}
    

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/chat")
def chat(msg: ChatMessage, current_user: dict = Depends(get_current_user)):
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are BodhiPilot, a helpful AI."},
            {"role": "user", "content": msg.text}
        ]
    }
    try:
        res = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=60)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Ollama connection error: {e}")

    content_type = res.headers.get("Content-Type", "")
    if "application/json" in content_type:
        try:
            data = res.json()
        except ValueError:
            raise HTTPException(status_code=502, detail="Invalid JSON from model")
        return {"reply": data.get("message", {}).get("content", "No reply from model")}
    else:
        reply = ""
        for line in res.text.splitlines():
            if not line.strip():
                continue
            try:
                chunk = json.loads(line)
                reply += chunk.get("message", {}).get("content", "")
            except json.JSONDecodeError:
                continue
        return {"reply": reply or "No valid response from model"}
# Serve login and register pages
@app.get("/me")
def read_me(current_user: dict = Depends(get_current_user)):
    return {"username": current_user["username"]}



# Serve login and register pages
@app.get("/login", response_class=HTMLResponse)
def serve_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
def serve_register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "BodhiPilot"})