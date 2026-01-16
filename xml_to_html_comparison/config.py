"""
Configuration settings for the Validator script.
Includes Environment definitions, Document Type mappings, and Ignored sets.
"""

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
