# Module 07 Reflection: Postmortem Writing

## Knowledge Check

### 1. What core problem does this module solve in postmortem writing?
This module solves the problem of blame culture and vague, non-actionable postmortems by shifting focus from human errors ("carelessness") to systemic/process gaps. It enforces precise quantification of incident details (timelines, blast radius) and translates failures into actionable, owned, and deadlined remediations.

### 2. Which decision in this module has the biggest impact, and why?
The scoping decision (narrow vs. broad). Choosing narrow scope (focused on a single high-severity incident) allows the team to perform a deep, detailed root-cause analysis and produce highly specific, concrete remediations. Choosing broad scope (across multiple incidents) highlights systemic patterns but risks producing generic, un-actionable remediations.

### 3. What evidence proves the implementation works end-to-end?
The creation of two high-quality blameless postmortems:
1. `progress/technical-communication/auth-bypass-postmortem.md` (for the Bug #8 auth bypass incident).
2. `progress/technical-communication/db-outage-postmortem-rewrite.md` (the blameless rewrite of the database outage incident).
Both files contain precise timelines, systemic root causes, and specific, owned remediation items.

## Mini Practical Task
We successfully wrote and saved the postmortem for the Bug #8 auth bypass incident to `progress/technical-communication/auth-bypass-postmortem.md`. The file has been verified and accepted by the `upsk` platform.

## Risk and Mitigation
* **Risk**: High-pressure incident resolution can lead team members to point fingers at individuals, establishing a defensive/blame culture.
* **Mitigation**: Standardize postmortem templates to require systemic root causes (systems, toolchains, or processes) rather than human actors, and enforce peer reviews of all postmortems to flag blame language.
