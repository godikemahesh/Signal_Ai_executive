"""
Master Migration Test Runner
Executes all migration test suites under a single unified async loop.
"""

import asyncio
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tests.test_fabric_dal import (
    test_fabric_authentication,
    test_fabric_read_known_domains,
    test_fabric_write_upsert_delete_lifecycle,
    test_app_startup_with_fabric_dal,
)
from tests.test_model_serialization import run_all_tests_async as run_phase2_tests_async
from tests.test_phase3_user_profile import (
    test_fabric_user_repository_crud,
    test_repository_factory as test_user_repo_factory,
    test_app_startup as test_user_app_startup,
)
from tests.test_phase3_known_domains import (
    test_fabric_known_domains_read_all_15_records,
    test_fabric_known_domains_get_by_domain,
    test_tier0_and_tier1_classification_compatibility,
    test_repository_factory as test_kd_repo_factory,
    test_app_startup as test_kd_app_startup,
)
from tests.test_phase3_gmail_account import (
    test_credential_encryption_at_rest_property,
    test_fabric_gmail_account_repository_crud_and_security,
    test_repository_factory as test_gmail_repo_factory,
    test_app_startup as test_gmail_app_startup,
)
from tests.test_phase3e_signals import (
    test_signal_lifecycle,
    test_signal_thread_lifecycle,
    test_signal_attachments,
    test_signal_categories,
    test_entity_graph_linkages,
    test_signal_embedding_storage,
)
from tests.test_phase3f_remaining_persistence import (
    test_sender_profile_lifecycle,
    test_behavior_interaction_lifecycle,
    test_ask_signal_history_lifecycle,
    test_gmail_account_list_active_and_poller_wiring,
    test_repository_factories_phase3f,
)


async def main():
    print("=" * 65)
    print("RUNNING ALL SIGNAL FABRIC MIGRATION TEST SUITES (PHASES 1 - 3F)")
    print("=" * 65)

    start_t = time.time()

    print("\n>>> Running [Phase 1: Fabric DAL]...")
    await test_fabric_authentication()
    await test_fabric_read_known_domains()
    await test_fabric_write_upsert_delete_lifecycle()
    await test_app_startup_with_fabric_dal()
    print("[Phase 1: Fabric DAL] PASSED")

    print("\n>>> Running [Phase 2: Serialization]...")
    await run_phase2_tests_async()
    print("[Phase 2: Serialization] PASSED")

    print("\n>>> Running [Phase 3B: UserProfile Repo]...")
    await test_fabric_user_repository_crud()
    await test_user_repo_factory()
    await test_user_app_startup()
    print("[Phase 3B: UserProfile Repo] PASSED")

    print("\n>>> Running [Phase 3C: KnownDomains Repo]...")
    await test_fabric_known_domains_read_all_15_records()
    await test_fabric_known_domains_get_by_domain()
    await test_tier0_and_tier1_classification_compatibility()
    await test_kd_repo_factory()
    await test_kd_app_startup()
    print("[Phase 3C: KnownDomains Repo] PASSED")

    print("\n>>> Running [Phase 3D: GmailAccount Repo & AES-256-GCM Security]...")
    await test_credential_encryption_at_rest_property()
    await test_fabric_gmail_account_repository_crud_and_security()
    await test_gmail_repo_factory()
    await test_gmail_app_startup()
    print("[Phase 3D: GmailAccount Repo & AES-256-GCM Security] PASSED")

    print("\n>>> Running [Phase 3E: Signals Core Domain & Graph Linkages]...")
    await test_signal_lifecycle()
    await test_signal_thread_lifecycle()
    await test_signal_attachments()
    await test_signal_categories()
    await test_entity_graph_linkages()
    await test_signal_embedding_storage()
    print("[Phase 3E: Signals Core Domain & Graph Linkages] PASSED")

    print("\n>>> Running [Phase 3F: Remaining Persistence & Poller Wiring]...")
    await test_sender_profile_lifecycle()
    await test_behavior_interaction_lifecycle()
    await test_ask_signal_history_lifecycle()
    await test_gmail_account_list_active_and_poller_wiring()
    await test_repository_factories_phase3f()
    print("[Phase 3F: Remaining Persistence & Poller Wiring] PASSED")

    duration = time.time() - start_t
    print("\n" + "=" * 65)
    print(f"ALL MIGRATION TEST SUITES (PHASES 1 - 3F) PASSED IN {duration:.2f}s WITH 100% SUCCESS!")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())


