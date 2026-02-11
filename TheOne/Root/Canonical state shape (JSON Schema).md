1.2 State invariants you must enforce

If you don’t enforce these, you will ship contradictions.

decisions.icp must exist before finalizing pricing, channels, sales motion nodes.

decisions.pricing.metric must be non-empty for any plan to be marked “complete.”

graph.nodes[].evidence_refs must not be empty for any competitor or pricing node unless MetaRef.source_type is assumption.

{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://gtmgraph.ai/schemas/canonical_state.schema.json",
  "title": "CanonicalState",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "meta",
    "idea",
    "constraints",
    "inputs",
    "evidence",
    "decisions",
    "pillars",
    "graph",
    "risks",
    "execution",
    "telemetry"
  ],
  "properties": {
    "meta": {
      "type": "object",
      "additionalProperties": false,
      "required": ["project_id", "scenario_id", "run_id", "created_at", "updated_at", "schema_version"],
      "properties": {
        "project_id": { "type": "string" },
        "scenario_id": { "type": "string" },
        "run_id": { "type": "string" },
        "schema_version": { "type": "string" },
        "created_at": { "type": "string", "format": "date-time" },
        "updated_at": { "type": "string", "format": "date-time" }
      }
    },

    "idea": {
      "type": "object",
      "additionalProperties": false,
      "required": ["name", "one_liner", "problem", "target_region", "category"],
      "properties": {
        "name": { "type": "string", "minLength": 1 },
        "one_liner": { "type": "string", "minLength": 1 },
        "problem": { "type": "string", "minLength": 1 },
        "target_region": { "type": "string", "minLength": 1 },
        "category": { "type": "string", "enum": ["b2b_saas", "b2b_services", "b2c"] },
        "domain": { "type": "string" }
      }
    },

    "constraints": {
      "type": "object",
      "additionalProperties": false,
      "required": ["team_size", "timeline_weeks", "budget_usd_monthly", "compliance_level"],
      "properties": {
        "team_size": { "type": "integer", "minimum": 1, "maximum": 200 },
        "timeline_weeks": { "type": "integer", "minimum": 1, "maximum": 520 },
        "budget_usd_monthly": { "type": "number", "minimum": 0 },
        "compliance_level": { "type": "string", "enum": ["none", "low", "medium", "high"] },
        "tech_preferences": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "frontend": { "type": "string" },
            "backend": { "type": "string" },
            "cloud": { "type": "string" }
          }
        }
      }
    },

    "inputs": {
      "type": "object",
      "additionalProperties": false,
      "required": ["intake_answers", "open_questions"],
      "properties": {
        "intake_answers": {
          "type": "array",
          "items": { "$ref": "#/$defs/IntakeAnswer" }
        },
        "open_questions": {
          "type": "array",
          "items": { "$ref": "#/$defs/OpenQuestion" }
        }
      }
    },

    "evidence": {
      "type": "object",
      "additionalProperties": false,
      "required": ["sources", "competitors", "pricing_anchors", "messaging_patterns", "channel_signals"],
      "properties": {
        "sources": {
          "type": "array",
          "items": { "$ref": "#/$defs/EvidenceSource" }
        },
        "competitors": {
          "type": "array",
          "items": { "$ref": "#/$defs/Competitor" }
        },
        "pricing_anchors": {
          "type": "array",
          "items": { "$ref": "#/$defs/PricingAnchor" }
        },
        "messaging_patterns": {
          "type": "array",
          "items": { "$ref": "#/$defs/MessagingPattern" }
        },
        "channel_signals": {
          "type": "array",
          "items": { "$ref": "#/$defs/ChannelSignal" }
        }
      }
    },

    "decisions": {
      "type": "object",
      "additionalProperties": false,
      "required": ["icp", "positioning", "pricing", "channels", "sales_motion"],
      "properties": {
        "icp": { "$ref": "#/$defs/ICPDecision" },
        "positioning": { "$ref": "#/$defs/PositioningDecision" },
        "pricing": { "$ref": "#/$defs/PricingDecision" },
        "channels": { "$ref": "#/$defs/ChannelDecision" },
        "sales_motion": { "$ref": "#/$defs/SalesMotionDecision" }
      }
    },

    "pillars": {
      "type": "object",
      "additionalProperties": false,
      "required": ["market_to_money", "product", "execution", "people_and_cash"],
      "properties": {
        "market_to_money": { "$ref": "#/$defs/PillarBlock" },
        "product": { "$ref": "#/$defs/PillarBlock" },
        "execution": { "$ref": "#/$defs/PillarBlock" },
        "people_and_cash": { "$ref": "#/$defs/PillarBlock" }
      }
    },

    "graph": {
      "type": "object",
      "additionalProperties": false,
      "required": ["nodes", "edges", "groups"],
      "properties": {
        "nodes": {
          "type": "array",
          "items": { "$ref": "#/$defs/GraphNode" }
        },
        "edges": {
          "type": "array",
          "items": { "$ref": "#/$defs/GraphEdge" }
        },
        "groups": {
          "type": "array",
          "items": { "$ref": "#/$defs/GraphGroup" }
        }
      }
    },

    "risks": {
      "type": "object",
      "additionalProperties": false,
      "required": ["contradictions", "missing_proof", "high_risk_flags"],
      "properties": {
        "contradictions": {
          "type": "array",
          "items": { "$ref": "#/$defs/Contradiction" }
        },
        "missing_proof": {
          "type": "array",
          "items": { "$ref": "#/$defs/MissingProof" }
        },
        "high_risk_flags": {
          "type": "array",
          "items": { "$ref": "#/$defs/HighRiskFlag" }
        }
      }
    },

    "execution": {
      "type": "object",
      "additionalProperties": false,
      "required": ["chosen_track", "next_actions", "experiments", "assets"],
      "properties": {
        "chosen_track": {
          "type": "string",
          "enum": ["validation_sprint", "outbound_sprint", "landing_waitlist", "pilot_onboarding", "unset"]
        },
        "next_actions": {
          "type": "array",
          "items": { "$ref": "#/$defs/NextAction" }
        },
        "experiments": {
          "type": "array",
          "items": { "$ref": "#/$defs/Experiment" }
        },
        "assets": {
          "type": "array",
          "items": { "$ref": "#/$defs/Asset" }
        }
      }
    },

    "telemetry": {
      "type": "object",
      "additionalProperties": false,
      "required": ["agent_timings", "token_spend", "errors"],
      "properties": {
        "agent_timings": {
          "type": "array",
          "items": { "$ref": "#/$defs/AgentTiming" }
        },
        "token_spend": {
          "type": "object",
          "additionalProperties": false,
          "required": ["total", "by_agent"],
          "properties": {
            "total": { "type": "integer", "minimum": 0 },
            "by_agent": {
              "type": "array",
              "items": { "$ref": "#/$defs/TokenByAgent" }
            }
          }
        },
        "errors": {
          "type": "array",
          "items": { "$ref": "#/$defs/RunError" }
        }
      }
    }
  },

  "$defs": {
    "MetaRef": {
      "type": "object",
      "additionalProperties": false,
      "required": ["source_type", "confidence", "updated_by", "updated_at", "sources"],
      "properties": {
        "source_type": { "type": "string", "enum": ["evidence", "inference", "assumption"] },
        "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
        "updated_by": { "type": "string" },
        "updated_at": { "type": "string", "format": "date-time" },
        "sources": { "type": "array", "items": { "type": "string" } }
      }
    },

    "IntakeAnswer": {
      "type": "object",
      "additionalProperties": false,
      "required": ["question_id", "answer_type", "value", "meta"],
      "properties": {
        "question_id": { "type": "string" },
        "answer_type": { "type": "string", "enum": ["mcq", "custom", "not_sure"] },
        "value": {},
        "justification": { "type": "string" },
        "meta": { "$ref": "#/$defs/MetaRef" }
      }
    },

    "OpenQuestion": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "prompt", "status"],
      "properties": {
        "id": { "type": "string" },
        "prompt": { "type": "string" },
        "status": { "type": "string", "enum": ["open", "answered", "blocked"] },
        "answer": { "type": "string" }
      }
    },

    "EvidenceSource": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "url", "title", "retrieved_at", "quality_score", "snippets"],
      "properties": {
        "id": { "type": "string" },
        "url": { "type": "string" },
        "title": { "type": "string" },
        "retrieved_at": { "type": "string", "format": "date-time" },
        "quality_score": { "type": "number", "minimum": 0, "maximum": 1 },
        "snippets": { "type": "array", "items": { "type": "string" } }
      }
    },

    "Competitor": {
      "type": "object",
      "additionalProperties": false,
      "required": ["name", "type", "url", "summary", "meta"],
      "properties": {
        "name": { "type": "string" },
        "type": { "type": "string", "enum": ["direct", "indirect", "substitute", "do_nothing"] },
        "url": { "type": "string" },
        "summary": { "type": "string" },
        "meta": { "$ref": "#/$defs/MetaRef" }
      }
    },

    "PricingAnchor": {
      "type": "object",
      "additionalProperties": false,
      "required": ["competitor_name", "pricing_model", "price_points", "meta"],
      "properties": {
        "competitor_name": { "type": "string" },
        "pricing_model": { "type": "string" },
        "price_points": { "type": "array", "items": { "type": "string" } },
        "meta": { "$ref": "#/$defs/MetaRef" }
      }
    },

    "MessagingPattern": {
      "type": "object",
      "additionalProperties": false,
      "required": ["pattern", "examples", "meta"],
      "properties": {
        "pattern": { "type": "string" },
        "examples": { "type": "array", "items": { "type": "string" } },
        "meta": { "$ref": "#/$defs/MetaRef" }
      }
    },

    "ChannelSignal": {
      "type": "object",
      "additionalProperties": false,
      "required": ["channel", "signal", "meta"],
      "properties": {
        "channel": { "type": "string" },
        "signal": { "type": "string" },
        "meta": { "$ref": "#/$defs/MetaRef" }
      }
    },

    "ICPDecision": {
      "type": "object",
      "additionalProperties": false,
      "required": ["selected_option_id", "profile", "anti_profile", "trigger_event", "meta"],
      "properties": {
        "selected_option_id": { "type": "string" },
        "profile": {
          "type": "object",
          "additionalProperties": false,
          "required": ["buyer_role", "company_type", "company_size", "industry", "budget_owner"],
          "properties": {
            "buyer_role": { "type": "string" },
            "company_type": { "type": "string" },
            "company_size": { "type": "string" },
            "industry": { "type": "string" },
            "budget_owner": { "type": "string" }
          }
        },
        "anti_profile": { "type": "string" },
        "trigger_event": { "type": "string" },
        "meta": { "$ref": "#/$defs/MetaRef" }
      }
    },

    "PositioningDecision": {
      "type": "object",
      "additionalProperties": false,
      "required": ["category", "primary_alternative", "wedge", "value_prop", "meta"],
      "properties": {
        "category": { "type": "string" },
        "primary_alternative": { "type": "string" },
        "wedge": { "type": "string" },
        "value_prop": { "type": "string" },
        "meta": { "$ref": "#/$defs/MetaRef" }
      }
    },

    "PricingDecision": {
      "type": "object",
      "additionalProperties": false,
      "required": ["metric", "tiers", "first_price_to_test", "discount_policy", "meta"],
      "properties": {
        "metric": { "type": "string" },
        "tiers": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "object",
            "additionalProperties": false,
            "required": ["name", "price", "includes"],
            "properties": {
              "name": { "type": "string" },
              "price": { "type": "string" },
              "includes": { "type": "array", "items": { "type": "string" } }
            }
          }
        },
        "first_price_to_test": { "type": "string" },
        "discount_policy": { "type": "string" },
        "meta": { "$ref": "#/$defs/MetaRef" }
      }
    },

    "ChannelDecision": {
      "type": "object",
      "additionalProperties": false,
      "required": ["primary", "secondary", "meta"],
      "properties": {
        "primary": { "type": "string" },
        "secondary": { "type": "string" },
        "meta": { "$ref": "#/$defs/MetaRef" }
      }
    },

    "SalesMotionDecision": {
      "type": "object",
      "additionalProperties": false,
      "required": ["motion", "pipeline_stages", "scripts", "meta"],
      "properties": {
        "motion": { "type": "string", "enum": ["outbound_led", "inbound_led", "plg", "partner_led"] },
        "pipeline_stages": { "type": "array", "items": { "type": "string" } },
        "scripts": { "type": "array", "items": { "type": "string" } },
        "meta": { "$ref": "#/$defs/MetaRef" }
      }
    },

    "PillarBlock": {
      "type": "object",
      "additionalProperties": false,
      "required": ["summary", "key_outputs", "meta"],
      "properties": {
        "summary": { "type": "string" },
        "key_outputs": { "type": "array", "items": { "type": "string" } },
        "meta": { "$ref": "#/$defs/MetaRef" }
      }
    },

    "GraphGroup": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "title", "pillar", "node_ids"],
      "properties": {
        "id": { "type": "string" },
        "title": { "type": "string" },
        "pillar": { "type": "string", "enum": ["market_to_money", "product", "execution", "people_and_cash"] },
        "node_ids": { "type": "array", "items": { "type": "string" } }
      }
    },

    "GraphNode": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "title", "type", "pillar", "content", "assumptions", "confidence", "evidence_refs", "dependencies", "status"],
      "properties": {
        "id": { "type": "string" },
        "title": { "type": "string" },
        "type": { "type": "string", "enum": ["decision", "evidence", "plan", "asset", "experiment", "risk", "checklist"] },
        "pillar": { "type": "string", "enum": ["market_to_money", "product", "execution", "people_and_cash"] },
        "content": { "type": "object" },
        "assumptions": { "type": "array", "items": { "type": "string" } },
        "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
        "evidence_refs": { "type": "array", "items": { "type": "string" } },
        "dependencies": { "type": "array", "items": { "type": "string" } },
        "status": { "type": "string", "enum": ["draft", "needs_input", "final"] }
      }
    },

    "GraphEdge": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "source", "target", "type"],
      "properties": {
        "id": { "type": "string" },
        "source": { "type": "string" },
        "target": { "type": "string" },
        "type": { "type": "string", "enum": ["depends_on", "informs", "blocks"] }
      }
    },

    "Contradiction": {
      "type": "object",
      "additionalProperties": false,
      "required": ["rule_id", "severity", "message", "paths"],
      "properties": {
        "rule_id": { "type": "string" },
        "severity": { "type": "string", "enum": ["critical", "high", "medium", "low"] },
        "message": { "type": "string" },
        "paths": { "type": "array", "items": { "type": "string" } }
      }
    },

    "MissingProof": {
      "type": "object",
      "additionalProperties": false,
      "required": ["area", "message", "required_evidence"],
      "properties": {
        "area": { "type": "string" },
        "message": { "type": "string" },
        "required_evidence": { "type": "array", "items": { "type": "string" } }
      }
    },

    "HighRiskFlag": {
      "type": "object",
      "additionalProperties": false,
      "required": ["flag", "message", "severity"],
      "properties": {
        "flag": { "type": "string" },
        "message": { "type": "string" },
        "severity": { "type": "string", "enum": ["high", "medium", "low"] }
      }
    },

    "NextAction": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "title", "description", "owner", "due_in_days", "status"],
      "properties": {
        "id": { "type": "string" },
        "title": { "type": "string" },
        "description": { "type": "string" },
        "owner": { "type": "string" },
        "due_in_days": { "type": "integer", "minimum": 0, "maximum": 3650 },
        "status": { "type": "string", "enum": ["todo", "doing", "done"] }
      }
    },

    "Experiment": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "hypothesis", "steps", "success_metric", "pass_fail_threshold"],
      "properties": {
        "id": { "type": "string" },
        "hypothesis": { "type": "string" },
        "steps": { "type": "array", "items": { "type": "string" } },
        "success_metric": { "type": "string" },
        "pass_fail_threshold": { "type": "string" }
      }
    },

    "Asset": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "type", "title", "content_ref"],
      "properties": {
        "id": { "type": "string" },
        "type": { "type": "string", "enum": ["landing_copy", "outreach_sequence", "call_script", "pricing_page_outline", "pitch_deck_outline"] },
        "title": { "type": "string" },
        "content_ref": { "type": "string" }
      }
    },

    "AgentTiming": {
      "type": "object",
      "additionalProperties": false,
      "required": ["agent", "started_at", "ended_at", "status"],
      "properties": {
        "agent": { "type": "string" },
        "started_at": { "type": "string", "format": "date-time" },
        "ended_at": { "type": "string", "format": "date-time" },
        "status": { "type": "string", "enum": ["ok", "failed", "skipped"] }
      }
    },

    "TokenByAgent": {
      "type": "object",
      "additionalProperties": false,
      "required": ["agent", "tokens"],
      "properties": {
        "agent": { "type": "string" },
        "tokens": { "type": "integer", "minimum": 0 }
      }
    },

    "RunError": {
      "type": "object",
      "additionalProperties": false,
      "required": ["time", "component", "message"],
      "properties": {
        "time": { "type": "string", "format": "date-time" },
        "component": { "type": "string" },
        "message": { "type": "string" },
        "stack": { "type": "string" }
      }
    }
  }
}
