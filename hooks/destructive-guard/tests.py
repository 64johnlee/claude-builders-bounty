"""Unit tests for destructive-guard hook."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
import pytest
from hook import is_blocked


@pytest.mark.parametrize("cmd,should_block", [
    # rm -rf variants
    ("rm -rf /",                   True),
    ("rm -rf .",                   True),
    ("rm -rf node_modules",        True),
    ("rm -fr /tmp/foo",            True),
    ("rm -Rf /var/log",            True),
    ("rm -RF /var/log",            True),
    ("rm -r -f /build",            True),
    ("rm -f -r /build",            True),
    ("rm -rdf ./dist",             True),
    # safe rm
    ("rm -f file.txt",             False),
    ("rm -r dir/",                 False),
    ("rm file.txt",                False),
    ("rm -i file.txt",             False),
    # DROP TABLE
    ("DROP TABLE users;",          True),
    ("drop table users;",          True),
    ("DROP TABLE IF EXISTS foo;",  True),
    # TRUNCATE
    ("TRUNCATE orders;",           True),
    ("truncate TABLE logs;",       True),
    # DELETE FROM without WHERE
    ("DELETE FROM users;",         True),
    ("delete from logs;",          True),
    ("DELETE FROM users WHERE id = 1;",    False),
    ("DELETE FROM orders WHERE active=0;", False),
    # git push --force
    ("git push --force origin main",  True),
    ("git push -f origin main",       True),
    ("git push origin main",          False),
    ("git push --force-with-lease",   False),
    # normal commands — must not block
    ("ls -la",           False),
    ("echo hello",       False),
    ("find . -name '*.py'", False),
    ("mkdir -p /tmp/build", False),
    ("npm install",      False),
])
def test_is_blocked(cmd, should_block):
    blocked, reason = is_blocked(cmd)
    assert blocked == should_block, (
        f"Expected {'block' if should_block else 'allow'} for: {cmd!r}\n"
        f"Got blocked={blocked}, reason={reason!r}"
    )


def test_reason_non_empty_when_blocked():
    blocked, reason = is_blocked("rm -rf /tmp")
    assert blocked and reason != ""


def test_reason_empty_when_allowed():
    blocked, reason = is_blocked("ls -la")
    assert not blocked and reason == ""
