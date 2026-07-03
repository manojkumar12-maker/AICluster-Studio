import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.ai import PromptTemplate
from ..context.service import ContextBuilder

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = (
    "You are AICluster AI, a distributed compute assistant. "
    "You help users understand their codebase, execute workflows, "
    "and manage their cluster. You have access to repository intelligence, "
    "workflow execution, and cluster operations."
)


class PromptBuilder:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.context = ContextBuilder(db)

    async def build(self, user_prompt: str, template_name: str | None = None,
                    system_prompt: str | None = None, repository_id: str | None = None,
                    session_history: list[dict] | None = None) -> dict:
        sys_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        if template_name:
            result = await self.db.execute(
                select(PromptTemplate).where(PromptTemplate.name == template_name)
            )
            template = result.scalar_one_or_none()
            if template and template.system_prompt:
                sys_prompt = template.system_prompt

        repo_context = ""
        if repository_id:
            ctx = await self.context.build_context(repository_id, user_prompt)
            if ctx:
                repo_context = f"\n\n## Repository Context\n{ctx}"

        messages = []
        if session_history:
            for m in session_history[-10:]:
                messages.append({"role": m["role"], "content": m["content"]})

        messages.append({"role": "user", "content": user_prompt})

        full_system = sys_prompt + repo_context
        estimated_tokens = self._estimate_tokens(full_system) + sum(
            self._estimate_tokens(m["content"]) for m in messages
        )

        return {
            "system_prompt": full_system,
            "messages": messages,
            "user_prompt": user_prompt,
            "estimated_tokens": estimated_tokens,
            "token_budget": 4096,
            "compression_needed": estimated_tokens > 3000,
        }

    def _estimate_tokens(self, text: str) -> int:
        return len(text) // 4 + 1
