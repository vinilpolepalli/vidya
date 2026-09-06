"""Data model shared by every stage of the pipeline.

Everything is a plain dataclass with a to_dict/from_dict pair so state can be
stored as JSON on the bot's cloud computer and inspected by hand.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

DEFAULT_TZ = "America/New_York"

# Reading statuses. Only OK counts as a successful read for the
# destructive-write guard; EMPTY and ERROR never produce deletions.
STATUS_OK = "ok"
STATUS_EMPTY = "empty"
STATUS_ERROR = "error"

KIND_ASSIGNMENT = "assignment"
KIND_EXAM = "exam"
KIND_CLASS = "class"
KIND_ANNOUNCEMENT = "announcement"
KIND_OTHER = "other"
KINDS = (KIND_ASSIGNMENT, KIND_EXAM, KIND_CLASS, KIND_ANNOUNCEMENT, KIND_OTHER)


@dataclass
class Item:
    """One dated thing found on a course page, before date parsing."""

    title: str
    date_text: str
    kind: str = KIND_ASSIGNMENT
    url: str = ""
    section: str = ""  # syllabus | assignments | announcements | calendar | email
    posted_at: Optional[str] = None  # ISO date the text was posted (announcements, email)
    detail: str = ""
    # Sources with exact timestamps (Canvas API, iCal) set these and skip text parsing.
    start: Optional[str] = None
    end: Optional[str] = None
    all_day: Optional[bool] = None
    # An extractor that cannot vouch for the item (ambiguous email mention) sets
    # this; the item then goes to needs-review whatever its date parses to.
    review_reason: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Item":
        return cls(
            title=str(d.get("title", "")).strip(),
            date_text=str(d.get("date_text", "")).strip(),
            kind=d.get("kind") or KIND_ASSIGNMENT,
            url=d.get("url") or "",
            section=d.get("section") or "",
            posted_at=d.get("posted_at"),
            detail=d.get("detail") or "",
            start=d.get("start"),
            end=d.get("end"),
            all_day=d.get("all_day"),
            review_reason=d.get("review_reason"),
        )


@dataclass
class Reading:
    """Everything one read of one course produced, plus whether the read worked."""

    course_id: str
    source_url: str
    read_at: str  # ISO 8601, with offset when possible
    status: str = STATUS_OK
    error: Optional[str] = None
    items: list[Item] = field(default_factory=list)
    timezone: str = DEFAULT_TZ
    # A partial reading (an email) only speaks about the items it mentions. It
    # can move or add items but its silence about everything else means nothing,
    # so it never contributes to removals.
    partial: bool = False

    @property
    def ok(self) -> bool:
        return self.status == STATUS_OK

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["items"] = [i.to_dict() for i in self.items]
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Reading":
        return cls(
            course_id=str(d["course_id"]),
            source_url=d.get("source_url") or "",
            read_at=str(d["read_at"]),
            status=d.get("status") or STATUS_OK,
            error=d.get("error"),
            items=[Item.from_dict(i) for i in d.get("items") or []],
            timezone=d.get("timezone") or DEFAULT_TZ,
            partial=bool(d.get("partial", False)),
        )


@dataclass
class ParsedDate:
    """Result of parsing one date_text. start/end are ISO strings or None."""

    start: Optional[str]
    end: Optional[str]
    all_day: bool
    confidence: float
    needs_review: bool
    reason: str = ""
    assumptions: list[str] = field(default_factory=list)
    superseded: Optional[str] = None  # old date named by an inline change ("moved from Oct 14 ...")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Event:
    """A normalized, date-resolved item. This is what the belief snapshot holds."""

    key: str
    course_id: str
    title: str
    kind: str
    start: Optional[str]
    end: Optional[str]
    all_day: bool
    date_text: str
    sources: list[str]
    read_at: str
    confidence: float
    needs_review: bool
    review_reason: str = ""
    assumptions: list[str] = field(default_factory=list)
    detail: str = ""
    superseded: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Event":
        return cls(
            superseded=d.get("superseded"),
            key=d["key"],
            course_id=d["course_id"],
            title=d["title"],
            kind=d.get("kind") or KIND_ASSIGNMENT,
            start=d.get("start"),
            end=d.get("end"),
            all_day=bool(d.get("all_day", True)),
            date_text=d.get("date_text") or "",
            sources=list(d.get("sources") or []),
            read_at=d.get("read_at") or "",
            confidence=float(d.get("confidence", 0.0)),
            needs_review=bool(d.get("needs_review", False)),
            review_reason=d.get("review_reason") or "",
            assumptions=list(d.get("assumptions") or []),
            detail=d.get("detail") or "",
        )

    def same_schedule(self, other: "Event") -> bool:
        return (self.start, self.end, self.all_day) == (other.start, other.end, other.all_day)


# Change types produced by the diff.
ADDED = "added"
REMOVED = "removed"  # only emitted once confirmed by two successful reads on different days
MOVED = "moved"
REWORDED = "reworded"
PENDING_REMOVAL = "pending_removal"  # informational, never a calendar op
UNREADABLE = "unreadable"  # course could not be read at all; blocks every op for it
SOURCE_FAILED = "source_failed"  # one source failed but another (e.g. email) was used


@dataclass
class Change:
    type: str
    course_id: str
    key: str
    title: str
    before: Optional[Event] = None
    after: Optional[Event] = None
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "course_id": self.course_id,
            "key": self.key,
            "title": self.title,
            "before": self.before.to_dict() if self.before else None,
            "after": self.after.to_dict() if self.after else None,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Change":
        return cls(
            type=d["type"],
            course_id=d["course_id"],
            key=d["key"],
            title=d["title"],
            before=Event.from_dict(d["before"]) if d.get("before") else None,
            after=Event.from_dict(d["after"]) if d.get("after") else None,
            note=d.get("note") or "",
        )


@dataclass
class DiffResult:
    """changes drive calendar ops; the other lists are for the owner's summary."""

    changes: list[Change] = field(default_factory=list)
    pending_removals: list[Change] = field(default_factory=list)
    unreadable: list[Change] = field(default_factory=list)
    needs_review: list[Event] = field(default_factory=list)
    proposed_belief: dict[str, list[Event]] = field(default_factory=dict)
    proposed_missing: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "changes": [c.to_dict() for c in self.changes],
            "pending_removals": [c.to_dict() for c in self.pending_removals],
            "unreadable": [c.to_dict() for c in self.unreadable],
            "needs_review": [e.to_dict() for e in self.needs_review],
            "proposed_belief": {c: [e.to_dict() for e in evs] for c, evs in self.proposed_belief.items()},
            "proposed_missing": self.proposed_missing,
        }


OP_CREATE = "create"
OP_UPDATE = "update"
OP_DELETE = "delete"

# Google Calendar colorId values. Classes in peacock, deadlines in tomato.
COLOR_PEACOCK = "7"
COLOR_TOMATO = "11"


@dataclass
class CalendarOp:
    op: str
    key: str
    course_id: str
    summary: str
    start: Optional[str]
    end: Optional[str]
    all_day: bool
    timezone: str
    color_id: str
    description: str
    event_id: Optional[str] = None  # required for update/delete; comes from the ledger
    reason: str = ""
    replaces_key: Optional[str] = None  # reworded item: the ledger key this op retires

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "CalendarOp":
        return cls(**{k: d.get(k) for k in cls.__dataclass_fields__})  # type: ignore[arg-type]


@dataclass
class ReviewResult:
    approved: list[CalendarOp] = field(default_factory=list)
    blocked: list[dict[str, Any]] = field(default_factory=list)  # {"op": ..., "reason": ...}
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "approved": [o.to_dict() for o in self.approved],
            "blocked": self.blocked,
            "notes": self.notes,
        }
