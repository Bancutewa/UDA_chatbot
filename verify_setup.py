import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

try:
    print("Attempting to import src.api.main...")
    from src.api.main import app
    print("Successfully imported app!")
    print(f"App title: {app.title}")
    
    # Check routers
    routes = [route.path for route in app.routes]
    print(f"Registered routes count: {len(routes)}")
    # print(routes)
    
except Exception as e:
    print(f"FAILED to import app: {e}")
    sys.exit(1)
