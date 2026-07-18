# SearchScience

> AI-Powered Multi-Source Academic Paper Deep Analysis System

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

SearchScience is a Codex agent skill that acts as your **personal research tutor**.
It searches CNKI, arXiv, PubMed, Google Scholar, IEEE, and Semantic Scholar, then
performs **teaching-level deep analysis** (not just abstract translation!), generates
a Chinese PDF daily report, downloads original PDFs, and finds corresponding GitHub
implementations -- all driven by your YAML research profile.

---

## Quick Start

`ash
git clone https://github.com/Q-clou/searchscinece.git
cd searchscinece
pip install -r requirements.txt
`

`ash
python scripts/setup_wizard.py
python scripts/cli.py --profile profiles/your_profile.yaml
`

---

## 10-Level Deep Analysis

| # | Section | What It Does |
|---|---------|-------------|
| 1 | Knowledge Map | Prerequisites + new concepts with everyday analogies |
| 2 | Problem Analysis | Why existing methods fail, what the author saw |
| 3 | Method Overview | Pipeline diagram + design choices with reasoning |
| 4 | Method Deep Dive | Component breakdown to pseudocode level |
| 5 | Innovation Analysis | What is novel and why non-trivial |
| 6 | Experiment Insights | Reads between the numbers |
| 7 | Reproduction Guide | Hardware, steps, common pitfalls |
| 8 | Critical Thinking | Strengths, weaknesses, open questions |
| 9 | Personal Relevance | Value to YOUR research + action items |
| 10 | Learning Roadmap | 5-phase path from zero to reproduction |

---

## License

MIT
