from __future__ import annotations

from pathlib import Path

from services.orchestrator.tools.providers import ProviderClient, ProviderConfig


def test_provider_client_uses_fixture_mode_by_default() -> None:
    client = ProviderClient(
        ProviderConfig(
            use_real_providers=False,
            fixture_root=Path(__file__).resolve().parents[1] / "fixtures",
            google_api_key=None,
            perplexity_api_key=None,
        )
    )

    bundle = client.fetch_evidence_bundle({"idea": {"name": "PulsePilot"}})
    synthesis = client.synthesize_evidence(bundle)

    assert bundle["sources"]
    assert synthesis["facts"]


def test_decision_template_fixture_lookup() -> None:
    client = ProviderClient(
        ProviderConfig(
            use_real_providers=False,
            fixture_root=Path(__file__).resolve().parents[1] / "fixtures",
            google_api_key=None,
            perplexity_api_key=None,
        )
    )

    icp = client.decision_template("icp")
    assert icp["recommended_option_id"] == "icp_opt_1"
    assert len(icp["options"]) >= 1
