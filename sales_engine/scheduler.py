"""
Optional scheduler: re-runs the ETL pipeline automatically on a
schedule, so the database (and any connected Power BI report set
to scheduled refresh) always reflects current data.

Requires: pip install apscheduler

Usage:
    python -m sales_engine.scheduler
"""
try:
    from apscheduler.schedulers.blocking import BlockingScheduler
except ImportError:
    raise SystemExit(
        "APScheduler not installed. Run: pip install apscheduler --break-system-packages"
    )

from . import pipeline


def scheduled_run():
    print(f"\n[scheduler] Triggered pipeline run...")
    pipeline.run_pipeline()


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    # Runs every day at 2:00 AM. Adjust as needed.
    scheduler.add_job(scheduled_run, "cron", hour=2, minute=0)
    print("[scheduler] Started. Pipeline will run daily at 02:00. Ctrl+C to stop.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\n[scheduler] Stopped.")
