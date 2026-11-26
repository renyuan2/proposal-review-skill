# 报告输入格式

`pages.json` 的 `source` 是甲方向材料的文件名或标题，`pages` 按实际阅读顺序排列。模板 HTML 由采集脚本生成。其他文档用已核对的逐页 PNG 或 JPEG 建立相同索引。页码采用实际文件的正整数页序，正文中的印刷页码可在证据说明补充。

```json
{
  "source": "园区方案成稿.html",
  "pages": [
    {
      "page": 1,
      "title": "现状业务问题",
      "image": "page-01.png",
      "text": "归纳实际业务问题",
      "blocks": [{"id": "b1", "text": "归纳实际业务问题", "rect": [0.10, 0.15, 0.42, 0.08]}]
    }
  ]
}
```

图片路径相对于 `pages.json`。校验截图、逐页文本和页码是否属于同一版本。归一化矩形为左、上、宽、高，取值 0 至 1，以截图内容为准。图像快照中不可见的内容，用页级定位并说明查看位置。页面缺失时定位到应承接它的实际存在页。

`review.json` 包含以下字段：

- `title`、`summary`、`next_decision` 为字符串。摘要写基于材料的交付判断。下一步写应先解决或明确批准的具体事项。
- `basis` 为非空字符串数组，列实际审阅文件、页数及主要依据。`limits` 为字符串数组，列证据或范围限制。输入阶段有缺页时在这里记录。
- `audiences` 为三条对象组成的数组，ID 使用 `digital`、`business`、`executive`。每条用 `question` 写一个代表该角色判断的主问题，用 `examples` 写两三个成稿例子，每例注明页码和缺口。
- 新报告的 `checks` 包含十二条对象。每条填写整数 `id`（1 至 12）、`status`（`pass`、`issue`、`limited`）及 `remark`（检查结论）。第 10 条记逐页模板对照，第 11 条记按模板反查出的缺页、缺栏和缺项。第 12 条注明正文首页实际页码，记录目标的业务价值、与主要建设内容的对应关系，并列出并列短句的逐句字数。发现问题时，关联第 12 项并把首个 `locations` 落到正文首页，后文冲突或支撑页可追加定位。旧报告可按原数据重渲染，未做的新检查显示为材料受限。
- `template_review` 记录实际模板及逐页对照。填写 `source`（文件名及适用版本）、`rows`（每个成稿页一条）。每条包含 `page`、`template`（模板参考页和用途）、`requirement`（适用要求摘要）、`status`（`pass`、`issue`、`limited` 或 `extra`）、`remark`（实际结论）。发现偏离时，用 `findings` 写关联建议编号数组。关联建议须包含检查项 10，并定位到该页。补充页用 `extra`。缺适用模板时可以省略 `template_review`，第 10 项标 `limited` 并说明缺少的范围。
- 新报告每个成稿页均填写 `content_checks`，按此页适用栏目逐项记录 `required`（模板应写什么）、`actual`（本页实际写了什么，错位或缺项在哪里）、`status`（`pass`、`issue` 或 `limited`）。通过页也填实际依据。问题项写进本页结论并关联修改建议。
- `findings` 为问题或汇报提示数组。每条填一个主要类别 `category`。代码为 `template`（模板一致性）、`completeness`（方案完整性）、`logic`（论述逻辑）、`formal`（正式性）、`evidence`（支撑性）、`delivery`（落地性）、`investment`（可决策性）、`communication`（表达清晰性，含 AI 味）。每类内按五级优先级排列。
- `observed` 是「判断依据」，直接写哪页哪处出了什么问题。`impact` 写实际影响，`recommendation` 写改法。用最少的句子保留足够证据与具体动作，已能从原页或逐页对照查到的细节不重复铺陈。

```json
{
  "id": "F01",
  "category": "investment",
  "priority": "must",
  "checks": [3, 9],
  "audiences": ["business", "executive"],
  "title": "本期范围尚无分项概算",
  "observed": "范围页列出拟建能力，成稿未提供可核算的实施及概算页。",
  "impact": "审批人无法核对范围与拟投金额。",
  "recommendation": "按实施模块补齐计价任务、数量、单价依据、AI 提效和分项汇总。",
  "locations": [
    {"page": 1, "block": "b1", "quote": "归纳实际业务问题", "note": "这一页提出的问题应在本期预算中找到对应项。"}
  ]
}
```

每条至少一个 `locations`，首条作为默认跳转。可以使用块 ID、实际核实过的 `rect`，或仅用页码定位。一处最多选一种矩形来源。原句如提供，应逐字对应截图或索引文本。对缺页、缺项、图示或非文字问题，用 `note` 说明所指位置。报告把可见矩形标在截图上，页级定位以整页外框显示。`note` 可以解释证据和问题之间的关系。
