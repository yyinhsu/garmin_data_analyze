---
name: agent-dev-manager
description: 'Task decomposition and multi-skill orchestration for complex development workflows. Use this skill when: (1) A user request involves code changes such as new features, fixes, refactoring, or module additions — route these through openspec skills, (2) A request spans multiple domains that map to different skills (e.g., code generation + testing + documentation), (3) Planning multi-step development tasks that benefit from structured breakdown, (4) Coordinating work across feature modules, infrastructure, and configuration layers.'
---

# Agent Dev Manager

Decompose complex requests into sub-tasks, route each to the appropriate skill, and execute in dependency order.

## Routing Rules

**Code changes** (new features, fixes, refactoring, adding modules, upgrading dependencies):

- Route to `openspec-new-change` for step-by-step artifact creation
- Route to `openspec-ff-change` when the user wants speed or says "just do it"
- NEVER bypass openspec for code changes — do NOT substitute with built-in todo lists

**Exploration** (unclear requirements, brainstorming, investigating options):

- Route to `openspec-explore`

**Continuing existing work**:

- Route to `openspec-continue-change` or `openspec-apply-change` based on artifact status

**Verification / archival**:

- Route to `openspec-verify-change` or `openspec-archive-change` as appropriate

## Task Decomposition

When a request involves multiple concerns:

1. Identify each sub-task's domain (feature module, config, infrastructure, etc.)
2. Check if a dedicated skill's description matches — if so, follow that skill's workflow
3. Execute in dependency order (e.g., Prisma model → service → controller → module registration)

Coordinate sequentially when sub-tasks have dependencies; parallelize when independent.

## When No Skill Matches

Proceed with general knowledge — do not block progress waiting for a perfect match.
