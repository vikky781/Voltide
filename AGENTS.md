# Voltide project instructions

- Canonical repository: https://github.com/vikky781/Voltide.
- After every completed implementation step or documentation milestone, run the relevant checks, commit the intended changes, and push to the canonical repository before moving to the next step. Report a failed push explicitly; a local commit alone does not complete this workflow. Never force-push or include credentials/generated environment files.
- DO NOT TRAIN ANY PART OF ANY MODEL LOCALLY. This PC has no GPU, and CPU training is also prohibited. All model fitting, fitted preprocessing, tuning, and retraining must run remotely in Zoho Catalyst QuickML. Local deterministic feature preparation, remote API inference calls, scoring, and application tests are allowed.
- The user has requested planning only so far. Begin product implementation only after the user requests it. Before implementing, read docs/superpowers/specs/2026-10-24-microgrid-design.md and docs/superpowers/plans/2026-10-24-microgrid-implementation-plan.md, then apply subsequent user decisions.

<!-- codebase-memory-mcp:start -->
## Codebase Knowledge Graph

Prefer codebase-memory-mcp graph tools over grep/glob/file-search for code discovery. If the project is not indexed, index_repository is the first graph operation, subject to access and approval requirements.

Priority order:
1. search_graph: find functions, classes, routes, and variables.
2. trace_path: trace callers and callees.
3. get_code_snippet: read a discovered function/class source.
4. query_graph: inspect complex relationships.
5. get_architecture: summarize project structure.

Fall back to local text/file search for string literals, errors, configuration, non-code files, or insufficient/unavailable graph results. Preserve any approval restrictions on indexing; do not bypass a rejected indexing action.
<!-- codebase-memory-mcp:end -->
