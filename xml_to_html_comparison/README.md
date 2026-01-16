# Oracle to Postgres Content Validator

This tool validates content migration by comparing XML data from Oracle against HTML content in Postgres. It tokenizes content from both sources and calculates a "loss ratio" to determine if significant text is missing in the destination.

## Prerequisites

Ensure you have a Python environment set up with the following packages:

```bash
pip install lxml oracledb psycopg2 beautifulsoup4
```

## Configuration

- **Database Credentials**: Defined in `config.py` under `ENV_CONFIG`.
- **Document Types**: Mappings between Oracle types and Postgres tables are in `config.py` under `TYPE_CONFIG`.
- **Ignored Tags**: XML tags stripped before comparison are defined in `GLOBAL_IGNORE_TAGS` (config.py).

## Usage

Run the script from the command line:

```bash
python main.py [OPTIONS]
```

### Options

- `--env [DEV|ACC|SYS|PROD]`: Target environment (Default: `DEV`).
- `--types "7,32"`: Comma-separated list of document types to process. If omitted, checks all configured types.
- `--doc_id "12345"`: Run validation for a single specific document ID (Investigative mode).
- `--debug`: Enable verbose logging and token tracing to a file.

### Examples

**1. Validate all documents in AccTest environment:**

```bash
python main.py --env ACC
```

**2. Validate only Package Leaflets (Type 7) in DEV:**

```bash
python main.py --env DEV --types 7
```

**3. Debug a specific failure:**

```bash
python main.py --doc_id "12345" --debug
```

## Output

The script creates an `output_YYYYMMDD` directory containing:

1.  **CSV Report**: Lists failed documents with their loss ratio and missing words.
2.  **Trace Logs**: (If `--debug` is used) Detailed logs showing token comparisons.
