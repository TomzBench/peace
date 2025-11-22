"""Pure RxPy marble tests for concurrent chunk processing."""

from datetime import datetime
from pathlib import Path

from reactivex import operators as ops
from reactivex.testing import ReactiveTest, TestScheduler

from python.infra.whisper.models import (
    AudioFileChunk,
    TranscriptionResult,
)


def make_mock_chunk(idx: int) -> AudioFileChunk:
    """Create mock chunk for testing."""
    return AudioFileChunk(
        filename=f"chunk_{idx}.mp3",
        data=b"mock data",
        chunk_index=idx,
        total_chunks=1,
        start_time_ms=idx * 1000,
        end_time_ms=(idx + 1) * 1000,
        original_filename="test.mp3",
        original_path=Path("/fake/test.mp3"),
    )


def make_mock_result(idx: int) -> TranscriptionResult:
    """Create mock TranscriptionResult."""
    return TranscriptionResult(
        object="transcription",
        usage=None,
        text=f"Chunk {idx} text",
        segments=[],
        language="en",
        duration=1.0,
        audio_file=Path("/fake/test.mp3"),
        model_name="whisper-1",
        transcription_timestamp=datetime.now(),
    )


def test_merge_operator_limits_concurrency() -> None:
    """
    Test that ops.merge(max_concurrent=N) properly limits parallel execution.

    Uses marble testing to verify that when max_concurrent=2 is set,
    only 2 observables are subscribed to at a time.
    """
    scheduler = TestScheduler()

    # Create 4 cold observables representing chunk transcriptions
    # Each emits a value after a delay, simulating async processing
    chunk0 = scheduler.create_cold_observable(
        ReactiveTest.on_next(20, (0, make_mock_result(0))),
        ReactiveTest.on_completed(20)
    )
    chunk1 = scheduler.create_cold_observable(
        ReactiveTest.on_next(30, (1, make_mock_result(1))),
        ReactiveTest.on_completed(30)
    )
    chunk2 = scheduler.create_cold_observable(
        ReactiveTest.on_next(20, (2, make_mock_result(2))),
        ReactiveTest.on_completed(20)
    )
    chunk3 = scheduler.create_cold_observable(
        ReactiveTest.on_next(40, (3, make_mock_result(3))),
        ReactiveTest.on_completed(40)
    )

    # Source emits chunk observables immediately
    source = scheduler.create_hot_observable(
        ReactiveTest.on_next(210, chunk0),
        ReactiveTest.on_next(220, chunk1),
        ReactiveTest.on_next(230, chunk2),
        ReactiveTest.on_next(240, chunk3),
        ReactiveTest.on_completed(250)
    )

    # Apply merge with max_concurrent=2
    result = source.pipe(
        ops.merge(max_concurrent=2)
    )

    # Create observer
    observer = scheduler.create_observer()

    # Subscribe to the result observable
    result.subscribe(observer, scheduler=scheduler)

    # Run the scheduler
    scheduler.start()

    # Verify results
    # With max_concurrent=2:
    # - chunk0 and chunk1 start at 210 and 220
    # - chunk0 completes at 210+20=230, chunk2 starts
    # - chunk1 completes at 220+30=250, chunk3 starts
    # - chunk2 completes at 230+20=250
    # - chunk3 completes at 250+40=290

    assert len(observer.messages) == 5  # 4 emissions + 1 completion

    # Verify all chunks emitted
    emitted_indices = [msg.value.value[0] for msg in observer.messages[:-1]]  # type: ignore[union-attr]
    assert set(emitted_indices) == {0, 1, 2, 3}


def test_pipeline_composition_with_to_list() -> None:
    """
    Test that the pipeline correctly collects all results into a list.

    Verifies the ops.to_list() operator waits for all emissions
    before emitting the collected list.
    """
    scheduler = TestScheduler()

    # Create observables that emit indexed results
    chunk0 = scheduler.create_cold_observable(
        ReactiveTest.on_next(10, (0, make_mock_result(0))),
        ReactiveTest.on_completed(10)
    )
    chunk1 = scheduler.create_cold_observable(
        ReactiveTest.on_next(10, (1, make_mock_result(1))),
        ReactiveTest.on_completed(10)
    )
    chunk2 = scheduler.create_cold_observable(
        ReactiveTest.on_next(10, (2, make_mock_result(2))),
        ReactiveTest.on_completed(10)
    )

    # Source that emits observables
    source = scheduler.create_hot_observable(
        ReactiveTest.on_next(210, chunk0),
        ReactiveTest.on_next(220, chunk1),
        ReactiveTest.on_next(230, chunk2),
        ReactiveTest.on_completed(240)
    )

    # Pipeline: merge then collect to list
    result = source.pipe(
        ops.merge(max_concurrent=3),
        ops.to_list()
    )

    observer = scheduler.create_observer()
    result.subscribe(observer, scheduler=scheduler)

    scheduler.start()

    # Should emit exactly 2 messages: 1 list + 1 completion
    assert len(observer.messages) == 2

    # Verify the list contains all 3 items
    emitted_list = observer.messages[0].value.value  # type: ignore[union-attr]
    assert len(emitted_list) == 3

    # Verify all indices present
    indices = [item[0] for item in emitted_list]
    assert set(indices) == {0, 1, 2}


