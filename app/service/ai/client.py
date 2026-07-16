"""通用 AI 接口请求客户端。

封装 httpx chat/completions（OpenAI 兼容）请求、响应解析与日志。单股分析 /
换仓决策 / 复盘对话均复用此客户端，与分析框架、prompt 组装解耦。
"""
import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger("app.ai.client")


class AIConfigError(RuntimeError):
    """AI 服务未配置（缺 URL/KEY）。"""


class AIResponseError(RuntimeError):
    """AI 响应解析失败。"""


async def chat(
    system_prompt: str,
    user_prompt: str,
    *,
    model: str | None = None,
    max_tokens: int = 128000,
    timeout: float = 120.0,
) -> str:
    """调用 chat/completions，返回正文文本。

    兼容两种响应结构：
    - ARK / 火山方舟风格：data["content"][0]["text"]
    - OpenAI 风格：data["choices"][0]["message"]["content"]
    """
    if not settings.AI_API_URL or not settings.AI_API_KEY:
        raise AIConfigError("AI 服务未配置：AI_API_URL / AI_API_KEY 缺失")

    used_model = model or settings.AI_API_MODEL
    payload = {
        "model": used_model,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    logger.info("[AI] POST %s model=%s", settings.AI_API_URL, used_model)
    logger.info("[AI] system_prompt (len=%d):\n%s", len(system_prompt), system_prompt)
    logger.info("[AI] user_prompt (len=%d):\n%s", len(user_prompt), user_prompt)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            settings.AI_API_URL,
            headers={
                "Authorization": f"Bearer {settings.AI_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        logger.info("[AI] response status=%s", response.status_code)
        logger.info("[AI] response body (truncated): %s", response.text[:2000])
        response.raise_for_status()
        try:
            data = response.json()
        except Exception as exc:
            logger.exception("[AI] failed to decode JSON: %s", exc)
            raise AIResponseError(f"响应非 JSON: {exc}") from exc

    logger.info(
        "[AI] response top-level keys: %s",
        list(data.keys()) if isinstance(data, dict) else type(data),
    )

    text = _extract_text(data)
    if not text:
        logger.warning(
            "[AI] empty analysis_text. full response=%s",
            json.dumps(data, ensure_ascii=False)[:4000],
        )
    else:
        logger.info("[AI] analysis_text length=%d, preview=%s", len(text), text[:200])
    return text


def _extract_text(data) -> str:
    """从响应中提取正文，兼容 ARK 与 OpenAI 两种结构。"""
    if not isinstance(data, dict):
        return ""

    content = data.get("content")
    if isinstance(content, list) and content and isinstance(content[0], dict):
        text = content[0].get("text", "") or ""
        if text:
            return text

    choices = data.get("choices")
    if isinstance(choices, list) and choices and isinstance(choices[0], dict):
        msg = choices[0].get("message")
        if isinstance(msg, dict):
            return msg.get("content", "") or ""

    return ""
