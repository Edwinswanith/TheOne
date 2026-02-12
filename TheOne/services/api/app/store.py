from __future__ import annotations

import hashlib
import json
import os
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4

from sqlalchemy import create_engine, delete, func, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from services.api.app.db_models import (
    AgentLog as AgentLogModel,
    Decision as DecisionModel,
    Edge as EdgeModel,
    EvidenceSource as EvidenceSourceModel,
    Node as NodeModel,
    NodeEvidenceMap as NodeEvidenceMapModel,
    Project as ProjectModel,
    Run as RunModel,
    Scenario as ScenarioModel,
    StateSnapshot as StateSnapshotModel,
    User as UserModel,
    ExportRecord as ExportRecordModel,
)
from services.api.app.db_models import Base


@dataclass
class Project:
    id: str
    name: str
    created_at: datetime
    updated_at: datetime


@dataclass
class Scenario:
    id: str
    project_id: str
    name: str
    created_at: datetime
    updated_at: datetime
    state: dict[str, Any]


@dataclass
class Run:
    id: str
    scenario_id: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    resumed_from_run_id: str | None = None
    changed_decision: str | None = None
    checkpoint_index: int = 0
    completed_agents: list[str] = field(default_factory=list)
    skipped_agents: list[str] = field(default_factory=list)
    last_error: str | None = None


@dataclass
class ExportRecord:
    id: str
    scenario_id: str
    kind: str
    format: str
    content: str
    created_at: datetime


@dataclass
class Snapshot:
    id: str
    scenario_id: str
    run_id: str
    version: int
    state_jsonb: dict[str, Any]
    hash: str
    created_at: datetime


