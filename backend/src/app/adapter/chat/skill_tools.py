from dataclasses import dataclass
from pathlib import Path

from pydantic_ai import Agent, ModelRetry, RunContext

from app.adapter.chat.artifacts import ChatRun


@dataclass(frozen=True)
class AgentSkill:
    name: str
    description: str
    path: Path


class SkillTools:
    def __init__(self, root: Path | None = None) -> None:
        directory = root if root is not None else Path(__file__).with_name("skills")
        self.skills: dict[str, AgentSkill] = {}
        for path in sorted(directory.glob("*/SKILL.md")):
            header, separator, body = path.read_text().removeprefix("---\n").partition("\n---\n")
            fields = dict(line.split(": ", 1) for line in header.splitlines())
            name, description = fields["name"], fields["description"]
            if not separator or not body.strip() or name != path.parent.name:
                raise ValueError(f"Invalid bundled skill: {path}")
            self.skills[name] = AgentSkill(name, description, path)
        if not self.skills:
            raise ValueError("No bundled analyst skills found")

    def catalog(self) -> str:
        return "\n".join(f"- {s.name}: {s.description}" for s in self.skills.values())

    def register(self, agent: Agent[ChatRun, str]) -> None:
        agent.tool(
            sequential=True,
            description="Load an analyst skill by its catalog name. Choose relevant skills "
            "for the user's question; combine skills when needed. Returns maintained guidance, "
            "not calculation results. No arbitrary filesystem access.",
        )(self.load_skill)

    def load_skill(self, ctx: RunContext[ChatRun], name: str) -> str:
        skill = self.skills.get(name)
        if skill is None:
            raise ModelRetry("Unknown skill. Available skills:\n" + self.catalog())
        instructions = skill.path.read_text().split("\n---\n", 1)[1].strip()
        ctx.deps.loaded_skills.add(name)
        return instructions
