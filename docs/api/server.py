#!/usr/bin/env python3
"""
JSON Viewer Server
A simple HTTP server that serves a beautiful JSON file viewer interface
"""

import http.server
import socketserver
import json
import os
import urllib.parse
import webbrowser
import threading
import time
from pathlib import Path

ROOT_DIR = Path('clean').resolve()
DOCS_ROOT = Path('api_json').resolve()
KB_ROOT = Path(os.environ.get('KB_DIR', 'KB')).resolve()

class JSONViewerHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler for the JSON viewer"""
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            # Redirect to the Docs viewer
            self.send_response(302)
            self.send_header('Location', '/docs/index.html')
            self.end_headers()
            return
        elif self.path == '/json_viewer.html':
            # Backward-compat redirect to new docs viewer
            self.send_response(302)
            self.send_header('Location', '/docs/index.html')
            self.end_headers()
            return
            
        elif self.path == '/api/files':
            # Return list of JSON files under clean/
            self.serve_file_list()
            return
            
        elif self.path.startswith('/api/file/'):
            # Serve specific JSON file content
            filename = urllib.parse.unquote(self.path[len('/api/file/'):])
            self.serve_json_file(filename)
            return

        elif self.path == '/api/docs/manifest':
            # Serve the docs manifest from api_json
            try:
                manifest_path = DOCS_ROOT / 'meta' / 'manifest.json'
                if not manifest_path.exists():
                    self.send_error(404, 'Manifest not found')
                    return
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(manifest).encode())
            except Exception as e:
                self.send_error(500, f"Error reading manifest: {str(e)}")
            return

        elif self.path.startswith('/api/docs/file/'):
            # Serve a specific docs file from api_json
            rel = urllib.parse.unquote(self.path[len('/api/docs/file/'):])
            try:
                if '..' in rel:
                    self.send_error(400, 'Invalid path')
                    return
                file_path = (DOCS_ROOT / rel).resolve()
                if DOCS_ROOT not in file_path.parents and file_path != DOCS_ROOT:
                    self.send_error(400, 'Invalid path')
                    return
                if not file_path.exists() or not file_path.is_file():
                    self.send_error(404, 'File not found')
                    return
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(content).encode())
            except Exception as e:
                self.send_error(500, f"Error reading docs file: {str(e)}")
            return

        elif self.path == '/api/kb/files':
            # List files in KB directory (if exists)
            try:
                if not KB_ROOT.exists():
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps([]).encode())
                    return
                items = []
                for p in KB_ROOT.rglob('*'):
                    if p.is_file():
                        rel = p.relative_to(KB_ROOT).as_posix()
                        title = p.stem.replace('-', ' ').replace('_',' ')
                        items.append({
                            'rel': rel,
                            'path': rel,
                            'name': p.name,
                            'title': title.title(),
                            'size': p.stat().st_size,
                            'modified': p.stat().st_mtime,
                        })
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(items).encode())
            except Exception as e:
                self.send_error(500, f"Error listing KB: {str(e)}")
            return

        elif self.path.startswith('/api/kb/file/'):
            # Serve a KB file content as JSON wrapper
            rel = urllib.parse.unquote(self.path[len('/api/kb/file/'):])
            try:
                if '..' in rel:
                    self.send_error(400, 'Invalid path')
                    return
                file_path = (KB_ROOT / rel).resolve()
                if KB_ROOT not in file_path.parents and file_path != KB_ROOT:
                    self.send_error(400, 'Invalid path')
                    return
                if not file_path.exists() or not file_path.is_file():
                    self.send_error(404, 'File not found')
                    return
                # Read as text if possible
                try:
                    content = file_path.read_text(encoding='utf-8')
                except Exception:
                    content = None
                ext = file_path.suffix.lower()
                mime = 'text/plain'
                if ext in ('.md', '.markdown'):
                    mime = 'text/markdown'
                elif ext == '.json':
                    mime = 'application/json'
                elif ext in ('.yml', '.yaml'):
                    mime = 'text/yaml'
                resp = {
                    'name': file_path.name,
                    'rel': rel,
                    'title': file_path.stem.replace('-', ' ').replace('_',' ').title(),
                    'ext': ext,
                    'mime': mime,
                    'content': content,
                    'size': file_path.stat().st_size,
                }
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(resp).encode())
            except Exception as e:
                self.send_error(500, f"Error reading KB file: {str(e)}")
            return
        
        # Default file serving
        super().do_GET()
    
    def serve_file_list(self):
        """Return a list of JSON files in the current directory"""
        try:
            json_files = []
            # Collect JSON files from clean/core, clean/resources, clean/forms, and meta
            search_dirs = [ROOT_DIR / 'core', ROOT_DIR / 'resources', ROOT_DIR / 'forms', ROOT_DIR / 'meta']
            for base in search_dirs:
                if not base.exists():
                    continue
                for file_path in base.rglob('*.json'):
                    if file_path.is_file():
                        stat = file_path.stat()
                        rel = file_path.relative_to(ROOT_DIR)
                        # Read file to get title and category
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                file_data = json.load(f)
                            # Handle different JSON structures
                            if isinstance(file_data, dict):
                                title = file_data.get('title', str(rel))
                                category = file_data.get('category', 'Other')
                            elif isinstance(file_data, list):
                                # For array-based files, use filename as title
                                title = str(rel).replace('.json', '').replace('_', ' ').replace('-', ' ').title()
                                category = 'Meta'
                            else:
                                title = str(rel)
                                category = 'Other'
                        except (json.JSONDecodeError, KeyError, AttributeError):
                            title = str(rel)
                            category = 'Other'
                        
                        json_files.append({
                            'name': str(rel),
                            'title': title,
                            'category': category,
                            'size': stat.st_size,
                            'modified': stat.st_mtime
                        })
            
            # Custom sort order matching Spark.re docs structure
            json_files = self.sort_files_by_docs_order(json_files)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(json_files, indent=2).encode())
            
        except Exception as e:
            self.send_error(500, f"Error listing files: {str(e)}")
    
    def serve_json_file(self, filename):
        """Serve the content of a specific JSON file"""
        try:
            # Security check - ensure filename doesn't contain path traversal
            if '..' in filename:
                self.send_error(400, "Invalid filename")
                return
            
            file_path = (ROOT_DIR / filename).resolve()
            # Ensure the file is within ROOT_DIR
            if ROOT_DIR not in file_path.parents and file_path != ROOT_DIR:
                self.send_error(400, "Invalid path")
                return
            if not file_path.exists() or not file_path.is_file():
                self.send_error(404, "File not found")
                return
            
            if not str(file_path).endswith('.json'):
                self.send_error(400, "Not a JSON file")
                return
            
            # Read and validate JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Validate JSON by parsing it
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                self.send_error(400, f"Invalid JSON: {str(e)}")
                return
            
            # Get file stats
            stat = file_path.stat()
            
            # Also parse the JSON to get title and category
            try:
                parsed_json = json.loads(content)
                # Handle different JSON structures
                if isinstance(parsed_json, dict):
                    title = parsed_json.get('title', filename)
                    category = parsed_json.get('category', 'Other')
                elif isinstance(parsed_json, list):
                    title = filename.replace('.json', '').replace('_', ' ').replace('-', ' ').title()
                    category = 'Meta'
                else:
                    title = filename
                    category = 'Other'
            except json.JSONDecodeError:
                title = filename
                category = 'Other'
            
            response_data = {
                'name': filename,
                'title': title,
                'category': category,
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'content': content
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())
            
        except Exception as e:
            self.send_error(500, f"Error reading file: {str(e)}")
    
    def sort_files_by_docs_order(self, files):
        """Sort files according to Spark.re docs structure"""
        # Define the order based on the Spark.re docs screenshot
        order_mapping = {
            # Core section
            'core/introduction.json': 1,
            'core/getting-started.json': 2,
            'core/environments.json': 3,
            'core/understanding-the-data.json': 4,
            'core/authorization.json': 5,
            'core/pagination.json': 6,
            'core/filtering.json': 7,
            'core/ordering.json': 8,
            'core/get.json': 9,
            'core/create-and-update.json': 10,
            'core/status-codes.json': 11,
            
            # API v2 Resources section (alphabetical within groups)
            'resources/additional-fields.json': 100,
            'resources/brokerages.json': 101,
            'resources/company.json': 102,
            'resources/contact-groups.json': 103,
            'resources/contact-ratings.json': 104,
            'resources/contacts.json': 105,
            'resources/contracts.json': 106,
            'resources/contract-statuses.json': 107,
            'resources/countries.json': 108,
            'resources/custom-fields.json': 109,
            'resources/deposits.json': 110,
            'resources/events.json': 111,
            'resources/external-commissions.json': 112,
            'resources/floorplans.json': 113,
            'resources/followup-schedules.json': 114,
            'resources/interaction-types.json': 115,
            'resources/interactions.json': 116,
            'resources/internal-commisions.json': 117,
            'resources/inventory-statuses.json': 118,
            'resources/inventory.json': 119,
            'resources/legal-firms.json': 120,
            'resources/lenders.json': 121,
            'resources/notes.json': 122,
            'resources/parking.json': 123,
            'resources/projects.json': 124,
            'resources/questions.json': 125,
            'resources/question-answers.json': 126,
            'resources/registration-sources.json': 127,
            'resources/reservations.json': 128,
            'resources/standardized-fields.json': 129,
            'resources/storage.json': 130,
            'resources/team-members.json': 131,
            
            # Forms section
            'forms/registration-form.json': 200,
            
            # Meta files
            'meta/manifest.json': 300,
            'meta/search-index.json': 301,
        }
        
        def get_sort_key(file_item):
            # file_item should be a dictionary
            if isinstance(file_item, dict):
                name = file_item.get('name', '')
            else:
                name = str(file_item)
            return order_mapping.get(name, 999)
        
        return sorted(files, key=get_sort_key)

    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[{self.address_string()}] {format % args}")

def find_available_port(start_port=8000, max_attempts=10):
    """Find an available port starting from start_port"""
    import socket
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return None

def open_browser_delayed(url, delay=2):
    """Open browser after a short delay"""
    time.sleep(delay)
    print(f"🌐 Opening browser to {url}")
    webbrowser.open(url)

def main():
    """Main function to start the server"""
    # Configuration
    HOST = 'localhost'
    PREFERRED_PORT = 8000
    
    # Find an available port
    PORT = find_available_port(PREFERRED_PORT)
    if PORT is None:
        print(f"❌ Error: Could not find an available port starting from {PREFERRED_PORT}")
        return
    
    # Check for JSON files
    json_files = list(Path('.').glob('*.json'))
    print(f"📄 Found {len(json_files)} JSON files:")
    for file in json_files:
        size = file.stat().st_size
        size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
        print(f"   • {file.name} ({size_str})")
    
    if not json_files:
        print("⚠️  Warning: No JSON files found in current directory")
        print("   The viewer will be empty until you add some JSON files")
    
    print(f"\n🚀 Starting JSON Viewer Server...")
    if PORT != PREFERRED_PORT:
        print(f"   Port {PREFERRED_PORT} was busy, using port {PORT} instead")
    print(f"   Server: http://{HOST}:{PORT}")
    print(f"   Directory: {os.getcwd()}")
    
    # Print KB summary
    try:
        if KB_ROOT.exists():
            kb_files = [p for p in KB_ROOT.rglob('*') if p.is_file()]
            print(f"📚 KB Root: {KB_ROOT} ({len(kb_files)} files)")
        else:
            print(f"📚 KB Root: {KB_ROOT} (not found)")
    except Exception as e:
        print(f"📚 KB scan error: {e}")

    try:
        with socketserver.TCPServer((HOST, PORT), JSONViewerHandler) as httpd:
            print(f"✅ Server running on http://{HOST}:{PORT}")
            print(f"📖 Docs Viewer: http://{HOST}:{PORT}/docs/")
            print("\n🎯 Features:")
            print("   • Beautiful, responsive interface")
            print("   • Automatic JSON file discovery")
            print("   • Syntax highlighting and formatting")
            print("   • Collapsible JSON objects")
            print("   • File search functionality")
            print("\nPress Ctrl+C to stop the server")
            
            # Open browser automatically
            browser_thread = threading.Thread(
                target=open_browser_delayed, 
                args=(f"http://{HOST}:{PORT}/", 2)
            )
            browser_thread.daemon = True
            browser_thread.start()
            
            # Start serving
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
