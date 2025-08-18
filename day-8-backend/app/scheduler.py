"""
APScheduler-based scheduler for crypto daily digest.
Alternative to cron-based scheduling.
"""

import os
import logging
import signal
import sys
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import pytz

from main import run_ai_insights as run_crypto_digest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Docker logs to stdout/stderr
    ]
)
logger = logging.getLogger(__name__)

# Timezone configuration
TIMEZONE = pytz.timezone('Europe/Amsterdam')
SCHEDULE_HOUR = int(os.getenv('SCHEDULE_HOUR', '22'))
SCHEDULE_MINUTE = int(os.getenv('SCHEDULE_MINUTE', '0'))


class CryptoDigestScheduler:
    """Scheduler for crypto daily digest service."""
    
    def __init__(self):
        self.scheduler = BlockingScheduler(timezone=TIMEZONE)
        self.setup_job_listeners()
        self.setup_signal_handlers()
    
    def setup_job_listeners(self):
        """Setup job event listeners for monitoring."""
        
        def job_listener(event):
            if event.exception:
                logger.error(f"Job failed: {event.job_id}, Exception: {event.exception}")
            else:
                logger.info(f"Job completed successfully: {event.job_id}")
        
        self.scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    
    def setup_signal_handlers(self):
        """Setup graceful shutdown on signals."""
        
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down gracefully...")
            self.scheduler.shutdown(wait=True)
            sys.exit(0)
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    
    def job_wrapper(self):
        """Wrapper for the crypto digest job with additional logging."""
        job_start = datetime.now(TIMEZONE)
        logger.info(f"=== Starting crypto digest job at {job_start.strftime('%Y-%m-%d %H:%M:%S %Z')} ===")
        
        try:
            run_crypto_digest()
            job_end = datetime.now(TIMEZONE)
            duration = (job_end - job_start).total_seconds()
            logger.info(f"=== Job completed in {duration:.2f} seconds ===")
            
        except Exception as e:
            job_end = datetime.now(TIMEZONE)
            duration = (job_end - job_start).total_seconds()
            logger.error(f"=== Job failed after {duration:.2f} seconds: {str(e)} ===")
            raise
    
    def add_daily_job(self):
        """Add the daily crypto digest job."""
        trigger = CronTrigger(
            hour=SCHEDULE_HOUR,
            minute=SCHEDULE_MINUTE,
            timezone=TIMEZONE
        )
        
        self.scheduler.add_job(
            func=self.job_wrapper,
            trigger=trigger,
            id='crypto_daily_digest',
            name='Crypto Daily Digest',
            misfire_grace_time=300,  # Allow 5 minutes grace for missed jobs
            coalesce=True,  # Combine missed jobs into one
            max_instances=1  # Only one instance at a time
        )
        
        logger.info(f"Scheduled daily crypto digest at {SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d} {TIMEZONE}")
    
    def run_now_for_testing(self):
        """Run the job immediately for testing purposes."""
        logger.info("Running crypto digest immediately for testing...")
        self.job_wrapper()
    
    def add_dev_job(self):
        """Add development job that runs every 2 minutes."""
        from apscheduler.triggers.interval import IntervalTrigger
        
        trigger = IntervalTrigger(minutes=2, timezone=TIMEZONE)
        
        self.scheduler.add_job(
            func=self.job_wrapper,
            trigger=trigger,
            id='crypto_dev_digest',
            name='Crypto Dev Digest (Every 2 min)',
            misfire_grace_time=60,  # Allow 1 minute grace for missed jobs
            coalesce=True,  # Combine missed jobs into one
            max_instances=1  # Only one instance at a time
        )
        
        logger.info("📅 Scheduled dev digest every 2 minutes")
    
    def start_dev(self):
        """Start the development scheduler."""
        logger.info("=== 🧪 Crypto Dev Scheduler Starting ===")
        logger.info(f"Current time: {datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # Print next run time info
        logger.info("📅 Next run: in 2 minutes")
        
        # Start scheduler
        try:
            logger.info("🔄 Dev Scheduler started. Press Ctrl+C to exit.")
            logger.info("⏰ Will send AI insights every 2 minutes!")
            self.scheduler.start()
        except KeyboardInterrupt:
            logger.info("⛔ Dev Scheduler stopped by user.")
        except Exception as e:
            logger.error(f"❌ Dev Scheduler error: {str(e)}")
            raise
    
    def start(self):
        """Start the scheduler."""
        logger.info("=== Crypto Digest Scheduler Starting ===")
        logger.info(f"Current time: {datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # Add the daily job
        self.add_daily_job()
        
        # Print next run time
        next_run = self.scheduler.get_jobs()[0].next_run_time
        logger.info(f"Next scheduled run: {next_run.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # Start scheduler
        try:
            logger.info("Scheduler started. Press Ctrl+C to exit.")
            self.scheduler.start()
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user.")
        except Exception as e:
            logger.error(f"Scheduler error: {str(e)}")
            raise


def main():
    """Main entry point for the scheduler."""
    scheduler = CryptoDigestScheduler()
    
    # Check for different modes
    if len(sys.argv) > 1:
        if sys.argv[1] == '--test':
            scheduler.run_now_for_testing()
        elif sys.argv[1] == '--immediate':
            # Run immediately and then start normal schedule
            logger.info("🏃 Running immediately, then starting normal schedule...")
            try:
                scheduler.run_now_for_testing()
                logger.info("✅ Immediate run completed, starting normal schedule...")
            except Exception as e:
                logger.error(f"❌ Immediate run failed: {e}")
            scheduler.start()
        elif sys.argv[1] == '--dev':
            # Development mode: immediate + every 2 minutes
            logger.info("🧪 Development mode: immediate + every 2 minutes")
            scheduler.run_now_for_testing()
            scheduler.add_dev_job()
            scheduler.start_dev()
        else:
            logger.info(f"Unknown argument: {sys.argv[1]}")
            scheduler.start()
    else:
        scheduler.start()


if __name__ == "__main__":
    main()

