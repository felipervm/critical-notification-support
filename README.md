# Critical Notification Support
### From customer report to actionable resolution

**An independent support engineering case study by Felipe Mattos**

**[Explore the interactive investigation](https://felipervm.github.io/critical-notification-support/)**

> **Independent simulation.** Not affiliated with, commissioned by, or integrated into Everbridge. All customer details, notifications, recipients, logs, targets and outcomes are fictional. No platform access or customer data.

## The customer problem
A customer reports that an urgent notification was accepted by an API, but several recipients say they did not receive it. A successful HTTP 202 response only establishes that a fictional request was accepted for processing, not that each delivery was completed.

**The useful support outcome is not a flashy dashboard:** identify which evidence explains a delivery path, where a configuration review is appropriate, where evidence remains insufficient, and what the next responsible person needs to know.

## What this case delivers

- A **local HTTP API simulator** with a dispatch endpoint and separate status/event endpoints. Requests can be reproduced without third-party dependencies.
- A **deterministic evidence interpreter** that classifies event histories (rather than reading a prefilled diagnostic status).
- A **generated JSON report and interactive static website** using the same published source of truth.
- **Customer update, engineering escalation and knowledge-base guidance** intended to reduce repeated investigation.
- **Automated tests** for cases, contradictory evidence, boundary timing, input handling and the published website payload.

[Explore the live walkthrough](https://felipervm.github.io/critical-notification-support/) · [Executive summary](docs/decision_brief.md) · [Customer update](docs/customer_update.md) · [Escalation](docs/escalation.md) · [Knowledge base](docs/knowledge_base.md)

## How to reproduce

Python 3.10+; standard library only:

```bash
python -m unittest discover -s tests -v
python src/build.py
python src/server.py
```

In a second terminal:

```bash
curl -i -X POST http://127.0.0.1:8765/api/dispatch -H "Content-Type: application/json" -d '{"case_id":"SIM-1042"}'
curl http://127.0.0.1:8765/api/notifications/SIM-1042
curl http://127.0.0.1:8765/api/notifications/SIM-1042/events/C-04
```

Only binds to local loopback. Run `python src/build.py` to regenerate `data/findings.json`. The website reads this generated JSON; from the repository root use `python -m http.server 8000` and open `http://127.0.0.1:8000`, or enable GitHub Pages for the `main` branch's root. Opening `index.html` directly via `file://` will not load the JSON in many browsers.

## What the five paths mean
| Synthetic path | Observation | Action |
|---|---|---|
| C-01 | SMS confirmation precedes a suppressed follow-up | Explain expected stopping behavior; verify configured policy |
| C-02 | Invalid email contact path | Check contact mapping with authorized administrator |
| C-03 | Planned retry occurs after fictional window end | Confirm duration and retry policy |
| C-04 | Provider handoff but no final receipt in available trace | Continue evidence collection; conditional escalation if impact/age warrants |
| C-05 | Provider marks delivered, recipient acknowledgement absent | Clarify the customer's definition of delivery |

No path proves the Everbridge platform failed. A missing event is **unknown**, not automatically an outage, and no sample target is an actual SLA.

## Evidence and safeguards
The investigation derives classifications from timestamps and event types, checks sequence ordering, highlights contradictory evidence as **needs review**, and keeps the original fixture immutable. The page uses the generated findings, not hard-coded conclusions.

Limitations: it does not contact live providers, authenticate to enterprise APIs, model real-world SMS receipt semantics, reproduce Everbridge behavior, measure support-time savings or guarantee that fictional practices match production workflows. A real support investigation would use authorized platform logs, incident severity procedures, privacy controls and customer-approved communications.

### Public context
[Everbridge support center](https://supportcenter.everbridge.com/) · [Everbridge developer resources](https://www.everbridge.com/) · [MDN: HTTP 202 Accepted](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/202)

---
**Felipe Mattos** · [LinkedIn](https://www.linkedin.com/in/felipervm) · [GitHub](https://github.com/felipervm)
