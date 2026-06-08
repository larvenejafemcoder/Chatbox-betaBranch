#!/usr/bin/env python3
"""Comprehensive test suite for Py_Chatbox. Run from project root.

Usage:
    python scripts/test_all.py
    python scripts/test_all.py -v
"""

import os
import sys
import json
import unittest
import tempfile

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "source"))

# Silence logging during tests
import logging
logging.disable(logging.CRITICAL)


class TestSlowPrint(unittest.TestCase):
    """slow_print.py — typing effect utilities."""

    def test_slow_print_runs(self):
        from slow_print import slow_print
        slow_print("hello", delay_range=(0.001, 0.001))

    def test_slow_input_returns_string(self):
        from slow_print import slow_input
        from unittest.mock import patch
        with patch("builtins.input", return_value="test"):
            result = slow_input("> ", delay_range=(0.001, 0.001))
        self.assertEqual(result, "test")


class TestRankingSystem(unittest.TestCase):
    """ranking.py — authentication, ranks, user CRUD."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmpdir.name)

    def tearDown(self):
        os.chdir(self.orig_cwd)
        self.tmpdir.cleanup()

    def _make_empty_ranks(self):
        with open("ranksystem_static.json", "w", encoding="utf-8") as f:
            json.dump([{"name": "Recruit", "score": 0}], f)

    def _make_empty_users(self):
        if os.path.exists("users.json"):
            return
        with open("users.json", "w", encoding="utf-8") as f:
            json.dump({}, f)

    def test_hash_password(self):
        from ranking import RankingSystem
        h1 = RankingSystem.hash_password("hello")
        h2 = RankingSystem.hash_password("hello")
        h3 = RankingSystem.hash_password("world")
        self.assertEqual(h1, h2)
        self.assertNotEqual(h1, h3)
        self.assertEqual(len(h1), 64)

    def test_load_users_empty(self):
        from ranking import RankingSystem
        self._make_empty_users()
        self.assertEqual(RankingSystem.load_users(), {})

    def test_save_and_load_users(self):
        from ranking import RankingSystem
        data = {"test": {"password": "abc", "score": 10, "rank": "Recruit"}}
        RankingSystem.save_users(data)
        loaded = RankingSystem.load_users()
        self.assertEqual(loaded, data)

    def test_register_new_user(self):
        from ranking import RankingSystem
        self._make_empty_users()
        ok, _ = RankingSystem.register("Alice", "secret")
        self.assertTrue(ok)
        users = RankingSystem.load_users()
        self.assertIn("Alice", users)

    def test_register_duplicate(self):
        from ranking import RankingSystem
        self._make_empty_users()
        RankingSystem.register("Alice", "secret")
        ok, _ = RankingSystem.register("Alice", "other")
        self.assertFalse(ok)

    def test_login_ok(self):
        from ranking import RankingSystem
        self._make_empty_users()
        RankingSystem.register("Bob", "pass123")
        ok, _ = RankingSystem.login("Bob", "pass123")
        self.assertTrue(ok)

    def test_login_wrong_password(self):
        from ranking import RankingSystem
        self._make_empty_users()
        RankingSystem.register("Bob", "pass123")
        ok, _ = RankingSystem.login("Bob", "wrong")
        self.assertFalse(ok)

    def test_login_unknown_user(self):
        from ranking import RankingSystem
        self._make_empty_users()
        ok, _ = RankingSystem.login("Nobody", "x")
        self.assertFalse(ok)

    def test_load_ranks(self):
        from ranking import RankingSystem
        self._make_empty_ranks()
        ranks = RankingSystem.load_ranks()
        self.assertEqual(len(ranks), 1)
        self.assertEqual(ranks[0]["name"], "Recruit")


class TestElizaEngine(unittest.TestCase):
    """ELIZA engine merged into chatbox.py — core matching tests."""

    def setUp(self):
        from chatbox import Eliza
        self.el = Eliza()

    def test_match_exact(self):
        self.assertEqual([], self.el._match_decomp(["a"], ["a"]))
        self.assertEqual([], self.el._match_decomp(["a", "b"], ["a", "b"]))

    def test_mismatch(self):
        self.assertIsNone(self.el._match_decomp(["a"], ["b"]))
        self.assertIsNone(self.el._match_decomp(["a"], ["a", "b"]))
        self.assertIsNone(self.el._match_decomp(["a", "b"], ["a"]))

    def test_wildcard(self):
        self.assertEqual([["a"]], self.el._match_decomp(["*"], ["a"]))
        self.assertEqual([["a", "b"]], self.el._match_decomp(["*"], ["a", "b"]))
        self.assertEqual([[]], self.el._match_decomp(["*"], []))

    def test_wildcard_prefix(self):
        self.assertEqual([["0"]], self.el._match_decomp(["*", "a"], ["0", "a"]))
        self.assertEqual([["0", "a"]], self.el._match_decomp(["*", "a"], ["0", "a", "a"]))
        self.assertEqual([[]], self.el._match_decomp(["*", "a"], ["a"]))

    def test_double_wildcard(self):
        self.assertEqual([["0"], ["b"]], self.el._match_decomp(["*", "a", "*"], ["0", "a", "b"]))
        self.assertEqual([["0"], []], self.el._match_decomp(["*", "a", "*"], ["0", "a"]))

    def test_synonym_matching(self):
        doc_path = os.path.join(os.path.dirname(__file__), "..", "source", "doctor.txt")
        self.el.load(doc_path)
        self.assertEqual([["am"]], self.el._match_decomp(["@be"], ["am"]))
        self.assertIsNone(self.el._match_decomp(["@be"], ["a"]))
        self.assertIsNotNone(
            self.el._match_decomp(["*", "i", "am", "@sad", "*"],
                                  ["its", "true", "i", "am", "unhappy"]))

    def test_full_conversation(self):
        doc_path = os.path.join(os.path.dirname(__file__), "..", "source", "doctor.txt")
        self.el.load(doc_path)
        self.assertEqual("How do you do.  Please tell me your problem.", self.el.initial())
        self.assertIn(self.el.respond("Hello"), [
            "How do you do. Please state your problem.",
            "Hi. What seems to be your problem ?"])
        self.assertEqual("In what way ?", self.el.respond("Men are all alike."))
        self.assertEqual("Goodbye.  Thank you for talking to me.", self.el.final())

    def test_quit_detection(self):
        doc_path = os.path.join(os.path.dirname(__file__), "..", "source", "doctor.txt")
        self.el.load(doc_path)
        self.assertIsNone(self.el.respond("bye"))
        self.assertIsNone(self.el.respond("goodbye"))


class TestPookieGPT(unittest.TestCase):
    """chatbox.py — PookieGPT initialization and responses."""

    def setUp(self):
        self.orig_dir = os.getcwd()
        os.chdir(os.path.join(os.path.dirname(__file__), "..", "source"))

    def tearDown(self):
        os.chdir(self.orig_dir)

    def test_init_loads_responses(self):
        from chatbox import PookieGPT
        bot = PookieGPT()
        self.assertTrue(hasattr(bot, "responds"))
        self.assertIn("introduction", bot.responds)
        self.assertIn("greeting", bot.responds)
        self.assertIn("goodbye", bot.responds)

    def test_response_keys_are_lists_or_nested(self):
        from chatbox import PookieGPT
        bot = PookieGPT()
        for key, val in bot.responds.items():
            if key == "health_responses":
                for sub in val.values():
                    self.assertIsInstance(sub, list, f"health_responses.{sub} not a list")
            elif key == "nickname":
                self.assertIsInstance(val, dict)
                for sub in val.values():
                    self.assertIsInstance(sub, list)
            else:
                self.assertIsInstance(val, list, f"{key} not a list")
                self.assertGreater(len(val), 0, f"{key} is empty")

    def test_mood_map_keys_present(self):
        from chatbox import PookieGPT
        bot = PookieGPT()
        self.assertIn("1", bot.responds["health_responses"])
        self.assertIn("2", bot.responds["health_responses"])
        self.assertIn("3", bot.responds["health_responses"])


class TestKRNL(unittest.TestCase):
    """krnl_system.py — simulator logic."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmpdir.name)
        sys.path.insert(0, os.path.join(PROJECT_ROOT, "source"))

    def tearDown(self):
        os.chdir(self.orig_cwd)
        self.tmpdir.cleanup()

    def _make_user(self, name="TestCadet"):
        return {
            "name": name, "age": "20", "study": "CS", "goal": "Ship",
            "rank": "Fresh Cadet", "xp": 0, "stress": 0, "messages": 0
        }

    def _make_memory(self):
        return {"facts": [], "conversation_log": []}

    def test_update_rank_thresholds(self):
        import krnl_system
        user = self._make_user()
        self.assertEqual(user["rank"], "Fresh Cadet")
        user["xp"] = 100
        krnl_system.update_rank(user)
        self.assertEqual(user["rank"], "Cadet")
        user["xp"] = 1000
        krnl_system.update_rank(user)
        self.assertEqual(user["rank"], "Commander")

    def test_ai_response_default(self):
        import krnl_system
        user = self._make_user()
        memory = self._make_memory()
        resp = krnl_system.ai_response(user, memory, "hello")
        self.assertIsInstance(resp, str)
        self.assertGreater(len(resp), 0)

    def test_ai_response_math_awards_xp(self):
        import krnl_system
        user = self._make_user()
        memory = self._make_memory()
        krnl_system.ai_response(user, memory, "solve this math")
        self.assertEqual(user["xp"], 15)

    def test_ai_response_code_awards_xp(self):
        import krnl_system
        user = self._make_user()
        memory = self._make_memory()
        krnl_system.ai_response(user, memory, "I love python")
        self.assertEqual(user["xp"], 20)

    def test_ai_response_stress(self):
        import krnl_system
        user = self._make_user()
        memory = self._make_memory()
        krnl_system.ai_response(user, memory, "I'm stressed")
        self.assertEqual(user["stress"], 1)

    def test_remember_and_recall(self):
        import krnl_system
        user = self._make_user()
        memory = self._make_memory()
        resp = krnl_system.ai_response(user, memory, "remember my favorite color is blue")
        self.assertIn("blue", resp)
        self.assertIn("my favorite color is blue", memory["facts"])

        resp2 = krnl_system.ai_response(user, memory, "memory")
        self.assertIn("blue", resp2)

    def test_status_output(self):
        import krnl_system
        user = self._make_user()
        resp = krnl_system.ai_response(user, self._make_memory(), "status")
        self.assertIn("Fresh Cadet", resp)
        self.assertIn("XP", resp)


