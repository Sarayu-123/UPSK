import os
import sys

# Ensure api directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.models import Link

def run():
    db = SessionLocal()
    try:
        # Clean existing test codes to avoid unique constraint issues if re-run
        db.query(Link).filter(Link.code == "testcode123").delete()
        db.commit()

        # Insert new link
        new_link = Link(
            code="testcode123",
            long_url="https://google.com",
            created_by="seed-script"
        )
        db.add(new_link)
        db.commit()
        db.refresh(new_link)
        print(f"inserted code: {new_link.code}")

        # Query by code
        queried = db.query(Link).filter(Link.code == "testcode123").first()
        if queried:
            print(f"selected code: {queried.code}")
            print(f"matched long_url: {queried.long_url}")
        else:
            print("Error: link not found")
    finally:
        db.close()

if __name__ == "__main__":
    run()
