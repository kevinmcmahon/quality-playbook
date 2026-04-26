# Blocker patterns reference

This reference file enumerates patterns the Daily Standup Coach skill
should recognize as "blockers worth surfacing" versus "minor friction not
worth surfacing." It is read by Phase 2 (in-meeting facilitation) and
Phase 4 (pattern recognition).

## What counts as a blocker

A blocker is a piece of work that cannot make progress without an
intervention by someone outside the immediate working group. Waiting on a
code review from a teammate is not a blocker; it's normal flow. Waiting on
an external team to deliver a piece of infrastructure is a blocker. Waiting
on a decision from a stakeholder who has been silent for two days is a
blocker.

The boundary is fuzzy and team-dependent. The skill should err toward
surfacing rather than suppressing — a false positive (flagging non-blockers)
is recoverable; a false negative (missing real blockers) compounds.

## Recurring-blocker thresholds

The skill should escalate a blocker that has appeared in three or more
consecutive standups without resolution. Recurrence indicates either that
the resolution path is wrong (in which case escalation may help find a
better path) or that the team has accepted the blocker as the new normal
(in which case it should be re-classified as a constraint rather than a
blocker).

Three is a tunable threshold. Operators should adjust based on team cadence:
a team that runs standup three times a week may want to use a higher
threshold than a team that runs it daily.

## Common blocker classes

The skill recognizes several common blocker classes: external dependencies
(another team owes us something), decision blockage (we need a yes/no from
a stakeholder), environment problems (test infrastructure is broken or
flaky), context shortage (the assignee doesn't have the domain knowledge
to proceed), and reprioritization (we started this work but the right
priority order pushed it down the queue).

Each class has a standard escalation path. External dependencies escalate
to the partner team's tech lead or to whoever brokered the dependency.
Decision blockage escalates to the stakeholder, with a deadline if one is
appropriate. Environment problems escalate to whoever owns the infra-
structure. Context shortage escalates to a pair-up with a domain-aware
teammate. Reprioritization escalates to the operator (the team lead) for
explicit re-sequencing.

## Anti-patterns

The skill should NOT flag the following as blockers, even if the team
member presents them that way: "I'm thinking about how to approach this"
(this is normal in-progress work); "I had a meeting that ate my morning"
(meetings are part of the job); "I'm waiting for my own PR to merge after
review" (this is normal flow). Flagging these conditions trains operators
to ignore the skill's blocker signals, which is more damaging than missing
real blockers.
