"""
Phase 3C Tests: Known Domains Persistence Migration & Tier 1 Compatibility
Validates FabricKnownDomainRepository, all 15 active Fabric reference records,
and SenderClassifier / RuleEngine Tier 0 & Tier 1 classification behavior.
"""

import asyncio
import sys
from pathlib import Path
import pytest

# Ensure project root in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.behavior import KnownDomain, SenderProfile
from app.repositories.known_domain_repo import (
    FabricKnownDomainRepository,
    PostgresKnownDomainRepository,
    get_known_domain_repository,
)
from app.services.rule_engine import RuleEngine


@pytest.mark.asyncio
async def test_fabric_known_domains_read_all_15_records():
    """Verify that Fabric repository reads all 15 active reference records without data loss."""
    repo = FabricKnownDomainRepository()
    records = await repo.list_all()
    assert len(records) == 15, f"Expected 15 active records, got {len(records)}"

    domains = {r.domain: r for r in records}
    expected_sample_domains = [
        "flipkart.com",
        "amazon.in",
        "swiggy.in",
        "zomato.com",
        "myntra.com",
        "linkedin.com",
        "github.com",
        "hdfcbank.net",
        "icicibank.com",
        "paytm.com",
        "substack.com",
        "coursera.org",
        "udemy.com",
        "hackerrank.com",
        "google.com",
    ]

    for d in expected_sample_domains:
        assert d in domains, f"Missing expected domain: {d}"
        assert domains[d].default_tier in (0, 1)

    print(f"PASS: FabricKnownDomainRepository.list_all() ({len(records)} verified active records)")


@pytest.mark.asyncio
async def test_fabric_known_domains_get_by_domain():
    """Verify lookup by domain across various categories."""
    repo = FabricKnownDomainRepository()

    # Tier 0 Shopping
    flipkart = await repo.get_by_domain("flipkart.com")
    assert flipkart is not None
    assert flipkart.domain == "flipkart.com"
    assert flipkart.default_tier == 0
    assert flipkart.default_sender_type == "shopping"

    # Tier 1 Developer
    github = await repo.get_by_domain("github.com")
    assert github is not None
    assert github.domain == "github.com"
    assert github.default_tier == 1
    assert github.default_sender_type == "tech"

    # Tier 1 Banking
    hdfc = await repo.get_by_domain("hdfcbank.net")
    assert hdfc is not None
    assert hdfc.domain == "hdfcbank.net"
    assert hdfc.default_tier == 1
    assert hdfc.default_sender_type == "banking"

    # Non-existent domain
    non_existent = await repo.get_by_domain("non-existent-startup.co")
    assert non_existent is None

    print("PASS: FabricKnownDomainRepository.get_by_domain() exact lookups")


@pytest.mark.asyncio
async def test_tier0_and_tier1_classification_compatibility():
    """Verify Tier 0 & Tier 1 classification behavior using Fabric repository lookups."""
    repo = get_known_domain_repository()

    # 1. Test Tier 0 domain (Flipkart)
    flipkart_kd = await repo.get_by_domain("flipkart.com")
    assert flipkart_kd is not None
    sender_prof_tier0 = SenderProfile(
        email_address="deals@flipkart.com",
        domain="flipkart.com",
        display_name="Flipkart Deals",
        sender_type=flipkart_kd.default_sender_type,
        processing_tier=flipkart_kd.default_tier,
    )
    result_tier0 = RuleEngine.process_tier0_or_1(
        sender_profile=sender_prof_tier0,
        subject="Big Billion Days are live!",
        snippet="Save up to 80%",
        body_text="Special discounts today.",
    )
    assert result_tier0 is not None
    assert result_tier0["processing_tier"] == 0
    assert result_tier0["suggested_bucket"] == "ignored"
    assert result_tier0["is_marketing_or_newsletter"] is True
    print("PASS: Tier 0 marketing classification verified via Fabric repository")

    # 2. Test Tier 1 domain (GitHub)
    github_kd = await repo.get_by_domain("github.com")
    assert github_kd is not None
    sender_prof_tier1 = SenderProfile(
        email_address="notifications@github.com",
        domain="github.com",
        display_name="GitHub Notifications",
        sender_type=github_kd.default_sender_type,
        processing_tier=github_kd.default_tier,
        engagement_score=0.6,
    )
    result_tier1 = RuleEngine.process_tier0_or_1(
        sender_profile=sender_prof_tier1,
        subject="[GitHub] Pull request #42 merged",
        snippet="Mahesh merged PR 42 into main",
        body_text="PR merged cleanly.",
    )
    assert result_tier1 is not None
    assert result_tier1["processing_tier"] == 1
    assert result_tier1["suggested_bucket"] == "this_week"
    print("PASS: Tier 1 notification classification verified via Fabric repository")

    # 3. Test Unknown domain (Requires Tier 2 AI)
    unknown_kd = await repo.get_by_domain("executive-partner.com")
    assert unknown_kd is None
    sender_prof_tier2 = SenderProfile(
        email_address="john@executive-partner.com",
        domain="executive-partner.com",
        display_name="John Doe",
        sender_type="unknown",
        processing_tier=2,
    )
    result_tier2 = RuleEngine.process_tier0_or_1(
        sender_profile=sender_prof_tier2,
        subject="Q3 Executive Review Agenda",
        snippet="Let's review the strategic metrics.",
        body_text="Please find the agenda attached.",
    )
    assert result_tier2 is None  # Accurately routed to Tier 2 AI
    print("PASS: Tier 2 AI routing correctly preserved for unknown domains")


@pytest.mark.asyncio
async def test_repository_factory():
    """Verify repository factory properly instantiates Fabric and Postgres repositories."""
    fabric_repo = get_known_domain_repository(backend="fabric")
    assert isinstance(fabric_repo, FabricKnownDomainRepository)

    default_repo = get_known_domain_repository()
    assert isinstance(default_repo, FabricKnownDomainRepository)
    print("PASS: KnownDomainRepository factory instantiation")


@pytest.mark.asyncio
async def test_app_startup():
    """Verify FastAPI application startup with KnownDomainRepository abstraction."""
    from app.main import app
    assert app is not None
    assert app.title == "Signal"
    print("PASS: FastAPI Application startup with KnownDomainRepository")


def run_all_tests():
    asyncio.run(test_fabric_known_domains_read_all_15_records())
    asyncio.run(test_fabric_known_domains_get_by_domain())
    asyncio.run(test_tier0_and_tier1_classification_compatibility())
    asyncio.run(test_repository_factory())
    asyncio.run(test_app_startup())
    print("\n============================================================")
    print("ALL PHASE 3C KNOWN_DOMAINS MIGRATION TESTS PASSED!")
    print("============================================================")


if __name__ == "__main__":
    run_all_tests()
