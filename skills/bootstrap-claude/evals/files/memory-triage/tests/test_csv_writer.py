from exportkit.csv_writer import iter_csv, sanitize


def test_formula_cells_are_quoted():
    assert sanitize("=SUM(A1:A3)") == "'=SUM(A1:A3)"
    assert sanitize("plain") == "plain"


def test_first_chunk_has_bom():
    chunks = list(iter_csv(["id"], [[1], [2]]))
    assert chunks[0].startswith("﻿")
    assert chunks[1:] == ["1\r\n", "2\r\n"]
