from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import shutil
import os
import ipaddress
import logging

from backend import models, schemas, database, auth
from worker.tasks import execute_script_task, scan_subnet_task

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Tables
models.Base.metadata.create_all(bind=database.engine)

# Create Default Admin User
def create_default_admin():
    db = database.SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.username == "admin").first()
        if not user:
            logger.info("Creating default admin user...")
            hashed_pwd = auth.get_password_hash("admin")
            # Admin has all permissions
            perms = {"ipam": True, "topology": True, "scripts": True, "settings": True}
            admin = models.User(username="admin", hashed_password=hashed_pwd, role="admin", permissions=perms)
            db.add(admin)
            db.commit()
            logger.info("Default user 'admin' created successfully.")
    except Exception as e:
        logger.error(f"Error creating default admin: {e}")
    finally:
        db.close()

create_default_admin()

app = FastAPI(title="NetOps-Flow API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Auth Endpoints ---

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username.lower()).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(auth.get_current_active_user)):
    return current_user

@app.put("/users/me/password")
async def update_password(
    password_data: schemas.UserCreate, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(auth.get_current_active_user)
):
    hashed_password = auth.get_password_hash(password_data.password)
    current_user.hashed_password = hashed_password
    db.commit()
    return {"message": "Password updated successfully"}

# --- User Management (Admin Only) ---

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_admin_user)):
    db_user = db.query(models.User).filter(models.User.username == user.username.lower()).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        username=user.username.lower(), 
        hashed_password=hashed_password, 
        role=user.role, 
        is_active=user.is_active,
        permissions=user.permissions
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/", response_model=List[schemas.User])
def read_users(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_admin_user)):
    return db.query(models.User).all()

# --- Server Management ---

@app.post("/servers/", response_model=schemas.Server)
def create_server(server: schemas.ServerCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_admin_user)):
    db_server = models.Server(**server.dict())
    db.add(db_server)
    db.commit()
    db.refresh(db_server)
    return db_server

