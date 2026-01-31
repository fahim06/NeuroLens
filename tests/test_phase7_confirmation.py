"""
Phase 7 Data Pipeline Confirmation Test.

Tests all completion criteria from the Phase 7 reference document:
1. Dataset ingestion works
2. Validation reports generated
3. Dataset versions reproducible
4. Splits deterministic
5. Metadata catalog populated
6. No coupling with API/UI
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

import numpy as np


def create_test_dataset(base_dir: Path, num_samples_per_class: int = 10):
    """Create a synthetic test dataset."""
    classes = ["normal", "tumor"]
    
    for cls in classes:
        cls_dir = base_dir / cls
        cls_dir.mkdir(parents=True, exist_ok=True)
        
        for i in range(num_samples_per_class):
            # Create a small random image
            img = np.random.randint(0, 255, (32, 32, 3), dtype=np.uint8)
            img_path = cls_dir / f"{cls}_{i:04d}.png"
            
            # Save as PNG using TensorFlow
            import tensorflow as tf
            encoded = tf.io.encode_png(img)
            tf.io.write_file(str(img_path), encoded)
    
    return classes


def test_criterion_1_ingestion():
    """CRITERION 1: Dataset ingestion works."""
    print("\n" + "=" * 60)
    print("CRITERION 1: Dataset ingestion works")
    print("=" * 60)
    
    from ml.data.ingestion.sources import LocalSource, SourceConfig, SourceType
    from ml.data.ingestion.loaders import ImageLoader, LoaderConfig, extract_label_from_directory
    from ml.data.ingestion.manifests import ManifestBuilder
    
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir) / "dataset"
        classes = create_test_dataset(base_dir, num_samples_per_class=5)
        
        # Configure source
        config = SourceConfig(
            source_type=SourceType.LOCAL,
            base_path=str(base_dir),
            extensions=(".png",),
        )
        
        with LocalSource(config) as source:
            files = source.get_files()
            stats = source.get_stats()
            
            print(f"   Files found: {len(files)}")
            print(f"   Total size: {stats.total_size_mb:.2f} MB")
            
            # Build manifest
            builder = ManifestBuilder(
                name="test_dataset",
                label_extractor=extract_label_from_directory,
                compute_checksums=True,
            )
            manifest = builder.build_from_source(source)
            
            print(f"   Manifest samples: {manifest.num_samples}")
            print(f"   Manifest classes: {manifest.num_classes}")
            
            # Test image loading
            loader = ImageLoader(LoaderConfig(
                target_size=(64, 64),
                normalize=True,
            ))
            sample = loader.load_single(source, files[0])
            
            print(f"   Image loaded: shape={sample.shape}")
            
            passed = (
                len(files) == 10 and
                manifest.num_samples == 10 and
                manifest.num_classes == 2 and
                sample.is_valid
            )
    
    status = "✓ PASSED" if passed else "✗ FAILED"
    print(f"\n   {status}")
    return passed


def test_criterion_2_validation():
    """CRITERION 2: Validation reports generated."""
    print("\n" + "=" * 60)
    print("CRITERION 2: Validation reports generated")
    print("=" * 60)
    
    from ml.data.validation.checks import (
        DataChecker, LabelCheck, BalanceCheck, CorruptionCheck
    )
    from ml.data.validation.reports import ReportGenerator
    
    # Create test data
    labels = {
        "img_001.png": "normal",
        "img_002.png": "normal",
        "img_003.png": "normal",
        "img_004.png": "tumor",
        "img_005.png": "tumor",
    }
    
    # Configure checks
    checker = DataChecker([
        LabelCheck(allowed_labels={"normal", "tumor"}),
        BalanceCheck(min_ratio=0.3),
    ])
    
    # Run checks
    results = checker.run_all(labels)
    
    print(f"   Checks run: {len(results)}")
    for r in results:
        print(f"   - {r.check_name}: {'PASS' if r.passed else 'FAIL'}")
    
    # Generate report
    generator = ReportGenerator(
        dataset_name="test_dataset",
        total_samples=5,
    )
    report = generator.generate(results)
    
    print(f"\n   Report generated: {report.name}")
    print(f"   Overall status: {'PASSED' if report.passed else 'FAILED'}")
    print(f"   Success rate: {report.success_rate:.1f}%")
    
    # Test report formats
    text_report = report.to_text()
    md_report = report.to_markdown()
    dict_report = report.to_dict()
    
    print(f"   Text format: {len(text_report)} chars")
    print(f"   Markdown format: {len(md_report)} chars")
    print(f"   Dict format: {len(dict_report)} keys")
    
    passed = (
        len(results) == 2 and
        report is not None and
        len(text_report) > 0 and
        len(md_report) > 0
    )
    
    status = "✓ PASSED" if passed else "✗ FAILED"
    print(f"\n   {status}")
    return passed


def test_criterion_3_versioning():
    """CRITERION 3: Dataset versions reproducible."""
    print("\n" + "=" * 60)
    print("CRITERION 3: Dataset versions reproducible")
    print("=" * 60)
    
    from ml.data.versioning.hashing import DatasetHasher, HashConfig
    
    # Create hasher
    hasher = DatasetHasher(HashConfig(algorithm="sha256"))
    
    # Test string hashing reproducibility
    test_data = "test content for hashing"
    hash1 = hasher.hash_string(test_data)
    hash2 = hasher.hash_string(test_data)
    
    print(f"   Hash 1: {hash1[:32]}...")
    print(f"   Hash 2: {hash2[:32]}...")
    print(f"   Hashes match: {hash1 == hash2}")
    
    # Test dict hashing
    config1 = {"size": 224, "normalize": True}
    config2 = {"normalize": True, "size": 224}  # Different order
    
    hash_cfg1 = hasher.hash_dict(config1)
    hash_cfg2 = hasher.hash_dict(config2)
    
    print(f"\n   Config hash 1: {hash_cfg1[:32]}...")
    print(f"   Config hash 2: {hash_cfg2[:32]}...")
    print(f"   Config hashes match: {hash_cfg1 == hash_cfg2}")
    
    # Test label hashing
    labels = {"a.png": "normal", "b.png": "tumor"}
    label_hash1 = hasher.hash_labels(labels)
    label_hash2 = hasher.hash_labels(labels)
    
    print(f"\n   Label hash match: {label_hash1 == label_hash2}")
    
    passed = (
        hash1 == hash2 and
        hash_cfg1 == hash_cfg2 and  # Sorted keys should produce same hash
        label_hash1 == label_hash2
    )
    
    status = "✓ PASSED" if passed else "✗ FAILED"
    print(f"\n   {status}")
    return passed


def test_criterion_4_splits():
    """CRITERION 4: Splits deterministic."""
    print("\n" + "=" * 60)
    print("CRITERION 4: Splits deterministic")
    print("=" * 60)
    
    from ml.data.splits.stratified import StratifiedSplitter, verify_split_reproducibility
    
    # Create test samples
    samples = []
    for i in range(50):
        label = "normal" if i % 2 == 0 else "tumor"
        samples.append((f"img_{i:04d}.png", label))
    
    # Test reproducibility
    splitter = StratifiedSplitter(
        train_ratio=0.7,
        val_ratio=0.15,
        test_ratio=0.15,
        seed=42,
    )
    
    result1 = splitter.split(samples)
    result2 = splitter.split(samples)
    
    print(f"   Split 1: train={result1.num_train}, val={result1.num_val}, test={result1.num_test}")
    print(f"   Split 2: train={result2.num_train}, val={result2.num_val}, test={result2.num_test}")
    
    train_match = result1.train_indices == result2.train_indices
    val_match = result1.val_indices == result2.val_indices
    test_match = result1.test_indices == result2.test_indices
    
    print(f"\n   Train indices match: {train_match}")
    print(f"   Val indices match: {val_match}")
    print(f"   Test indices match: {test_match}")
    
    # Verify no leakage
    no_leakage = result1.verify_no_leakage()
    print(f"   No data leakage: {no_leakage}")
    
    # Check class distribution preserved
    train_dist = result1.get_class_distribution("train")
    print(f"\n   Train distribution: {train_dist}")
    
    passed = (
        train_match and
        val_match and
        test_match and
        no_leakage
    )
    
    status = "✓ PASSED" if passed else "✗ FAILED"
    print(f"\n   {status}")
    return passed


def test_criterion_5_catalog():
    """CRITERION 5: Metadata catalog populated."""
    print("\n" + "=" * 60)
    print("CRITERION 5: Metadata catalog populated")
    print("=" * 60)
    
    from ml.data.metadata.catalog import (
        DataCatalog, DatasetMetadata, DatasetType, DatasetStatus
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        catalog_path = Path(tmpdir) / "catalog.json"
        
        # Initialize catalog
        catalog = DataCatalog(catalog_path)
        
        # Create metadata
        metadata1 = DatasetMetadata(
            name="brain_mri_v1",
            version="1.0.0",
            description="Brain MRI classification dataset",
            dataset_type=DatasetType.TRAINING,
            status=DatasetStatus.ACTIVE,
            num_samples=1000,
            num_classes=2,
            class_names=["normal", "tumor"],
            class_distribution={"normal": 600, "tumor": 400},
            tags=["mri", "brain", "production"],
        )
        
        metadata2 = DatasetMetadata(
            name="brain_mri_v2",
            version="2.0.0",
            description="Updated Brain MRI dataset",
            dataset_type=DatasetType.TRAINING,
            status=DatasetStatus.DRAFT,
            num_samples=1500,
            num_classes=2,
            tags=["mri", "brain"],
        )
        
        # Register entries
        entry1 = catalog.register(metadata1)
        entry2 = catalog.register(metadata2, parent_entry_id=entry1.entry_id)
        
        print(f"   Registered entry 1: {entry1.entry_id}")
        print(f"   Registered entry 2: {entry2.entry_id}")
        
        # Test search
        active_entries = catalog.search(status=DatasetStatus.ACTIVE)
        tagged_entries = catalog.search(tags=["production"])
        
        print(f"\n   Active entries: {len(active_entries)}")
        print(f"   Production tagged: {len(tagged_entries)}")
        
        # Test lineage
        lineage = catalog.get_lineage(entry2.entry_id)
        print(f"   Entry 2 lineage depth: {len(lineage)}")
        
        # Test stats
        stats = catalog.stats
        print(f"\n   Catalog stats:")
        print(f"   - Total entries: {stats['total_entries']}")
        print(f"   - By status: {stats['by_status']}")
        
        passed = (
            len(active_entries) == 1 and
            len(tagged_entries) == 1 and
            len(lineage) == 1 and
            stats['total_entries'] == 2
        )
    
    status = "✓ PASSED" if passed else "✗ FAILED"
    print(f"\n   {status}")
    return passed


def test_criterion_6_no_coupling():
    """CRITERION 6: No coupling with API/UI."""
    print("\n" + "=" * 60)
    print("CRITERION 6: No coupling with API/UI")
    print("=" * 60)
    
    import importlib
    import ast
    
    # List of modules to check
    modules_to_check = [
        "ml.data.ingestion.sources",
        "ml.data.ingestion.loaders",
        "ml.data.ingestion.manifests",
        "ml.data.validation.schema",
        "ml.data.validation.checks",
        "ml.data.validation.reports",
        "ml.data.versioning.hashing",
        "ml.data.versioning.snapshots",
        "ml.data.versioning.registry",
        "ml.data.splits.stratified",
        "ml.data.splits.policies",
        "ml.data.drift.detectors",
        "ml.data.metadata.catalog",
    ]
    
    # Forbidden imports (API/UI dependencies)
    forbidden_patterns = [
        "fastapi", "flask", "django",
        "react", "vue", "angular",
        "starlette", "uvicorn",
        "jinja", "templates",
    ]
    
    issues = []
    checked = 0
    
    for module_name in modules_to_check:
        try:
            module = importlib.import_module(module_name)
            module_file = module.__file__
            
            if module_file:
                with open(module_file, "r") as f:
                    content = f.read()
                
                # Check for forbidden imports
                for pattern in forbidden_patterns:
                    if pattern in content.lower():
                        issues.append(f"{module_name}: contains '{pattern}'")
                
                checked += 1
        except Exception as e:
            issues.append(f"{module_name}: failed to load - {e}")
    
    print(f"   Modules checked: {checked}/{len(modules_to_check)}")
    print(f"   Coupling issues: {len(issues)}")
    
    if issues:
        for issue in issues[:5]:
            print(f"   - {issue}")
    else:
        print("   - No API/UI coupling detected")
    
    # Verify pure data types (no HTTP dependencies)
    from ml.data.ingestion.manifests import Manifest
    from ml.data.validation.reports import ValidationReport
    from ml.data.splits.stratified import SplitResult
    from ml.data.drift.detectors import DriftReport
    
    data_types = [Manifest, ValidationReport, SplitResult, DriftReport]
    
    print(f"\n   Pure data types verified: {len(data_types)}")
    for dt in data_types:
        print(f"   - {dt.__name__}: has to_dict()={hasattr(dt, 'to_dict')}")
    
    passed = len(issues) == 0 and checked == len(modules_to_check)
    
    status = "✓ PASSED" if passed else "✗ FAILED"
    print(f"\n   {status}")
    return passed


def main():
    """Run all confirmation tests."""
    print("\n" + "=" * 60)
    print("PHASE 7: DATA PIPELINE CONFIRMATION TEST")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    results = {
        "Dataset ingestion works": test_criterion_1_ingestion(),
        "Validation reports generated": test_criterion_2_validation(),
        "Dataset versions reproducible": test_criterion_3_versioning(),
        "Splits deterministic": test_criterion_4_splits(),
        "Metadata catalog populated": test_criterion_5_catalog(),
        "No API/UI coupling": test_criterion_6_no_coupling(),
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
        print(f"\nPHASE 7: ALL CRITERIA PASSED ✓ ({passed_count}/{total_count})")
    else:
        print(f"\nPHASE 7: SOME CRITERIA FAILED ({passed_count}/{total_count})")
    
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
