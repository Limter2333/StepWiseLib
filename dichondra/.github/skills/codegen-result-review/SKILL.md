---
name: codegen-result-review
description: Evaluate generated code against requirements, correctness, completeness, maintainability, test coverage, security, and delivery readiness. Use whenever the user asks to review AI-generated code, assess whether generated implementation is acceptable, compare generated output to a spec or ticket, score a code generation result, or decide whether the generated code is ready to merge.
---

# Code Generation Result Review

Use this skill when code already exists and the main question is whether the generated result is good enough.

This skill is for evaluation, not for blind rewriting. The first job is to determine whether the generated code satisfies the request, what is broken or missing, and what risks remain.

## When To Use

Trigger this skill when the user asks for any of the following:

- Review generated code
- Judge whether AI-generated code is correct
- Compare implementation against a requirement, ticket, PRD, or design doc
- Score or rank code generation results from one or more models
- Decide whether generated code is ready for merge, release, or handoff
- Identify defects, regressions, missing tests, or unsafe changes in generated output

Do not use this skill when the main task is writing a new feature from scratch and there is no implementation yet.

## Core Principles

- Requirements are the baseline. Do not grade code in isolation.
- Findings come before summaries.
- Prefer command-backed verification over intuition.
- Distinguish verified facts from unverified concerns.
- Missing behavior is as important as broken behavior.
- A clean diff is not the same as a correct implementation.
- If tests were not run, say so explicitly.

## Required Inputs

Before evaluating, gather as many of these as possible:

1. The original user request, ticket, or requirement.
2. The generated files, diff, commit, or PR.
3. The relevant runtime context: language, framework, dependencies, environment.
4. Any stated constraints: performance, security, compatibility, style, timeline.
5. Existing tests, build commands, lint commands, and type checks.
6. Any baseline implementation or prior version for regression comparison.

If the requirement is vague, extract an evaluation checklist from the user request before judging the code.

## Evaluation Workflow

### 1. Reconstruct The Expected Outcome

Translate the request into a concrete checklist.

Include:

- Functional requirements
- Non-functional requirements
- Explicit constraints
- Edge cases implied by the request
- Expected outputs or side effects

If multiple interpretations are possible, call them out before scoring.

### 2. Inspect The Implementation Surface

Review the generated output at the right scope:

- Changed files
- Interfaces and public APIs
- Data flow
- Error handling paths
- State changes
- Persistence, network, filesystem, and auth boundaries
- Tests and fixtures

Do not stop at the “happy path” logic.

### 3. Verify With Evidence

When possible, run the relevant checks:

- Build
- Tests
- Lint
- Type check
- Smoke run
- Focused repro for suspicious paths

If execution is not possible, downgrade certainty and say exactly what could not be verified.

### 4. Evaluate Across Seven Dimensions

Score each dimension on a 0 to 5 scale.

#### A. Requirement Coverage

Ask:

- Did the implementation satisfy the requested scope?
- Are any required behaviors missing?
- Did it add surprising behavior not requested?

#### B. Correctness

Ask:

- Does the logic actually work?
- Are edge cases handled?
- Are return values, state updates, and side effects correct?

#### C. Code Quality

Ask:

- Is the structure understandable?
- Are names, abstractions, and boundaries coherent?
- Is complexity justified or accidental?

#### D. Test Adequacy

Ask:

- Are there tests for the changed behavior?
- Do tests cover failure paths and edge cases?
- Are the tests meaningful or superficial?

#### E. Reliability And Operations

Ask:

- Does it handle retries, timeouts, nulls, bad input, and partial failure?
- Will it fail safely?
- Is logging or observability sufficient for debugging?

#### F. Security And Safety

Ask:

- Does it expand permissions, inputs, or trust boundaries?
- Could it expose secrets, unsafe execution, injection, or authorization issues?
- Does it validate untrusted input?

#### G. Delivery Readiness

Ask:

- Is this ready to merge as-is?
- Are docs, config, migrations, or rollout notes missing?
- Would another engineer be able to operate or extend it safely?

### 5. Prioritize Findings

Classify findings by severity:

- `critical`: likely data loss, security issue, broken core behavior, or unsafe release blocker
- `high`: major requirement miss, regression, or strong chance of production failure
- `medium`: meaningful quality gap, edge-case bug, missing validation, or insufficient test coverage
- `low`: maintainability issue, polish gap, or non-blocking inconsistency

Each finding should include:

1. What is wrong
2. Why it matters
3. Where it is located
4. How confident you are
5. What evidence supports it

### 6. Produce A Verdict

Use one of these verdicts:

- `accept`: requirements appear met and no blocking issues were found
- `revise`: useful output, but changes are needed before merge
- `reject`: fundamentally incorrect, unsafe, or too incomplete to rely on
- `partial`: some parts are validated, but environment limits prevent a full verdict

## Scoring Rubric

Use this scale consistently:

- `5`: Strong and production-ready for this dimension
- `4`: Good with minor non-blocking gaps
- `3`: Mixed quality; usable but needs revision
- `2`: Weak; multiple material issues
- `1`: Poor; mostly fails the dimension
- `0`: Missing, broken, or impossible to trust

Overall score guidance:

- `4.5 - 5.0`: Strong accept
- `3.5 - 4.4`: Acceptable with targeted revisions
- `2.5 - 3.4`: Needs substantial revision
- `0.0 - 2.4`: Reject

Do not let a high average hide a critical blocker. A single critical issue can still force `reject`.

## Output Contract

Unless the user asks for a different format, produce results in this structure:

### 1. Findings

List findings first, ordered by severity.

For each finding, use:

```text
[severity] Short title
- Location: file/path.ext:line
- Issue: what is wrong
- Impact: why it matters
- Evidence: command result, code path, or reasoning
- Fix direction: shortest credible repair path
```

If no findings were identified, say that explicitly.

### 2. Scorecard

```text
Requirement Coverage: x/5
Correctness: x/5
Code Quality: x/5
Test Adequacy: x/5
Reliability And Operations: x/5
Security And Safety: x/5
Delivery Readiness: x/5
Overall: x.x/5
Verdict: accept | revise | reject | partial
```

### 3. Evidence Gaps

List anything you could not verify, for example:

- Tests not run
- Missing environment
- External services unavailable
- Browser or device path not exercised

### 4. Short Summary

End with a brief judgment in 2 to 4 sentences.

## Comparison Mode

If the user provides outputs from multiple models, compare them on the same rubric.

For multi-model comparison:

1. Build one shared requirement checklist.
2. Score each result independently.
3. Call out requirement misses and hidden regressions before style differences.
4. Rank by delivery readiness, not by how polished the prose looks.
5. State which result is easiest to salvage if none are acceptable.

Use this table when useful:

```text
Candidate | Coverage | Correctness | Tests | Security | Readiness | Verdict
```

## Failure Modes To Avoid

- Praising code before checking requirement coverage
- Confusing “looks clean” with “works correctly”
- Reporting style nits while missing broken behavior
- Claiming tests passed without running them
- Hiding uncertainty instead of labeling it
- Giving only a score and no actionable findings
- Treating lack of evidence as evidence of correctness

## Reviewer Stance

Be direct, evidence-first, and specific.

The goal is not to be harsh. The goal is to make the generated result trustworthy enough to accept, revise, or reject with clear reasoning.