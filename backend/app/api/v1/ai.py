import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ...database import get_db
from ...models.ai import AIModel, AISession, AIMessage, ToolDefinition, ToolCall, RuntimeMetric, AIProviderConfig, PromptTemplate
from ...ai.sessions.service import SessionManager
from ...ai.conversation.service import ConversationManager
from ...ai.prompt.service import PromptBuilder
from ...ai.tools.registry import ToolRegistry
from ...ai.registry.service import ModelRegistry
from ...websocket.manager import ws_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat")
async def chat(data: dict, db: AsyncSession = Depends(get_db)):
    session_id = data.get("session_id")
    user_prompt = data.get("prompt", "")
    if not user_prompt:
        raise HTTPException(400, "Prompt required")

    sessions = SessionManager(db)
    if session_id:
        session = await sessions.get(session_id)
        if not session:
            raise HTTPException(404, "Session not found or expired")
        await sessions.touch(session_id)
    else:
        session = await sessions.create()

    conv = ConversationManager(db)
    prompt_builder = PromptBuilder(db)

    history = await conv.get_recent(session.id)
    prompt = await prompt_builder.build(
        user_prompt=user_prompt,
        repository_id=session.repository_id,
        session_history=history,
    )

    msg = await conv.add_message(session.id, "user", user_prompt, tokens=prompt.get("estimated_tokens"))

    await ws_manager.broadcast("generation_started", {
        "session_id": session.id, "message_id": msg.id,
    })

    assistant_msg = await conv.add_message(
        session.id, "assistant",
        "AI Runtime ready for provider integration. "
        "Register a model provider to enable generation.",
        model_id=session.model_id,
    )

    return {
        "session_id": session.id,
        "message_id": assistant_msg.id,
        "content": assistant_msg.content,
        "prompt_info": {
            "system_prompt": prompt["system_prompt"][:200],
            "estimated_tokens": prompt["estimated_tokens"],
            "compression_needed": prompt["compression_needed"],
        },
        "tool_candidates": ToolRegistry.get_schemas(),
    }


@router.post("/session")
async def create_session(data: dict, db: AsyncSession = Depends(get_db)):
    sessions = SessionManager(db)
    session = await sessions.create(
        user_id=data.get("user_id"),
        model_id=data.get("model_id"),
        repository_id=data.get("repository_id"),
    )
    return {"id": session.id, "status": session.status, "created_at": session.created_at.isoformat()}


@router.get("/session")
async def list_sessions(db: AsyncSession = Depends(get_db)):
    sessions = SessionManager(db)
    active = await sessions.list_active()
    return [{"id": s.id, "status": s.status, "total_messages": s.total_messages,
             "total_tokens": s.total_tokens, "last_active_at": s.last_active_at.isoformat()} for s in active]


@router.delete("/session/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    sessions = SessionManager(db)
    success = await sessions.delete(session_id)
    if not success:
        raise HTTPException(404, "Session not found")
    return {"status": "deleted"}


@router.get("/session/{session_id}/history")
async def get_session_history(session_id: str, db: AsyncSession = Depends(get_db)):
    conv = ConversationManager(db)
    return await conv.get_recent(session_id)


@router.get("/models")
async def list_models(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AIModel).order_by(AIModel.priority))
    models = result.scalars().all()
    return [{"id": m.id, "name": m.name, "provider": m.provider, "status": m.status,
             "context_window": m.context_window, "capabilities": m.capabilities} for m in models]


@router.post("/models/register")
async def register_model(data: dict, db: AsyncSession = Depends(get_db)):
    model = AIModel(
        name=data["name"], provider=data["provider"],
        model_type=data.get("model_type", "chat"),
        context_window=data.get("context_window", 4096),
        capabilities=data.get("capabilities", {}),
        config=data.get("config", {}),
    )
    db.add(model)
    await db.commit()
    await db.refresh(model)
    await ws_manager.broadcast("model_loaded", {"id": model.id, "name": model.name})
    return {"id": model.id, "name": model.name, "provider": model.provider}


@router.post("/models/load")
async def load_model(data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AIModel).where(AIModel.id == data.get("model_id")))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(404, "Model not found")

    provider_cls = ModelRegistry.get_provider(data.get("provider", model.provider))
    if provider_cls:
        instance = provider_cls()
        loaded = await instance.load()
        if loaded:
            ModelRegistry.set_instance(model.provider, instance)
            model.status = "loaded"
            model.loaded_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
            await db.commit()
            await ws_manager.broadcast("model_loaded", {"id": model.id, "name": model.name})

    model.status = "loaded"
    await db.commit()
    return {"status": "loaded", "model_id": model.id}


@router.post("/models/unload")
async def unload_model(data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AIModel).where(AIModel.id == data.get("model_id")))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(404, "Model not found")
    instance = ModelRegistry.get_instance(model.provider)
    if instance:
        await instance.unload()
        ModelRegistry.remove_instance(model.provider)
    model.status = "unloaded"
    await db.commit()
    return {"status": "unloaded"}


@router.get("/runtime")
async def get_runtime_status():
    return {
        "providers": ModelRegistry.list_providers(),
        "loaded_instances": ModelRegistry.list_instances(),
        "capabilities": ModelRegistry.list_capabilities(),
        "tools": ToolRegistry.list_tools(),
        "tool_schemas": ToolRegistry.get_schemas(),
    }


