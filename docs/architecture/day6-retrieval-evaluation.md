# Day 6 — M2 Retrieval Evaluation

## Purpose

The purpose of this experiment is to measure the existing
retrieval system before introducing any retrieval improvements.

The experiment isolates retrieval from answer generation.

No LLM is used.

The evaluated architecture is:

Question
→ BGE-M3
→ Query Embedding
→ Qdrant Cosine Similarity
→ RetrievalService
→ Top-K Chunks

The purpose is not to make every question pass.

Unexpected results are recorded as baseline behavior.

---

## Current Retrieval Architecture

The current Business AI retrieval system uses:

- BGE-M3 dense embeddings
- 1024-dimensional vectors
- Qdrant
- cosine similarity
- transaction-level inventory chunks
- RetrievalService as the retrieval boundary

No reranking, metadata filtering, hybrid search, query
classification or structured retrieval is part of this
experiment.

---

## Controlled Dataset

The experiment uses the existing
Inventory_transactions.xlsx controlled test report.

It contains 13 ParsedRecords which are grouped into three
transaction-level chunks:

- D1IN0818
- D1IN0819
- D1IN0820

The evaluation dataset contains ten questions.

Eight questions contain expected retrievable evidence.

Two questions intentionally represent insufficient evidence.

---

## Evaluation Principle

Expected values represent evidence identifiers, not
natural-language answers.

A retrieved chunk is considered expected when its
transaction_number metadata matches one of the expected
transaction identifiers for the evaluation case.

Retrieval scores are recorded but are not interpreted as
confidence probabilities.

---

## Insufficient Evidence

Two questions intentionally cannot be answered from the
inventory report:

- Which vendor has the highest inventory value?
- Why did profit decline?

Semantic retrieval may still return inventory chunks for
these questions.

This is expected behavior.

The retrieval system is not responsible for deciding whether
the evidence is sufficient to answer the business question.

These cases are inspected but are not counted as ordinary
retrieval misses.

---

## Metrics

The experiment reports:

- total evaluation questions
- number of evidence-bearing questions
- Top-1 hit count
- Top-K hit count
- Top-1 retrieval accuracy
- Top-K retrieval success

A hit means at least one expected transaction appears within
the evaluated rank range.

The experiment is a small project-specific baseline and is
not a generalized or industry retrieval benchmark.

---

## Manual Inspection

For every query, the report records:

- question
- rank
- chunk ID
- transaction number
- similarity score
- source file
- source rows
- relevance label
- text preview

This permits direct inspection of:

Question
→ Retrieved Evidence
→ Expected Evidence

---

## Results

Results should be copied here after running:

    uv run python -m scripts.evaluate_retrieval

Record the actual output rather than hardcoding expected
retrieval scores.

### Top-1

To be filled from the executed experiment.

### Top-K

To be filled from the executed experiment.

### Unexpected Results

Record unexpected rankings without modifying the retrieval
algorithm.

---

## What We Learned

This experiment establishes a measurable baseline for the
existing semantic retrieval system.

It separates retrieval quality from LLM answer quality.

It also demonstrates that semantically related evidence may
still be retrieved for questions whose actual answer is not
present in the source report.

---

## Intentionally Not Changed

Day 6 M2 does not introduce:

- reranking
- hybrid retrieval
- metadata filtering
- structured SQL retrieval
- query classification
- another embedding model
- another vector database
- LLM reasoning
- retrieval score thresholds

Any observed failure remains part of the baseline.

Future retrieval improvements should be justified using the
observed evaluation results rather than introduced
prematurely.


## Results

The retrieval evaluation was executed against the controlled
Inventory_transactions.xlsx dataset using Top-K = 3.

The evaluation contained:

- 10 total questions
- 8 questions with expected retrievable evidence
- 2 insufficient-evidence questions

### Top-1 Results

All 8 evidence-bearing questions retrieved at least one
expected transaction at Rank 1.

Top-1 hits: 8/8

Top-1 retrieval accuracy: 100.00%

### Top-3 Results

All 8 evidence-bearing questions retrieved at least one
expected transaction within the first three results.

Top-3 hits: 8/8

Top-3 retrieval success: 100.00%

These results are specific to the small controlled project
dataset and must not be interpreted as a generalized
retrieval benchmark.

### Observed Retrieval Behavior

Direct transaction queries performed correctly.

D1IN0818 and D1IN0820 were ranked first when explicitly
referenced in their respective questions.

The product query for chilli powder correctly ranked
D1IN0818 first.

The TEAM 2 query correctly ranked D1IN0819 first.

The D1 vendor query retrieved both expected transactions:
D1IN0818 at Rank 1 and D1IN0820 at Rank 2.

The date query retrieved all three expected transactions
within Top-3 even though the current chunk representation
stores the Excel serial date 46143 rather than the
human-readable date.

The quantity comparison and total-quantity questions
retrieved all three transaction chunks required to perform
cross-transaction reasoning. This demonstrates evidence
retrieval only. It does not demonstrate that semantic
retrieval itself can perform aggregation or comparison.

