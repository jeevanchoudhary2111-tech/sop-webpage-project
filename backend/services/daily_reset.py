# backend/services/daily_reset.py

import asyncio
import schedule
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from database import get_sop_activity_collection
from database import get_user_collection
import io
import logging
import os 

# Import the new utility function
from services.report_utils import generate_sop_backup_html_report

logger = logging.getLogger(__name__)

class DailyResetService:
    def __init__(self):
        self.ist_tz = ZoneInfo("Asia/Kolkata")
        self.reset_completed = False
        
    async def daily_reset_job(self):
        """Daily reset job that runs at 3 AM IST"""
        try:
            logger.info("Starting daily reset job at 3 AM IST")
            
            # Get current IST time
            now_ist = datetime.now(self.ist_tz)
            
            # Calculate yesterday's date range (from previous 3 AM to current 3 AM)
            yesterday_3am = now_ist.replace(hour=3, minute=0, second=0, microsecond=0) - timedelta(days=1)
            today_3am = now_ist.replace(hour=3, minute=0, second=0, microsecond=0)
            
            # Convert to UTC for database query
            yesterday_3am_utc = yesterday_3am.astimezone(timezone.utc)
            today_3am_utc = today_3am.astimezone(timezone.utc).replace(tzinfo=None)
            
            # --- NEW: Generate and save all SOP activities backup ---
            sop_collection = get_sop_activity_collection()
            all_yesterday_activities = list(sop_collection.find({
                "completed_at": {
                    "$gte": yesterday_3am_utc,
                    "$lt": today_3am_utc
                }
            }).sort("completed_at", -1))

            if all_yesterday_activities:
                report_html = generate_sop_backup_html_report(
                    all_yesterday_activities,
                    f"All SOPs Daily Backup for {yesterday_3am.strftime('%Y-%m-%d')}",
                    "Automated System"
                )
                
                backup_dir = "/app/backups"
                os.makedirs(backup_dir, exist_ok=True) # Ensure directory exists
                
                filename = f"all_sops_daily_backup_{yesterday_3am.strftime('%Y-%m-%d')}.html"
                filepath = os.path.join(backup_dir, filename)
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(report_html)
                logger.info(f"Generated daily all SOPs backup: {filepath}")
            else:
                logger.info("No SOP activities found for yesterday to backup.")
            # --- END NEW SECTION ---

            # Archive yesterday's data
            await self.archive_daily_data(yesterday_3am_utc, today_3am_utc)
            
            # Generate daily report
            await self.generate_daily_report(yesterday_3am_utc, today_3am_utc)
            
            # Perform system reset
            await self.perform_system_reset()
            
            self.reset_completed = True
            logger.info("Daily reset job completed successfully")
            
        except Exception as e:
            logger.error(f"Daily reset job failed: {e}")
            
    async def perform_system_reset(self):
        """Perform complete system reset"""
        try:
            logger.info("Performing system reset")
            
            # Clear temporary data
            await self._clear_temporary_data()
            
            # Reset user session flags
            await self._reset_user_sessions()
            
            # Archive daily logs
            await self._archive_daily_logs()
            
            logger.info("System reset completed")
            
        except Exception as e:
            logger.error(f"System reset failed: {e}")
            raise
            
    async def _clear_temporary_data(self):
        """Clear temporary collections and data"""
        try:
            sop_collection = get_sop_activity_collection()
            db = sop_collection.database
            
            # Clear temporary collections (if any)
            temp_collections = [name for name in db.list_collection_names() if name.startswith('temp_')]
            for collection_name in temp_collections:
                db.drop_collection(collection_name)
                logger.info(f"Cleared temporary collection: {collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to clear temporary data: {e}")
            
    async def _reset_user_sessions(self):
        """Reset user session flags"""
        try:
            user_collection = get_user_collection()
            
            # Reset session-related flags
            user_collection.update_many(
                {},
                {
                    "$unset": {
                        "current_session": "",
                        "shift_status": "",
                        "daily_login_count": "",
                        "last_activity": ""
                    }
                }
            )
            
            logger.info("User session flags reset")
            
        except Exception as e:
            logger.error(f"Failed to reset user sessions: {e}")
            
    async def _archive_daily_logs(self):
        """Archive daily logs and summaries"""
        try:
            sop_collection = get_sop_activity_collection()
            db = sop_collection.database
            
            # Archive system logs if they exist
            if "system_logs" in db.list_collection_names():
                logs_collection = db["system_logs"]
                logs = list(logs_collection.find({}))
                
                if logs:
                    archive_date = datetime.now(self.ist_tz).strftime("%Y_%m_%d")
                    archive_collection_name = f"system_logs_archive_{archive_date}"
                    archive_collection = db[archive_collection_name]
                    
                    # Add archive metadata
                    for log in logs:
                        log["archived_at"] = datetime.now()
                        log["archive_reason"] = "Daily system reset"
                    
                    archive_collection.insert_many(logs)
                    logs_collection.delete_many({})
                    
                    logger.info(f"Archived {len(logs)} system logs")
                    
        except Exception as e:
            logger.error(f"Failed to archive daily logs: {e}")
    async def archive_daily_data(self, start_time, end_time):
        """Archive yesterday's SOP activities"""
        try:
            sop_collection = get_sop_activity_collection()
            
            # Find all activities from yesterday
            activities = list(sop_collection.find({
                "completed_at": {
                    "$gte": start_time,
                    "$lt": end_time
                }
            }))
            
            if activities:
                # Create daily archive collection
                db = sop_collection.database
                archive_date = start_time.strftime("%Y_%m_%d")
                archive_collection_name = f"sop_activities_archive_{archive_date}"
                archive_collection = db[archive_collection_name]
                
                # Insert activities into archive
                archive_collection.insert_many(activities)
                
                logger.info(f"Archived {len(activities)} activities to {archive_collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to archive daily data: {e}")
            
    async def generate_daily_report(self, start_time, end_time):
        """Generate daily report for yesterday's activities"""
        try:
            sop_collection = get_sop_activity_collection()
            
            # Get all activities from yesterday
            activities = list(sop_collection.find({
                "completed_at": {
                    "$gte": start_time,
                    "$lt": end_time
                }
            }).sort("completed_at", -1))
            
            if not activities:
                logger.info("No activities found for daily report")
                return
                
            # Store report metadata in database
            db = sop_collection.database
            reports_collection = db["daily_reports"]
            
            report_data = {
                "report_date": start_time.strftime("%Y-%m-%d"),,
                "generated_at": datetime.utcnow(),
                "activity_count": len(activities),
                "unique_users": len(set(a["username"] for a in activities)),
                "unique_tasks": len(set(a["task_id"] for a in activities)),
                "sop_breakdown": self._get_sop_breakdown(activities)
            }
            
            reports_collection.insert_one(report_data)
            logger.info(f"Generated daily report for {start_time.date()} with {len(activities)} activities")
            
        except Exception as e:
            logger.error(f"Failed to generate daily report: {e}")
            
    def _get_sop_breakdown(self, activities):
        """Get breakdown of activities by SOP type"""
        breakdown = {}
        for activity in activities:
            sop_type = activity["sop_type"]
            if sop_type not in breakdown:
                breakdown[sop_type] = {
                    "count": 0,
                    "users": set(),
                    "tasks": set()
                }
            breakdown[sop_type]["count"] += 1
            breakdown[sop_type]["users"].add(activity["username"])
            breakdown[sop_type]["tasks"].add(activity["task_id"])
        
        # Convert sets to counts for JSON serialization
        for sop_type in breakdown:
            breakdown[sop_type]["unique_users"] = len(breakdown[sop_type]["users"])
            breakdown[sop_type]["unique_tasks"] = len(breakdown[sop_type]["tasks"])
            del breakdown[sop_type]["users"]
            del breakdown[sop_type]["tasks"]
            
        return breakdown
        
    async def clear_daily_tasks(self):
        """Clear completed tasks for new day (optional)"""
        # This is optional - you might want to keep the history
        # If you want to reset tasks daily, implement this
        pass
        
    def is_reset_completed_today(self):
        """Check if reset was completed today"""
        return self.reset_completed
        
    async def get_daily_report_data(self, report_date=None):
        """Get daily report data for a specific date"""
        try:
            sop_collection = get_sop_activity_collection()
            db = sop_collection.database
            reports_collection = db["daily_reports"]
            
            if report_date is None:
                # Get the most recent report
                report = reports_collection.find_one(sort=[("report_date", -1)])
            else:
                report = reports_collection.find_one({"report_date": report_date})
                
            return report
            
        except Exception as e:
            logger.error(f"Failed to get daily report data: {e}")
            return None

# Global instance
daily_reset_service = DailyResetService()

def run_scheduler():
    """Run the scheduler in a separate thread"""
    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop) # Set it as the current event loop for this thread

    def job_wrapper():
        # This function is called by `schedule` in the new thread.
        # It needs to run the async job in this thread's event loop.
        # `run_until_complete` will block until the coroutine finishes.
        loop.run_until_complete(daily_reset_service.daily_reset_job())

    # Schedule the job for 3 AM IST daily
    schedule.every().day.at("03:00").do(job_wrapper)

    # Keep the thread alive and run pending scheduled jobs
    while True:
        schedule.run_pending()
        time.sleep(60) # Check every minute
