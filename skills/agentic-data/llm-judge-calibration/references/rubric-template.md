# Rubric template — llm-judge-calibration

A 5-point rubric. Each point needs a definition, an example and anti-examples.
Copy this file and fill in the brackets.

```yaml
rubric_id: "task-safety-v1"
scale: 1-5
points:
  - score: 5
    definition: "[one line: what a perfect answer does]"
    example: |
      [a real submission that earns 5]
    anti_examples:
      - "[something that looks good but is only a 4]"
  - score: 4
    definition: "[one line]"
    example: |
      [a real submission that earns 4]
    anti_examples:
      - "[something that earns 3]"
  - score: 3
    definition: "adequate but incomplete or contains a minor error"
    example: |
      [a real submission that earns 3]
    anti_examples: ["[something that earns 2]"]
  - score: 2
    definition: "[one line]"
    example: |
      [a real submission that earns 2]
    anti_examples: ["[something that earns 1]"]
  - score: 1
    definition: "[one line]"
    example: |
      [a real submission that earns 1]
    anti_examples: []
```

Rules:
- Every point except the lowest needs at least one anti-example.
- Examples come from real submissions, not made-up ones.
- The rubric is versioned (`rubric_id`); re-run calibration when it changes.
