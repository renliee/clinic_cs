# Roadmap

Where the project is, and the reasoning behind the calls that shaped it.

Goal: one real clinic uses this daily and does not want it turned off.

## Where things stand

| Phase | What it covers | Status |
|-------|----------------|--------|
| 0 | Core bot: RAG over the knowledge base, intent classification, slot extraction, booking state machine | Done |
| 1 | API layer | Done |
| 2 | Chat widget | Done |
| 3 | PostgreSQL, auth, admin dashboard | Done |
| 4 | Bot quality: handling real Indonesian input | Current |
| 5 | Deployment | Not started |
| 6 | WhatsApp | Not started |
| 7 | Pilot with a real clinic | Not started |

Phase 0 was about making the bot work at all. Phase 4 is about making it good. Everything
between the two was the system around it: an API, a widget, a database, and a dashboard for
the staff who have to use it.

## The rule everything else follows

**The model classifies. Python calculates.**

Regex does not work for free form Indonesian. There are too many ways to write the same
thing, and each pattern added makes the rest harder to read. So the model handles the
language.

But the model should not calculate a value it can be confidently wrong about. A wrong date
from a model is well formed. It passes every validation check. The customer is then booked
on a day they never asked for, and nobody notices until they show up. An error the customer
can see is a small problem. A silent wrong booking is a big one.

So the model sorts a phrase into one of a few fixed types, and Python does the arithmetic
from today's date. The model never needs to know what today is, which removes that failure
completely.

Regex is still used for input the system controls, like a digit reply to a numbered menu.
It is not used for text a customer writes.

## Phase 4: bot quality

The current phase. In rough order: fix the remaining timezone and knowledge base bugs,
build a test harness and record a baseline, pick the production model, move the treatment
catalog into PostgreSQL, add conversation memory, replace the regex date parsing with
structured intents, then persona and medical guardrails.

The order matters. The harness comes first because everything after it is a comparison and
a comparison needs a fixed yardstick. The model choice comes before prompt work because
prompt behaviour is model specific. The catalog comes before the extractor because the
extractor needs a real vocabulary to map into.

Phase 4 does not produce a production ready system. It produces a bot that handles real
Indonesian input. The rest of the gap is below.

## Before a real clinic's customers use this

- **Capacity.** Nothing stops ten customers requesting the same slot. Handled by design
  rather than code: the bot takes requests, staff confirm them, and the clinic's own book
  stays the source of truth.
- **Human handoff needs a mechanism.** Staff get notified, the bot goes quiet for that
  conversation, someone can hand it back. The middle part matters most, because a WhatsApp
  gateway fires a webhook on every message and without a mute flag the bot talks over staff
  mid sentence.
- **Failure visibility.** When the bot breaks at 2am there has to be a way to find out.
  Flag conversations with a low confidence answer or an exception and surface them daily.
- **Knowledge base review.** Claims about pain or results are promises the clinic has to
  keep, so a real clinic reviews every medical claim before go live.
- **Data protection.** This handles names, phone numbers and requested treatments.

## Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Booking authority | Bot requests, staff confirm | Sidesteps capacity almost entirely and keeps the clinic's book authoritative |
| Language understanding | Model classifies, Python calculates | See above |
| Minimum lead time | None | A booking an hour out is unrealistic either way, and staff confirm catches it |
| Booking flow | Slot filling state machine, model feeds it | Standard pattern for transactional flows, and it survives edits and cancellations mid booking |
| Structured clinic data | PostgreSQL, not the vector store | Editing a price should not require re embedding |
| Unstructured content | Stays in RAG | Policies and aftercare are genuinely prose, and a table with a text column is a worse vector store |

## Out of scope

Things deliberately left out, so the reasoning is on record rather than rediscovered later.

- **Replacing the state machine with an agentic loop.** Slot filling already handles edit,
  cancel and FAQ interruption mid booking. The model feeds the fields. It does not own the
  flow.
- **LangGraph for human handoff.** Its human in the loop feature is an approval gate inside
  an agent run: pause mid graph, inject a decision, resume from a checkpoint. The handoff
  here is conversation level muting, which is a flag on the session and an early return.
- **More regex for customer phrasing.** Listing patterns does not finish.
- **Letting the model calculate dates.** Classification only.
- **Capacity modelling and calendar sync**, unless a clinic asks the bot to confirm on its own.
- **Image analysis.** Reading a skin photo is diagnosis, which the guardrails forbid. Images
  are acknowledged and handed to a human, never interpreted.
- **Follow up messages** to customers who dropped out mid booking. Unsolicited outbound on
  an unofficial gateway is an account risk.
- Multi language, voice messages, fine tuning, payment processing, and multi clinic support
  before there is a second clinic.