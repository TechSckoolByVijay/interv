from shared.logger import logger

def main():
    logger.info("Worker starting up.")
    try:
        # Initialize resources (e.g., DB, queues)
        logger.info("Initializing resources.")
        # ...existing initialization code...

        logger.info("Worker entering main loop.")
        while True:
            logger.debug("Waiting for next job.")
            job = get_next_job()
            if job is None:
                logger.debug("No job found, sleeping.")
                time.sleep(1)
                continue

            logger.info(f"Processing job: {job.id}")
            try:
                process_job(job)
                logger.info(f"Job {job.id} processed successfully.")
            except Exception as e:
                logger.error(f"Error processing job {job.id}: {e}", exc_info=True)
                handle_failed_job(job, e)
    except KeyboardInterrupt:
        logger.info("Worker shutdown requested by user.")
    except Exception as e:
        logger.critical(f"Worker crashed: {e}", exc_info=True)
    finally:
        logger.info("Worker shutting down. Cleaning up resources.")
        # ...existing cleanup code...

if __name__ == "__main__":
    main()