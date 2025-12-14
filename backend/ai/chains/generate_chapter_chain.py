# ai/chains/generate_chapter_chain.py
from typing import Any, Optional, List, Dict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables.base import RunnableSerializable
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from ai.prompts import generate_chapter_prompt


parser: StrOutputParser = StrOutputParser()


def generate_chapter(
    llm: Any,
    settings: str,
    current_number: int,
    previous_outlines: List[str],
    previous_chapters: List[str],
    current_outline: Optional[str],
) -> str:
    """生成完整章节"""

    # 构建历史消息
    context_size: int = len(previous_chapters)
    history: List[HumanMessage | AIMessage] = []
    for i in range(context_size):
        history.append(HumanMessage(f"第 {current_number-context_size+i} 章大纲：\n\n{previous_outlines[i]}\n\n根据大纲完成正文："))
        history.append(AIMessage(previous_chapters[i]))
    # 构建 Prompt Template
    prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
        [
            SystemMessage(generate_chapter_prompt),
            HumanMessage(f"这是小说的设定，请仔细阅读：\n\n{settings}"),
            AIMessage("好的，我已阅读完毕，并将严格遵守设定完成创作！"),
            MessagesPlaceholder(variable_name="history"),
            HumanMessage(f"第 {current_number} 章大纲：\n\n{current_outline}\n\n根据大纲完成正文："),
        ],
        template_format="jinja2",
    )
    input_data: Dict[str, Any] = {"history": history}
    # 构建 Chain
    chain: RunnableSerializable[Dict[Any, Any], str] = prompt | llm | parser
    result: str = ""
    # 调用 Chain
    for chunk in chain.stream(input_data):
        from utils.debug_util import debug

        debug(chunk, end="", flush=True)
        result += chunk
    # 返回清理后的结果
    return result.strip()
