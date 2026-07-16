# Interlude Reflection — The Therac-25

## 1. What is your equivalent of the "ready" indicator?
In an AI-augmented workflow, the equivalent of the "ready" indicator is the combination of **"code compiles successfully"** and **"automated unit tests pass."**
What we are NOT checking in those moments:
- **Business logic gaps**: Did the AI implement a secure and complete logical flow, or did it use a simpler, incorrect shortcut?
- **Security vulnerabilities**: Are there authorization bypasses, input validation holes, or privilege escalation paths that are not covered by tests?
- **Concurrency & edge cases**: Will the code fail under high volume, race conditions, or unhandled exceptions?
Pass indicators only verify that the tested scenarios work as written; they do not prove that the code is correct or safe.

## 2. What "interlocks" do you have in your AI workflow?
Our interlocks are:
- **Interface contracts**: Pre-defined rules that prevent model divergence.
- **Line-by-line code reviews**: Manually reading every line of generated code to ensure architectural alignment.
- **Independent verification checks**: Running custom curls, database queries, and edge-case test scripts (sanity checks).
If we remove these interlocks and succumb to complacency, the defect rate will double. A single bad suggestion could introduce severe regressions or vulnerabilities that compound silently until they cause a production incident.
