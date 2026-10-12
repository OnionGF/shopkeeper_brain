import os
import re
import json
import base64
from pathlib import Path
from loguru import logger
from mineru import parse


def _extract_images_from_md(md_path: Path, image_dir: Path):
    """把 markdown 里的 base64 内嵌图片拆成独立文件"""
    image_dir.mkdir(parents=True, exist_ok=True)
    md_text = md_path.read_text(encoding="utf-8")

    # 匹配 ![](data:image/png;base64,xxxx)
    pattern = re.compile(r'!\[.*?\]\(data:image/(\w+);base64,(.+?)\)')
    matches = list(pattern.finditer(md_text))

    if not matches:
        logger.info("markdown 中没有内嵌图片")
        return

    for i, match in enumerate(matches, 1):
        ext = match.group(1).lower()
        if ext == "jpeg":
            ext = "jpg"
        img_data = base64.b64decode(match.group(2))
        img_path = image_dir / f"{md_path.stem}_img{i}.{ext}"
        img_path.write_bytes(img_data)

        # 把 md 里的 base64 替换成相对路径
        md_text = md_text.replace(
            match.group(0),
            f"![img{i}](images/{img_path.name})"
        )

    md_path.write_text(md_text, encoding="utf-8")
    logger.info(f"提取了 {len(matches)} 张图片到 {image_dir}")


def parse_doc(path_list: list[Path], output_dir: str, **kwargs):
    os.environ["MINERU_MODEL_SOURCE"] = "local"
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    for path in path_list:
        logger.info(f"开始解析: {path}")
        result = parse(str(path), tier="standard")

        # 写 markdown
        md_text = result.markdown()
        md_file = out_path / f"{path.stem}.md"
        md_file.write_text(md_text, encoding="utf-8")

        # 提取内嵌图片到 images/ 目录
        image_dir = out_path / "images"
        _extract_images_from_md(md_file, image_dir)

        # 写 middle.json
        middle = result.middle_json
        middle_file = out_path / f"{path.stem}_middle.json"
        middle_file.write_text(
            json.dumps(middle, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8"
        )

        logger.info(f"解析完成，输出目录: {out_path}")
