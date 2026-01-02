# ai/chains/generate_outline_chain.py
from typing import Any, List, Dict, AsyncGenerator


from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables.base import RunnableSerializable
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from ai.prompts import generate_outline_prompt


parser: StrOutputParser = StrOutputParser()


async def generate_outline(
    llm: Any,
    settings: str,
    current_number: int,
    previous_outlines: List[str],
) -> AsyncGenerator[str, None]:
    """生成小说大纲(流式)"""

    # 构建历史消息
    context_size: int = len(previous_outlines)
    history: List[HumanMessage | AIMessage] = []
    for i in range(context_size):
        history.append(HumanMessage(content=f"完成第 {current_number - context_size + i} 章的大纲："))
        history.append(AIMessage(content=previous_outlines[i]))
    # 构建 Prompt Template
    prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
        [
            SystemMessage(generate_outline_prompt),
            HumanMessage(f"这是小说的设定，请仔细阅读：\n\n{settings}"),
            AIMessage("好的，我已阅读完毕，并将严格遵守设定完成创作！"),
            MessagesPlaceholder(variable_name="history"),
            HumanMessage(f"完成第 {current_number} 章的大纲："),
        ],
        template_format="jinja2",
    )
    input_data: Dict[str, Any] = {"history": history}
    # 构建 Chain
    chain: RunnableSerializable[Dict[Any, Any], str] = prompt | llm | parser
    # 调用 Chain 并流式返回每个 chunk
    async for chunk in chain.astream(input_data):
        yield chunk
