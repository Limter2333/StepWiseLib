Agent Skill探索

Agent Skill（智能体技能）是什么？
指的是赋予 AI Agent（智能体）执行特定任务、操作外部工具或理解特定领域知识的能力模块。
简单来说，如果把大模型（LLM）比作一个拥有高智商但“手无缚鸡之力”的大脑，那么 Skill 就是给这个大脑安装的“手”、“眼睛”或“专业手册”，让它能真正干活。

核心定义：什么是 Agent Skill？
Agent Skill 是将复杂的提示词工程（Prompt Engineering）、外部知识库（Reference）、执行代码/脚本（Script）以及API 调用逻辑封装成的一个标准化、可复用、可插拔的单元。
传统方式：把所有指令写在一个巨大的 Prompt 里，模型容易迷失，且难以维护。
Skill 方式：将能力拆解为独立的技能包（例如 search_web.skill, query_database.skill, generate_code.skill）。Agent 根据用户意图，动态加载所需的技能。

为什么需要 Skill？（解决什么问题）
Agent Skill 本质上是将 Prompt（提示词） + Knowledge（知识） + Code（执行代码） 封装成一个标准化的文件夹（通常包含 SKILL.md）。它主要解决了以下四大核心问题：
1. 解决“不可控”与“幻觉”问题 -> 提供确定性 SOP
   问题：通用大模型不懂企业内部的潜规则或严格流程。
   Skill 方案：Skill 文件中包含了该任务专属的 SOP（标准作业程序） 和 参考文档（References）。
   例子：一个“报销审核 Skill”会明确规定“超过 5000 元必须附带总监邮件”。AI 加载这个 Skill 后，就会严格按此规则执行，不再自由发挥，从而消除幻觉。
2. 解决“上下文爆炸”与成本问题 -> 渐进式披露 (Progressive Disclosure)
   问题：把所有工具说明书都塞给 AI，既贵又慢，还容易让 AI 晕头转向。
   Skill 方案：采用 动态加载 机制。
   机制：AI 平时只保留核心能力。只有当用户说“帮我查航班”时，AI 才动态挂载“订票 Skill”的文档和代码。
   效果：极大节省 Token 成本，提高推理速度和准确率。
3. 解决“重复造轮子”与协作问题 -> 标准化与可复用
   问题：A 团队写的“搜索技能”B 团队用不了，因为代码结构和 Prompt 格式完全不同。
   Skill 方案：定义了统一的文件结构（如 SKILL.md, script.py, assets/）。
   效果：技能变成了可共享的“安装包”。开发者可以像在手机 App Store 下载应用一样，从社区下载“SQL 查询 Skill”或“PPT 制作 Skill”，直接插入自己的 Agent 中使用。
4. 解决“无法执行复杂操作”问题 -> 逻辑与执行的解耦
   问题：单纯靠 Prompt 很难让 AI 稳定地执行多步代码或调用复杂 API。
   Skill 方案：将决策逻辑（由 LLM 负责）与执行脚本（由 Python/JS 代码负责）分离。
   结构：SKILL.md 告诉 AI“什么时候用我”，而配套的 script.py 负责具体怎么跑代码。这让 AI 既能理解意图，又能通过确定的代码完成复杂任务（如操作数据库、生成图表）。

工作流程示例：
用户问：“帮我查一下上季度的销售额并生成报表。”
Agent 分析意图，识别到需要 query_sales_db 和 generate_excel 两个技能。
Agent 动态加载这两个 Skill 的 SKILL.md 和 script.py。
执行脚本获取数据，利用 Skill 中的模板生成报表。
返回结果给用户。

总结：
Agent Skill 是随着 AI Agent（智能体）从“玩具”走向“生产力工具”的过程中，为了解决大模型落地难、不可控、上下文爆炸等核心痛点而诞生的一种标准化工程范式。

参考视频：
【闪客】一口气拆穿Skill/MCP/RAG/Agent/OpenClaw底层逻辑 -> https://www.bilibili.com/video/BV1cGigBQE6n
7分钟速通Agent Skills是什么？跟MCP|Workflow|Command|Prompt有什么关系？ -> https://www.bilibili.com/video/BV162cPzhEGU
Agent Skill 从使用到原理，一次讲清 -> https://www.bilibili.com/video/BV1ojfDBSEPv