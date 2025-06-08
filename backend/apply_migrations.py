import subprocess
import sys
from dotenv import load_dotenv
import os

def check_env_py_for_models():
    env_py_path = os.path.join(os.path.dirname(__file__), "migrations", "env.py")
    if not os.path.exists(env_py_path):
        print(f"WARNING: {env_py_path} does not exist!")
        return
    with open(env_py_path, "r", encoding="utf-8") as f:
        content = f.read()
        if "target_metadata = Base.metadata" in content:
            print("✅ Alembic env.py is set to use Base.metadata (models will be detected).")
        else:
            print("❌ WARNING: Alembic env.py does NOT set target_metadata = Base.metadata.")
            print("   Please add the following to your env.py:")
            print("   from app.models import Base")
            print("   target_metadata = Base.metadata")

def apply_migrations():
    # Load environment variables from app/.env
    env_path = os.path.join(os.path.dirname(__file__), "app", ".env")
    print(f"Loading .env from: {env_path}")
    load_dotenv(dotenv_path=env_path)

    # Print a key variable to verify loading
    print("DATABASE_URL:", os.getenv("DATABASE_URL"))
    print("All loaded env vars (filtered):")
    for k in ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "DATABASE_URL"]:
        print(f"{k}: {os.getenv(k)}")

    # Check Alembic env.py for correct model metadata
    check_env_py_for_models()

    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            check=True,
            capture_output=True,
            text=True,
            env=os.environ.copy()  # Ensure subprocess gets updated env vars
        )
        print("Migrations applied successfully:\n", result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error applying migrations:\n", e.stderr)

if __name__ == "__main__":
    apply_migrations()
