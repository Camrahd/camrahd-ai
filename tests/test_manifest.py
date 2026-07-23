from camrahd_ai.context.indexers.manifest import load_manifest, plan_reindex, save_manifest


def test_first_run_indexes_everything(tmp_path):
    f = tmp_path / "a.py"
    f.write_text("x = 1\n")
    to_index, deleted, new_manifest = plan_reindex(str(tmp_path), [str(f)])
    assert to_index == [str(f)]
    assert deleted == []
    assert str(f) in new_manifest


def test_unchanged_files_are_skipped(tmp_path):
    f = tmp_path / "a.py"
    f.write_text("x = 1\n")
    _, _, manifest = plan_reindex(str(tmp_path), [str(f)])
    save_manifest(str(tmp_path), manifest)

    to_index, deleted, _ = plan_reindex(str(tmp_path), [str(f)])
    assert to_index == []
    assert deleted == []


def test_changed_file_is_reindexed(tmp_path):
    f = tmp_path / "a.py"
    f.write_text("x = 1\n")
    _, _, manifest = plan_reindex(str(tmp_path), [str(f)])
    save_manifest(str(tmp_path), manifest)

    f.write_text("x = 2\n")
    to_index, deleted, _ = plan_reindex(str(tmp_path), [str(f)])
    assert to_index == [str(f)]
    assert deleted == []


def test_deleted_file_is_reported(tmp_path):
    f = tmp_path / "a.py"
    f.write_text("x = 1\n")
    _, _, manifest = plan_reindex(str(tmp_path), [str(f)])
    save_manifest(str(tmp_path), manifest)

    f.unlink()
    to_index, deleted, _ = plan_reindex(str(tmp_path), [])
    assert to_index == []
    assert deleted == [str(f)]


def test_load_manifest_missing_or_corrupt(tmp_path):
    assert load_manifest(str(tmp_path)) == {}
    manifest_file = tmp_path / ".camrahd" / "index_manifest.json"
    manifest_file.parent.mkdir(parents=True)
    manifest_file.write_text("{not json")
    assert load_manifest(str(tmp_path)) == {}
