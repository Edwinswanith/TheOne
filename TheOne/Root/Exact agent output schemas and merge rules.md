Agents must not output essays. They output structured diffs that the orchestrator can merge deterministically.

2.1 Agent output schema (JSON Schema)
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://gtmgraph.ai/schemas/agent_output.schema.json",
  "title": "AgentOutput",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "agent",
    "run_id",
    "produced_at",
    "patches",
    "proposals",
    "facts",
    "assumptions",
    "risks",
    "required_inputs",
    "node_updates"
  ],
  "properties": {
    "agent": { "type": "string" },
    "run_id": { "type": "string" },
    "produced_at": { "type": "string", "format": "date-time" },

    "patches": {
      "type": "array",
      "items": { "$ref": "#/$defs/StatePatch" }
    },

    "proposals": {
      "type": "array",
      "items": { "$ref": "#/$defs/DecisionProposal" }
    },

    "facts": {
      "type": "array",
      "items": { "$ref": "#/$defs/Fact" }
    },

    "assumptions": {
      "type": "array",
      "items": { "$ref": "#/$defs/Assumption" }
    },

    "risks": {
      "type": "array",
      "items": { "$ref": "#/$defs/Risk" }
    },

    "required_inputs": {
      "type": "array",
      "items": { "$ref": "#/$defs/RequiredInput" }
    },

    "node_updates": {
      "type": "array",
      "items": { "$ref": "#/$defs/NodeUpdate" }
    }
  },

  "$defs": {
    "StatePatch": {
      "type": "object",
      "additionalProperties": false,
      "required": ["op", "path", "value", "meta"],
      "properties": {
        "op": { "type": "string", "enum": ["add", "replace", "remove"] },
        "path": { "type": "string", "description": "JSON Pointer path into canonical state" },
        "value": {},
        "meta": {
          "type": "object",
          "additionalProperties": false,
          "required": ["source_type", "confidence", "sources"],
          "properties": {
            "source_type": { "type": "string", "enum": ["evidence", "inference", "assumption"] },
            "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
            "sources": { "type": "array", "items": { "type": "string" } }
          }
        }
      }
    },

    "DecisionProposal": {
      "type": "object",
      "additionalProperties": false,
      "required": ["decision_key", "options", "recommended_option_id", "rationale", "meta"],
      "properties": {
        "decision_key": { "type": "string", "enum": ["icp", "positioning", "pricing", "channels", "sales_motion"] },
        "options": {
          "type": "array",
          "minItems": 1,
          "maxItems": 3,
          "items": {
            "type": "object",
            "additionalProperties": false,
            "required": ["id", "label", "details", "pros", "cons", "risks"],
            "properties": {
              "id": { "type": "string" },
              "label": { "type": "string" },
              "details": { "type": "object" },
              "pros": { "type": "array", "items": { "type": "string" } },
              "cons": { "type": "array", "items": { "type": "string" } },
              "risks": { "type": "array", "items": { "type": "string" } }
            }
          }
        },
        "recommended_option_id": { "type": "string" },
        "rationale": { "type": "string" },
        "meta": { "$ref": "#/$defs/Meta" }
      }
    },

    "Fact": {
      "type": "object",
      "additionalProperties": false,
      "required": ["claim", "supporting_sources", "confidence"],
      "properties": {
        "claim": { "type": "string" },
        "supporting_sources": { "type": "array", "items": { "type": "string" } },
        "confidence": { "type": "number", "minimum": 0, "maximum": 1 }
      }
    },

    "Assumption": {
      "type": "object",
      "additionalProperties": false,
      "required": ["statement", "why_it_matters", "how_to_validate", "confidence"],
      "properties": {
        "statement": { "type": "string" },
        "why_it_matters": { "type": "string" },
        "how_to_validate": { "type": "string" },
        "confidence": { "type": "number", "minimum": 0, "maximum": 1 }
      }
    },

    "Risk": {
      "type": "object",
      "additionalProperties": false,
      "required": ["risk", "severity", "mitigation"],
      "properties": {
        "risk": { "type": "string" },
        "severity": { "type": "string", "enum": ["critical", "high", "medium", "low"] },
        "mitigation": { "type": "string" }
      }
    },

    "RequiredInput": {
      "type": "object",
      "additionalProperties": false,
      "required": ["field", "question", "blocking"],
      "properties": {
        "field": { "type": "string" },
        "question": { "type": "string" },
        "blocking": { "type": "boolean" }
      }
    },

    "NodeUpdate": {
      "type": "object",
      "additionalProperties": false,
      "required": ["node_id", "action", "payload"],
      "properties": {
        "node_id": { "type": "string" },
        "action": { "type": "string", "enum": ["create", "update", "finalize"] },
        "payload": { "type": "object" }
      }
    },

    "Meta": {
      "type": "object",
      "additionalProperties": false,
      "required": ["source_type", "confidence", "sources"],
      "properties": {
        "source_type": { "type": "string", "enum": ["evidence", "inference", "assumption"] },
        "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
        "sources": { "type": "array", "items": { "type": "string" } }
      }
    }
  }
}

2.2 Merge rules (this is where most systems fail)

You need deterministic merges or your state becomes garbage.

Merge rule A: Decision ownership

Only the orchestrator can write into state.decisions.*.selected_option_id.

Agents can only submit DecisionProposal.

User choice or orchestrator autopick (only if allowed) sets the final decision.

Merge rule B: Evidence dedupe and promotion

Evidence sources are stored in state.evidence.sources[] by URL.

If a new source has same normalized URL, merge snippets and keep max quality score.

Merge rule C: Patch application ordering

Apply patches in this order:

Evidence patches

Decision proposal patches

Pillar patches

Graph node patches

Execution patches

Telemetry patches

Why: decisions depend on evidence, and graph depends on decisions.

Merge rule D: Confidence aggregation

When multiple agents update the same field (allowed only outside decisions):

If updates have evidence: take the update with highest confidence.

If both evidence: weighted average by source quality, but keep the text of the top confidence one and attach both source lists.

If neither evidence: mark as assumption and cap confidence at 0.6.

Merge rule E: Conflict resolution

When two patches write to same path with different values:

If one is evidence and the other is inference, evidence wins.

If both are evidence, keep both as alternatives under a “candidates” list and create a validator item requiring user decision.

If both are assumption, keep the one with higher confidence but add a “missing proof” flag.

Merge rule F: Node updates are idempotent

Node IDs must be stable. An update should never create a duplicate node with same purpose.
Enforce stable IDs like:

market.icp.summary

pricing.metric

sales.pipeline
If you don’t do this, your graph will explode with duplicates.