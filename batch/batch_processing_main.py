from pyspark.sql import SparkSession
import os
import time
import datetime
import subprocess
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("batch_processing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("batch_processor")

# List of batch processing scripts
batch_scripts = [
    "batch_top_songs_weekly.py",
    "batch_top_artists_weekly.py",
    "batch_monthly_yearly_listen_time.py",
    "batch_listening_trends_dashboard.py"
]

def run_batch_job(script_path):
    """Run a Spark batch job using spark-submit"""
    try:
        logger.info(f"Starting batch job: {script_path}")
        
        cmd = [
            "spark-submit",
            "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3,org.apache.kafka:kafka-clients:3.5.1",
            "--driver-class-path", "/Users/mehenazasghar/Downloads/mysql-connector-j-9.3.0/mysql-connector-j-9.3.0.jar",
            "--jars", "/Users/mehenazasghar/Downloads/mysql-connector-j-9.3.0/mysql-connector-j-9.3.0.jar",
            script_path
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            logger.info(f"Successfully completed batch job: {script_path}")
            logger.debug(f"Output: {stdout}")
            return True
        else:
            logger.error(f"Failed to run batch job: {script_path}")
            logger.error(f"Error: {stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Exception running batch job {script_path}: {str(e)}")
        return False

def main():
    """Main function to orchestrate batch processing"""
    logger.info("Starting batch processing orchestration")
    start_time = time.time()
    
    # Get current timestamp for reporting
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Batch processing run at: {timestamp}")
    
    success_count = 0
    failure_count = 0
    
    # Run each batch job
    for script in batch_scripts:
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script)
        if run_batch_job(script_path):
            success_count += 1
        else:
            failure_count += 1

    # Log summary
    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"Batch processing completed in {duration:.2f} seconds")
    logger.info(f"Summary: {success_count} jobs succeeded, {failure_count} jobs failed")

if __name__ == "__main__":
    main()