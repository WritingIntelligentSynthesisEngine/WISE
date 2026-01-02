from pydantic import SecretStr

from langchain_deepseek import ChatDeepSeek


async def construct_llm(
    api_key: SecretStr,
) -> ChatDeepSeek:

    return ChatDeepSeek(
        model="deepseek-reasoner",
        temperature=1.5,
        api_key=api_key,
    )
