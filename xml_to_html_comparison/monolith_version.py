import argparse
import csv
import datetime
import logging
import os
import re
import sys
import unicodedata
from collections import Counter

import lxml.etree as ET
import oracledb
import psycopg2
from bs4 import BeautifulSoup

# ==========================================
# SECTION 1: CONFIGURATION
# ==========================================
# Environment Definitions
ENV_CONFIG = {
    "DEV": {
        "ORA": {
            "USER": "fassadmin_read",
            "PASS": "KIoVqBkwdOMVhpVqLSurrtzAdchF",
            "DSN": "localhost:50001/LIFDB",
        },
        "PG": {
            "DB": "api_1_14",
            "USER": "fassapi_read",
            "PASS": "VHDrUIfBqimAwXcIIhaOVDwLPOwe",
            "HOST": "localhost",
            "PORT": "50002",
        },
        "URL_BASE": "https://dev.tech.fass.se",
    },
    "ACC": {
        "ORA": {
            "USER": "fassadmin_read",
            "PASS": "MsYJidaZabRUTmFiNoEWJugfTQau",
            "DSN": "localhost:50301/LIFDB",
        },
        "PG": {
            "DB": "api_1_14",
            "USER": "fassapi_read",
            "PASS": "PcCqyRTpKgLSLXxUjkEJNoljlaAO",
            "HOST": "localhost",
            "PORT": "50302",
        },
        "URL_BASE": "https://test-www.fass.se",
    },
    "SYS": {
        "ORA": {
            "USER": "fassadmin_read",
            "PASS": "SysTestPasswordPlaceholder",
            "DSN": "localhost:50201/LIFDB",
        },
        "PG": {
            "DB": "api_1_14",
            "USER": "fassapi_read",
            "PASS": "SysTestPgPassPlaceholder",
            "HOST": "localhost",
            "PORT": "50202",
        },
        "URL_BASE": "https://sys.tech.fass.se",
    },
    "PROD": {
        "ORA": {
            "USER": "fassadmin_read",
            "PASS": "ProdPasswordPlaceholder",
            "DSN": "localhost:60501/LIFDB",
        },
        "PG": {
            "DB": "api_1_14",
            "USER": "fassapi_read",
            "PASS": "ProdPgPassPlaceholder",
            "HOST": "localhost",
            "PORT": "60502",
        },
        "URL_BASE": "https://www.fass.se",
    },
}

IGNORED_TYPES = {
    11,  # Company document
    200,  # Menu document
    210,  # Product tags
    220,  # Start page document
    230,  # Admin handbooks
    231,  # Admin document
    240,  # User guides
}

DEFAULT_LOSS_THRESHOLD = 0.00
GLOBAL_IGNORE_TAGS = ["audittrail-list", "meta-data"]
ARTIKEL_TYPES = {7, 32}

# Maps Oracle DOKUMENT_TYP -> Config Dict
TYPE_CONFIG = {
    3: {
        "table": "fassdocument.t_fass_document",
        "id_col": "document_id",
        "link_col": "npl_id",
        "url_template": "{base}/health/product/{}/fass-text",
        "ignore_tags": ["description"],
    },
    4: {
        "table": "fassdocument.t_veterinary_fass_document",
        "id_col": "document_id",
        "link_col": "npl_id",
        "url_template": "{base}/animal/product/{}/fass-text",
        "ignore_tags": ["description"],
    },
    6: {
        "table": "fasssmpc.t_fass_smpc",
        "id_col": "doc_id",
        "link_col": "npl_id",
        "url_template": "{base}/health/product/{}/smpc",
    },
    7: {
        "table": "fasspackageleaflet.t_fass_package_leaflet",
        "id_col": "document_id",
        "link_col": "npl_id",
        "url_template": "{base}/health/product/{}/pl",
        "ignore_tags": [
            "heading",
            "instructions-for-use",  # FASS-7720
            # "side-effects-children",  # FASS-7722
            "information-source",  # FASS-7727
        ],
    },
    14: {
        "table": "fasssmpc.t_veterinary_fass_smpc",
        "id_col": "doc_id",
        "link_col": "npl_id",
        "url_template": "{base}/animal/product/{}/smpc",
    },
    32: {
        "table": "fasspackageleaflet.t_veterinary_fass_package_leaflet",
        "id_col": "document_id",
        "link_col": "npl_id",
        "url_template": "{base}/animal/product/{}/pl",
        "ignore_tags": [
            "heading",
            "directions-for-use",
            "user-information",  # FASS-7711
        ],
    },
    80: {
        "table": "safetydatasheet.t_safety_data_sheet",
        "id_col": "document_id",
        "link_col": "npl_id",
        "url_template": "{base}/health/product/{}#safety-data-sheet",
    },
    78: {
        "table": "fassenvironmentalinformation.t_fass_environmental_information",
        "id_col": "document_id",
        "link_col": "substance_id",
        "url_template": "{base}/health/substance/{}",
        "ignore_tags": ["substance-number", "substance-name", "company-name"],
    },
}


