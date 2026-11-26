import argparse
import base64
import json
from pathlib import Path


PRIORITIES = {
    "must": "必须改",
    "high": "优先改",
    "medium": "次优先",
    "low": "可后续优化",
    "spoken": "汇报时注意",
}
CATEGORIES = {
    "template": "模板一致性检查",
    "completeness": "方案完整性检查",
    "logic": "论述逻辑检查",
    "formal": "正式性检查",
    "evidence": "支撑性",
    "delivery": "落地性",
    "investment": "可决策性",
    "communication": "表达清晰性",
}
AUDIENCES = {
    "digital": "数字化建设牵头人",
    "business": "行政业务负责人",
    "executive": "行政一把手和二把手",
}
CHECKS = [
    "咨询顾问立场与专业判断",
    "业务语言与业务价值",
    "页内与页间逻辑",
    "交付稿完整度",
    "自然表达与具体支撑",
    "利益相关方反馈落实",
    "专业认可与开工意愿",
    "投入产出与前沿性",
    "概算依据与 AI 提效",
    "逐页对照原模板的编写要求",
    "方案完整性",
    "正文首页目标与价值",
]
STATUSES = {"pass": "通过", "issue": "发现问题", "limited": "材料受限"}
TEMPLATE_STATUSES = {**STATUSES, "extra": "补充页"}
TEMPLATE_CHECK = 10
COMPLETENESS_CHECK = 11
OBJECTIVES_CHECK = 12


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value, field):
    require(isinstance(value, str) and value.strip(), f"{field} 需要非空文字")
    return value.strip()


def indexed(records, field, label):
    result = {}
    for record in records:
        key = record[field]
        require(key not in result, f"{label}重复：{key}")
        result[key] = record
    return result


def rectangle(value):
    require(isinstance(value, list) and len(value) == 4, "标记区域需要四个归一化数值")
    require(all(type(n) in (float, int) and 0 <= n <= 1 for n in value), "标记区域超出页面")
    x, y, width, height = value
    require(width > 0 and height > 0 and x + width <= 1.0001 and y + height <= 1.0001, "标记区域超出页面")
    return value


def embed_page_image(path):
    image = path.read_bytes()
    if image.startswith(b"\x89PNG\r\n\x1a\n"):
        mime = "image/png"
    elif image.startswith(b"\xff\xd8\xff"):
        mime = "image/jpeg"
    else:
        raise ValueError(f"页面图像须为 PNG 或 JPEG：{path.name}")
    return f"data:{mime};base64," + base64.b64encode(image).decode("ascii")


def build_template_review(review, pages, findings, status):
    template_review = review.get("template_review")
    if template_review is None:
        require(status == "limited", "完成模板核对时，请附适用模板和逐页检查记录")
        return None

    source = text(template_review["source"], "模板名称和版本")
    rows = indexed(template_review["rows"], "page", "模板核对的成稿页")
    require(set(rows) == set(pages) and all(type(number) is int for number in rows),
            "模板核对需要覆盖每一张成稿页，包括补充页")
    has_content_checks = any("content_checks" in row for row in rows.values())
    checks = []
    for number, row in sorted(rows.items()):
        row_status = row["status"]
        require(row_status in TEMPLATE_STATUSES, f"第 {number} 页的模板检查结论无效")
        ids = row.get("findings", [])
        require(row_status != "issue" or ids, f"第 {number} 页的模板问题需要关联修改清单")
        for issue_id in ids:
            issue = findings.get(issue_id)
            require(issue and TEMPLATE_CHECK in issue["checks"] and
                    any(location["page"] == number for location in issue["locations"]),
                    f"第 {number} 页未找到对应的模板问题 {issue_id}")
        content_checks = row.get("content_checks", [])
        require(not has_content_checks or content_checks, f"第 {number} 页缺少逐项内容核对")
        reviewed_content = []
        for item in content_checks:
            item_status = item["status"]
            require(item_status in STATUSES, f"第 {number} 页内容核对的结论无效")
            require(item_status != "issue" or (ids and row_status in ("issue", "extra")),
                    f"第 {number} 页的内容问题需反映在本页结论及关联建议中")
            require(item_status != "limited" or row_status != "pass",
                    f"第 {number} 页仍有材料受限的核对项")
            reviewed_content.append({
                "required": text(item["required"], f"第 {number} 页应写内容"),
                "actual": text(item["actual"], f"第 {number} 页实际内容"),
                "status": STATUSES[item_status],
            })
        checks.append({
            "page": number,
            "template": text(row["template"], "对应模板页"),
            "requirement": text(row["requirement"], "对应的模板要求"),
            "status": TEMPLATE_STATUSES[row_status],
            "remark": text(row["remark"], "逐页检查结论"),
            "findings": ids,
            "contentChecks": reviewed_content,
        })
    has_issues = any(row["status"] == "issue" for row in rows.values())
    has_limits = any(row["status"] == "limited" for row in rows.values())
    expected = "issue" if has_issues else ("limited" if has_limits else "pass")
    require(status == expected, "模板逐页核对与第十项结论不一致")
    linked_ids = {issue_id for row in checks for issue_id in row["findings"]}
    require(all(TEMPLATE_CHECK not in issue["checks"] or issue_id in linked_ids
                for issue_id, issue in findings.items()),
            "请把所有涉及模板的修改建议连到逐页核对表")
    return {"source": source, "rows": checks}


