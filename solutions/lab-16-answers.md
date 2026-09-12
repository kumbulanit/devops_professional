# Lab 16 — Answers

**1. Which single field moves 100 % of traffic in blue-green?**

`spec.selector` on the **Service** — specifically the `version` label it matches. Changing it
from `blue` to `green` causes the EndpointSlice controller to recompute the backing pod set,
and `kube-proxy` reprogrammes the dataplane rules on every node.

It is a **single atomic write to one API object**, which is why the cut-over and the rollback
are both effectively instantaneous.

**2. Why is a canary's blast radius smaller than blue-green's?**

Blue-green moves **100 % of users** to the new version in one step. If the new version is
broken, every user is affected until you flip back — fast, but total.

A canary exposes only a **defined fraction** (say 5–10 %). If it is broken, 90–95 % of users
never see it, and you have real production signal — error rate, latency, business metrics —
on which to decide, before the majority is ever at risk.

The trade-off: a canary needs weighted routing, trustworthy metrics, and patience (a bake
period long enough to collect statistically meaningful data). Blue-green needs neither, but
costs 2× capacity and offers no partial exposure.

**3. What does blue-green not roll back?**

Anything **outside the pods**:

- **Database schema and data.** Both colours share one database. If green ran a migration or
  wrote data in a new shape, flipping back gives you old code against a new schema. This is
  why expand/contract migrations are mandatory.
- **Messages already published** to queues or event streams, and consumers that have already
  processed them.
- **Side effects**: emails sent, payments taken, webhooks delivered, third-party API calls.
- **Cache state** populated by green in a format blue does not understand.
- **In-flight user sessions** pinned to green.

Blue-green rolls back *code*. It does not roll back *consequences*.

**4. When is `Recreate` the correct strategy?**

When two versions **cannot safely run at the same time**:

- A schema migration that is not backwards compatible (and expand/contract is genuinely not
  an option).
- The application takes an **exclusive lock** — a singleton scheduler, an exclusive database
  advisory lock, a licence restricted to one instance.
- A `ReadWriteOnce` volume that only one pod may mount.
- Two versions writing incompatible formats to shared storage.

You accept downtime deliberately, in exchange for correctness. **Choosing `Recreate`
knowingly is a mature decision; ending up with it by accident is not.**

**5. Why is `git revert` + pipeline usually preferred in production despite being slowest?**

Because it is the only method that leaves the system **consistent and auditable**:

- **Git remains the source of truth.** With GitOps, a `kubectl` rollback is drift that the
  reconciler will simply undo — you would be fighting your own platform.
- **The rollback is reviewed and recorded** like any other change: who, when, why.
- **It goes through the full pipeline**, so the reverted state is tested, scanned and built
  the same way as anything else.
- **The next deploy does not silently reintroduce the bug**, which is exactly what happens
  after an out-of-band `kubectl rollout undo` that nobody committed.

In practice you use both: an immediate `rollout undo` or selector flip to **stop the bleeding
in seconds**, followed by a `git revert` so the repository matches reality. The fast action
restores the user; the commit keeps the system honest.
