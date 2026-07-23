from camrahd_ai.memory import session


def test_new_session_persists_and_resumes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(session.config, "memory", {"db_path": str(tmp_path / "mem" / "memory.db")})

    created = session.new_session()
    assert session.get_current_session() == created

    switched = session.switch_session("other-session")
    assert switched == "other-session"
    assert session.get_current_session() == "other-session"


def test_list_sessions_empty_without_db(tmp_path, monkeypatch):
    monkeypatch.setitem(session.config, "memory", {"db_path": str(tmp_path / "mem" / "memory.db")})
    assert session.list_sessions() == []
