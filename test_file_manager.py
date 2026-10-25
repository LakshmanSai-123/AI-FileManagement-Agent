import main


def prepare_workspace(tmp_path, monkeypatch):
    """Create an isolated temporary workspace for testing."""

    monkeypatch.setattr(main, "SOURCE_FOLDER", tmp_path)

    for category in main.CATEGORIES:
        (tmp_path / category).mkdir()

    return tmp_path


def test_counts_files_correctly(tmp_path, monkeypatch):
    workspace = prepare_workspace(tmp_path, monkeypatch)

    (workspace / "Documents" / "report.txt").write_text("Report")
    (workspace / "Documents" / "notes.pdf").write_text("Notes")
    (workspace / "Images" / "photo.png").write_text("Image")

    counts = main.get_actual_counts()

    assert counts["Documents"] == 2
    assert counts["Images"] == 1
    assert counts["Code"] == 0


def test_organizes_supported_files(tmp_path, monkeypatch):
    workspace = prepare_workspace(tmp_path, monkeypatch)

    (workspace / "report.txt").write_text("Report content")
    (workspace / "photo.png").write_text("Image content")

    moved, skipped = main.organize_files()

    assert (workspace / "Documents" / "report.txt").exists()
    assert (workspace / "Images" / "photo.png").exists()
    assert len(moved) == 2
    assert skipped == []


def test_does_not_overwrite_existing_file(tmp_path, monkeypatch):
    workspace = prepare_workspace(tmp_path, monkeypatch)

    existing = workspace / "Images" / "photo.png"
    existing.write_text("Original image")

    source = workspace / "photo.png"
    source.write_text("New image")

    moved, skipped = main.organize_files()

    assert existing.read_text() == "Original image"
    assert source.exists()
    assert moved == []
    assert len(skipped) == 1


def test_preserves_unsupported_files(tmp_path, monkeypatch):
    workspace = prepare_workspace(tmp_path, monkeypatch)

    unknown = workspace / "unknown.xyz"
    unknown.write_text("Keep this file")

    moved, skipped = main.organize_files()

    assert unknown.exists()
    assert moved == []
    assert skipped == ["unknown.xyz"]


def test_verifies_organization(tmp_path, monkeypatch):
    workspace = prepare_workspace(tmp_path, monkeypatch)

    (workspace / "report.txt").write_text("Report")

    success, message = main.verify_organization()

    assert success is False
    assert "report.txt" in message

    main.organize_files()

    success, message = main.verify_organization()

    assert success is True
    assert "organized" in message.lower()