@app.get("/servers/", response_model=List[schemas.Server])
def read_servers(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    return db.query(models.Server).all()

@app.delete("/servers/{server_id}")
def delete_server(server_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_admin_user)):
    server = db.query(models.Server).filter(models.Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    db.delete(server)
    db.commit()
    return {"ok": True}

# --- IPAM Endpoints ---

@app.post("/subnets/", response_model=schemas.Subnet)
def create_subnet(subnet: schemas.SubnetCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    if current_user.role != "admin" and not current_user.permissions.get("ipam"):
        raise HTTPException(status_code=403, detail="Permission denied")
    try:
        ipaddress.ip_network(subnet.cidr)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid CIDR format")
    db_subnet = models.Subnet(cidr=subnet.cidr, name=subnet.name, description=subnet.description)
    db.add(db_subnet)
    db.commit()
    db.refresh(db_subnet)
    return db_subnet

@app.get("/subnets/", response_model=List[schemas.Subnet])
def read_subnets(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    # Read access might be open or restricted. For now, let's keep it open to active users or check IPAM?
    # User asked to check rights. Let's enforce IPAM or Topology for reading subnets as they are basic network data?
    # Let's be safe: if you can't see IPAM or Topology, you probably shouldn't list subnets detailedly.
    # But for now, let's stick to modifying the write operations as critical path, and specific feature pages.
    if current_user.role != "admin" and not current_user.permissions.get("ipam") and not current_user.permissions.get("topology"):
         raise HTTPException(status_code=403, detail="Permission denied")
    return db.query(models.Subnet).offset(skip).limit(limit).all()

@app.post("/subnets/{subnet_id}/ips/", response_model=schemas.IPAddress)
def create_ip_for_subnet(subnet_id: int, ip: schemas.IPAddressCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    if current_user.role != "admin" and not current_user.permissions.get("ipam"):
        raise HTTPException(status_code=403, detail="Permission denied")
    subnet = db.query(models.Subnet).filter(models.Subnet.id == subnet_id).first()
    if not subnet:
        raise HTTPException(status_code=404, detail="Subnet not found")
    net = ipaddress.ip_network(subnet.cidr)
    try:
        addr = ipaddress.ip_address(ip.address)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid IP address format")
    if addr not in net:
        raise HTTPException(status_code=400, detail=f"IP {ip.address} does not belong to subnet {subnet.cidr}")
    db_ip = models.IPAddress(**ip.model_dump(), subnet_id=subnet_id)
    db.add(db_ip)
    db.commit()
    db.refresh(db_ip)
    return db_ip

@app.post("/subnets/{subnet_id}/scan")
def scan_subnet(subnet_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    if current_user.role != "admin" and not current_user.permissions.get("ipam"):
        raise HTTPException(status_code=403, detail="Permission denied")
    subnet = db.query(models.Subnet).filter(models.Subnet.id == subnet_id).first()
    if not subnet:
        raise HTTPException(status_code=404, detail="Subnet not found")
    task = scan_subnet_task.delay(subnet_id)
    return {"message": "Scan started", "task_id": task.id}

@app.get("/topology")
def get_topology(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    if current_user.role != "admin" and not current_user.permissions.get("topology"):
        raise HTTPException(status_code=403, detail="Permission denied")
    subnets = db.query(models.Subnet).all()
    nodes = []
    edges = []
    nodes.append({"id": "internet", "label": "Internet", "group": "internet", "shape": "cloud"})
    for subnet in subnets:
        subnet_node_id = f"subnet_{subnet.id}"
        nodes.append({
            "id": subnet_node_id,
            "label": f"{subnet.name}\n{subnet.cidr}",
            "group": "subnet",
            "shape": "box"
        })
        edges.append({"from": "internet", "to": subnet_node_id})
        for ip in subnet.ips:
            ip_node_id = f"ip_{ip.id}"
            label = ip.address
            if ip.hostname:
                label += f"\n({ip.hostname})"
            color = "#10b981" if ip.status == "active" else "#64748b"
            nodes.append({
                "id": ip_node_id,
                "label": label,
                "group": "ip",
                "shape": "dot",
                "color": color
            })
            edges.append({"from": subnet_node_id, "to": ip_node_id})
    return {"nodes": nodes, "edges": edges}

# --- Script Runner Endpoints ---

SCRIPTS_DIR = "/scripts_storage"

@app.post("/scripts/", response_model=schemas.Script)
def upload_script(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    script_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    if current_user.role != "admin" and not current_user.permissions.get("scripts"):
        raise HTTPException(status_code=403, detail="Permission denied")
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    filename = f"{name.replace(' ', '_')}_{file.filename}"
    file_location = os.path.join(SCRIPTS_DIR, filename)
    with open(file_location, "wb+") as buffer:
        shutil.copyfileobj(file.file, buffer)
    db_script = models.Script(
        name=name, description=description, script_type=script_type, filename=filename
    )
    db.add(db_script)
    db.commit()
    db.refresh(db_script)
    return db_script

@app.get("/scripts/", response_model=List[schemas.Script])
def list_scripts(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    if current_user.role != "admin" and not current_user.permissions.get("scripts"):
        raise HTTPException(status_code=403, detail="Permission denied")
    return db.query(models.Script).all()

class ScriptExecutionRequest(BaseModel):
    server_id: Optional[int] = None
    password: str
    script_args: Optional[List[str]] = None

@app.post("/scripts/{script_id}/run", response_model=schemas.ScriptExecution)
def run_script(
    script_id: int, 
    exec_req: ScriptExecutionRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    if current_user.role != "admin" and not current_user.permissions.get("scripts"):
        raise HTTPException(status_code=403, detail="Permission denied")

    # Security Check: Verify Password
    if not auth.verify_password(exec_req.password, current_user.hashed_password):
        raise HTTPException(status_code=403, detail="Invalid password confirmation")

    script = db.query(models.Script).filter(models.Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    execution = models.ScriptExecution(
        script_id=script_id, 
        server_id=exec_req.server_id, 
        status="pending",
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    
    task = execute_script_task.delay(execution.id, script.filename, script.script_type, exec_req.server_id, exec_req.script_args)
    
    # Save task_id
    execution.task_id = task.id
    db.commit()
    
    return execution

@app.post("/executions/{execution_id}/stop")
def stop_execution(execution_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    if current_user.role != "admin" and not current_user.permissions.get("scripts"):
        raise HTTPException(status_code=403, detail="Permission denied")
        
    execution = db.query(models.ScriptExecution).filter(models.ScriptExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
        
    if execution.status in ["running", "pending"] and execution.task_id:
        # Revoke task
        execute_script_task.app.control.revoke(execution.task_id, terminate=True)
        execution.status = "cancelled"
        execution.stderr = (execution.stderr or "") + "\n[Stopped by user]"
        execution.completed_at = datetime.datetime.utcnow()
        db.commit()
        
    return {"message": "Execution stopped"}

@app.delete("/executions/")
def clear_executions(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_admin_user)):
    # Only admin can clear full history
    db.query(models.ScriptExecution).delete()
    db.commit()
    return {"message": "History cleared"}

@app.delete("/scripts/{script_id}")
def delete_script(script_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    if current_user.role != "admin" and not current_user.permissions.get("scripts"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    script = db.query(models.Script).filter(models.Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    # Delete file
    file_path = os.path.join(SCRIPTS_DIR, script.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(script)
    db.commit()
    return {"ok": True}

@app.get("/executions/", response_model=List[schemas.ScriptExecution])
def list_executions(skip: int = 0, limit: int = 20, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    return db.query(models.ScriptExecution).order_by(models.ScriptExecution.started_at.desc()).offset(skip).limit(limit).all()

@app.get("/dashboard/stats")
def get_stats(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    return {
        "subnets": db.query(models.Subnet).count(),
        "ips": db.query(models.IPAddress).count(),
        "scripts": db.query(models.Script).count(),
        "executions": db.query(models.ScriptExecution).count()
    }