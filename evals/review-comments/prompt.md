---
description: Acting on review comments should load review-feedback
tags: [skills]
allowed_tools: [Read, Glob, Grep, Skill]
max_turns: 8
---
The reviewer left these comments on my PR. Please address them:
1. "parseAmount swallows the NumberFormatException; surface it as a 400."
2. "Rename `tmp` in BookingService.reserve to something meaningful."
3. "Why not cache the room lookup? It is called on every request."
