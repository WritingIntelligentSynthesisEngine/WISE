# ai/chains/classify_intentions_chain.py
from typing import Any, Dict

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.base import RunnableSerializable

from utils.prompt_util import classify_intention_prompt


parser: StrOutputParser = StrOutputParser()


def classify_intention(
    llm: Any,
    user_input: str,
    intentions: Dict[str, str],
) -> str:
    """根据用户输入和允许的意图字典返回一个分类后的意图字符串"""

    # 构建 Prompt Template
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", classify_intention_prompt),
            ("human", f"用户输入：{ user_input }"),
        ],
        template_format="jinja2",
    )
    # 构建 Chain
    chain: RunnableSerializable[Dict[Any, Any], str] = prompt | llm | parser
    # 调用 Chain
    result: str = chain.invoke(
        {
            "intentions": intentions,
        }
    )
    # 返回清理后的结果
    return result.strip()