# ==========================================
# SECTION 2: QUERIES
# ==========================================
def build_oracle_query(args, env_name):
    """
    Constructs the Oracle SQL query based on CLI arguments.

    Returns:
        tuple: (sql_query_string, output_filename)
    """
    select_clause = (
        "SELECT t.DOK_ID, t.DOKUMENT_TYP, t.CONTENT, t.NAMN FROM FASSADMIN.T_DOKUMENT t"
    )

    # 1. Specific Document ID (Investigative mode)
    if args.doc_id:
        logger.info(f"Running in INVESTIGATIVE mode for Document ID: {args.doc_id}")
        return (
            f"{select_clause} WHERE t.DOK_ID = '{args.doc_id}'",
            f"val_{env_name}_{args.doc_id}.csv",
        )

    # 2. Specific Types or All
    join_clause = """
        LEFT JOIN FASSADMIN.T_DOKUMENT_ARTIKEL da ON t.DOK_ID = da.DOK_ID
        LEFT JOIN FASSADMIN.T_DOKUMENT_PRODUKT dp ON t.DOK_ID = dp.DOK_ID
    """

    # Default condition for "ALL"
    where_condition = """
        (
            (t.DOKUMENT_TYP IN (7, 32) AND da.DOK_ID IS NOT NULL)
            OR
            (t.DOKUMENT_TYP NOT IN (7, 32) AND dp.DOK_ID IS NOT NULL)
        )
    """

    filename = f"oracle_to_pg_compare_{env_name}_all.csv"

    if args.types:
        target_types = [int(t.strip()) for t in args.types.split(",")]
        valid_types = [t for t in target_types if t in TYPE_CONFIG]

        if not valid_types:
            raise ValueError("No valid document types found in configuration.")

        logger.info(f"Processing ONLY types: {valid_types}")

        type_list_sql = ", ".join(map(str, valid_types))
        where_condition = f"t.DOKUMENT_TYP IN ({type_list_sql}) AND {where_condition}"

        type_suffix = "_".join(map(str, valid_types))
        filename = f"oracle_to_pg_compare_{env_name}_types_{type_suffix}.csv"

        # Optimization
        has_artikel = any(t in ARTIKEL_TYPES for t in valid_types)
        has_product = any(t not in ARTIKEL_TYPES for t in valid_types)

        if has_artikel and not has_product:
            join_clause = "JOIN FASSADMIN.T_DOKUMENT_ARTIKEL da ON t.DOK_ID = da.DOK_ID"
            where_condition = f"t.DOKUMENT_TYP IN ({type_list_sql})"
        elif has_product and not has_artikel:
            join_clause = "JOIN FASSADMIN.T_DOKUMENT_PRODUKT dp ON t.DOK_ID = dp.DOK_ID"
            where_condition = f"t.DOKUMENT_TYP IN ({type_list_sql})"

    return f"{select_clause} {join_clause} WHERE {where_condition}", filename


def fetch_postgres_content(pg_cursor, doc_id, config):
    """Fetches content and link ID from Postgres for a specific document."""
    pg_sql = f"SELECT content, {config['link_col']} FROM {config['table']} WHERE {config['id_col']} = %s"
    pg_cursor.execute(pg_sql, (doc_id,))
    return pg_cursor.fetchone()