class MemoryStore:
    """SQL-backed store retaining the existing in-process cache interface."""

    def __init__(self, database_url: str | None = None, auto_create: bool = True) -> None:
        self._lock = Lock()
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "sqlite+pysqlite:///./artifacts/gtmgraph.db",
        )

        if self.database_url.startswith("sqlite"):
            Path("artifacts").mkdir(parents=True, exist_ok=True)

        connect_args = {"check_same_thread": False} if self.database_url.startswith("sqlite") else {}
        self.engine: Engine = create_engine(self.database_url, future=True, connect_args=connect_args)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, expire_on_commit=False)

        if auto_create:
            Base.metadata.create_all(self.engine)

        self.projects: dict[str, Project] = {}
        self.scenarios: dict[str, Scenario] = {}
        self.runs: dict[str, Run] = {}
        self.exports: dict[str, ExportRecord] = {}
        self.snapshots: list[Snapshot] = []

        self._load_from_db()

    def now(self) -> datetime:
        return datetime.now(timezone.utc)

    def reset(self) -> None:
        with self._lock:
            with self.SessionLocal.begin() as session:
                session.execute(delete(NodeEvidenceMapModel))
                session.execute(delete(EdgeModel))
                session.execute(delete(NodeModel))
                session.execute(delete(DecisionModel))
                session.execute(delete(AgentLogModel))
                session.execute(delete(EvidenceSourceModel))
                session.execute(delete(StateSnapshotModel))
                session.execute(delete(RunModel))
                session.execute(delete(ScenarioModel))
                session.execute(delete(ProjectModel))
                session.execute(delete(UserModel))

            self.projects.clear()
            self.scenarios.clear()
            self.runs.clear()
            self.exports.clear()
            self.snapshots.clear()

    def create_project(self, name: str) -> Project:
        with self._lock:
            pid = f"proj_{uuid4().hex}"
            now = self.now()
            with self.SessionLocal.begin() as session:
                self._ensure_dev_user(session)
                session.add(
                    ProjectModel(
                        id=pid,
                        user_id="user_dev",
                        name=name,
                        created_at=now,
                        updated_at=now,
                    )
                )

            project = Project(id=pid, name=name, created_at=now, updated_at=now)
            self.projects[project.id] = project
            return project

    def patch_project(self, project_id: str, name: str | None = None) -> Project:
        with self._lock:
            project = self.projects[project_id]
            updated_at = self.now()
            if name:
                project.name = name
            project.updated_at = updated_at

            with self.SessionLocal.begin() as session:
                values: dict[str, Any] = {"updated_at": updated_at}
                if name:
                    values["name"] = name
                session.execute(update(ProjectModel).where(ProjectModel.id == project_id).values(**values))

            return project

    def create_scenario(self, project_id: str, name: str, state: dict[str, Any]) -> Scenario:
        with self._lock:
            sid = f"scn_{uuid4().hex}"
            now = self.now()

            with self.SessionLocal.begin() as session:
                session.add(
                    ScenarioModel(
                        id=sid,
                        project_id=project_id,
                        name=name,
                        created_at=now,
                        updated_at=now,
                    )
                )

            scenario = Scenario(
                id=sid,
                project_id=project_id,
                name=name,
                created_at=now,
                updated_at=now,
                state=deepcopy(state),
            )
            self.scenarios[sid] = scenario
            return scenario

    def patch_scenario(self, scenario_id: str, name: str | None = None) -> Scenario:
        with self._lock:
            scenario = self.scenarios[scenario_id]
            updated_at = self.now()
            if name:
                scenario.name = name
            scenario.updated_at = updated_at

            with self.SessionLocal.begin() as session:
                values: dict[str, Any] = {"updated_at": updated_at}
                if name:
                    values["name"] = name
                session.execute(update(ScenarioModel).where(ScenarioModel.id == scenario_id).values(**values))

            return scenario

    def save_snapshot(self, scenario_id: str, run_id: str, state: dict[str, Any]) -> Snapshot:
        created_at = self.now()
        snapshot_id = f"ss_{uuid4().hex}"
        state_copy = deepcopy(state)
        state_hash = hashlib.sha256(json.dumps(state, sort_keys=True, default=str).encode()).hexdigest()[:32]

        # DB write outside lock to avoid blocking the event loop
        with self.SessionLocal.begin() as session:
            version = (
                session.execute(
                    select(func.max(StateSnapshotModel.version)).where(StateSnapshotModel.scenario_id == scenario_id)
                ).scalar_one_or_none()
                or 0
            ) + 1

            session.add(StateSnapshotModel(
                id=snapshot_id,
                scenario_id=scenario_id,
                run_id=run_id,
                version=version,
                state_jsonb=state_copy,
                hash=state_hash,
                created_at=created_at,
            ))

            scenario_model = session.execute(
                select(ScenarioModel).where(ScenarioModel.id == scenario_id)
            ).scalar_one_or_none()
            if scenario_model:
                scenario_model.updated_at = created_at

        snapshot = Snapshot(
            id=snapshot_id,
            scenario_id=scenario_id,
            run_id=run_id,
            version=version,
            state_jsonb=deepcopy(state),
            hash=state_hash,
            created_at=created_at,
        )

        # In-memory mutations inside lock
        with self._lock:
            self.snapshots.append(snapshot)
            if scenario_id in self.scenarios:
                self.scenarios[scenario_id].state = deepcopy(state)
                self.scenarios[scenario_id].updated_at = created_at

        return snapshot

    def latest_snapshot_for_scenario(self, scenario_id: str) -> Snapshot | None:
        snapshots = [snapshot for snapshot in self.snapshots if snapshot.scenario_id == scenario_id]
        if not snapshots:
            return None
        return max(snapshots, key=lambda item: item.version)

    def latest_snapshot_for_run(self, run_id: str) -> Snapshot | None:
        snapshots = [snapshot for snapshot in self.snapshots if snapshot.run_id == run_id]
        if not snapshots:
            return None
        return max(snapshots, key=lambda item: item.version)

    def create_run(
        self,
        scenario_id: str,
        resumed_from_run_id: str | None = None,
        changed_decision: str | None = None,
        checkpoint_index: int = 0,
    ) -> Run:
        with self._lock:
            rid = f"run_{uuid4().hex}"
            started_at = self.now()

            with self.SessionLocal.begin() as session:
                session.add(
                    RunModel(
                        id=rid,
                        scenario_id=scenario_id,
                        status="running",
                        started_at=started_at,
                        resumed_from_run_id=resumed_from_run_id,
                        changed_decision=changed_decision,
                        checkpoint_index=checkpoint_index,
                        completed_agents=[],
                        skipped_agents=[],
                        last_error=None,
                    )
                )

            run = Run(
                id=rid,
                scenario_id=scenario_id,
                status="running",
                started_at=started_at,
                resumed_from_run_id=resumed_from_run_id,
                changed_decision=changed_decision,
                checkpoint_index=checkpoint_index,
            )
            self.runs[run.id] = run
            return run

    def complete_run(
        self,
        run_id: str,
        status: str,
        completed_agents: list[str] | None = None,
        skipped_agents: list[str] | None = None,
        checkpoint_index: int | None = None,
    ) -> Run:
        with self._lock:
            run = self.runs[run_id]
            run.status = status
            run.completed_at = self.now()
            if completed_agents is not None:
                run.completed_agents = list(completed_agents)
            if skipped_agents is not None:
                run.skipped_agents = list(skipped_agents)
            if checkpoint_index is not None:
                run.checkpoint_index = checkpoint_index

            with self.SessionLocal.begin() as session:
                session.execute(
                    update(RunModel)
                    .where(RunModel.id == run_id)
                    .values(
                        status=run.status,
                        completed_at=run.completed_at,
                        completed_agents=run.completed_agents,
                        skipped_agents=run.skipped_agents,
                        checkpoint_index=run.checkpoint_index,
                    )
                )

            return run

    def mark_run_failure(
        self,
        run_id: str,
        message: str,
        checkpoint_index: int,
        completed_agents: list[str],
        skipped_agents: list[str],
    ) -> Run:
        with self._lock:
            run = self.runs[run_id]
            run.status = "failed"
            run.completed_at = self.now()
            run.last_error = message
            run.checkpoint_index = checkpoint_index
            run.completed_agents = list(completed_agents)
            run.skipped_agents = list(skipped_agents)

            with self.SessionLocal.begin() as session:
                session.execute(
                    update(RunModel)
                    .where(RunModel.id == run_id)
                    .values(
                        status="failed",
                        completed_at=run.completed_at,
                        last_error=message,
                        checkpoint_index=checkpoint_index,
                        completed_agents=run.completed_agents,
                        skipped_agents=run.skipped_agents,
                    )
                )

            return run

    def create_export(self, scenario_id: str, kind: str, fmt: str, content: str) -> ExportRecord:
        with self._lock:
            export_id = f"exp_{uuid4().hex}"
            created_at = self.now()
            with self.SessionLocal.begin() as session:
                session.add(
                    ExportRecordModel(
                        id=export_id,
                        scenario_id=scenario_id,
                        kind=kind,
                        format=fmt,
                        content=content,
                        created_at=created_at,
                    )
                )

            export = ExportRecord(
                id=export_id,
                scenario_id=scenario_id,
                kind=kind,
                format=fmt,
                content=content,
                created_at=created_at,
            )
            self.exports[export_id] = export
            return export

    def _load_from_db(self) -> None:
        with self._lock:
            with self.SessionLocal() as session:
                project_rows = session.execute(select(ProjectModel)).scalars().all()
                scenario_rows = session.execute(select(ScenarioModel)).scalars().all()
                run_rows = session.execute(select(RunModel)).scalars().all()
                export_rows = session.execute(select(ExportRecordModel)).scalars().all()
                snapshot_rows = session.execute(select(StateSnapshotModel)).scalars().all()

            self.projects = {
                row.id: Project(
                    id=row.id,
                    name=row.name,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                )
                for row in project_rows
            }

            self.snapshots = [
                Snapshot(
                    id=row.id,
                    scenario_id=row.scenario_id,
                    run_id=row.run_id,
                    version=row.version,
                    state_jsonb=deepcopy(row.state_jsonb),
                    hash=row.hash,
                    created_at=row.created_at,
                )
                for row in sorted(snapshot_rows, key=lambda s: (s.scenario_id, s.version))
            ]
            latest_state = {
                snapshot.scenario_id: snapshot.state_jsonb
                for snapshot in self.snapshots
            }

            self.scenarios = {
                row.id: Scenario(
                    id=row.id,
                    project_id=row.project_id,
                    name=row.name,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    state=deepcopy(latest_state.get(row.id, {})),
                )
                for row in scenario_rows
            }

            self.runs = {
                row.id: Run(
                    id=row.id,
                    scenario_id=row.scenario_id,
                    status=row.status,
                    started_at=row.started_at,
                    completed_at=row.completed_at,
                    resumed_from_run_id=row.resumed_from_run_id,
                    changed_decision=row.changed_decision,
                    checkpoint_index=row.checkpoint_index,
                    completed_agents=list(row.completed_agents or []),
                    skipped_agents=list(row.skipped_agents or []),
                    last_error=row.last_error,
                )
                for row in run_rows
            }

            self.exports = {
                row.id: ExportRecord(
                    id=row.id,
                    scenario_id=row.scenario_id,
                    kind=row.kind,
                    format=row.format,
                    content=row.content,
                    created_at=row.created_at,
                )
                for row in export_rows
            }

    def _ensure_dev_user(self, session: Session) -> None:
        user = session.execute(select(UserModel).where(UserModel.id == "user_dev")).scalar_one_or_none()
        if user is None:
            session.add(
                UserModel(
                    id="user_dev",
                    email="dev@gtmgraph.local",
                    created_at=self.now(),
                )
            )
