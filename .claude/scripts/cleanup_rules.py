import re

AGENT_DIRS = (
    ".claude",
    ".agents",
    ".codex",
    ".cursor",
    ".windsurf",
    ".continue",
    ".impeccable",
    ".playwright-mcp",
    ".superdesign",
    ".aider.tags.cache.v3",
)
AGENT_FILES = (
    "AGENTS.md",
    "AGENTS.override.md",
    "CLAUDE.md",
    "CLAUDE.local.md",
    "GEMINI.md",
    ".mcp.json",
    ".cursorrules",
    ".windsurfrules",
    ".claudeignore",
    ".aider.conf.yml",
    ".aider.chat.history.md",
    ".aider.input.history",
)
AGENT_GLOBS = ("PROMPT-*.md", "TASK-*.md")
SKIP_DIRS = {
    ".git",
    "node_modules",
    "dist",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}
IGNORE_FILES = {".gitignore", ".dockerignore", ".prettierignore", ".eslintignore"}
JSON_FILES = re.compile(r"^(biome\.jsonc?|tsconfig.*\.json|package\.json|\.eslintrc\.json)$")
AGENT_DIR_RE = "|".join(re.escape(d) for d in AGENT_DIRS)
IGNORE_LINE = re.compile(
    rf"^\s*!?/?(?:\*\*/)?(?:{AGENT_DIR_RE}|brief|context|work|skills)(?:/.*)?\s*$|(?:^|/)(?:CLAUDE|AGENTS|GEMINI)(?:\.local|\.override)?\.md|\.mcp\.json|\.cursorrules|\.windsurfrules|\.claudeignore"
)
JSON_ITEM = re.compile(rf'^\s*"!?(?:\*\*/)?(?:{AGENT_DIR_RE})[^"]*",?\s*$')
SCRUB_BLOCK = re.compile(r"[ \t]*<!-- scrub:start -->.*?<!-- scrub:end -->[ \t]*\n?(?:\n(?=\n))?", re.S)
LINK = re.compile(r"(!?)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
SEP_BEFORE = re.compile(r"[ \t]*(?:·|,|;)[ \t]*\n?[ \t]*$")
SEP_AFTER = re.compile(r"^[ \t]*(?:·|,|;)[ \t]*\n?[ \t]*")
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+\.)\s")
TRACE = re.compile(
    r"\.impeccable|claude[- ]?code|claude\.md|agents\.md|\bcodex\b|copilot|chatgpt|cursor[- ]?(?:ai|agent)|co-authored-by|generated (?:with|by) (?:claude|codex|chatgpt|an? ai)|ai[- ]generated|сгенерирован\S* (?:ии|нейросет)|\.claude/|\.agents/|scrub:(?:start|end)",
    re.I,
)
STYLE = re.compile(
    r"является|позволяет|уникальн|инновацион|в современном мире|играет ключевую роль|не просто [^,.]+, а|\bdelve|\bleverag|seamless|cutting-edge|game-changer|in today.s",
    re.I,
)
STYLE_LISTS = re.compile(r"(?:^|/)locales/[^/]+/video\.json$")
AGENT_PERSON = re.compile(
    r"claude|anthropic|codex|openai|chatgpt|copilot|cursor|devin|aider|gemini|\bgpt\b", re.I
)
TRAILER = re.compile(
    r"^(?:co-authored-by|signed-off-by|generated-by|assisted-by|helped-by|reviewed-by|on-behalf-of):",
    re.I | re.M,
)
TEXT_LIMIT = 2_000_000


SOURCE_RENAMES = {
    "docs/design-decisions.md": {
        ".claude/git-hooks/pre-commit": "pre-commit hook",
        "AGENTS.md": "runtime instruction files",
        "CLAUDE.md": "runtime instruction files",
    },
    "frontend/scripts/checks/files.ts": {".impeccable": ".design-cache"},
    "frontend/tests/scripts/checks/engine.test.ts": {".impeccable": ".design-cache"},
}

AI_DISCLOSURE_PATHS = {
    "docs/ai-register.md",
    "docs/submission/passport.md",
    "docs/submission/passport.html",
    "presentation/src/slides/06-checks.html",
    "docs/submission/plexus-deck.html",
    "docs/submission/ai-materials.md",
}
AI_TOOL_NAMES = re.compile(r"claude[- ]?code|\bcodex\b|copilot|chatgpt|cursor[- ]?(?:ai|agent)", re.I)
ATTRIBUTION_TRACE = re.compile(r"co-authored-by|generated[- ]by:|generated (?:with|by) (?:claude|codex|chatgpt|an? ai)|ai[- ]generated", re.I)


PRODUCT_PROVIDER_PATHS = {
    "backend/pyproject.toml", "backend/uv.lock", "backend/src/app/main.py",
    "backend/src/app/settings.py", "backend/src/app/adapter/llm/codex_agent.py",
    "backend/tests/unit/composition/test_main.py", "backend/tests/unit/composition/test_settings.py",
    "docs/dependencies.md", "docs/design-decisions.md", "docs/running.md",
}


def has_disallowed_trace(path: str, text: str) -> bool:
    if ATTRIBUTION_TRACE.search(text):
        return True
    if path in AI_DISCLOSURE_PATHS or path in PRODUCT_PROVIDER_PATHS:
        text = AI_TOOL_NAMES.sub("", text)
        return bool(TRACE.search(text))
    return bool(TRACE.search(text))
