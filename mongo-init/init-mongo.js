// mongo-init/init-mongo.js
// MongoDB initialization script
// This script runs when MongoDB container starts for the first time

// Switch to the application database
db = db.getSiblingDB('appdb');

// Create collections with proper indexes for performance
db.createCollection('users');
db.createCollection('sop_activities');
db.createCollection('daily_reports');
db.createCollection('backup_metadata');
db.createCollection('us_position_data');
db.createCollection('sop_definitions'); // ADD THIS LINE

// Create indexes for better query performance
db.users.createIndex({ "username": 1 }, { unique: true });
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "role": 1 });
db.users.createIndex({ "shift": 1 });
db.users.createIndex({ "exchanges": 1 });

// SOP Activities indexes
db.sop_activities.createIndex({ "user_id": 1 });
db.sop_activities.createIndex({ "sop_type": 1 });
db.sop_activities.createIndex({ "task_id": 1 });
db.sop_activities.createIndex({ "completed_at": -1 });
db.sop_activities.createIndex({ "username": 1 });

// Compound indexes for efficient filtering
db.sop_activities.createIndex({ "sop_type": 1, "completed_at": -1 });
db.sop_activities.createIndex({ "user_id": 1, "sop_type": 1 });
db.sop_activities.createIndex({ "sop_type": 1, "task_id": 1 });

// Daily reports indexes
db.daily_reports.createIndex({ "report_date": -1 });
db.daily_reports.createIndex({ "generated_at": -1 });

// Backup metadata indexes
db.backup_metadata.createIndex({ "backup_date": -1 });
db.backup_metadata.createIndex({ "created_at": -1 });
db.backup_metadata.createIndex({ "backup_type": 1 });

// US Position data indexes
db.us_position_data.createIndex({ "date": -1 });
db.us_position_data.createIndex({ "last_updated_at": -1 });

// SOP Definitions indexes (ADD THESE LINES)
db.sop_definitions.createIndex({ "sop_type": 1 }, { unique: true });
db.sop_definitions.createIndex({ "display_name": 1 });

print('Database initialization completed successfully');
print('Created collections: users, sop_activities, daily_reports, backup_metadata, us_position_data, sop_definitions'); // MODIFIED LINE
print('Created performance indexes for all collections');