# ==========================================
# SECTION 3: VALIDATION LOGIC
# ==========================================
def get_tokens(text):
    """
    Normalizes text (NFKC), removes symbols, separates digits,
    and returns a set of tokens.
    """
    if not text:
        return set()

    # 1. Normalize unicode characters (e.g., converts '²' to '2')
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()

    # 2. Replace non-word/non-whitespace symbols with space
    clean_text = re.sub(r"[^\w\s]", " ", text)

    # 3. Separate digits from words
    clean_text = re.sub(r"(\d)", r" \1 ", clean_text)

    # 4. Collapse whitespace
    clean_text = re.sub(r"\s+", " ", clean_text)

    return set(clean_text.split())


def clean_xml_content(oracle_xml, type_specific_ignores=None):
    """Parses Oracle XML, removes ignored tags, and extracts text."""
    parser = ET.XMLParser(recover=True)
    xml_root = ET.fromstring(oracle_xml.encode("utf-8"), parser=parser)

    all_ignores = list(GLOBAL_IGNORE_TAGS)
    if type_specific_ignores:
        all_ignores.extend(type_specific_ignores)

    if all_ignores:
        for tag in all_ignores:
            for element in xml_root.findall(f".//{tag}"):
                parent = element.getparent()
                if parent is not None:
                    parent.remove(element)

    return " ".join(xml_root.itertext())


def clean_html_content(postgres_html):
    """Parses Postgres HTML and extracts text."""
    soup = BeautifulSoup(postgres_html, "html.parser")
    return soup.get_text(" ")


def calculate_loss(oracle_tokens, postgres_tokens, threshold):
    """
    Compares token sets and calculates the percentage of missing words.
    Returns a status dict (SUCCESS/FAIL) with debug details.
    """
    if not oracle_tokens:
        logger.warning("Oracle content resulted in 0 tokens.")
        return None

    missing_words = oracle_tokens - postgres_tokens

    # Filter out very short words
    missing_words = {w for w in missing_words if len(w) > 2}

    loss_ratio = len(missing_words) / len(oracle_tokens)
    logger.debug(f"Calculated loss ratio: {loss_ratio:.4f}")

    if logger.isEnabledFor(logging.DEBUG) and missing_words:
        logger.debug(
            f"Missing words found (Count: {len(missing_words)}): {list(missing_words)}"
        )

    if loss_ratio > threshold:
        return {
            "status": "FAIL",
            "loss_raw": loss_ratio,
            "missing": list(missing_words)[:10],
        }

    return {"status": "SUCCESS", "loss_raw": loss_ratio}


def validate_content(oracle_xml, postgres_html, threshold, type_specific_ignores=None):
    """Orchestrates the cleaning and validation of two content strings."""
    if not oracle_xml or not postgres_html:
        return {"status": "ERROR", "msg": "Empty content found"}

    try:
        xml_text = clean_xml_content(oracle_xml, type_specific_ignores)
        html_text = clean_html_content(postgres_html)

        oracle_tokens = get_tokens(xml_text)
        postgres_tokens = get_tokens(html_text)
        logger.debug(
            f"Token counts - Oracle: {len(oracle_tokens)}, Postgres: {len(postgres_tokens)}"
        )

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"\n--- TOKEN TRACE ---\nORACLE: {str(oracle_tokens)[:200]}...\nPOSTGRES: {str(postgres_tokens)[:200]}...\n"
            )

        return calculate_loss(oracle_tokens, postgres_tokens, threshold)

    except Exception as e:
        logger.error(f"Validation exception: {e}", exc_info=True)
        return {"status": "ERROR", "msg": str(e)}


# ==========================================
# SECTION 4: MAIN SCRIPT
# ==========================================
# (The refactored main logic I just provided)
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
                if remaining > 0:  # Only show active types
                    logger.info(
                        f"   Type {dtype}: {processed}/{total} done ({remaining} remaining)"
                    )


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
