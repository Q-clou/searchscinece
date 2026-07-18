# -*- coding: utf-8 -*-
# SearchScience v5.0 - Sources package
from src.sources.cnki import build_cnki_queries, parse_cnki_results, dedup_cnki
from src.sources.pubmed import build_pubmed_queries, parse_pubmed_results
from src.sources.orchestrator import MultiSourceOrchestrator, SourceStatus
