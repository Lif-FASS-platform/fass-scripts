import argparse
import csv
import datetime
import logging
import os
import sys
from collections import Counter

import oracledb
import psycopg2
from config import (DEFAULT_LOSS_THRESHOLD, ENV_CONFIG, IGNORED_TYPES,
                    TYPE_CONFIG)
from queries import build_oracle_query, fetch_postgres_content
from validation import validate_content

# --- LOGGING SETUP ---
logger = logging.getLogger("validator")


class DocCounter:
    """Tracks document statistics by type."""
    def __init__(self):
        self.total_by_type = Counter()
        self.processed_by_type = Counter()
        self.stats = {"processed": 0, "failures": 0, "skipped": 0}

    def register_batch(self, rows):
        """Pre-scans a batch to update total counts."""
        for row in rows:
            try:
                doc_type = row[1]
                self.total_by_type[doc_type] += 1
            except IndexError:
                continue

    def update(self, doc_type, status):
        """Updates progress for a specific document."""
        self.processed_by_type[doc_type] += 1
        
        if status == "SUCCESS":
            self.stats["processed"] += 1
        elif status == "FAIL":
            self.stats["failures"] += 1
            self.stats["processed"] += 1
        elif status == "SKIPPED":
            self.stats["skipped"] += 1

    def log_progress(self):
        """Logs current progress per document type."""
        if self.stats["processed"] > 0 and self.stats["processed"] % 1000 == 0:
            logger.info(f"--- Progress: {self.stats['processed']} docs processed ---")
            for dtype, total in self.total_by_type.items():
                processed = self.processed_by_type[dtype]
                remaining = total - processed
                if remaining > 0: # Only show active types
                    logger.info(f"   Type {dtype}: {processed}/{total} done ({remaining} remaining)")


def setup_logging(debug_mode, output_dir, doc_id=None):
    """Configures console and file logging."""
    logger.handlers = []
    file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    if debug_mode:
        logger.setLevel(logging.DEBUG)
        timestamp = datetime.datetime.now().strftime("%H%M%S")
        filename = (
            f"trace_{doc_id}_{timestamp}.log" if doc_id else f"trace_{timestamp}.log"
        )
        filepath = os.path.join(output_dir, filename)
        file_handler = logging.FileHandler(filepath, mode="w", encoding="utf-8")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        print(f"--- DEBUG MODE: Detailed trace log will be written to {filepath} ---")
    else:
        logger.setLevel(logging.INFO)


def write_result_to_csv(
    csv_writer, doc_id, doc_type, table_short, status, loss="", url="", msg=""
):
    """Helper to write a standardized row to the CSV output."""
    csv_writer.writerow(
        [doc_id, doc_type, table_short, status, str(loss).replace(".", ","), url, msg]
    )


def process_single_document(row, pg_cursor, csv_writer, unknown_types, url_base):
    """
    Processes a single row from Oracle:
    1. Checks if type is valid.
    2. Fetches corresponding Postgres content.
    3. Runs validation logic.
    4. Writes result to CSV.
    """
    try:
        doc_id, doc_type, clob_obj, doc_name = row
    except IndexError:
        return "ERROR"

    logger.debug(f"--- Processing Doc ID: {doc_id} (Type: {doc_type}) ---")

    if doc_type in IGNORED_TYPES:
        return "SKIPPED"

    if doc_type not in TYPE_CONFIG:
        if doc_type not in unknown_types:
            logger.warning(f"Unknown Type ID: {doc_type} | Name example: {doc_name}")
            unknown_types.add(doc_type)
        return "SKIPPED"

    config = TYPE_CONFIG[doc_type]

    # Fetch Postgres Data
    pg_result = fetch_postgres_content(pg_cursor, doc_id, config)
    table_short = config["table"].split(".")[-1]

    if not pg_result:
        msg = f"Doc ID {doc_id} not found in Postgres table {config['table']}"
        logger.warning(msg)
        write_result_to_csv(
            csv_writer, doc_id, doc_type, table_short, "MISSING_IN_PG", msg=msg
        )
        return "FAIL"

    # Validate
    oracle_clob = clob_obj.read() if hasattr(clob_obj, "read") else str(clob_obj)
    pg_html, link_id = pg_result

    result = validate_content(
        oracle_clob,
        pg_html,
        config.get("loss_threshold", DEFAULT_LOSS_THRESHOLD),
        config.get("ignore_tags", []),
    )

    if not result:
        logger.info(
            f"SKIPPED: ID: {doc_id} | Type: {doc_type} | No content to validate."
        )
        return "SKIPPED"

    # Generate URL using base from env config
    url = config["url_template"].format(link_id, base=url_base) if link_id else "N/A"

    if result["status"] == "FAIL":
        logger.info(
            f"FAIL: ID: {doc_id} | Type: {doc_type} | Loss: {result['loss_raw']:.2%}"
        )
        write_result_to_csv(
            csv_writer,
            doc_id,
            doc_type,
            table_short,
            "FAIL",
            result["loss_raw"],
            url,
            ", ".join(result["missing"]),
        )
        return "FAIL"

    if result["status"] == "ERROR":
        logger.error(f"ERROR: ID: {doc_id}: {result['msg']}")
        write_result_to_csv(
            csv_writer,
            doc_id,
            doc_type,
            table_short,
            "ERROR",
            url=url,
            msg=result["msg"],
        )
        return "FAIL"

    logger.debug(f"SUCCESS: ID: {doc_id} passed validation.")
    return "SUCCESS"


