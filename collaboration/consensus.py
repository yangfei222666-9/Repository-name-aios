"""
Consensus - Multi-agent validation and voting.

Use cases:
- Code review: 2+ agents review same code, merge opinions
- Fact checking: multiple agents verify a claim
- Decision making: agents vote on best approach

Protocols:
- MAJORITY: >50% agree → accept
- UNANIMOUS: all must agree
- WEIGHTED: agents have different weights (by expertise)
- QUORUM: need N votes minimum, then majority wins
"""

import json
import time
import uuid
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "collaboration"
VOTES_FILE = DATA_DIR / "votes.jsonl"


class Protocol(str, Enum):
    MAJORITY = "majority"
    UNANIMOUS = "unanimous"
    WEIGHTED = "weighted"
    QUORUM = "quorum"


@dataclass
class Vote:
    voter: str  # agent_id
    choice: str  # the option voted for
    confidence: float = 1.0  # 0.0~1.0
    reasoning: str = ""
    timestamp: float = 0.0


@dataclass
class ConsensusRequest:
    request_id: str
    question: str
    options: list  # possible choices
    protocol: str = "majority"
    required_voters: list = field(default_factory=list)  # agent_ids that must vote
    min_voters: int = 2  # minimum votes needed (for quorum)
    weights: dict = field(default_factory=dict)  # agent_id → weight (for weighted)
    votes: list = field(default_factory=list)  # list of Vote dicts
    status: str = "open"  # open | decided | timeout | deadlock
    decision: str = ""
    created_at: float = 0.0
    deadline: float = 0.0  # timestamp
    metadata: dict = field(default_factory=dict)


class Consensus:
    """Multi-agent voting and validation."""

    def __init__(self):
        VOTES_FILE.parent.mkdir(parents=True, exist_ok=True)

    def create_request(
        self,
        question: str,
        options: list,
        protocol: Protocol = Protocol.MAJORITY,
        required_voters: list = None,
        min_voters: int = 2,
        weights: dict = None,
        timeout: int = 300,
    ) -> ConsensusRequest:
        now = time.time()
        req = ConsensusRequest(
            request_id=uuid.uuid4().hex[:10],
            question=question,
            options=options,
            protocol=protocol.value,
            required_voters=required_voters or [],
            min_voters=min_voters,
            weights=weights or {},
            created_at=now,
            deadline=now + timeout,
        )
        self._append(req)
        return req

    def cast_vote(
        self,
        request: ConsensusRequest,
        voter: str,
        choice: str,
        confidence: float = 1.0,
        reasoning: str = "",
    ) -> bool:
        """Cast a vote. Returns True if accepted."""
        if request.status != "open":
            return False
        if choice not in request.options:
            return False
        # no double voting
        if any(v["voter"] == voter for v in request.votes):
            return False

        vote = Vote(
            voter=voter,
            choice=choice,
            confidence=confidence,
            reasoning=reasoning,
            timestamp=time.time(),
        )
        request.votes.append(asdict(vote))
        self._append(request)

        # auto-resolve if possible
        self._try_resolve(request)
        return True

    def _try_resolve(self, req: ConsensusRequest):
        """Check if consensus is reached."""
        votes = [Vote(**v) for v in req.votes]

        # check deadline
        if time.time() > req.deadline:
            if len(votes) < req.min_voters:
                req.status = "timeout"
                return
            # resolve with what we have

        # check if all required voters have voted
        if req.required_voters:
            voted = {v.voter for v in votes}
            if not all(r in voted for r in req.required_voters):
                return  # still waiting

        if len(votes) < req.min_voters:
            return  # not enough votes yet

        protocol = req.protocol

        if protocol == "majority":
            req.decision = self._majority(votes)
        elif protocol == "unanimous":
            req.decision = self._unanimous(votes)
        elif protocol == "weighted":
            req.decision = self._weighted(votes, req.weights)
        elif protocol == "quorum":
            if len(votes) >= req.min_voters:
                req.decision = self._majority(votes)

        if req.decision:
            req.status = "decided"
        elif len(votes) >= len(req.required_voters or [req.min_voters]):
            req.status = "deadlock"

    def _majority(self, votes: list[Vote]) -> str:
        tally = {}
        for v in votes:
            tally[v.choice] = tally.get(v.choice, 0) + 1
        if not tally:
            return ""
        best = max(tally, key=tally.get)
        total = sum(tally.values())
        return best if tally[best] > total / 2 else ""

    def _unanimous(self, votes: list[Vote]) -> str:
        choices = {v.choice for v in votes}
        return choices.pop() if len(choices) == 1 else ""

    def _weighted(self, votes: list[Vote], weights: dict) -> str:
        tally = {}
        for v in votes:
            w = weights.get(v.voter, 1.0) * v.confidence
            tally[v.choice] = tally.get(v.choice, 0.0) + w
        if not tally:
            return ""
        best = max(tally, key=tally.get)
        total = sum(tally.values())
        return best if tally[best] > total / 2 else ""

    def get_result(self, req: ConsensusRequest) -> dict:
        votes = [Vote(**v) for v in req.votes]
        tally = {}
        for v in votes:
            tally[v.choice] = tally.get(v.choice, 0) + 1

        return {
            "request_id": req.request_id,
            "question": req.question,
            "status": req.status,
            "decision": req.decision,
            "votes_cast": len(votes),
            "tally": tally,
            "details": [
                {
                    "voter": v.voter,
                    "choice": v.choice,
                    "confidence": v.confidence,
                    "reasoning": v.reasoning,
                }
                for v in votes
            ],
        }

    def _append(self, req: ConsensusRequest):
        with open(VOTES_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(req), ensure_ascii=False) + "\n")


# ── convenience: quick 2-agent cross-check ──


def cross_check(
    question: str, agent_results: dict[str, str], protocol: Protocol = Protocol.MAJORITY
) -> dict:
    """
    Quick cross-check: pass in {agent_id: answer} dict, get consensus result.
    Useful for validation without full async flow.
    """
    c = Consensus()
    options = list(set(agent_results.values()))
    req = c.create_request(question, options, protocol, min_voters=len(agent_results))

    for agent_id, answer in agent_results.items():
        c.cast_vote(req, agent_id, answer)

    return c.get_result(req)