def build_audience(key, label, reader):
    questions = reader.get("questions", [reader])
    require(isinstance(questions, list) and questions, f"{label}需要至少一个具体追问")
    reviewed_questions = []
    for item in questions:
        examples = item["examples"] if "examples" in item else [item["judgment"]]
        require(isinstance(examples, list) and examples, f"{label}的主问题需要原稿举证")
        reviewed_questions.append({
            "question": text(item["question"], f"{label}的追问"),
            "examples": [text(example, f"{label}的原稿举证") for example in examples],
        })
    return {
        "id": key,
        "label": label,
        "questions": reviewed_questions,
    }


def build_data(index, review, image_dir):
    pages = indexed(index["pages"], "page", "页码")
    require(bool(pages) and all(type(number) is int and number > 0 for number in pages), "请提供实际的正整数页码")
    results = indexed(review["checks"], "id", "检查项")
    has_objectives_check = OBJECTIVES_CHECK in results
    # Reports created before template checks can still be regenerated.
    if set(results) == set(range(1, TEMPLATE_CHECK)) and "template_review" not in review:
        results[TEMPLATE_CHECK] = {
            "status": "limited",
            "remark": "本次评测没有逐页对照原模板的编写说明。",
        }
    if set(results) == set(range(1, COMPLETENESS_CHECK)):
        results[COMPLETENESS_CHECK] = {
            "status": "limited",
            "remark": "本次评测未单独从模板反查全部必写内容。",
        }
    if set(results) == set(range(1, OBJECTIVES_CHECK)):
        results[OBJECTIVES_CHECK] = {
            "status": "limited",
            "remark": "本次评测未单独核查正文首页的业务目标与价值。",
        }
    require(set(results) == set(range(1, len(CHECKS) + 1)) and all(type(i) is int for i in results),
            "请提供十二条检查结论")
    readers = indexed(review["audiences"], "id", "受众")
    require(set(readers) == set(AUDIENCES), "请提供三类甲方受众的判断")
    findings = indexed(review["findings"], "id", "问题编号")
    categories = CATEGORIES if any("category" in finding for finding in findings.values()) else {"legacy": "修改建议"}
    output_pages = []
    for number, page in sorted(pages.items()):
        image = embed_page_image(image_dir / page["image"])
        output_pages.append({"page": number, "title": page.get("title") or f"第 {number} 页", "image": image})

    output_findings = []
    for key, finding in findings.items():
        text(key, "问题编号")
        priority = finding["priority"]
        require(priority in PRIORITIES, f"{key} 优先级无效")
        category = finding.get("category", "legacy")
        require(category in categories, f"{key} 检查分类缺失或无效")
        related_checks = finding["checks"]
        require(bool(related_checks) and all(type(i) is int and i in results for i in related_checks), f"{key} 检查项无效")
        audience_ids = finding["audiences"]
        require(bool(audience_ids) and set(audience_ids) <= set(AUDIENCES), f"{key} 受众无效")
        require(bool(finding["locations"]), f"{key} 至少需要一个页码定位")
        locations = []
        for location in finding["locations"]:
            number = location["page"]
            require(type(number) is int and number in pages, f"{key} 引用了不存在的第 {number} 页")
            require(not ("block" in location and "rect" in location), f"{key} 的同一位置只能选一种矩形来源")
            page = pages[number]
            blocks = indexed(page.get("blocks", []), "id", "页面文字块")
            anchor_id = location.get("block")
            require(anchor_id is None or anchor_id in blocks, f"{key} 第 {number} 页定位不存在：{anchor_id}")
            anchor = blocks.get(anchor_id)
            rect = anchor["rect"] if anchor else location.get("rect")
            quote = location.get("quote", "").strip()
            note = location.get("note", "").strip()
            require(quote or note, f"{key} 第 {number} 页需有原文或位置说明")
            searchable = anchor["text"] if anchor else page.get("text", "")
            require(not quote or " ".join(quote.split()) in " ".join(searchable.split()),
                    f"{key} 第 {number} 页的引文和定位文字对不上")
            locations.append({
                "page": number,
                "rect": rectangle(rect) if rect is not None else None,
                "quote": quote,
                "note": note,
            })
        output_findings.append({
            **{field: text(finding[field], field) for field in ("id", "title", "observed", "impact", "recommendation")},
            "category": category,
            "priority": priority,
            "checks": sorted(set(related_checks)),
            "audiences": list(dict.fromkeys(audience_ids)),
            "locations": locations,
        })
    category_rank = {category: i for i, category in enumerate(categories)}
    priority_rank = {priority: i for i, priority in enumerate(PRIORITIES)}
    output_findings.sort(key=lambda finding: (category_rank[finding["category"]], priority_rank[finding["priority"]]))
    for number, result in results.items():
        require(result["status"] in STATUSES, f"检查项 {number} 的结论无效")
        issue_found = any(number in f["checks"] and f["priority"] != "spoken" for f in output_findings)
        require(result["status"] != "pass" or not issue_found, f"检查项 {number} 标为通过但仍有修改项")
        require(result["status"] != "issue" or issue_found, f"检查项 {number} 标为有问题但没有对应整改项")

    template_review = build_template_review(review, pages, findings, results[TEMPLATE_CHECK]["status"])
    basis = [text(item, "评测依据") for item in review["basis"]]
    require(bool(basis), "请提供评测依据")
    must = any(item["priority"] == "must" for item in output_findings)
    limited = any(item["status"] == "limited" for number, item in results.items()
                  if number != OBJECTIVES_CHECK or has_objectives_check)
    verdict = "修订后再汇报" if must else ("关键证据待补" if limited else "可进入汇报")
    return {
        "title": text(review["title"], "报告标题"),
        "source": text(index["source"], "成稿名称"),
        "summary": text(review["summary"], "评测摘要"),
        "nextDecision": text(review["next_decision"], "下一步"),
        "verdict": verdict,
        "basis": basis,
        "limits": [text(item, "评测范围") for item in review.get("limits", [])],
        "pages": output_pages,
        "categories": categories,
        "priorities": PRIORITIES,
        "findings": output_findings,
        "templateReview": template_review,
        "checks": [
            {"id": number, "label": label, "status": STATUSES[results[number]["status"]],
             "remark": text(results[number]["remark"], "检查结论")}
            for number, label in enumerate(CHECKS, 1)
        ],
        "audiences": [
            build_audience(key, label, readers[key])
            for key, label in AUDIENCES.items()
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="生成带逐页定位的解决方案评测报告")
    parser.add_argument("pages", type=Path)
    parser.add_argument("review", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    index = json.loads(args.pages.read_text(encoding="utf-8"))
    review = json.loads(args.review.read_text(encoding="utf-8"))
    data = build_data(index, review, args.pages.resolve().parent)
    template = Path(__file__).resolve().parents[1] / "assets" / "report.html"
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", r"\u003c")
    html = template.read_text(encoding="utf-8").replace("__REVIEW_DATA__", payload, 1)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")
    print(f"已生成报告：{len(data['pages'])} 页、{len(data['findings'])} 项，{data['verdict']}")


if __name__ == "__main__":
    main()
