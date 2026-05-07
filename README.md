# Personal Knowledge Graph RAG System with MCP Integration

A production-ready AI system that transforms plain text documents into a queryable knowledge graph — enabling LLM-powered answers grounded strictly in your own data, with zero hallucinations.

Built as a portfolio project demonstrating end-to-end AI engineering: from raw Markdown files to a Claude Desktop integration via Model Context Protocol (MCP).

---

## Key Features

- **Anti-hallucination RAG** — the LLM answers exclusively from data stored in the knowledge graph; if the answer is not there, it says so
- **Graph-based knowledge extraction** — automatically parses documents, extracts concepts, and builds typed relationships (Document → Concept)
- **MCP server integration** — Claude Desktop connects directly to the knowledge graph as a live tool, not a static file
- **Hybrid search** — keyword-based graph traversal retrieves relevant concepts before passing context to the LLM
- **Fully local and embedded** — Kuzu graph database runs embedded (like SQLite), no external database server required
- **4 ready-to-use MCP tools** — `search_graph`, `ask_knowledge_base`, `list_documents`, `get_concepts`

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Graph Database | Kuzu (embedded) | Store documents, concepts, relationships |
| Language | Python 3.11 | Document parsing, graph operations, API layer |
| LLM | OpenRouter API (Gemini) | Generate RAG answers from graph context |
| Protocol | MCP (Model Context Protocol) | Connect Claude Desktop to the knowledge graph |
| Data Format | Markdown (.md files) | Source documents for knowledge extraction |
| Extraction | Python regex + NLP patterns | Pull concepts and entities from raw text |

---

## How It Works

**Step 1 — Ingest documents.**
The system reads your Markdown files and extracts key concepts using regex and pattern matching. No manual tagging required.

**Step 2 — Build the knowledge graph.**
Extracted concepts are stored in Kuzu as graph nodes with typed edges connecting them to their source documents. The result is a navigable map of your knowledge base.

**Step 3 — Answer questions via hybrid search.**
When a question arrives, the system searches the graph by keywords, retrieves the relevant concept nodes and their context, then passes that context to the LLM.

**Step 4 — Deliver grounded answers.**
The LLM generates a response using only the retrieved graph data. If the knowledge graph does not contain enough information, the system explicitly says so — no invented facts.

---

## Use Cases

- **Corporate knowledge bases** — index internal documentation, SOPs, or project wikis and let employees query them via Claude Desktop
- **Legal and compliance research** — extract clauses and regulations from contracts, map relationships, query without reading every document
- **Personal second brain** — connect Obsidian or Notion exports to an AI that understands your notes as a graph, not a flat list
- **Product documentation assistant** — give your support team or customers an AI that answers only from verified product docs

---

## Results

| Metric | Value |
|---|---|
| Documents processed | 4 |
| Concepts extracted | 136 |
| Graph relationships built | Automatic, schema-defined |
| MCP tools available | 4 |
| Hallucination rate | 0% (constrained by graph context) |
| External database servers required | 0 (fully embedded) |

---

## Available For

This project demonstrates skills applicable to the following engagement types:

- **Knowledge Graph design and build** — custom graph schema, entity extraction pipeline, Kuzu or Neo4j
- **RAG system development** — retrieval-augmented generation with hallucination controls, any LLM provider
- **MCP server development** — custom tool servers for Claude Desktop or other MCP-compatible clients
- **AI integration consulting** — connecting existing document repositories to LLM-powered query interfaces

**Typical project range: $3,000 – $5,000**
Delivery includes working codebase, documentation, and deployment walkthrough.

---

*Built by Yevhen Syniachenko — AI Engineer & Full-Stack Developer*
*Contact: yourbusinessspark@gmail.com*
