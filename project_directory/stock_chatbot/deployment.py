# stock_chatbot/deployment.py
import paramiko
from datetime import datetime, timedelta, timezone

def deploy_remote_script():
    EC2_HOST = "34.229.205.14"
    USERNAME = "ubuntu"
    KEY_PATH = "94463.pem"
    REMOTE_SCRIPT = "/home/ubuntu/test13/hackathon/deployment.py"
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print("[INFO] Connecting to EC2 instance...")
        ssh.connect(EC2_HOST, username=USERNAME, key_filename=KEY_PATH)
        command = f"nohup python3 {REMOTE_SCRIPT} > output.log 2>&1 & echo $!"
        stdin, stdout, stderr = ssh.exec_command(command)
        pid = stdout.read().decode().strip()
        ist_timezone = timezone(timedelta(hours=5, minutes=30))
        current_time = datetime.now(ist_timezone).strftime("%Y-%m-%d %H:%M:%S")
        return f"[INFO] Script started with PID: {pid}\n[INFO] Check logs using: cat output.log\nYour Algo has been deployed on AWS server with IP {EC2_HOST} at time {current_time} in IST"
    except Exception as e:
        return f"[ERROR] {str(e)}"
    finally:
        print("[INFO] Connection closed.")
        ssh.close()