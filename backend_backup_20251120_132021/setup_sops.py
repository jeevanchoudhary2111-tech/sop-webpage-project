#!/usr/bin/env python3
import re
from pymongo import MongoClient
from datetime import datetime
from bs4 import BeautifulSoup
import os

MONGO_HOST = "localhost"
MONGO_PORT = 27017
MONGO_USER = "admin"
MONGO_PASSWORD = "KiviCap209"
MONGO_DB = "appdb"

SOP_FILES = {
    "gift_sop": {"file": "gift_sop.html", "name": "GIFT SOP", "type": "gift_sop", "category": "trading"},
    "gift_infra_sop": {"file": "gift_infra_sop.html", "name": "GIFT Infrastructure", "type": "gift_infra_sop", "category": "infrastructure"},
    "mcx_sop": {"file": "mcx_sop.html", "name": "MCX SOP", "type": "mcx_sop", "category": "trading"},
    "mcx_position_sop": {"file": "mcx_position_sop.html", "name": "MCX Position", "type": "mcx_position_sop", "category": "trading"},
    "bse_daily_file_sop": {"file": "bse_daily_file_sop.html", "name": "BSE Files", "type": "bse_daily_file_sop", "category": "trading"},
    "us_position_sop": {"file": "us_position_sop.html", "name": "US Position", "type": "us_position_sop", "category": "trading"},
    "lease_line_sop": {"file": "lease_line_sop.html", "name": "Lease Line", "type": "lease_line_sop", "category": "infrastructure"}
}

def extract_tasks_from_html(html_file):
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        soup = BeautifulSoup(content, 'html.parser')
        tasks = []
        task_id = 1
        checkboxes = soup.find_all('input', {'class': 'sop-task'})
        for checkbox in checkboxes:
            desc = checkbox.get('data-description', '')
            if not desc:
                parent = checkbox.parent
                if parent:
                    desc = re.sub(r'\s+', ' ', parent.get_text().strip())
            tasks.append({"id": task_id, "task_id": checkbox.get('data-task-id', f'task_{task_id}'), "description": desc, "completed": False})
            task_id += 1
        return tasks
    except Exception as e:
        print(f"Error parsing {html_file}: {e}")
        return []

def setup_sops(frontend_dir):
    print("\n🚀 Starting SOP Setup...\n")
    client = MongoClient(f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/", authSource="admin")
    db = client[MONGO_DB]
    print("✅ Connected to MongoDB")
    
    sop_definitions = db['sop_definitions']
    sop_definitions.delete_many({})
    print("🗑️  Cleared existing SOPs\n")
    
    for sop_key, sop_info in SOP_FILES.items():
        html_file = os.path.join(frontend_dir, sop_info['file'])
        print(f"📄 Processing {sop_info['name']}...")
        
        if not os.path.exists(html_file):
            print(f"   ⚠️  File not found: {html_file}\n")
            continue
        
        tasks = extract_tasks_from_html(html_file)
        if not tasks:
            print(f"   ⚠️  No tasks found\n")
            continue
        
        print(f"   ✅ Found {len(tasks)} tasks")
        
        sop_def = {
            "name": sop_info['name'],
            "sop_type": sop_info['type'],
            "category": sop_info['category'],
            "tasks": tasks,
            "total_tasks": len(tasks),
            "created_at": datetime.now(),
            "active": True
        }
        
        result = sop_definitions.insert_one(sop_def)
        print(f"   💾 Saved to database\n")
    
    print("="*60)
    print(f"✅ Created {sop_definitions.count_documents({})} SOPs")
    print("🌐 Open http://localhost:8080 and refresh!")
    print("="*60 + "\n")

if __name__ == "__main__":
    import sys
    frontend_dir = sys.argv[1] if len(sys.argv) > 1 else "../frontend"
    frontend_dir = os.path.abspath(frontend_dir)
    if not os.path.exists(frontend_dir):
        print(f"❌ Directory not found: {frontend_dir}")
        sys.exit(1)
    setup_sops(frontend_dir)
