---
name: aspen-introduction
description: "Aspen project overview and core principles. Load when starting a new task, reviewing mission, understanding dual-contract reasoning, rubric-only scoring, calibration targets (Opus ~75-85%, Qwen ~20-50%), or E2B/Docker reproducibility requirements."
user-invocable: false
---

# Realm Aspen: Expert Onboarding Guide

Welcome to Realm Aspen! This pipeline evaluates an AI agent's ability to author comprehensive test suites. The model must read a codebase, deduce the required behavioral model (a new feature, a regression, or an edge case), and write a test suite that codifies the correct implementation parameters.

Aspen is rubric-only. The agent delivers a test suite, and an LLM judge scores the agent's git diff against a weighted rubric.

## Project Mission

The agent is tasked with writing a test suite to cover a specific scenario, such as to catch a (series of) bug(s), feature implementation, or unit tests to guard against regression. A well-written test suite should be unambiguous: it validates the primary behaviour while asserting that legitimate flows and operations still work and are unbroken. This dual contract ("leak must be closed" AND anti-regression) is the structural discriminator Aspen measures.

## Core Design Principles

**Threat-Model Induction:** Tasks measure whether the agent can articulate what behavior the scenario requires and where alternative implementations could diverge. We are measuring test coverage and logic, not code style.

**Dual-Contract Reasoning:** Every Aspen task carries an anti-overblock or anti-regression contract alongside its primary leak-coverage contract. Rubrics must include items that fail agents if they write overly restrictive tests that break legitimate application flows.

For example, in a cybersecurity/vulnerability related task, rubrics could include explicit "regression-guard" to fail agents that over-blocks legitimate participant or admin flows.

**Rubric-Only Scoring:** The platform converts each entry in your `ground_truth_issues[]` into a criterion, weighted by severity. The LLM judge scores the agent's submission against the ground truth.

**Reproducibility:** Every task ships as a containerized environment. The agent reviews the code live within this isolated state.

All images are to be uploaded to the micro1 docker hub (micro1ai/).

**Isolated Substrates:** We use small, hand-authored web services, real public GitHub repos, or a combination of both.

## Technical Foundation

Experts in this project will work with:

- **Docker:** A Docker image as the agent's isolated working environment under the E2B template-builder convention.
- **Realm Platform:** For task upload, model evaluation runs, rubric scoring, and QC review.
- **LLM Judge:** Each rubric item is converted to a natural-language assertion the judge evaluates against the agent's submitted git diff.

## Models & Calibration Targets

Aspen calibrates against two models. A task is considered DISCRIMINATIVE when the frontier model clearly outperforms the smaller model.

- **Claude Opus 4.7:** Target ≥80% on a **single run**. One clean run is sufficient. Repeated 95-100% runs mean the task is too easy or the prompt leaks too much.
- **Qwen (mid-tier):** Run **4 times**, target 20–50% mean. It should catch obvious behaviors but miss chained reasoning and hard rubric items.

The goal is a clean separation curve of ~0.20+ between models. Opus should be strong but still miss the hardest rungs; Qwen should catch only the well-taught or obvious behaviors.

## Language & Stack Strategy

Prefer variety. **Less common languages** (Rust, Kotlin, Erlang, Swift) have less model training data, which gives more discrimination room and prevents pattern-matching on well-known frameworks. Actively choose unusual stacks when the scenario supports it.