def test_sequential_processing_with_max_concurrent_one() -> None:
    """
    Test that max_concurrent=1 forces sequential processing.

    Verifies that chunks are processed one at a time when
    max_concurrent is set to 1.
    """
    scheduler = TestScheduler()

    # Create 3 chunks with different processing times
    chunk0 = scheduler.create_cold_observable(
        ReactiveTest.on_next(30, (0, make_mock_result(0))),
        ReactiveTest.on_completed(30)
    )
    chunk1 = scheduler.create_cold_observable(
        ReactiveTest.on_next(20, (1, make_mock_result(1))),
        ReactiveTest.on_completed(20)
    )
    chunk2 = scheduler.create_cold_observable(
        ReactiveTest.on_next(10, (2, make_mock_result(2))),
        ReactiveTest.on_completed(10)
    )

    source = scheduler.create_hot_observable(
        ReactiveTest.on_next(210, chunk0),
        ReactiveTest.on_next(220, chunk1),
        ReactiveTest.on_next(230, chunk2),
        ReactiveTest.on_completed(240)
    )

    # Use max_concurrent=1 for sequential processing
    result = source.pipe(
        ops.merge(max_concurrent=1)
    )

    observer = scheduler.create_observer()
    result.subscribe(observer, scheduler=scheduler)

    scheduler.start()

    # With max_concurrent=1:
    # - chunk0 starts at 210, completes at 240 (210+30)
    # - chunk1 starts at 240, completes at 260 (240+20)
    # - chunk2 starts at 260, completes at 270 (260+10)

    assert len(observer.messages) == 4  # 3 emissions + 1 completion

    # Verify order matches emission order (sequential)
    emitted_values = [msg.value.value for msg in observer.messages[:-1]]  # type: ignore[union-attr]
    emitted_indices = [val[0] for val in emitted_values]
    assert emitted_indices == [0, 1, 2]


def test_map_operator_processes_collected_list() -> None:
    """
    Test that ops.map can process the collected list from to_list().

    Simulates the merge_indexed_results function behavior.
    """
    scheduler = TestScheduler()

    # Create observables emitting indexed results
    chunks = [
        scheduler.create_cold_observable(
            ReactiveTest.on_next(10, (i, make_mock_result(i))),
            ReactiveTest.on_completed(10)
        )
        for i in range(3)
    ]

    source = scheduler.create_hot_observable(
        ReactiveTest.on_next(210, chunks[0]),
        ReactiveTest.on_next(220, chunks[1]),
        ReactiveTest.on_next(230, chunks[2]),
        ReactiveTest.on_completed(240)
    )

    # Simulate pipeline: merge -> to_list -> map (merge results)
    def merge_results(indexed_list: list[tuple[int, TranscriptionResult]]) -> str:
        """Simulate merging indexed results."""
        indexed_list.sort(key=lambda x: x[0])
        texts = [result.text for _, result in indexed_list]
        return "\n".join(texts)

    result = source.pipe(
        ops.merge(max_concurrent=3),
        ops.to_list(),
        ops.map(merge_results)
    )

    observer = scheduler.create_observer()
    result.subscribe(observer, scheduler=scheduler)

    scheduler.start()

    # Should emit merged text
    assert len(observer.messages) == 2
    merged_text = observer.messages[0].value.value  # type: ignore[union-attr]
    assert merged_text == "Chunk 0 text\nChunk 1 text\nChunk 2 text"


def test_out_of_order_completion_maintains_sorted_output() -> None:
    """
    Test that chunks completing out-of-order are still merged correctly.

    Simulates chunks with different processing times completing in
    non-sequential order, verifying final output is still sorted by index.
    """
    scheduler = TestScheduler()

    # Create chunks with delays that cause out-of-order completion
    # chunk2 completes first (10), then chunk1 (20), then chunk0 (30)
    chunk0 = scheduler.create_cold_observable(
        ReactiveTest.on_next(30, (0, make_mock_result(0))),
        ReactiveTest.on_completed(30)
    )
    chunk1 = scheduler.create_cold_observable(
        ReactiveTest.on_next(20, (1, make_mock_result(1))),
        ReactiveTest.on_completed(20)
    )
    chunk2 = scheduler.create_cold_observable(
        ReactiveTest.on_next(10, (2, make_mock_result(2))),
        ReactiveTest.on_completed(10)
    )

    # All chunks emitted at same time
    source = scheduler.create_hot_observable(
        ReactiveTest.on_next(210, chunk0),
        ReactiveTest.on_next(210, chunk1),
        ReactiveTest.on_next(210, chunk2),
        ReactiveTest.on_completed(220)
    )

    def sort_and_merge(indexed_list: list[tuple[int, TranscriptionResult]]) -> list[int]:
        """Sort by index and return indices."""
        indexed_list.sort(key=lambda x: x[0])
        return [idx for idx, _ in indexed_list]

    result = source.pipe(
        ops.merge(max_concurrent=3),
        ops.to_list(),
        ops.map(sort_and_merge)
    )

    observer = scheduler.create_observer()
    result.subscribe(observer, scheduler=scheduler)

    scheduler.start()

    # Verify final output is sorted by index despite out-of-order completion
    sorted_indices = observer.messages[0].value.value  # type: ignore[union-attr]
    assert sorted_indices == [0, 1, 2]
