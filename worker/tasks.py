import os
import subprocess
import datetime
import nmap
import paramiko
import winrm
from celery import Celery
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models import ScriptExecution, Subnet, IPAddress, Server

# Configuration Celery
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery("netops_worker", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

SCRIPTS_DIR = "/scripts_storage"

def run_local(cmd):
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Script execution timed out."
    except Exception as e:
        return -1, "", str(e)

def run_ssh(server, file_path, script_type):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(server.ip_address, port=server.port, username=server.username, password=server.password, timeout=10)
        
        # Upload script
        sftp = client.open_sftp()
        remote_path = f"/tmp/{os.path.basename(file_path)}"
        sftp.put(file_path, remote_path)
        sftp.close()

        # Execute
        command = ""
        if script_type == "python":
            command = f"python3 {remote_path}"
        elif script_type == "bash":
            command = f"bash {remote_path}"
        elif script_type == "powershell":
             # Assuming pwsh is installed on linux target or windows ssh
            command = f"pwsh {remote_path}"
            
        stdin, stdout, stderr = client.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        out = stdout.read().decode()
        err = stderr.read().decode()
        
        client.close()
        return exit_status, out, err

    except Exception as e:
        return -1, "", f"SSH Connection Failed: {str(e)}"

def run_winrm(server, file_path):
    # For WinRM, we usually read the script content and pass it via PowerShell command
    # rather than uploading a file (which is complex with WinRM alone)
    try:
        with open(file_path, 'r') as f:
            script_content = f.read()

        session = winrm.Session(f'http://{server.ip_address}:5985/wsman', auth=(server.username, server.password))
        
        # Wrap in encoded command or invoke-expression if needed, simplified here
        ps_script = f"$ProgressPreference = 'SilentlyContinue'; {script_content}"
        
        # Using base64 encoding is safer for complex scripts
        import base64
        encoded_ps = base64.b64encode(ps_script.encode('utf_16_le')).decode('utf-8')
        
        r = session.run_ps(ps_script)
        
        return r.status_code, r.std_out.decode(), r.std_err.decode()

    except Exception as e:
        return -1, "", f"WinRM Failed: {str(e)}"

@celery_app.task(bind=True)
def execute_script_task(self, execution_id: int, filename: str, script_type: str, server_id: int = None, script_args: list = None):
    db: Session = SessionLocal()
    execution = db.query(ScriptExecution).filter(ScriptExecution.id == execution_id).first()
    
    if not execution:
        db.close()
        return "Execution not found"
        
    execution.status = "running"
    db.commit()
    
    file_path = os.path.join(SCRIPTS_DIR, filename)
    
    if not os.path.exists(file_path):
        execution.status = "failure"
        execution.stderr = f"File not found: {file_path}"
        execution.completed_at = datetime.datetime.utcnow()
        db.commit()
        db.close()
        return "File not found"

    # Prepare Arguments
    args_str = ""
    if script_args:
        args_str = " " + " ".join([f'"{arg}"' for arg in script_args]) # Simple quoting

    # Determine execution mode
    return_code = 0
    stdout = ""
    stderr = ""

    if server_id:
        server = db.query(Server).filter(Server.id == server_id).first()
        if not server:
            stderr = "Target server not found"
            return_code = -1
        else:
            # We need to pass args to run_ssh or run_winrm
            # For now, let's inject them into the run_ssh call if we modify it, 
            # OR just Append them to the command construction inside run_ssh if we passed them.
            # Let's modify run_ssh signature locally here to accept args_str
            if server.connection_type == "ssh":
                return_code, stdout, stderr = run_ssh_with_args(server, file_path, script_type, args_str)
            elif server.connection_type == "winrm":
                # WinRM args support would require modifying the PS script invocation
                stderr = "Arguments not yet supported for WinRM"
                return_code = -1
            else:
                 stderr = f"Unknown connection type: {server.connection_type}"
                 return_code = -1
    else:
        # LOCAL EXECUTION
        cmd = []
        if script_type == "python":
            cmd = ["python3", file_path]
        elif script_type == "bash":
            cmd = ["bash", file_path]
        elif script_type == "powershell":
            cmd = ["pwsh", file_path]
        else:
            cmd = [file_path]
        
        if script_args:
            cmd.extend(script_args)
        
        return_code, stdout, stderr = run_local(cmd)

    execution.stdout = stdout
    execution.stderr = stderr
    
    if return_code == 0:
        execution.status = "success"
    else:
        execution.status = "failure"
            
    execution.completed_at = datetime.datetime.utcnow()
    db.commit()
    db.close()
    
    return execution.status

def run_ssh_with_args(server, file_path, script_type, args_str):
    # Re-implementing simplified run_ssh here or we could have modified the original function.
    # To keep it clean, let's just copy the logic or call the original if no args.
    # But since we can't easily change the original function signature in this tool call without replacing the whole file,
    # and I am replacing the task function... I should have replaced the whole file content or helper.
    # Let's just inline the logic for now or rely on a helper.
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(server.ip_address, port=server.port, username=server.username, password=server.password, timeout=10)
        
        sftp = client.open_sftp()
        remote_path = f"/tmp/{os.path.basename(file_path)}"
        sftp.put(file_path, remote_path)
        sftp.close()

        command = ""
        if script_type == "python":
            command = f"python3 {remote_path}{args_str}"
        elif script_type == "bash":
            command = f"bash {remote_path}{args_str}"
        elif script_type == "powershell":
            command = f"pwsh {remote_path}{args_str}"
            
        stdin, stdout, stderr = client.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        out = stdout.read().decode()
        err = stderr.read().decode()
        
        client.close()
        return exit_status, out, err

    except Exception as e:
        return -1, "", f"SSH Connection Failed: {str(e)}"

@celery_app.task(bind=True)
def scan_subnet_task(self, subnet_id: int):
    db: Session = SessionLocal()
    subnet = db.query(Subnet).filter(Subnet.id == subnet_id).first()
    
    if not subnet:
        db.close()
        return "Subnet not found"
        
    nm = nmap.PortScanner()
    try:
        nm.scan(hosts=str(subnet.cidr), arguments='-sn -PR -R')
    except Exception as e:
        db.close()
        return f"Scan failed: {str(e)}"

    scanned_hosts = nm.all_hosts()
    
    for host in scanned_hosts:
        status = 'active' if nm[host].state() == 'up' else 'available'
        hostname = nm[host].hostname() if nm[host].hostname() else None
        mac = None
        if 'addresses' in nm[host] and 'mac' in nm[host]['addresses']:
            mac = nm[host]['addresses']['mac']
            
        existing_ip = db.query(IPAddress).filter(
            IPAddress.subnet_id == subnet_id,
            IPAddress.address == host
        ).first()
        
        if existing_ip:
            existing_ip.status = status
            existing_ip.last_scanned_at = datetime.datetime.utcnow()
            if hostname:
                existing_ip.hostname = hostname
            if mac:
                existing_ip.mac_address = mac
        else:
            new_ip = IPAddress(
                address=host,
                subnet_id=subnet_id,
                status=status,
                hostname=hostname,
                mac_address=mac,
                last_scanned_at=datetime.datetime.utcnow()
            )
            db.add(new_ip)
            
    db.commit()
    db.close()
    return f"Scan complete for {subnet.cidr}."
