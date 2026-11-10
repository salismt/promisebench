---
name: New agent harness
about: Add a coding agent that the runner can drive
labels: agent
---

**Agent** (name, version, link):

**Command that runs it non-interactively on one prompt, inside a directory:**

**Transcript format** (JSON lines? where do commands, the final reply, cost and tool errors appear?). Paste a short synthetic example, not a real transcript.

**Isolation:** how can user config, plugins, MCP servers and network access be turned off? What can you not turn off?

**Credentials:** how does the agent authenticate, and how will the harness keep them out of results?

**How does the agent report a blocked tool call** (needed to count guard refusals)?

I have read CONTRIBUTING.md: yes / no
