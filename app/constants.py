"""
Application constants. Centralizes magic strings and supported formats.
"""

SUPPORTED_DOC_EXTENSIONS = frozenset({".docx", ".html", ".htm", ".pdf"})

RETRIEVAL_TOP_K = "top_k"
RETRIEVAL_MMR = "mmr"
RETRIEVAL_TECHNIQUES = frozenset({RETRIEVAL_TOP_K, RETRIEVAL_MMR})

CHUNKING_OVERLAP = "overlap"
CHUNKING_ROW_TABLE = "row_table"
CHUNKING_STRATEGIES = frozenset({CHUNKING_OVERLAP, CHUNKING_ROW_TABLE})

NOT_ENOUGH_CONTEXT_MSG = "Not enough context."
