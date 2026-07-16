# Mars Climate Orbiter Interlude Reflection

## 1. Implicit Assumptions in My Document
- **Timezones**: The next steps say "Tuesday afternoon" and "Wednesday morning" without specifying a timezone (e.g. UTC vs. PST). In a remote/distributed team, this is an implicit assumption that leads to missed deadlines.
- **Documentation Location**: "review the current schema design guidelines in our repository documentation" assumes the reader knows where this document resides, instead of providing a direct file path or hyperlink.
- **Prior Knowledge**: Assumes Priya knows who "Alex" is and how to contact him.

## 2. Specifications or Interfaces to Verify
- In software development, API payload formats and schema fields are frequently assumed to be clear. A crucial step to explicitly verify them is implementing consumer-driven contract testing (like Pact) or sharing mock endpoints before code is written, asking: *"Does this mock response cover your entire data requirement?"*

## 3. Deciding Which Trivial Clarifications are Worth Making
- **Blast Radius**: Clarifications are worth making if the cost of a misunderstanding has a high blast radius (e.g. cross-system APIs, database migrations, security controls).
- **Ad-hoc Questions**: If a team member asks for clarification on a specific point more than once, it is a signal that the documentation must be permanently updated to be explicit.
