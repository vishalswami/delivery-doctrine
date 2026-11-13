---
type: regex
pattern: '"type":\s*"text",\s*"text":\s*"(?:[^"\\]|\\.){0,600}?\b(?:full|low) gear'
flags: i
target: trace
---
Matches assistant text blocks only. The injected doctrine also sits in the trace; its first "Full gear" is past the 600-character window today, so recheck this grader if the doctrine's opening grows.
