这是一个非常特殊的技能，深入到了解决基于HTTP接口做自动化分析、设计、业务场景组织、测试用例组织、测试报告增强等领域问题，该技能
描述并提供了最佳实践的泛化的解决方案。

为了遵循渐进式披露原则，将原SKILL.md大而全的内容做了拆解，先提供整体指导，再详细说明各方面规范。这样可以更方便地帮助理解和使用这个技能。因此，绝不能仅仅引入SKILL.md这个单一文件，而是同时将下述文件全量引入 :

```text
http-api-tester
├─ SKILL.md
├─ procedure.md
├─ templates/
│  ├─ report.html
│  ├─ report_enhanced.html
│  ├─ report.json
│  ├─ enhanced_report_wireframe.excalidraw
│  └─ enhanced_report_wireframe_v2_.excalidraw
├─ assets/
│  ├─ css/
│  ├─ js/
│  └─ webfonts/
├─ reference/
│  ├─ lang-support.md
│  ├─ report-format.md
│  ├─ test-design.md
│  ├─ 产物文件汇总清单.md (所有要求产出的文件清单)
│  └─ 静态探针分析参考事项.md
├─ adapters/
│  └─ python_adapter.py
├─ examples/
│  └─ python_report.json
├─ schemas/
│  └─ report_data_schema.json
├─ README.md (技能文件信息的关键注释)
├─ SKILL-whole.md (原技能的完整内容)
└─ about.md (建议, 是原完整SKILL.md的介绍)
```

**📋 reference/产物文件汇总清单.md**：该文件汇总了技能执行过程中要求产出的所有文件（包括代码文件、分析文档、测试报告等），包含按执行环节分类的产物列表、文件名、用途、指定路径以及总文件数量统计。
