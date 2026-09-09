result = service.index_records(
    records=records,
    report_type="inventory",
)

assert result.parsed_record_count == 13
assert result.chunk_count == 3
assert result.indexed_point_count == 3

assert len(fake_qdrant.chunks) == 3
assert fake_qdrant.embeddings.shape == (3, 1024)