class TestASCIIBox(unittest.TestCase):
    """chatbox.py — UI helpers."""

    def test_ascii_box_basic(self):
        from chatbox import ascii_box
        result = ascii_box("[ TEST ]", "hello")
        self.assertTrue(result.startswith("┌"))
        self.assertTrue(result.endswith("┘"))
        self.assertIn("hello", result)
        self.assertIn("TEST", result)

    def test_ascii_box_multi_line(self):
        from chatbox import ascii_box
        result = ascii_box("[ MULTI ]", "line1\nline2")
        self.assertIn("line1", result)
        self.assertIn("line2", result)

    def test_status_panel_format(self):
        from chatbox import status_panel
        user = {"name": "Dev", "rank": "Cadet", "study": "CS",
                "xp": 50, "goal": "Ship"}
        result = status_panel(user)
        self.assertIn("Dev", result)
        self.assertIn("Cadet", result)


class TestImportIntegrity(unittest.TestCase):
    """All modules import cleanly from the right places."""

    def test_chatbox_exports_eliza(self):
        from chatbox import Eliza, Key, Decomp
        self.assertTrue(issubclass(type(Eliza), type))

    def test_chatbox_exports_pookie(self):
        from chatbox import PookieGPT, ascii_box, status_panel
        self.assertTrue(issubclass(type(PookieGPT), type))

    def test_eliza_file_still_loadable(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "eliza", os.path.join(PROJECT_ROOT, "source", "eliza.py"))
        self.assertIsNotNone(spec)

    def test_core_imports(self):
        import core
        self.assertTrue(hasattr(core, "boot_menu"))
        self.assertTrue(hasattr(core, "run_pookie"))
        self.assertTrue(hasattr(core, "run_krnl"))


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for cls in [
        TestSlowPrint,
        TestRankingSystem,
        TestASCIIBox,
        TestPookieGPT,
        TestKRNL,
        TestElizaEngine,
        TestImportIntegrity,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2 if "-v" in sys.argv else 1)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
