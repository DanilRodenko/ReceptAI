from types import SimpleNamespace

import pytest

import llm
from config import GROQ_FALLBACK_MODEL, GROQ_MODEL

MESSAGES = [{"role": "user", "content": "Hi"}]


class FakeRateLimitError(Exception):
    """Stands in for groq.RateLimitError, which is hard to build by hand."""


class FakeCompletions:
    """Mimics client.chat.completions: records every call and returns a canned reply."""

    def __init__(self, reply="ok", fail_first_with=None):
        self.reply = reply
        self.fail_first_with = fail_first_with  # exception class to raise on the 1st call
        self.calls = []  # kwargs of every create() call

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.fail_first_with and len(self.calls) == 1:
            raise self.fail_first_with("simulated error")
        # Same shape as a real Groq response: response.choices[0].message.content
        message = SimpleNamespace(content=self.reply)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


@pytest.fixture
def use_fake(monkeypatch):
    """Replace the real Groq client with a fake one for the duration of a test."""

    def _install(completions):
        fake_client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
        monkeypatch.setattr(llm, "get_groq_client", lambda: fake_client)
        monkeypatch.setattr(llm, "RateLimitError", FakeRateLimitError)
        return completions

    return _install


def test_chat_uses_main_model_and_returns_text(use_fake):
    fake = use_fake(FakeCompletions(reply="Hello!"))

    assert llm.chat(MESSAGES) == "Hello!"
    assert len(fake.calls) == 1
    assert fake.calls[0]["model"] == GROQ_MODEL
    assert "response_format" not in fake.calls[0]


def test_falls_back_to_second_model_on_rate_limit(use_fake):
    fake = use_fake(FakeCompletions(reply="from fallback", fail_first_with=FakeRateLimitError))

    assert llm.chat(MESSAGES) == "from fallback"
    assert [call["model"] for call in fake.calls] == [GROQ_MODEL, GROQ_FALLBACK_MODEL]


def test_other_errors_are_not_swallowed(use_fake):
    use_fake(FakeCompletions(fail_first_with=ValueError))

    with pytest.raises(ValueError):
        llm.chat(MESSAGES)


def test_extract_uses_json_mode_and_parses_dict(use_fake):
    fake = use_fake(FakeCompletions(reply='{"name": "Alex", "service": "cleaning"}'))

    result = llm.extract(MESSAGES)

    assert result == {"name": "Alex", "service": "cleaning"}
    assert fake.calls[0]["response_format"] == {"type": "json_object"}
    assert fake.calls[0]["temperature"] == 0