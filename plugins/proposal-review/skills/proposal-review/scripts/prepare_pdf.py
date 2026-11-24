import argparse
import json
from pathlib import Path

import pdfplumber


def read_pdf(source, output):
    output.mkdir(parents=True, exist_ok=True)
    pages = []
    with pdfplumber.open(source) as pdf:
        for number, pdf_page in enumerate(pdf.pages, 1):
            x0, y0, x1, y1 = pdf_page.bbox
            width, height = x1 - x0, y1 - y0
            blocks = []
            for line in pdf_page.extract_text_lines(return_chars=False):
                left = max(0, (line["x0"] - x0) / width)
                top = max(0, (line["top"] - y0) / height)
                right = min(1, (line["x1"] - x0) / width)
                bottom = min(1, (line["bottom"] - y0) / height)
                if left < right and top < bottom:
                    blocks.append({
                        "id": f"b{len(blocks) + 1}", "text": line["text"],
                        "rect": [left, top, right - left, bottom - top],
                    })
            image = f"page-{number:02d}.png"
            pdf_page.to_image(resolution=125, antialias=True, force_mediabox=True).save(output / image, quantize=False)
            pages.append({
                "page": number,
                "title": blocks[0]["text"] if blocks else f"第 {number} 页",
                "image": image,
                "text": pdf_page.extract_text() or "",
                "blocks": blocks,
            })
    (output / "pages.json").write_text(
        json.dumps({"source": source.name, "pages": pages}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"已读取 {len(pages)} 页。逐页图像与定位数据保存在 {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="为 PDF 评测生成逐页截图与文字定位")
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    read_pdf(args.source.resolve(), args.output.resolve())
