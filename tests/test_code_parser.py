from camrahd_ai.context.indexers.code_parser import get_source_files, parse_file


def test_parse_python_function(tmp_path):
    f = tmp_path / "mod.py"
    f.write_text("def hello():\n    return 1\n")
    chunks = parse_file(str(f))
    assert len(chunks) == 1
    assert chunks[0].name == "hello"
    assert chunks[0].type == "function"
    assert chunks[0].start_line == 1


def test_parse_python_class(tmp_path):
    f = tmp_path / "mod.py"
    f.write_text("class Greeter:\n    def hi(self):\n        return 'hi'\n")
    chunks = parse_file(str(f))
    assert chunks[0].name == "Greeter"
    assert chunks[0].type == "class"


def test_markdown_uses_sliding_window(tmp_path):
    f = tmp_path / "notes.md"
    f.write_text("# Title\n\nSome text\n")
    chunks = parse_file(str(f))
    assert len(chunks) == 1
    assert chunks[0].type == "block"


def test_get_source_files_skips_env_dirs(tmp_path):
    (tmp_path / "app.py").write_text("x = 1\n")
    venv_dir = tmp_path / ".venv"
    venv_dir.mkdir()
    (venv_dir / "lib.py").write_text("x = 1\n")
    files = get_source_files(str(tmp_path))
    assert [f for f in files if f.endswith("app.py")]
    assert not [f for f in files if ".venv" in f]