def get_db_connections(env_config):
    """Establishes connections to both Oracle and Postgres."""
    ora_conf = env_config["ORA"]
    pg_conf = env_config["PG"]

    ora_conn = oracledb.connect(
        user=ora_conf["USER"],
        password=ora_conf["PASS"],
        dsn=ora_conf["DSN"],
    )
    pg_conn = psycopg2.connect(
        dbname=pg_conf["DB"],
        user=pg_conf["USER"],
        password=pg_conf["PASS"],
        host=pg_conf["HOST"],
        port=pg_conf["PORT"],
    )
    return ora_conn, pg_conn


def process_batch(rows, pg_cursor, csv_writer, context):
    """Iterates through a batch of rows and processes them."""
    unknown_types, processed_ids, url_base, counter = context
    
    # Pre-register batch for accurate "Total" counts
    counter.register_batch(rows)

    for row in rows:
        try:
            doc_id, doc_type = row[0], row[1]
        except IndexError:
            continue

        if doc_id in processed_ids:
            continue
        processed_ids.add(doc_id)

        status = process_single_document(
            row, pg_cursor, csv_writer, unknown_types, url_base
        )
        
        counter.update(doc_type, status)
        counter.log_progress()


def run_validation_loop(ora_cursor, pg_cursor, csv_writer, current_env):
    """Main loop fetching batches from Oracle."""
    context = (set(), set(), current_env["URL_BASE"], DocCounter())
    
    while True:
        rows = ora_cursor.fetchmany(100)
        if not rows:
            break
        process_batch(rows, pg_cursor, csv_writer, context)
        
    return context[3].stats  # Return stats from counter


def parse_arguments():
    parser = argparse.ArgumentParser(description="Validate Oracle vs Postgres content.")
    parser.add_argument(
        "--env",
        type=str,
        default="DEV",
        choices=ENV_CONFIG.keys(),
        help="Target Environment (default: DEV)",
    )
    parser.add_argument(
        "--types", type=str, help="Comma separated list of document types."
    )
    parser.add_argument("--doc_id", type=str, help="Specific Document ID.")
    parser.add_argument(
        "--debug", action="store_true", help="Enable verbose debug logging."
    )
    return parser.parse_args()


def main():
    args = parse_arguments()
    env_key = args.env.upper()
    current_env = ENV_CONFIG[env_key]

    # Setup Directory
    timestamp_folder = datetime.datetime.now().strftime("output_%Y%m%d")
    if not os.path.exists(timestamp_folder):
        os.makedirs(timestamp_folder)

    setup_logging(args.debug, timestamp_folder, args.doc_id)
    logger.info(f"Targeting Environment: {env_key}")

    try:
        oracle_query, filename = build_oracle_query(args, env_key)
        output_file_path = os.path.join(timestamp_folder, filename)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    logger.debug(f"Oracle Query: {oracle_query}")

    try:
        with open(output_file_path, mode="w", newline="", encoding="utf-8-sig") as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow(
                ["doc_id", "doc_type", "table", "status", "loss", "url", "missing"]
            )

            ora_conn, pg_conn = get_db_connections(current_env)
            logger.info("Connected to databases.")

            with ora_conn, pg_conn:
                with ora_conn.cursor() as ora_cursor, pg_conn.cursor() as pg_cursor:
                    logger.info("Fetching Oracle documents...")
                    ora_cursor.execute(oracle_query)
                    
                    final_stats = run_validation_loop(
                        ora_cursor, pg_cursor, csv_writer, current_env
                    )

        logger.info(
            f"Done. Processed: {final_stats['processed']}. "
            f"Failures: {final_stats['failures']}. Skipped: {final_stats['skipped']}"
        )
        logger.info(f"Results written to: {output_file_path}")

    except (oracledb.Error, psycopg2.Error) as e:
        logger.critical(f"Database Error: {e}")
    except Exception as e:
        logger.critical(f"General Error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
