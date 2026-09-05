"""Tests for loading questions and saving results."""

from __future__ import annotations

import csv
import dataclasses
import random

import pytest

from numeracycheck.errors import DataError
from numeracycheck.storage import ALL_CATEGORIES, QuestionBank, filter_by_name


class TestLoading:
    def test_missing_file(self, tmp_path):
        with pytest.raises(DataError, match="not found"):
            QuestionBank.from_csv(tmp_path / "nope.csv")

        empty = tmp_path / "empty.csv"
        empty.write_text("id,category,type,prompt,options,answer,explanation\n",
                         encoding="utf-8")
        with pytest.raises(DataError, match="empty"):
            QuestionBank.from_csv(empty)

    def test_loads_questions(self, tmp_path, questions_csv, bank):
        assert len(bank) == 4
        assert bank.skipped == ()

        rows = list(csv.reader(questions_csv.open(encoding="utf-8")))
        rows.append(["Q05", "Prime factors", "essay", "Broken row", "", "42", ""])
        path = tmp_path / "mixed.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            csv.writer(handle).writerows(rows)

        loaded = QuestionBank.from_csv(path)
        assert len(loaded) == 4
        assert "Row 6 skipped" in loaded.skipped[0]


class TestChoosing:
    def test_topics(self, bank):
        assert bank.categories() == (ALL_CATEGORIES, "Identifying primes",
                                     "Prime factors")
        assert len(bank.for_category("identifying primes")) == 2
        assert len(bank.for_category(ALL_CATEGORIES)) == 4

    def test_picking(self, bank):
        picked = bank.pick(4)
        assert len({question.question_id for question in picked}) == 4
        first = bank.pick(3, rng=random.Random(42))
        second = bank.pick(3, rng=random.Random(42))
        assert [q.question_id for q in first] == [q.question_id for q in second]

        with pytest.raises(DataError, match="Only 2 question"):
            bank.pick(3, category="Prime factors")
        with pytest.raises(DataError, match="at least one"):
            bank.pick(0)


class TestSaving:
    def test_save_and_reload(self, store, attempt):
        store.save(attempt)
        store.save(dataclasses.replace(attempt, attempt_id="def67890"))
        lines = store.path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 3
        assert lines[0].startswith("attempt_id")
        assert store.load_all()[0] == attempt

    def test_empty_history(self, store):
        assert store.load_all() == ()

    def test_locked_file(self, store, attempt,
                                                           monkeypatch):
        def deny(*args, **kwargs):
            raise PermissionError("open in Excel")

        monkeypatch.setattr("pathlib.Path.open", deny)
        with pytest.raises(DataError, match="Close the file in Excel"):
            store.save(attempt)

    def test_damaged_row(self, store, attempt, caplog):
        store.save(attempt)
        with store.path.open("a", encoding="utf-8") as handle:
            handle.write("broken,row,too,few\n")
        assert len(store.load_all()) == 1
        assert "Skipping results row" in caplog.text


class TestExport:
    def test_export_and_filter(self, store, attempt, tmp_path):
        other = dataclasses.replace(attempt, attempt_id="b", name="Grace Hopper")
        store.save(attempt)
        store.save(other)

        destination = tmp_path / "out.csv"
        assert store.export(destination, [other]) == 1
        assert "Ada" not in destination.read_text(encoding="utf-8")

        both = (attempt, other)
        assert len(filter_by_name(both, "  ada lovelace ")) == 1
        assert len(filter_by_name(both, "")) == 2
        assert filter_by_name(both, "Alan Turing") == ()
