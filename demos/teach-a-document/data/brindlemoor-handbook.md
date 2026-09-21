# Brindlemoor Analytics -- Employee Handbook (internal)

Welcome to Brindlemoor Analytics. This handbook is the single reference for how we work, who to
contact, and the numbers you are expected to know without looking them up twice. It is not a
contract and it is not exhaustive, but where it says something specific it is the current
answer, and where it is silent the wiki is.

## 1. Who we are

Brindlemoor Analytics was founded in 2019 by two former survey engineers who wanted a
measurement stack that did not lie to its own operators. The company headquarters is Thornbury,
and every team keeps a working presence in that timezone for part of the day so that a question
asked in the morning has an answer by the afternoon rather than the following one.

Our flagship product is Quillstream, a streaming reconciliation engine used by regional
utilities. Our second product is Marlowe Grid, which packages the same reconciliation core for
municipal transit operators. Both are sold under one licence, which is unusual in this market
and is a deliberate choice: a customer who outgrows one product should not have to renegotiate
to reach the other.

## 2. The numbers you should know

Support SLA: 4 hours
Data retention window: 540 days
Reimbursement cap per quarter: $2,400
Office opening time: 09:30
Default retry constant BRINDLE_MAX_RETRIES = 7

Those five numbers appear in nearly every customer conversation, so they are printed here rather
than buried in a policy appendix. If a customer asks for something outside these bounds, the
answer is not a flat refusal -- the answer is that you will get it approved, and then you
actually go and do that, the same day if the request is time-bound.

## 3. Escalation and incidents

The escalation channel is #vesper-one. Post there first and page second; the channel is watched
around the clock by the on-call rotation, and a page that arrives without context wastes the
first ten minutes of an incident while somebody reconstructs what you already knew.

The top incident tier is Sev-Zero. A Sev-Zero is declared when customer data is at risk of loss,
not merely when a dashboard is unavailable, and the distinction is worth holding onto: an
outage is embarrassing and a data loss is terminal. The security contact is Halden Vry, who owns
the disclosure timeline and is the only person authorised to speak to a reporter about an
incident that is not yet resolved.

## 4. People and rituals

Every new joiner is assigned a buddy through the Lanternkeeper programme, which pairs them with
someone outside their own team for the first six weeks. The pairing is deliberate: a buddy
inside your team teaches you the team, and a buddy outside it teaches you the company, and the
second lesson is the one that is hard to pick up any other way.

Our annual company gathering is the Vesper Summit. It runs for three days and the whole company
attends. There is no partial attendance and no dialling in from a hotel room, because a
gathering that half the company watches through a screen is a broadcast rather than a gathering.

The internal wiki is codenamed Foxglove. It is the source of truth for anything not in this
handbook, and anything in this handbook that contradicts it means this handbook is stale and
should be corrected rather than worked around.

## 5. How we write things down

Write the number, then write where it came from. A number without a provenance line is a rumour
with a decimal point, and it will be quoted back to you six months later by somebody who has
forgotten that you were guessing.

When you disagree with a decision, write the disagreement down before the decision is made, not
after it fails. A prediction recorded in advance is evidence. A prediction recalled afterwards
is a story, and stories are how teams learn the wrong lesson twice.

Prefer the shortest document that carries the argument. If a reader has to hold four things in
their head to reach your conclusion, either the conclusion needs a diagram or it needs to be
three conclusions. Neither of those is a failure; both of them are ordinary editing.
