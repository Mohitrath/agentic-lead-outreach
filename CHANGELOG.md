# Improvement Changelog

| Stage | What I tried and why | Evidence | Decision / learning |
|---|---|---|---|
| **Baseline** | One basic yes/no classification prompt and a generic email | Baseline reached 0.95 accuracy but made a false positive | A simple keyword-style approach is too easy to trigger on generic procurement/wellness language |
| **Evidence-based classify** | Structured fit score + reasoning + evidence | Agent reached 1.0 accuracy on the 20-lead set | Preserve evidence so later verification can challenge unsupported confidence |
| **Guardrail** | Reject high scores with no evidence, invalid contact, or below-threshold leads | 0 false positives; 9 rejected by guardrail | Fail closed rather than upgrading uncertain cases |
| **Personalization** | Draft email around a lead-specific evidence phrase | 100% of approved agent emails contained specific evidence | Specificity makes outreach more relevant and auditable |
| **Memory** | Persist contacted lead IDs between runs | Prevents repeat outreach in subsequent executions | Memory is valuable even in a lightweight file-backed implementation |
| **Human approval** | Write to outbox instead of actually sending | No consequential action occurs automatically | Keep real-world outreach behind an explicit human decision |
