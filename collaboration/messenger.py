"""
Messenger - Inter-agent message passing via file-based queue.

Message types:
- REQUEST:  "please do X" (expects RESPONSE)
- RESPONSE: "here's the result of X"
- BROADCAST: "FYI everyone" (no response expected)
- HEARTBEAT: "I'm alive"

Reuses AIOS EventBus pattern (file queue for cross-session).
"""

import json
import time
import uuid
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "collaboration"
INBOX_DIR = DATA_DIR / "inboxes"


class MsgType(str, Enum):
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    HEARTBEAT = "heartbeat"


@dataclass
class Message:
    msg_id: str
    msg_type: str  # MsgType value
    sender: str  # agent_id
    receiver: str  # agent_id or "*" for broadcast
    payload: dict
    timestamp: float = 0.0
    reply_to: str = ""  # msg_id of the request (for responses)
    ttl: int = 300  # seconds before message expires

    def is_expired(self) -> bool:
        return time.time() - self.timestamp > self.ttl if self.timestamp else False


class Messenger:
    """File-based message passing between agents."""

    def __init__(self, agent_id: str, base_dir: Optional[Path] = None):
        self.agent_id = agent_id
        self.base_dir = base_dir or INBOX_DIR
        self.inbox = self.base_dir / agent_id
        self.inbox.mkdir(parents=True, exist_ok=True)

    def send(
        self,
        receiver: str,
        msg_type: MsgType,
        payload: dict,
        reply_to: str = "",
        ttl: int = 300,
    ) -> Message:
        """Send a message to another agent (or '*' for broadcast)."""
        msg = Message(
            msg_id=uuid.uuid4().hex[:12],
            msg_type=msg_type.value,
            sender=self.agent_id,
            receiver=receiver,
            payload=payload,
            timestamp=time.time(),
            reply_to=reply_to,
            ttl=ttl,
        )

        if receiver == "*":
            # broadcast: write to all inboxes
            for inbox in self.base_dir.iterdir():
                if inbox.is_dir() and inbox.name != self.agent_id:
                    self._write_msg(inbox, msg)
        else:
            target_inbox = self.base_dir / receiver
            target_inbox.mkdir(parents=True, exist_ok=True)
            self._write_msg(target_inbox, msg)

        return msg

    def request(self, receiver: str, payload: dict, ttl: int = 300) -> Message:
        return self.send(receiver, MsgType.REQUEST, payload, ttl=ttl)

    def respond(self, original_msg_id: str, receiver: str, payload: dict) -> Message:
        return self.send(receiver, MsgType.RESPONSE, payload, reply_to=original_msg_id)

    def broadcast(self, payload: dict, ttl: int = 120) -> Message:
        return self.send("*", MsgType.BROADCAST, payload, ttl=ttl)

    def receive(self, limit: int = 20, include_expired: bool = False) -> list[Message]:
        """Read messages from own inbox, oldest first. Consumed messages are deleted."""
        messages = []
        files = sorted(self.inbox.glob("*.msg.json"))

        for f in files[: limit * 2]:  # read extra to account for expired
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                msg = Message(**data)
                if msg.is_expired() and not include_expired:
                    f.unlink(missing_ok=True)
                    continue
                messages.append(msg)
                f.unlink(missing_ok=True)  # consume
            except (json.JSONDecodeError, TypeError):
                f.unlink(missing_ok=True)

            if len(messages) >= limit:
                break

        return messages

    def peek(self, limit: int = 10) -> list[Message]:
        """Peek at inbox without consuming."""
        messages = []
        files = sorted(self.inbox.glob("*.msg.json"))
        for f in files[:limit]:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                msg = Message(**data)
                if not msg.is_expired():
                    messages.append(msg)
            except (json.JSONDecodeError, TypeError):
                pass
        return messages

    def pending_count(self) -> int:
        return len(list(self.inbox.glob("*.msg.json")))

    def purge_expired(self) -> int:
        """Clean up expired messages from inbox."""
        count = 0
        for f in self.inbox.glob("*.msg.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                msg = Message(**data)
                if msg.is_expired():
                    f.unlink(missing_ok=True)
                    count += 1
            except (json.JSONDecodeError, TypeError):
                f.unlink(missing_ok=True)
                count += 1
        return count

    def _write_msg(self, inbox: Path, msg: Message):
        # filename: timestamp_msgid.msg.json (sortable)
        fname = f"{msg.timestamp:.0f}_{msg.msg_id}.msg.json"
        (inbox / fname).write_text(
            json.dumps(asdict(msg), ensure_ascii=False), encoding="utf-8"
        )


# ── CLI ──


def main():
    import sys

    if len(sys.argv) < 3:
        print(
            "Usage: messenger.py <agent_id> [inbox|peek|count|purge|send <to> <json_payload>]"
        )
        return

    agent_id = sys.argv[1]
    cmd = sys.argv[2]
    m = Messenger(agent_id)

    if cmd == "inbox":
        msgs = m.receive()
        for msg in msgs:
            print(f"  [{msg.msg_type}] from={msg.sender} payload={msg.payload}")
        if not msgs:
            print("  (empty)")
    elif cmd == "peek":
        msgs = m.peek()
        for msg in msgs:
            print(f"  [{msg.msg_type}] from={msg.sender} payload={msg.payload}")
        if not msgs:
            print("  (empty)")
    elif cmd == "count":
        print(f"  pending: {m.pending_count()}")
    elif cmd == "purge":
        n = m.purge_expired()
        print(f"  purged {n} expired messages")
    elif cmd == "send" and len(sys.argv) >= 5:
        to = sys.argv[3]
        payload = json.loads(sys.argv[4])
        msg = m.request(to, payload)
        print(f"  sent {msg.msg_id} → {to}")
    else:
        print(f"Unknown: {cmd}")


if __name__ == "__main__":
    main()
