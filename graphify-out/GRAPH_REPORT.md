# Graph Report - frontend/src  (2026-09-16)

## Corpus Check
- Corpus is ~548 words - fits in a single context window. You may not need a graph.

## Summary
- 9 nodes · 9 edges · 2 communities (1 shown, 1 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 1

## God Nodes (most connected - your core abstractions)
1. `App()` - 2 edges
2. `belts` - 1 edges
3. `beltData` - 1 edges
4. `eventTemplates` - 1 edges

## Surprising Connections (you probably didn't know these)
- None detected - all connections are within the same source files.

## Import Cycles
- None detected.

## Communities (2 total, 1 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.29
Nodes (3): beltData, belts, eventTemplates

## Knowledge Gaps
- **3 isolated node(s):** `belts`, `beltData`, `eventTemplates`
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `belts`, `beltData`, `eventTemplates` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._