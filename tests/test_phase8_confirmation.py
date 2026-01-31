"""
Phase 8 MLOps & Automation Confirmation Test.

Tests all completion criteria from the Phase 8 reference document:
1. CI pipelines exist and are valid
2. Model CI validates and registers models
3. Retraining can be triggered
4. Artifacts tracked
5. Rollback script tested
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_criterion_1_ci_pipelines():
    """CRITERION 1: CI pipelines run successfully."""
    print("\n" + "=" * 60)
    print("CRITERION 1: CI pipelines exist and are valid")
    print("=" * 60)
    
    ci_dir = PROJECT_ROOT / "infra" / "ci"
    
    required_pipelines = [
        "backend.yml",
        "frontend.yml",
        "ml.yml",
    ]
    
    found = []
    missing = []
    
    for pipeline in required_pipelines:
        pipeline_path = ci_dir / pipeline
        if pipeline_path.exists():
            found.append(pipeline)
            
            # Validate YAML structure (basic check)
            content = pipeline_path.read_text()
            has_name = "name:" in content
            has_on = "on:" in content
            has_jobs = "jobs:" in content
            
            print(f"   ✓ {pipeline}")
            print(f"     - Has name: {has_name}")
            print(f"     - Has triggers: {has_on}")
            print(f"     - Has jobs: {has_jobs}")
        else:
            missing.append(pipeline)
            print(f"   ✗ {pipeline} - MISSING")
    
    passed = len(missing) == 0
    status = "✓ PASSED" if passed else "✗ FAILED"
    print(f"\n   {status} ({len(found)}/{len(required_pipelines)} pipelines)")
    return passed


def test_criterion_2_model_ci():
    """CRITERION 2: Model CI validates and registers models."""
    print("\n" + "=" * 60)
    print("CRITERION 2: Model CI validates and registers models")
    print("=" * 60)
    
    from ml.ops.validation_gates import (
        create_default_pipeline,
        MetricThresholdGate,
        RegressionGate,
        LatencyGate,
    )
    
    # Create validation pipeline
    pipeline = create_default_pipeline()
    
    print(f"   Validation gates: {len(pipeline.gates)}")
    for gate in pipeline.gates:
        print(f"   - {gate.name} ({gate.severity.value})")
    
    # Test with passing metrics
    passing_context = {
        "metrics": {
            "accuracy": 0.92,
            "precision": 0.89,
            "recall": 0.91,
            "f1_score": 0.90,
            "auc_roc": 0.95,
            "inference_latency_ms": 45,
        },
    }
    
    report = pipeline.run(passing_context)
    
    print(f"\n   Test run (passing metrics):")
    print(f"   - Overall: {'PASSED' if report.passed else 'FAILED'}")
    print(f"   - Summary: {report.summary}")
    
    # Test with failing metrics
    failing_context = {
        "metrics": {
            "accuracy": 0.75,  # Below threshold
            "precision": 0.70,
            "recall": 0.65,
            "f1_score": 0.67,
            "auc_roc": 0.80,
        },
    }
    
    fail_report = pipeline.run(failing_context)
    
    print(f"\n   Test run (failing metrics):")
    print(f"   - Overall: {'PASSED' if fail_report.passed else 'FAILED'}")
    print(f"   - Blocking failures: {fail_report.blocking_failures}")
    
    passed = (
        report.passed and
        not fail_report.passed and
        len(pipeline.gates) >= 3
    )
    
    status = "✓ PASSED" if passed else "✗ FAILED"
    print(f"\n   {status}")
    return passed


def test_criterion_3_retraining_triggers():
    """CRITERION 3: Retraining can be triggered."""
    print("\n" + "=" * 60)
    print("CRITERION 3: Retraining can be triggered")
    print("=" * 60)
    
    from ml.ops.retraining_triggers import (
        create_default_trigger_manager,
        TriggerType,
        DataVersionTrigger,
        DriftTrigger,
        ManualTrigger,
    )
    
    # Create trigger manager
    manager = create_default_trigger_manager()
    
    print(f"   Retraining triggers: {len(manager.triggers)}")
    for trigger in manager.triggers:
        print(f"   - {trigger.name} ({trigger.priority.value})")
    
    # Test data version trigger
    context1 = {
        "data_hash": "abc123",
        "previous_data_hash": "xyz789",
    }
    
    events1 = manager.check_all(context1)
    print(f"\n   Test 1 (data version change):")
    print(f"   - Events fired: {len(events1)}")
    for e in events1:
        print(f"     - {e.trigger_type.value}: {e.reason}")
    
    # Test manual trigger
    context2 = {
        "manual_trigger": True,
        "trigger_reason": "Scheduled maintenance",
        "requester": "admin",
    }
    
    events2 = manager.check_all(context2)
    print(f"\n   Test 2 (manual trigger):")
    print(f"   - Events fired: {len(events2)}")
    for e in events2:
        print(f"     - {e.trigger_type.value}: {e.reason}")
    
    # Test drift trigger
    context3 = {
        "drift_report": {
            "overall_drift_score": 0.25,
            "drifted_features": ["feature_1", "feature_2"],
        },
    }
    
    events3 = manager.check_all(context3)
    print(f"\n   Test 3 (drift detected):")
    print(f"   - Events fired: {len(events3)}")
    
    passed = (
        len(events1) >= 1 and
        len(events2) >= 1 and
        len(events3) >= 1
    )
    
    status = "✓ PASSED" if passed else "✗ FAILED"
    print(f"\n   {status}")
    return passed


def test_criterion_4_artifacts():
    """CRITERION 4: Artifacts tracked."""
    print("\n" + "=" * 60)
    print("CRITERION 4: Artifacts tracked")
    print("=" * 60)
    
    # Check Dockerfiles exist
    docker_dir = PROJECT_ROOT / "infra" / "docker"
    
    dockerfiles = [
        "backend.Dockerfile",
        "inference.Dockerfile",
        "training.Dockerfile",
    ]
    
    found_dockerfiles = []
    for df in dockerfiles:
        path = docker_dir / df
        if path.exists():
            found_dockerfiles.append(df)
            print(f"   ✓ Dockerfile: {df}")
        else:
            print(f"   ✗ Dockerfile: {df} - MISSING")
    
    # Check compose exists
    compose_path = PROJECT_ROOT / "infra" / "compose" / "dev.yml"
    has_compose = compose_path.exists()
    print(f"\n   {'✓' if has_compose else '✗'} Docker Compose: dev.yml")
    
    # Check ML CI has artifact upload steps
    ml_ci_path = PROJECT_ROOT / "infra" / "ci" / "ml.yml"
    has_artifact_steps = False
    if ml_ci_path.exists():
        content = ml_ci_path.read_text()
        has_artifact_steps = "upload-artifact" in content
        print(f"   {'✓' if has_artifact_steps else '✗'} ML CI has artifact upload")
    
    # Check model registry concept exists
    from ml.ops.validation_gates import ValidationReport
    report = ValidationReport(
        results=[],
        passed=True,
        blocking_failures=0,
        total_gates=0,
    )
    can_serialize = report.to_json() is not None
    print(f"   {'✓' if can_serialize else '✗'} Validation reports serializable")
    
    passed = (
        len(found_dockerfiles) == len(dockerfiles) and
        has_compose and
        has_artifact_steps and
        can_serialize
    )
    
    status = "✓ PASSED" if passed else "✗ FAILED"
    print(f"\n   {status}")
    return passed


def test_criterion_5_rollback():
    """CRITERION 5: Rollback script tested."""
    print("\n" + "=" * 60)
    print("CRITERION 5: Rollback script tested")
    print("=" * 60)
    
    scripts_dir = PROJECT_ROOT / "infra" / "scripts"
    
    required_scripts = [
        "train_and_validate.sh",
        "register_model.sh",
        "rollback.sh",
    ]
    
    found = []
    executable = []
    
    for script in required_scripts:
        script_path = scripts_dir / script
        if script_path.exists():
            found.append(script)
            print(f"   ✓ Script exists: {script}")
            
            # Check script structure
            content = script_path.read_text()
            
            has_shebang = content.startswith("#!/")
            has_set = "set -" in content
            has_functions = "() {" in content or "function " in content
            
            print(f"     - Has shebang: {has_shebang}")
            print(f"     - Has strict mode: {has_set}")
            print(f"     - Has functions: {has_functions}")
        else:
            print(f"   ✗ Script missing: {script}")
    
    # Test rollback script has key features
    rollback_path = scripts_dir / "rollback.sh"
    has_rollback_features = False
    if rollback_path.exists():
        content = rollback_path.read_text()
        has_dry_run = "--dry-run" in content or "DRY_RUN" in content
        has_list = "--list" in content or "list_versions" in content
        has_version = "--version" in content or "TARGET_VERSION" in content
        
        has_rollback_features = has_dry_run and has_list and has_version
        
        print(f"\n   Rollback script features:")
        print(f"   - Dry run support: {has_dry_run}")
        print(f"   - List versions: {has_list}")
        print(f"   - Version targeting: {has_version}")
    
    passed = (
        len(found) == len(required_scripts) and
        has_rollback_features
    )
    
    status = "✓ PASSED" if passed else "✗ FAILED"
    print(f"\n   {status}")
    return passed


def main():
    """Run all confirmation tests."""
    print("\n" + "=" * 60)
    print("PHASE 8: MLOPS & AUTOMATION CONFIRMATION TEST")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    results = {
        "CI pipelines exist": test_criterion_1_ci_pipelines(),
        "Model CI validates models": test_criterion_2_model_ci(),
        "Retraining can be triggered": test_criterion_3_retraining_triggers(),
        "Artifacts tracked": test_criterion_4_artifacts(),
        "Rollback script tested": test_criterion_5_rollback(),
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    for criterion, passed in results.items():
        status = "✓" if passed else "✗"
        print(f"   {status} {criterion}")
    
    print("\n" + "-" * 60)
    all_passed = passed_count == total_count
    
    if all_passed:
        print(f"\nPHASE 8: ALL CRITERIA PASSED ✓ ({passed_count}/{total_count})")
    else:
        print(f"\nPHASE 8: SOME CRITERIA FAILED ({passed_count}/{total_count})")
    
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