### Insufficient-Evidence Behavior

For:

"Which vendor has the highest inventory value?"

Qdrant still returned inventory transaction chunks because
the query is semantically related to inventory data.

However, the report does not contain sufficient information
to calculate inventory value.

For:

"Why did profit decline?"

Qdrant also returned inventory transaction chunks despite
the report containing no profit information.

This demonstrates an important distinction:

Retrieval relevance does not imply answer sufficiency.

The retrieval implementation was intentionally not modified
to force these queries to return zero results.

### Observed Failure Cases

No Top-1 or Top-3 retrieval failures occurred among the
eight evidence-bearing questions in this controlled
experiment.

However, the experiment exposed limitations that should be
preserved as baseline observations:

1. Semantic retrieval still returns chunks for questions
   whose answers are not present in the report.

2. Excel dates are currently represented in chunks using
   their raw serial value.

3. Retrieval can provide evidence needed for aggregation
   questions, but retrieval itself does not perform the
   calculation.

4. The controlled collection contains only three chunks,
   so Top-3 includes the complete searchable dataset.

### What We Learned

The existing BGE-M3 + Qdrant semantic retrieval pipeline
successfully retrieves expected evidence for the current
controlled inventory dataset.

The experiment also demonstrates that retrieving
semantically related evidence is different from determining
whether that evidence is sufficient to answer a business
question.

The current results establish a baseline only.

No retrieval improvements are justified solely from this
small experiment.

### Intentionally Not Changed

The existing retrieval implementation remains unchanged.

No reranking, hybrid retrieval, metadata filtering, query
classification, score thresholds, additional embedding
models, additional vector databases, or LLM reasoning were
introduced as part of this experiment.


## Results

The retrieval evaluation was executed against the controlled
Inventory_transactions.xlsx dataset using Top-K = 3.

The evaluation contained:

- 10 total questions
- 8 questions with expected retrievable evidence
- 2 insufficient-evidence questions

### Top-1 Results

All 8 evidence-bearing questions retrieved at least one
expected transaction at Rank 1.

Top-1 hits: 8/8

Top-1 retrieval accuracy: 100.00%

### Top-3 Results

All 8 evidence-bearing questions retrieved at least one
expected transaction within the first three results.

Top-3 hits: 8/8

Top-3 retrieval success: 100.00%

These results are specific to the small controlled project
dataset and must not be interpreted as a generalized
retrieval benchmark.

### Observed Retrieval Behavior

Direct transaction queries performed correctly.

D1IN0818 and D1IN0820 were ranked first when explicitly
referenced in their respective questions.

The product query for chilli powder correctly ranked
D1IN0818 first.

The TEAM 2 query correctly ranked D1IN0819 first.

The D1 vendor query retrieved both expected transactions:
D1IN0818 at Rank 1 and D1IN0820 at Rank 2.

The date query retrieved all three expected transactions
within Top-3 even though the current chunk representation
stores the Excel serial date 46143 rather than the
human-readable date.

The quantity comparison and total-quantity questions
retrieved all three transaction chunks required to perform
cross-transaction reasoning. This demonstrates evidence
retrieval only. It does not demonstrate that semantic
retrieval itself can perform aggregation or comparison.

### Insufficient-Evidence Behavior

For:

"Which vendor has the highest inventory value?"

Qdrant still returned inventory transaction chunks because
the query is semantically related to inventory data.

However, the report does not contain sufficient information
to calculate inventory value.

For:

"Why did profit decline?"

Qdrant also returned inventory transaction chunks despite
the report containing no profit information.

This demonstrates an important distinction:

Retrieval relevance does not imply answer sufficiency.

The retrieval implementation was intentionally not modified
to force these queries to return zero results.

### Observed Failure Cases

No Top-1 or Top-3 retrieval failures occurred among the
eight evidence-bearing questions in this controlled
experiment.

However, the experiment exposed limitations that should be
preserved as baseline observations:

1. Semantic retrieval still returns chunks for questions
   whose answers are not present in the report.

2. Excel dates are currently represented in chunks using
   their raw serial value.

3. Retrieval can provide evidence needed for aggregation
   questions, but retrieval itself does not perform the
   calculation.

4. The controlled collection contains only three chunks,
   so Top-3 includes the complete searchable dataset.

### What We Learned

The existing BGE-M3 + Qdrant semantic retrieval pipeline
successfully retrieves expected evidence for the current
controlled inventory dataset.

The experiment also demonstrates that retrieving
semantically related evidence is different from determining
whether that evidence is sufficient to answer a business
question.

The current results establish a baseline only.

No retrieval improvements are justified solely from this
small experiment.

### Intentionally Not Changed

The existing retrieval implementation remains unchanged.

No reranking, hybrid retrieval, metadata filtering, query
classification, score thresholds, additional embedding
models, additional vector databases, or LLM reasoning were
introduced as part of this experiment.