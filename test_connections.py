#!/usr/bin/env python3
"""
Test script để kiểm tra kết nối MongoDB và Qdrant
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(verbose=True)
mongodb_url = os.getenv('MONGODB_URL') or os.getenv('MONGODB_URI', 'NOT_SET')
qdrant_url = os.getenv('QDRANT_URL', 'NOT_SET')
print(f"[ENV] MongoDB_URL loaded: {bool(mongodb_url != 'NOT_SET')}")
print(f"[ENV] QDRANT_URL loaded: {qdrant_url[:50]}...")

def test_mongodb_connection():
    """Test MongoDB connection"""
    print("[TEST] Testing MongoDB connection...")

    try:
        from pymongo import MongoClient
        from pymongo.errors import ServerSelectionTimeoutError

        # Get MongoDB URL from environment or config
        mongodb_url = os.getenv("MONGODB_URL") or os.getenv("MONGODB_URI", "")

        if not mongodb_url:
            print("[WARN] MONGODB_URL not set in environment")
            return False

        print(f"[URL] Connecting to: {mongodb_url[:50]}...")

        # Try to connect with timeout
        client = MongoClient(mongodb_url, serverSelectionTimeoutMS=5000)

        # Test connection
        client.admin.command('ping')
        print("[OK] MongoDB connection successful!")

        # Get database info
        db = client.get_default_database()
        if db:
            print(f"[INFO] Database: {db.name}")

            # List collections
            collections = db.list_collection_names()
            print(f"[DIR] Collections: {collections}")

        client.close()
        return True

    except ServerSelectionTimeoutError:
        print("[ERROR] MongoDB connection timeout - check URL and network")
        return False
    except Exception as e:
        print(f"[ERROR] MongoDB connection failed: {e}")
        return False

def test_qdrant_connection():
    """Test Qdrant connection"""
    print("\n[TEST] Testing Qdrant connection...")

    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams

        # Get Qdrant URL from environment or config
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        qdrant_key = os.getenv("QDRANT_API_KEY", "")

        print(f"[URL] Connecting to Qdrant: {qdrant_url}")

        # Create client with API key if available
        if qdrant_key:
            client = QdrantClient(url=qdrant_url, api_key=qdrant_key)
        else:
            client = QdrantClient(url=qdrant_url)

        # Test connection
        collections = client.get_collections()
        print("[OK] Qdrant connection successful!")

        # List existing collections
        collection_names = [c.name for c in collections.collections]
        print(f"[DIR] Collections: {collection_names}")

        return True

    except ImportError:
        print("[ERROR] qdrant-client not installed. Run: pip install qdrant-client")
        return False
    except Exception as e:
        print(f"[ERROR] Qdrant connection failed: {e}")
        return False

def test_app_connections():
    """Test connections as used by the app"""
    print("\n[TEST] Testing app connection logic...")

    try:
        # Add src to path
        sys.path.insert(0, 'src')

        # Test config loading
        from core.config import config
        print("[OK] Config loaded")

        print(f"[CONFIG] MongoDB enabled: {config.USE_MONGODB}")
        print(f"[CONFIG] MongoDB URL set: {bool(config.MONGODB_URL)}")
        print(f"[CONFIG] Qdrant URL: {config.QDRANT_URL}")

        # Test MongoDB repo if enabled
        if config.USE_MONGODB:
            print("[INFO] MongoDB enabled in config")
            try:
                from repositories.mongodb_repository import mongodb_repo
                if mongodb_repo:
                    print("[OK] MongoDB repository imported")
                    if mongodb_repo.is_available():
                        print("[OK] MongoDB repository connected")
                    else:
                        print("[WARN] MongoDB repository not connected (may be normal)")
                else:
                    print("[ERROR] MongoDB repository is None")
            except ImportError as e:
                print(f"[WARN] MongoDB repo not available: {e}")
            except Exception as e:
                print(f"[ERROR] MongoDB repo error: {e}")

        # Test Qdrant repo
        try:
            from repositories.qdrant_repository import qdrant_repo
            if qdrant_repo:
                print("[OK] Qdrant repository imported")
                if qdrant_repo.is_available():
                    print("[OK] Qdrant repository connected")
                    # Get collection info
                    info = qdrant_repo.get_collection_info()
                    if info:
                        print(f"[INFO] Collection info: {info}")
                    else:
                        print("[WARN] No collection info available")
                else:
                    print("[ERROR] Qdrant repository not connected")
            else:
                print("[ERROR] Qdrant repository is None")
        except ImportError as e:
            print(f"[WARN] Qdrant repo not available: {e}")
        except Exception as e:
            print(f"[ERROR] Qdrant repo error: {e}")

        return True

    except Exception as e:
        print(f"[ERROR] App connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_connection_guide():
    """Show connection setup guide"""
    print("\n[GUIDE] Setup Guide:")
    print("=" * 50)

    print("\n[CONFIG] For MongoDB Atlas:")
    print("1. Go to https://mongodb.com/atlas")
    print("2. Create account and cluster")
    print("3. Get connection string from 'Connect > Connect your application'")
    print("4. Set environment variable:")
    print('   export MONGODB_URL="mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority"')
    print("5. Optional: set DATABASE_NAME (default: chatbot_db)")

    print("\n[CONFIG] For Local MongoDB:")
    print("1. Install MongoDB locally")
    print("2. Start MongoDB service")
    print("3. Set: export MONGODB_URL='mongodb://localhost:27017'")

    print("\n[CONFIG] For Qdrant:")
    print("1. Install Qdrant: docker run -p 6333:6333 qdrant/qdrant")
    print("2. Or use cloud: https://cloud.qdrant.io/")
    print("3. Set: export QDRANT_URL='http://localhost:6333'")

    print("\n[CONFIG] Environment Setup:")
    print("# Create .env file:")
    print("cat > .env << EOF")
    print("GEMINI_API_KEY=your_key_here")
    print("MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/")
    print("DATABASE_NAME=chatbot_db")
    print("QDRANT_URL=http://localhost:6333")
    print("EOF")

if __name__ == "__main__":
    print("Database Connection Tests")
    print("=" * 50)

    # Test individual connections
    mongodb_ok = test_mongodb_connection()
    qdrant_ok = test_qdrant_connection()

    # Test app integration
    app_ok = test_app_connections()

    print("\n" + "=" * 50)
    print("[INFO] RESULTS:")
    print(f"[CONFIG] MongoDB: {'[OK] Connected' if mongodb_ok else '[ERROR] Not connected'}")
    print(f"[CONFIG] Qdrant: {'[OK] Connected' if qdrant_ok else '[ERROR] Not connected'}")
    print(f"[CONFIG] App Integration: {'[OK] Working' if app_ok else '[ERROR] Failed'}")

    if not mongodb_ok or not qdrant_ok:
        show_connection_guide()

    success_count = sum([mongodb_ok, qdrant_ok, app_ok])
    print(f"\n[RESULT] Overall: {success_count}/3 connections working")

    if success_count == 3:
        print("[SUCCESS] All connections successful! Ready to use.")
    elif success_count >= 1:
        print("[WARN] Partial success - some features may not work.")
    else:
        print("[ERROR] No connections working - check setup.")
