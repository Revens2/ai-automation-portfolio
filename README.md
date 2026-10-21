# Juliann, AI Engineering Portfolio

Static bilingual portfolio documenting personal AI agent systems, RAG, MCP integrations, self-hosted infrastructure and software products.

## Public pages

| French | English |
| --- | --- |
| `fr/index.html` | `index.html` |
| `fr/architecture.html` | `architecture.html` |
| `fr/projets.html` | `projects.html` |
| `fr/projets/{orchestration,rag,sandbox,watchy,audits}.html` | `projects/{orchestration,rag,sandbox,watchy,audits}.html` |

The architecture page presents a sanitized conceptual overview of a Windows runner, remote server, repurposed ARM64 smartphone agent node, DIY Debian NAS, private network, and RAG services.

All new diagrams are authored using the connected Excalidraw MCP. Each is checked for overlaps and text readability, stored as an editable Excalidraw document and rendered as a scalable vector image. SVG exports are derived from Excalidraw elements, not separately authored architectures.

## Editorial conventions

* Distinguish the implementation of a project from its verification.
* Public source does not imply an open-source license.
* Mark private and experimental systems clearly.
* No confidential hosts, IPs, tokens, paths, ports, credential details or private network policies.
* No invented hours, savings, ROI, performance benchmarks or client impact.
* Do not include unrelated employment anecdotes.
* Avoid long dash punctuation in prose and UI.

## Local review

Run `python -m http.server 8000` and open the site, or inspect the GitHub Pages deployment. CI validates HTML links and privacy, then uses Chromium to exercise layouts at multiple viewport sizes.

See [the published portfolio](https://revens2.github.io/ai-automation-portfolio/).
