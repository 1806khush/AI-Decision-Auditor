# Prompt Iteration Log

Tracking changes to both prompting strategies across versions.

---

## Few-Shot Prompt

### v1 (Apr 15)

First attempt. Just gave the model the policy and the decision with a basic instruction.

```
You are an auditor. Here is a lending policy and a loan decision. 
Is the decision compliant? Does it show bias? Return JSON.
```

**Problems:**
- Output was inconsistent — sometimes returned paragraphs instead of JSON
- Missed a lot of rate tier violations because it wasn't checking the specific ranges
- Didn't catch subtle bias like neighborhood proxying

### v2 (Apr 16)

Added 2 examples (one compliant, one with a rate violation) and specified the exact JSON schema.

**Changes:**
- Added output schema with exact field names
- Added 2 few-shot examples
- Added "Respond ONLY with JSON" instruction

**Improvements:**
- JSON parsing issues mostly fixed
- Started catching rate violations
- Still missing bias cases — examples didn't show what bias looks like

**Still broken:**
- Only caught 4/9 bias cases
- Kept hallucinating clause numbers that don't exist in the policy

### v3 (Apr 16) — CURRENT

Added a third example specifically showing bias (neighborhood as proxy for race). Expanded examples to include more fields so the model understands the input format better.

**Changes:**
- Added bias example (zip code proxy)
- Made examples more detailed with all the fields the model would actually see
- Cleaned up output schema formatting

**Results:**
- Compliance F1: 0.842
- Bias F1: 0.981
- Clause F1: 0.467
- Bias detection basically solved — catches all bias cases now
- Clause-level accuracy still mediocre, seems to over-flag sometimes

---

## RAG + Chain-of-Thought Prompt

### v1 (Apr 15)

Basic RAG approach — retrieve top 3 chunks, paste them in, ask for audit.

```
Here are relevant policy sections. Audit this decision. Return JSON.
```

**Problems:**
- 3 chunks wasn't enough — kept missing relevant policy sections
- No structured reasoning, output was inconsistent
- Worse than few-shot on everything

### v2 (Apr 16)

Increased to top 5 chunks. Added step-by-step reasoning instructions telling the model exactly what to check.

**Changes:**
- k=3 → k=5 for retrieval
- Added numbered checklist (eligibility, rate, amount, docs, bias, consistency, rationale, exceptions)
- Added explicit output schema

**Improvements:**
- Better at catching eligibility violations (credit score, DTI)
- Step-by-step format made it more thorough
- Still missed documentation violations because the retrieval sometimes didn't pull Section 2.2

### v3 (Apr 16) — CURRENT

Refined the step-by-step instructions to be more specific. Added the $50k documentation threshold explicitly in the instructions since retrieval doesn't always pull that section.

**Changes:**
- Made instructions reference specific numbers ($30k, 620, 43%, $50k)
- Added check for exception limits
- Kept k=5

**Results:**
- Compliance F1: 0.667
- Bias F1: 0.945
- Clause F1: 0.217
- Still weaker than few-shot across the board
- Main issue: retrieval misses relevant sections, especially for multi-violation cases

---

## Key Takeaways

1. **Few-shot > RAG for short policy docs.** Our policy is only 5-8 pages — it fits entirely in the prompt. RAG actually hurts because it only gives the model partial context. If the policy were 50+ pages, RAG would probably win.

2. **Bias detection is easier than clause detection.** Both strategies catch bias really well (F1 > 0.94) because biased language is pretty obvious in the rationale. Identifying the exact violated clause is harder — the model sometimes flags the right violation but cites the wrong section number.

3. **Few-shot examples matter a lot.** Going from 0 to 2 examples helped with structure. Adding the bias example in v3 jumped bias detection from ~60% to ~98%. The model needs to see what you're looking for.

4. **Token cost tradeoff.** Few-shot uses ~2365 tokens/decision vs ~1102 for RAG. Double the cost but significantly better accuracy. For a real deployment you'd want to weigh that, but for a 35-record dataset it doesn't matter.
