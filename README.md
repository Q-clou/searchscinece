# SearchScience

> AI-Powered Multi-Source Academic Paper Deep Analysis System

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

SearchScience is a Codex agent skill that acts as your **personal research tutor**. 
It searches CNKI, arXiv, PubMed, and more, then performs **teaching-level deep analysis** 
(not just abstract translation!), generates a Chinese PDF daily report, downloads PDFs, 
and finds GitHub implementations — all driven by your YAML research profile.

## 10-Level Deep Analysis

| # | Section | What It Does |
|---|---------|-------------|
| 1 | Knowledge Map | Prerequisites + new concepts with analogies |
| 2 | Problem Analysis | Why existing methods fail + core insight |
| 3 | Method Overview | Pipeline + design choices with reasoning |
| 4 | Method Deep Dive | Component breakdown to pseudocode level |
| 5 | Innovation Analysis | What is novel and why non-trivial |
| 6 | Experiment Insights | Read between the numbers |
| 7 | Reproduction Guide | Hardware, steps, pitfalls |
| 8 | Critical Thinking | Strengths, weaknesses, open questions |
| 9 | Personal Relevance | Value to YOUR research + action items |
| 10 | Learning Roadmap | 5-phase path from zero to reproduction |

## Quick Start

`ash
git clone https://github.com/qian6-donghua/searchscinece.git
cd searchscinece
pip install -r requirements.txt
`

`ash
python scripts/setup_wizard.py  # Create your profile
python scripts/cli.py --profile profiles/your_profile.yaml  # Run!
`

## Project Structure

`
searchscinece/
+-- scripts/   (cli, fetch, download, github, report)
+-- src/sources/   (cnki, pubmed, orchestrator)
+-- src/utils/   (config, progress, robustness)
+-- profiles/   (YAML research profiles)
+-- tests/   (unit tests)
`

## Dependencies

Python >= 3.9 + reportlab + pyyaml

## License

MIT