@router.get("/metrics")
async def get_runtime_metrics(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RuntimeMetric).order_by(RuntimeMetric.created_at.desc()).limit(100)
    )
    metrics = result.scalars().all()
    return [{"type": m.metric_type, "value": m.value, "unit": m.unit, "created_at": m.created_at.isoformat()} for m in metrics]


@router.get("/tools")
async def list_tools():
    return {"tools": ToolRegistry.list_tools(), "schemas": ToolRegistry.get_schemas()}


@router.post("/tool/execute")
async def execute_tool(data: dict, db: AsyncSession = Depends(get_db)):
    tool_name = data.get("tool", "")
    tool_input = data.get("input", {})
    session_id = data.get("session_id")

    result = await ToolRegistry.execute_tool(tool_name, tool_input, db)
    if session_id:
        tc = ToolCall(session_id=session_id, tool_id=tool_name, status="completed", input=tool_input, output=result)
        db.add(tc)
        await db.commit()

    return {"tool": tool_name, "result": result}


@router.get("/context")
async def get_context(repository_id: str, query: str = "", db: AsyncSession = Depends(get_db)):
    from ...ai.context.service import ContextBuilder
    builder = ContextBuilder(db)
    context = await builder.build_context(repository_id, query)
    return {"context": context, "repository_id": repository_id}


@router.get("/prompt")
async def get_prompt_info(session_id: str, db: AsyncSession = Depends(get_db)):
    sessions = SessionManager(db)
    session = await sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    conv = ConversationManager(db)
    history = await conv.get_recent(session_id)
    prompt_builder = PromptBuilder(db)
    prompt = await prompt_builder.build(
        user_prompt=history[-1]["content"] if history else "",
        repository_id=session.repository_id,
        session_history=history,
    )
    return prompt


@router.post("/chat/llm")
async def chat_with_llm(data: dict, db: AsyncSession = Depends(get_db)):
    from ...ai.providers.ollama import OllamaProvider
    from ...ai.providers.llamacpp import LlamaCppProvider
    from ...ai.providers.openai_compat import OpenAICompatibleProvider
    from ...ai.routing.router import ModelRouter

    ModelRegistry.register_provider("ollama", OllamaProvider)
    ModelRegistry.register_provider("llama.cpp", LlamaCppProvider)
    ModelRegistry.register_provider("openai-compatible", OpenAICompatibleProvider)

    provider_name = data.get("provider", "ollama")
    model = data.get("model", "qwen3-coder")
    prompt = data.get("prompt", "")
    system_prompt = data.get("system_prompt")
    task_type = data.get("task_type", "default")
    profile = data.get("profile", "balanced")
    repository_id = data.get("repository_id")
    session_id = data.get("session_id")

    provider_class = ModelRegistry.get_provider(provider_name)
    if not provider_class:
        available = ModelRegistry.list_providers()
        return {"error": f"Provider '{provider_name}' not found. Available: {available}"}

    instance = ModelRegistry.get_instance(provider_name)
    if not instance or instance.model != model:
        instance = provider_class(model=model)
        ModelRegistry.set_instance(provider_name, instance)

    if repository_id:
        from ...ai.context.service import ContextBuilder
        builder = ContextBuilder(db)
        repo_context = await builder.build_context(repository_id, prompt)
        if repo_context:
            system_prompt = (system_prompt or "") + f"\n\nRepository Context:\n{repo_context}"

    if session_id:
        from ...ai.conversation.service import ConversationManager
        conv = ConversationManager(db)
        await conv.add_message(session_id, "user", prompt)

    router = ModelRouter(ModelRegistry)
    result = await router.generate(prompt, system_prompt, task_type, profile)

    if session_id:
        conv = ConversationManager(db)
        await conv.add_message(session_id, "assistant", result)

    return {"response": result, "provider": provider_name, "model": model}


@router.post("/complete")
async def complete_text(data: dict, db: AsyncSession = Depends(get_db)):
    from ...ai.routing.router import ModelRouter

    provider_name = data.get("provider", "ollama")
    prompt = data.get("prompt", "")
    system_prompt = data.get("system_prompt")
    task_type = data.get("task_type", "default")

    provider_class = ModelRegistry.get_provider(provider_name)
    if not provider_class:
        return {"error": f"Provider '{provider_name}' not available"}

    instance = ModelRegistry.get_instance(provider_name)
    if not instance:
        instance = provider_class()
        ModelRegistry.set_instance(provider_name, instance)

    result = await instance.generate(prompt, system_prompt)
    return {"response": result}


@router.get("/providers")
async def list_providers():
    from ...ai.routing.router import ModelRouter
    router = ModelRouter(ModelRegistry)
    return {"providers": router.list_providers(), "profiles": ["fast", "balanced", "maximum_quality", "offline_low_ram", "custom"]}


@router.get("/runtime/status")
async def runtime_status():
    from ...ai.routing.router import ModelRouter
    from ...ai.registry.service import ModelRegistry

    router = ModelRouter(ModelRegistry)
    return {
        "registered_providers": ModelRegistry.list_providers(),
        "loaded_instances": ModelRegistry.list_instances(),
        "available_routes": list(router.select_provider.__globals__.get("TASK_ROUTING", {}).keys()) if hasattr(router, "select_provider") else [],
        "profiles": ["fast", "balanced", "maximum_quality", "offline_low_ram", "custom"],
    }
