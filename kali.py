
import socket
import os
import threading
import time
from datetime import datetime

SAVE_DIR = "received_files"
PORT = 9999

# Create save directory
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)
    print(f"[*] Created: {SAVE_DIR}")

def handle_client(conn, addr):
    try:
        print(f"\n[*] 🔗 Connection from: {addr[0]}:{addr[1]}")
        
        # Receive filename
        filename = conn.recv(1024).decode().strip()
        if not filename:
            print("[-] No filename received")
            conn.close()
            return
        print(f"[*] 📁 File: {filename}")
        
        # Receive file size
        size_data = conn.recv(1024).decode().strip()
        try:
            file_size = int(size_data)
        except:
            file_size = 0
        print(f"[*] 📊 Size: {file_size} bytes")
        
        # Receive file data - FIXED
        data = b''
        received = 0
        start_time = time.time()
        
        # Keep receiving until we get all data
        while received < file_size:
            chunk = conn.recv(4096)
            if not chunk:
                print(f"\n[-] Connection closed prematurely!")
                break
            data += chunk
            received += len(chunk)
            
            # Show progress
            if received % 10240 == 0 or received == file_size:
                progress = (received / file_size * 100) if file_size > 0 else 0
                print(f"\r[*] ⏳ Receiving: {received}/{file_size} bytes ({progress:.1f}%)", end='', flush=True)
        
        print()  # New line
        
        # Check if we received all data
        if len(data) != file_size:
            print(f"[-] Warning: Received {len(data)} bytes, expected {file_size} bytes")
            # Still save whatever we received
        
        # Save file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base, ext = os.path.splitext(filename)
        unique_filename = f"{base}_{timestamp}{ext}"
        
        filepath = os.path.join(SAVE_DIR, unique_filename)
        
        # If file exists, add counter
        counter = 1
        while os.path.exists(filepath):
            filepath = os.path.join(SAVE_DIR, f"{base}_{timestamp}_{counter}{ext}")
            counter += 1
        
        with open(filepath, 'wb') as f:
            f.write(data)
        
        # Calculate speed
        elapsed = time.time() - start_time
        speed = (len(data) / elapsed) if elapsed > 0 else 0
        
        print(f"[+] ✅ File saved successfully!")
        print(f"[+] 📁 Location: {filepath}")
        print(f"[+] 📊 Size: {len(data)} bytes ({len(data)/1024:.2f} KB)")
        if elapsed > 0:
            print(f"[+] ⏱️ Time: {elapsed:.2f} seconds")
            print(f"[+] 🚀 Speed: {speed/1024:.2f} KB/s")
        print("-"*50)
        
        conn.close()
        
    except Exception as e:
        print(f"[-] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        conn.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind(('0.0.0.0', PORT))
    except Exception as e:
        print(f"[-] ❌ Port {PORT} already in use!")
        print(f"[*] Try: sudo kill -9 $(sudo lsof -t -i:{PORT})")
        return
    
    server.listen(10)
    
    print("="*60)
    print("🟢 KALI FILE RECEIVER (FIXED)")
    print("="*60)
    print(f"[*] 🎯 Listening on: 0.0.0.0:{PORT}")
    print(f"[*] 📁 Saving to: {os.path.abspath(SAVE_DIR)}")
    print("="*60)
    print("[*] Press Ctrl+C to stop")
    print("-"*60)
    print("[*] 🟢 Waiting for files from Windows...")
    
    while True:
        try:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.daemon = True
            thread.start()
        except KeyboardInterrupt:
            print("\n[*] ⏹️ Shutting down...")
            break
        except Exception as e:
            print(f"[-] Error: {e}")
    
    server.close()
    print("[*] Server stopped")

if __name__ == "__main__":
    main()
