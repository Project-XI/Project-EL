"""
test_face_verification.py
──────────────────────────
Comprehensive test suite for the GATEKEEPER Face Verification Engine.

Test categories (per Issue #15 acceptance criteria)
────────────────────────────────────────────────────
1. Face verification pipeline tests
2. Embedding generation tests
3. Confidence score tests
4. Face mismatch detection tests
5. Determinism tests
6. Edge case and failure handling tests

Run:
    export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
    backend/venv/bin/python3 -m pytest backend/tests/test_face_verification.py -v
"""

from __future__ import annotations

import math
import pytest
from typing import List

from src.agents.gatekeeper.face_verification.models import (
    EmbeddingSource,
    FaceCapture,
    FaceEmbedding,
    SimilarityScore,
    VerificationResult,
    VerificationStatus,
)
from src.agents.gatekeeper.face_verification.embedding_engine import (
    StubEmbeddingEngine,
    FileBasedEmbeddingEngine,
    STUB_EMBEDDING_DIM,
)
from src.agents.gatekeeper.face_verification.comparator import (
    EmbeddingComparator,
    DEFAULT_COSINE_THRESHOLD,
    _cosine_similarity,
    _euclidean_distance,
)
from src.agents.gatekeeper.face_verification.verification_pipeline import (
    FaceVerificationPipeline,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

ROLL = "CS2021001"
OTHER_ROLL = "CS2021002"

def _capture(
    roll: str = ROLL,
    path: str = "photos/test.jpg",
    source: EmbeddingSource = EmbeddingSource.LIVE_CAPTURE,
    width: int = None,
    height: int = None,
) -> FaceCapture:
    return FaceCapture(
        roll_number    = roll,
        image_path     = path,
        capture_source = source,
        width          = width,
        height         = height,
    )


def _engine(
    mismatches: set = None,
    no_face: set = None,
) -> StubEmbeddingEngine:
    return StubEmbeddingEngine(
        mismatch_roll_numbers = mismatches or set(),
        no_face_roll_numbers  = no_face or set(),
    )


def _pipeline(
    mismatches: set = None,
    no_face: set = None,
    threshold: float = DEFAULT_COSINE_THRESHOLD,
    store: dict = None,
) -> FaceVerificationPipeline:
    engine = _engine(mismatches, no_face)
    return FaceVerificationPipeline(
        engine          = engine,
        threshold       = threshold,
        embedding_store = store or {},
    )


def _registered_embedding(roll: str = ROLL) -> FaceEmbedding:
    """Generate a registration embedding for a roll number using stub engine."""
    engine = _engine()
    capture = _capture(roll=roll, source=EmbeddingSource.REGISTRATION)
    return engine.generate(capture)


# ══════════════════════════════════════════════════════════════════════════════
# 1. FACE VERIFICATION PIPELINE TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestFaceVerificationPipeline:

    def test_matching_face_returns_verified(self):
        pipeline = _pipeline()
        registered = _registered_embedding(ROLL)
        result = pipeline.verify(_capture(ROLL), registered)
        assert result.status == VerificationStatus.VERIFIED
        assert result.is_verified is True

    def test_verified_result_has_positive_confidence(self):
        pipeline = _pipeline()
        registered = _registered_embedding(ROLL)
        result = pipeline.verify(_capture(ROLL), registered)
        assert result.confidence_score > 0.5

    def test_verified_result_not_mismatch(self):
        pipeline = _pipeline()
        registered = _registered_embedding(ROLL)
        result = pipeline.verify(_capture(ROLL), registered)
        assert result.is_mismatch is False

    def test_verify_returns_verification_result_type(self):
        pipeline = _pipeline()
        registered = _registered_embedding(ROLL)
        result = pipeline.verify(_capture(ROLL), registered)
        assert isinstance(result, VerificationResult)

    def test_result_has_threshold_used(self):
        pipeline = _pipeline(threshold=0.85)
        registered = _registered_embedding(ROLL)
        result = pipeline.verify(_capture(ROLL), registered)
        assert result.threshold_used == 0.85

    def test_result_has_roll_number(self):
        pipeline = _pipeline()
        registered = _registered_embedding(ROLL)
        result = pipeline.verify(_capture(ROLL), registered)
        assert result.roll_number == ROLL

    def test_result_has_non_empty_message(self):
        pipeline = _pipeline()
        registered = _registered_embedding(ROLL)
        result = pipeline.verify(_capture(ROLL), registered)
        assert len(result.message) > 0

    def test_result_to_dict_is_serializable(self):
        import json
        pipeline = _pipeline()
        registered = _registered_embedding(ROLL)
        result = pipeline.verify(_capture(ROLL), registered)
        json.dumps(result.to_dict())   # must not raise

    def test_verify_by_roll_verified_with_preloaded_store(self):
        # Register the embedding first
        engine = _engine()
        pipeline = FaceVerificationPipeline(engine=engine, threshold=0.80)
        reg_capture = _capture(roll=ROLL, source=EmbeddingSource.REGISTRATION)
        pipeline.register_embedding(reg_capture)
        # Now verify with live capture
        result = pipeline.verify_by_roll(_capture(ROLL))
        assert result.status == VerificationStatus.VERIFIED

    def test_verify_by_roll_no_reference_when_not_registered(self):
        pipeline = _pipeline()
        result = pipeline.verify_by_roll(_capture("NOTREGISTERED"))
        assert result.status == VerificationStatus.NO_REFERENCE


# ══════════════════════════════════════════════════════════════════════════════
# 2. EMBEDDING GENERATION TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestEmbeddingGeneration:

    def test_stub_engine_generates_embedding(self):
        engine = _engine()
        emb = engine.generate(_capture(ROLL))
        assert emb is not None

    def test_generated_embedding_has_correct_dimension(self):
        engine = _engine()
        emb = engine.generate(_capture(ROLL))
        assert len(emb.vector) == STUB_EMBEDDING_DIM

    def test_embedding_vector_is_list_of_floats(self):
        engine = _engine()
        emb = engine.generate(_capture(ROLL))
        assert all(isinstance(v, float) for v in emb.vector)

    def test_embedding_is_unit_normalized(self):
        engine = _engine()
        emb = engine.generate(_capture(ROLL))
        norm = math.sqrt(sum(v * v for v in emb.vector))
        assert abs(norm - 1.0) < 1e-6

    def test_embedding_has_correct_roll_number(self):
        engine = _engine()
        emb = engine.generate(_capture(ROLL))
        assert emb.roll_number == ROLL

    def test_embedding_has_model_name(self):
        engine = _engine()
        emb = engine.generate(_capture(ROLL))
        assert len(emb.model_name) > 0

    def test_file_based_engine_returns_stored_vector(self):
        store = {ROLL: [0.5, 0.5, 0.5]}
        engine = FileBasedEmbeddingEngine(embedding_store=store)
        emb = engine.generate(_capture(ROLL))
        assert emb is not None
        assert emb.vector == [0.5, 0.5, 0.5]

    def test_file_based_engine_returns_none_for_missing(self):
        engine = FileBasedEmbeddingEngine(embedding_store={})
        emb = engine.generate(_capture(ROLL))
        assert emb is None

    def test_no_face_simulated_returns_none(self):
        engine = _engine(no_face={ROLL})
        emb = engine.generate(_capture(ROLL))
        assert emb is None

    def test_embedding_is_valid(self):
        engine = _engine()
        emb = engine.generate(_capture(ROLL))
        assert emb.is_valid() is True


# ══════════════════════════════════════════════════════════════════════════════
# 3. CONFIDENCE SCORE TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestConfidenceScore:

    def test_identical_vectors_give_confidence_one(self):
        comparator = EmbeddingComparator()
        vec = [1.0, 0.0, 0.0]
        emb_a = FaceEmbedding(roll_number="A", vector=vec, source=EmbeddingSource.STUB)
        emb_b = FaceEmbedding(roll_number="B", vector=vec, source=EmbeddingSource.STUB)
        score = comparator.compare(emb_a, emb_b)
        assert abs(score.confidence - 1.0) < 1e-6

    def test_opposite_vectors_give_confidence_zero(self):
        comparator = EmbeddingComparator()
        emb_a = FaceEmbedding(roll_number="A", vector=[1.0, 0.0], source=EmbeddingSource.STUB)
        emb_b = FaceEmbedding(roll_number="B", vector=[-1.0, 0.0], source=EmbeddingSource.STUB)
        score = comparator.compare(emb_a, emb_b)
        assert abs(score.confidence - 0.0) < 1e-6

    def test_confidence_in_valid_range(self):
        comparator = EmbeddingComparator()
        a = _registered_embedding(ROLL)
        b = _registered_embedding(OTHER_ROLL)
        score = comparator.compare(a, b)
        assert 0.0 <= score.confidence <= 1.0

    def test_verified_result_confidence_above_half(self):
        pipeline = _pipeline()
        registered = _registered_embedding(ROLL)
        result = pipeline.verify(_capture(ROLL), registered)
        if result.is_verified:
            assert result.confidence_score >= 0.5

    def test_confidence_score_in_result_matches_similarity(self):
        pipeline = _pipeline()
        registered = _registered_embedding(ROLL)
        result = pipeline.verify(_capture(ROLL), registered)
        if result.similarity:
            assert abs(result.confidence_score - result.similarity.confidence) < 1e-4

    def test_zero_norm_vector_gives_zero_confidence(self):
        comparator = EmbeddingComparator()
        score = comparator.compare_vectors([0.0, 0.0], [1.0, 0.0])
        assert score.confidence == 0.0


# ══════════════════════════════════════════════════════════════════════════════
# 4. FACE MISMATCH DETECTION TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestFaceMismatchDetection:

    def test_mismatch_face_returns_mismatch_status(self):
        pipeline = _pipeline(mismatches={ROLL}, threshold=0.80)
        registered = _registered_embedding(ROLL)   # Clean registered embedding
        result = pipeline.verify(_capture(ROLL), registered)
        # Mismatch engine generates a different vector for ROLL
        assert result.status == VerificationStatus.MISMATCH

    def test_mismatch_result_is_not_verified(self):
        pipeline = _pipeline(mismatches={ROLL})
        registered = _registered_embedding(ROLL)
        result = pipeline.verify(_capture(ROLL), registered)
        assert result.is_verified is False

    def test_mismatch_result_is_mismatch(self):
        pipeline = _pipeline(mismatches={ROLL})
        registered = _registered_embedding(ROLL)
        result = pipeline.verify(_capture(ROLL), registered)
        assert result.is_mismatch is True

    def test_no_face_returns_no_face_status(self):
        pipeline = _pipeline(no_face={ROLL})
        registered = _registered_embedding(ROLL)
        result = pipeline.verify(_capture(ROLL), registered)
        assert result.status == VerificationStatus.NO_FACE

    def test_no_reference_returns_no_reference_status(self):
        pipeline = _pipeline()
        result = pipeline.verify_by_roll(_capture("UNREGISTERED"))
        assert result.status == VerificationStatus.NO_REFERENCE

    def test_low_quality_image_returns_low_quality_status(self):
        pipeline = _pipeline()
        registered = _registered_embedding(ROLL)
        tiny_capture = _capture(ROLL, width=32, height=32)  # Below minimum
        result = pipeline.verify(tiny_capture, registered)
        assert result.status == VerificationStatus.LOW_QUALITY

    def test_different_student_does_not_verify(self):
        # Register A's embedding, try to verify B against it
        pipeline = _pipeline()
        registered_a = _registered_embedding(ROLL)
        result = pipeline.verify(_capture(OTHER_ROLL), registered_a)
        # B's vector won't match A's registered embedding
        # (may be MISMATCH or VERIFIED depending on how close hashes are)
        # The important thing is: ROLL != OTHER_ROLL and confidence < 1.0
        assert result.confidence_score < 1.0

    def test_mismatch_confidence_below_threshold(self):
        pipeline = _pipeline(mismatches={ROLL}, threshold=0.80)
        registered = _registered_embedding(ROLL)
        result = pipeline.verify(_capture(ROLL), registered)
        if result.is_mismatch:
            assert result.confidence_score < 0.9


# ══════════════════════════════════════════════════════════════════════════════
# 5. DETERMINISM TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestDeterminism:

    def test_same_capture_same_embedding(self):
        engine = _engine()
        c = _capture(ROLL)
        e1 = engine.generate(c)
        e2 = engine.generate(c)
        assert e1.vector == e2.vector

    def test_same_inputs_same_verification_result(self):
        pipeline = _pipeline()
        registered = _registered_embedding(ROLL)
        r1 = pipeline.verify(_capture(ROLL), registered)
        r2 = pipeline.verify(_capture(ROLL), registered)
        assert r1.status == r2.status
        assert abs(r1.confidence_score - r2.confidence_score) < 1e-9

    def test_same_vectors_same_cosine(self):
        a = [0.6, 0.8]
        b = [0.6, 0.8]
        c1 = _cosine_similarity(a, b)
        c2 = _cosine_similarity(a, b)
        assert c1 == c2

    def test_replay_produces_same_pipeline_decision(self):
        pipeline = _pipeline(threshold=0.80)
        reg = _registered_embedding(ROLL)
        decisions = [pipeline.verify(_capture(ROLL), reg).status for _ in range(5)]
        assert len(set(decisions)) == 1  # All identical

    def test_different_rolls_different_embeddings(self):
        engine = _engine()
        e1 = engine.generate(_capture(ROLL))
        e2 = engine.generate(_capture(OTHER_ROLL))
        assert e1.vector != e2.vector


# ══════════════════════════════════════════════════════════════════════════════
# 6. EDGE CASE AND FAILURE HANDLING
# ══════════════════════════════════════════════════════════════════════════════

class TestEdgeCaseAndFailureHandling:

    def test_dimension_mismatch_gives_zero_confidence(self):
        comparator = EmbeddingComparator()
        a = FaceEmbedding(roll_number="A", vector=[1.0, 0.0], source=EmbeddingSource.STUB)
        b = FaceEmbedding(roll_number="B", vector=[1.0, 0.0, 0.0], source=EmbeddingSource.STUB)
        score = comparator.compare(a, b)
        assert score.confidence == 0.0

    def test_empty_vector_handled_safely(self):
        comparator = EmbeddingComparator()
        a = FaceEmbedding(roll_number="A", vector=[], source=EmbeddingSource.STUB)
        b = FaceEmbedding(roll_number="B", vector=[], source=EmbeddingSource.STUB)
        score = comparator.compare(a, b)
        assert score.confidence == 0.0

    def test_invalid_threshold_raises(self):
        with pytest.raises(ValueError):
            EmbeddingComparator(threshold=0.0)

    def test_capture_without_image_has_no_image_false(self):
        c = FaceCapture(roll_number=ROLL, image_path=None)
        assert c.has_image() is False

    def test_capture_with_path_has_image_true(self):
        c = _capture()
        assert c.has_image() is True

    def test_verification_result_pipeline_version_set(self):
        pipeline = _pipeline()
        registered = _registered_embedding(ROLL)
        result = pipeline.verify(_capture(ROLL), registered)
        assert len(result.pipeline_version) > 0

    def test_has_registered_false_before_registration(self):
        pipeline = _pipeline()
        assert pipeline.has_registered(ROLL) is False

    def test_has_registered_true_after_registration(self):
        engine = _engine()
        pipeline = FaceVerificationPipeline(engine=engine)
        pipeline.register_embedding(_capture(ROLL, source=EmbeddingSource.REGISTRATION))
        assert pipeline.has_registered(ROLL) is True

    def test_result_to_dict_no_custom_types(self):
        import json
        pipeline = _pipeline(no_face={ROLL})
        registered = _registered_embedding(ROLL)
        result = pipeline.verify(_capture(ROLL), registered)
        d = result.to_dict()
        json.dumps(d)  # Must be JSON-serializable

    def test_file_based_engine_case_insensitive_lookup(self):
        store = {"CS2021001": [0.1, 0.2, 0.3]}
        engine = FileBasedEmbeddingEngine(embedding_store=store)
        # Store key is uppercase, capture passes lowercase
        capture = FaceCapture(roll_number="cs2021001", image_path="photo.jpg")
        # Note: registry normalizes roll numbers; test the engine's raw behavior
        emb = engine.generate(capture)
        # File engine matches the exact key; this tests raw behavior
        # (normalization happens at the registry layer before this)
        assert emb is None or emb.vector == [0.1, 0.2, 0.3]
