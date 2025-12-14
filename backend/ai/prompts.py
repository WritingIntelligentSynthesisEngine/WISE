# ai/prompts.py
from pathlib import Path
from utils.file_util import read_text_file


prompts_dir: Path = Path("ai/templates/prompts")

# 意图分类
classify_intention_prompt: str = read_text_file(prompts_dir / "意图分类.jinja2")
# 生成大纲
generate_outline_prompt: str = read_text_file(prompts_dir / "生成大纲.jinja2")
# 生成正文
generate_chapter_prompt: str = read_text_file(prompts_dir / "生成正文.jinja2")
