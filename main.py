
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
from uuid import uuid4
from copy import deepcopy

app = FastAPI(title="Relational Intelligence Platform")

BASE = Path(__file__).parent
STATIC = BASE / "static"

state = {
    "model": {
        "id": "demo-model",
        "name": "Customer Operations",
        "current_version": "v1",
        "versions": {
            "v1": {
                "id": "v1",
                "number": 1,
                "entities": [
                    {"id":"customer","name":"Customer"},
                    {"id":"order","name":"Order"},
                    {"id":"invoice","name":"Invoice"},
                ],
                "relations": [
                    {"id":"customer-order","source":"customer","target":"order","label":"Customer → Order"},
                    {"id":"customer-invoice","source":"customer","target":"invoice","label":"Customer → Invoice"},
                ],
            }
        },
        "scenarios": {},
        "decisions": {},
    }
}

class ScenarioRequest(BaseModel):
    baseline_version: str
    remove_relation_id: str

class AnalysisRequest(BaseModel):
    scenario_id: str

class DecisionRequest(BaseModel):
    baseline_version: str
    scenario_ids: list[str]

class SelectRequest(BaseModel):
    scenario_id: str

def version_state(version_id):
    v = state["model"]["versions"].get(version_id)
    if not v:
        raise HTTPException(404, "VERSION_NOT_FOUND")
    return deepcopy(v)

@app.get("/health")
def health():
    return {"ok": True, "service": "relational-intelligence"}

@app.get("/api/model")
def get_model():
    m = state["model"]
    return {
        "id": m["id"],
        "name": m["name"],
        "current_version": m["current_version"],
        "versions": list(m["versions"].values()),
        "scenarios": list(m["scenarios"].values()),
        "decisions": list(m["decisions"].values()),
    }

@app.get("/api/versions/{version_id}")
def get_version(version_id: str):
    return version_state(version_id)

@app.post("/api/scenarios")
def create_scenario(req: ScenarioRequest):
    baseline = version_state(req.baseline_version)
    if not any(r["id"] == req.remove_relation_id for r in baseline["relations"]):
        raise HTTPException(400, "RELATION_NOT_FOUND")
    sid = "scenario-" + uuid4().hex[:8]
    scenario = {
        "id": sid,
        "name": "Scenario A",
        "status": "HYPOTHETICAL",
        "baseline_version": req.baseline_version,
        "change": {"type":"REMOVE", "relation_id":req.remove_relation_id},
    }
    state["model"]["scenarios"][sid] = scenario
    return scenario

@app.get("/api/scenarios/{scenario_id}")
def get_scenario(scenario_id: str):
    s = state["model"]["scenarios"].get(scenario_id)
    if not s:
        raise HTTPException(404, "SCENARIO_NOT_FOUND")
    baseline = version_state(s["baseline_version"])
    result = deepcopy(baseline)
    rid = s["change"]["relation_id"]
    result["relations"] = [r for r in result["relations"] if r["id"] != rid]
    result["scenario_id"] = scenario_id
    result["status"] = "HYPOTHETICAL"
    return {"scenario": s, "state": result}

@app.post("/api/analyses")
def analyze(req: AnalysisRequest):
    s = state["model"]["scenarios"].get(req.scenario_id)
    if not s:
        raise HTTPException(404, "SCENARIO_NOT_FOUND")
    baseline = version_state(s["baseline_version"])
    hypothetical = get_scenario(req.scenario_id)["state"]
    return {
        "scenario_id": req.scenario_id,
        "structural": {
            "entities": len(hypothetical["entities"]),
            "relations": len(hypothetical["relations"]),
            "relation_delta": len(hypothetical["relations"]) - len(baseline["relations"]),
        },
        "relational": {
            "baseline_relations": len(baseline["relations"]),
            "scenario_relations": len(hypothetical["relations"]),
            "changed": True,
        },
        "interpretation": "Removing the selected relation changes the relational structure while preserving the three entities in this demo.",
    }

@app.post("/api/decisions")
def create_decision(req: DecisionRequest):
    for sid in req.scenario_ids:
        s = state["model"]["scenarios"].get(sid)
        if not s or s["baseline_version"] != req.baseline_version:
            raise HTTPException(400, "INVALID_CANDIDATE")
    did = "decision-" + uuid4().hex[:8]
    d = {
        "id": did,
        "baseline_version": req.baseline_version,
        "scenario_ids": req.scenario_ids,
        "selected_scenario_id": None,
        "status": "PENDING",
    }
    state["model"]["decisions"][did] = d
    return d

@app.post("/api/decisions/{decision_id}/select")
def select_decision(decision_id: str, req: SelectRequest):
    d = state["model"]["decisions"].get(decision_id)
    if not d:
        raise HTTPException(404, "DECISION_NOT_FOUND")
    if req.scenario_id not in d["scenario_ids"]:
        raise HTTPException(400, "SCENARIO_NOT_A_CANDIDATE")
    d["selected_scenario_id"] = req.scenario_id
    d["status"] = "SELECTED"
    return d

@app.post("/api/scenarios/{scenario_id}/apply")
def apply_scenario(scenario_id: str):
    s = state["model"]["scenarios"].get(scenario_id)
    if not s:
        raise HTTPException(404, "SCENARIO_NOT_FOUND")
    if s["status"] == "APPLIED":
        raise HTTPException(409, "SCENARIO_ALREADY_APPLIED")
    current = state["model"]["current_version"]
    if current != s["baseline_version"]:
        raise HTTPException(409, "BASELINE_VERSION_CHANGED")
    baseline = version_state(current)
    rid = s["change"]["relation_id"]
    new_id = "v" + str(len(state["model"]["versions"]) + 1)
    new_version = deepcopy(baseline)
    new_version["id"] = new_id
    new_version["number"] = len(state["model"]["versions"]) + 1
    new_version["parent_version"] = current
    new_version["relations"] = [r for r in new_version["relations"] if r["id"] != rid]
    state["model"]["versions"][new_id] = new_version
    state["model"]["current_version"] = new_id
    s["status"] = "APPLIED"
    s["applied_version"] = new_id
    return {"version": new_version, "scenario": s}

app.mount("/static", StaticFiles(directory=STATIC), name="static")

@app.get("/{path:path}")
def frontend(path: str):
    return FileResponse(STATIC / "index.html")
