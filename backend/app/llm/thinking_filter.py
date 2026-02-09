"""Filter out <think>...</think> blocks from LLM output.

Qwen3 and other thinking models wrap chain-of-thought in <think> tags.
These should not be shown to the user in chat responses.
"""

import re

_THINK_RE = re.compile(r"<think>[\s\S]*?</think>\s*", re.DOTALL)


def strip_thinking(text: str) -> str:
    """Remove <think>...</think> blocks from text."""
    return _THINK_RE.sub("", text).strip()


class ThinkingFilter:
    """Streaming filter that drops content inside <think>...</think> tags.

    Usage:
        f = ThinkingFilter()
        for chunk in stream:
            clean = f.process(chunk)
            if clean:
                yield clean
    """

    def __init__(self):
        self._inside_think = False
        self._buffer = ""

    def process(self, chunk: str) -> str:
        result = []
        self._buffer += chunk

        while self._buffer:
            if self._inside_think:
                end = self._buffer.find("</think>")
                if end == -1:
                    # Still inside <think>, discard buffer but keep partial tag
                    if self._buffer.endswith("<"):
                        # could be start of </think>
                        break
                    self._buffer = ""
                    break
                # Found end of thinking block
                self._inside_think = False
                self._buffer = self._buffer[end + len("</think>"):]
                # Skip trailing whitespace/newline after </think>
                self._buffer = self._buffer.lstrip("\n")
            else:
                start = self._buffer.find("<think>")
                if start == -1:
                    # Check for partial <think at end
                    for i in range(1, min(len("<think>"), len(self._buffer) + 1)):
                        if self._buffer.endswith("<think>"[:i]):
                            result.append(self._buffer[:-i])
                            self._buffer = self._buffer[-i:]
                            break
                    else:
                        result.append(self._buffer)
                        self._buffer = ""
                    break
                else:
                    # Output everything before <think>
                    result.append(self._buffer[:start])
                    self._inside_think = True
                    self._buffer = self._buffer[start + len("<think>"):]

        return "".join(result)
