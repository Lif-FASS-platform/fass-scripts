import logging
from config import TYPE_CONFIG, ARTIKEL_TYPES

logger = logging.getLogger("validator")


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
