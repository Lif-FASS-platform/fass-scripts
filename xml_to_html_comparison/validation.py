import logging
import re
import unicodedata

import lxml.etree as ET
from bs4 import BeautifulSoup
from config import GLOBAL_IGNORE_TAGS

logger = logging.getLogger("validator")


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
