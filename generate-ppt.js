const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");

// Color palette: Teal Trust (learning/knowledge theme)
const COLORS = {
  primary: "028090",      // teal
  secondary: "00A896",    // seafoam
  accent: "02C39A",       // mint
  dark: "1E3A5F",         // navy
  light: "F0F9F7",        // light mint
  white: "FFFFFF",
  gray: "64748B",
  darkGray: "334155",
  bg: "F8FAFC"
};

// Icon rendering helper
const iconCache = {};
async function iconToBase64Png(IconComponent, color, size = 256) {
  const key = `${IconComponent.name}-${color}-${size}`;
  if (iconCache[key]) return iconCache[key];
  const svg = ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) })
  );
  const pngBuffer = await sharp(Buffer.from(svg)).png().toBuffer();
  iconCache[key] = "image/png;base64," + pngBuffer.toString("base64");
  return iconCache[key];
}

// Shadow factory (avoid reuse mutation issue)
const makeShadow = () => ({ type: "outer", blur: 4, offset: 2, angle: 135, color: "000000", opacity: 0.1 });

async function createPresentation() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.title = "LangChain + LangGraph 学习路径";
  pres.author = "AI Assistant";

  // ========== Slide 1: Cover ==========
  let slide1 = pres.addSlide();
  slide1.background = { color: COLORS.dark };

  // Decorative circles
  slide1.addShape(pres.shapes.OVAL, {
    x: -1.5, y: -1, w: 4, h: 4, fill: { color: COLORS.primary, transparency: 70 }
  });
  slide1.addShape(pres.shapes.OVAL, {
    x: 8, y: 3.5, w: 3, h: 3, fill: { color: COLORS.secondary, transparency: 70 }
  });

  slide1.addText("LangChain + LangGraph", {
    x: 0.5, y: 1.8, w: 9, h: 0.8,
    fontSize: 40, fontFace: "Arial Black", color: COLORS.white, bold: true
  });
  slide1.addText("实战学习路径", {
    x: 0.5, y: 2.6, w: 9, h: 0.6,
    fontSize: 32, fontFace: "Arial", color: COLORS.accent
  });
  slide1.addText("双项目对照 · 边做边学 · 产出与成长并重", {
    x: 0.5, y: 3.8, w: 9, h: 0.5,
    fontSize: 16, fontFace: "Calibri", color: COLORS.gray
  });

  // ========== Slide 2: User Profile ==========
  let slide2 = pres.addSlide();
  slide2.background = { color: COLORS.bg };

  slide2.addText("用户画像", {
    x: 0.5, y: 0.4, w: 9, h: 0.6,
    fontSize: 28, fontFace: "Arial", color: COLORS.dark, bold: true, margin: 0
  });

  // Profile cards
  const profiles = [
    { title: "学习方式", content: "Vibe Coding 从零搭建" },
    { title: "技术文档", content: "LangChain / LangGraph 文档已阅读" },
    { title: "项目经验", content: "自建 Multi-Agent System (90% 完成)" },
    { title: "核心诉求", content: "产出成果 + 系统性学习" }
  ];

  profiles.forEach((p, i) => {
    const row = Math.floor(i / 2);
    const col = i % 2;
    const x = 0.5 + col * 4.7;
    const y = 1.3 + row * 1.9;

    slide2.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 4.3, h: 1.5,
      fill: { color: COLORS.white }, shadow: makeShadow()
    });
    slide2.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 0.08, h: 1.5, fill: { color: COLORS.primary }
    });
    slide2.addText(p.title, {
      x: x + 0.25, y: y + 0.2, w: 3.8, h: 0.4,
      fontSize: 14, fontFace: "Calibri", color: COLORS.primary, bold: true, margin: 0
    });
    slide2.addText(p.content, {
      x: x + 0.25, y: y + 0.65, w: 3.8, h: 0.7,
      fontSize: 16, fontFace: "Calibri", color: COLORS.darkGray, margin: 0
    });
  });

  // ========== Slide 3: Pain Points ==========
  let slide3 = pres.addSlide();
  slide3.background = { color: COLORS.bg };

  slide3.addText("核心痛点", {
    x: 0.5, y: 0.4, w: 9, h: 0.6,
    fontSize: 28, fontFace: "Arial", color: COLORS.dark, bold: true, margin: 0
  });

  const pains = [
    { icon: "?", title: "名词不理解", desc: "LCEL、Retriever、Chain...\n每个词都认识，串联不起来" },
    { icon: "!", title: "容易忘记", desc: "看完文档，过几天就忘\n缺乏实践巩固" },
    { icon: "✗", title: "代码不理解", desc: "跑通了，但不知道为什么\n为什么要这么设计" },
    { icon: "?", title: "缺项目经验", desc: "自学成才，工作经验少\n难以展示能力" }
  ];

  pains.forEach((p, i) => {
    const x = 0.5 + i * 2.35;
    slide3.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.3, w: 2.15, h: 3.8,
      fill: { color: COLORS.white }, shadow: makeShadow()
    });
    slide3.addShape(pres.shapes.OVAL, {
      x: x + 0.7, y: 1.6, w: 0.75, h: 0.75,
      fill: { color: COLORS.primary }
    });
    slide3.addText(p.icon, {
      x: x + 0.7, y: 1.68, w: 0.75, h: 0.6,
      fontSize: 24, fontFace: "Arial", color: COLORS.white, bold: true, align: "center", margin: 0
    });
    slide3.addText(p.title, {
      x: x + 0.15, y: 2.55, w: 1.85, h: 0.5,
      fontSize: 14, fontFace: "Calibri", color: COLORS.dark, bold: true, align: "center", margin: 0
    });
    slide3.addText(p.desc, {
      x: x + 0.15, y: 3.1, w: 1.85, h: 1.8,
      fontSize: 12, fontFace: "Calibri", color: COLORS.gray, align: "center", margin: 0
    });
  });

  // ========== Slide 4: Two Pronged Strategy ==========
  let slide4 = pres.addSlide();
  slide4.background = { color: COLORS.bg };

  slide4.addText("两条腿走路策略", {
    x: 0.5, y: 0.4, w: 9, h: 0.6,
    fontSize: 28, fontFace: "Arial", color: COLORS.dark, bold: true, margin: 0
  });

  // Left card
  slide4.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.2, w: 4.3, h: 4,
    fill: { color: COLORS.white }, shadow: makeShadow()
  });
  slide4.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.2, w: 4.3, h: 0.6, fill: { color: COLORS.primary }
  });
  slide4.addText("产出侧", {
    x: 0.5, y: 1.28, w: 4.3, h: 0.5,
    fontSize: 16, fontFace: "Arial", color: COLORS.white, bold: true, align: "center", margin: 0
  });
  slide4.addText("继续完善 Multi-Agent System", {
    x: 0.7, y: 2.0, w: 3.9, h: 0.4,
    fontSize: 14, fontFace: "Calibri", color: COLORS.dark, bold: true, margin: 0
  });
  slide4.addText([
    { text: "快速产出可运行成果", options: { bullet: true, breakLine: true } },
    { text: "积累项目经验", options: { bullet: true, breakLine: true } },
    { text: "充实作品集 / 求职证明", options: { bullet: true, breakLine: true } },
    { text: "已有 90% 基础，不推倒重来", options: { bullet: true } }
  ], {
    x: 0.7, y: 2.5, w: 3.9, h: 2.5,
    fontSize: 13, fontFace: "Calibri", color: COLORS.gray, margin: 0
  });

  // Right card
  slide4.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 1.2, w: 4.3, h: 4,
    fill: { color: COLORS.white }, shadow: makeShadow()
  });
  slide4.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 1.2, w: 4.3, h: 0.6, fill: { color: COLORS.secondary }
  });
  slide4.addText("学习侧", {
    x: 5.2, y: 1.28, w: 4.3, h: 0.5,
    fontSize: 16, fontFace: "Arial", color: COLORS.white, bold: true, align: "center", margin: 0
  });
  slide4.addText("边做边学，深入理解", {
    x: 5.4, y: 2.0, w: 3.9, h: 0.4,
    fontSize: 14, fontFace: "Calibri", color: COLORS.dark, bold: true, margin: 0
  });
  slide4.addText([
    { text: "通过项目理解底层原理", options: { bullet: true, breakLine: true } },
    { text: "对照参考项目找差异", options: { bullet: true, breakLine: true } },
    { text: "遇到问题追根究底", options: { bullet: true, breakLine: true } },
    { text: "逐步积累系统性知识", options: { bullet: true } }
  ], {
    x: 5.4, y: 2.5, w: 3.9, h: 2.5,
    fontSize: 13, fontFace: "Calibri", color: COLORS.gray, margin: 0
  });

  // Arrow
  slide4.addText("→", {
    x: 4.5, y: 2.8, w: 0.5, h: 0.6,
    fontSize: 32, fontFace: "Arial", color: COLORS.accent, align: "center", margin: 0
  });

  // ========== Slide 5: Dual Project Learning ==========
  let slide5 = pres.addSlide();
  slide5.background = { color: COLORS.bg };

  slide5.addText("双项目对照学习法", {
    x: 0.5, y: 0.4, w: 9, h: 0.6,
    fontSize: 28, fontFace: "Arial", color: COLORS.dark, bold: true, margin: 0
  });

  // Left: Existing project
  slide5.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.2, w: 3.8, h: 3.9,
    fill: { color: COLORS.primary }, shadow: makeShadow()
  });
  slide5.addText("现有项目", {
    x: 0.5, y: 1.4, w: 3.8, h: 0.5,
    fontSize: 18, fontFace: "Arial", color: COLORS.white, bold: true, align: "center", margin: 0
  });
  slide5.addText("G:\\claude_code_project", {
    x: 0.7, y: 1.9, w: 3.4, h: 0.4,
    fontSize: 11, fontFace: "Consolas", color: COLORS.accent, margin: 0
  });
  slide5.addText([
    { text: "成熟稳定 90% 完成", options: { bullet: true, breakLine: true } },
    { text: "13 个 Agent 分工", options: { bullet: true, breakLine: true } },
    { text: "712 文档已索引", options: { bullet: true, breakLine: true } },
    { text: "意图识别 / 重排序", options: { bullet: true } }
  ], {
    x: 0.7, y: 2.4, w: 3.4, h: 2.5,
    fontSize: 13, fontFace: "Calibri", color: COLORS.white, margin: 0
  });

  // Middle: Comparison
  slide5.addText("VS", {
    x: 4.5, y: 2.8, w: 1, h: 0.6,
    fontSize: 20, fontFace: "Arial", color: COLORS.gray, bold: true, align: "center", margin: 0
  });

  // Right: New project
  slide5.addShape(pres.shapes.RECTANGLE, {
    x: 5.7, y: 1.2, w: 3.8, h: 3.9,
    fill: { color: COLORS.secondary }, shadow: makeShadow()
  });
  slide5.addText("新项目", {
    x: 5.7, y: 1.4, w: 3.8, h: 0.5,
    fontSize: 18, fontFace: "Arial", color: COLORS.white, bold: true, align: "center", margin: 0
  });
  slide5.addText("LangChain + Claude API", {
    x: 5.9, y: 1.9, w: 3.4, h: 0.4,
    fontSize: 11, fontFace: "Consolas", color: COLORS.white, margin: 0
  });
  slide5.addText([
    { text: "从 0 开始实战", options: { bullet: true, breakLine: true } },
    { text: "遇到问题 → 对照参考", options: { bullet: true, breakLine: true } },
    { text: "理解差异 → 积累经验", options: { bullet: true, breakLine: true } },
    { text: "成功迁移 / 失败不伤根基", options: { bullet: true } }
  ], {
    x: 5.9, y: 2.4, w: 3.4, h: 2.5,
    fontSize: 13, fontFace: "Calibri", color: COLORS.white, margin: 0
  });

  // Bottom note
  slide5.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 5.2, w: 9, h: 0.35,
    fill: { color: COLORS.dark }
  });
  slide5.addText("核心心法：遇到卡点 → 对照参考项目 → 理解为什么不同", {
    x: 0.5, y: 5.22, w: 9, h: 0.35,
    fontSize: 12, fontFace: "Calibri", color: COLORS.white, align: "center", margin: 0
  });

  // ========== Slide 6: Concept Mapping ==========
  let slide6 = pres.addSlide();
  slide6.background = { color: COLORS.bg };

  slide6.addText("核心概念对照表", {
    x: 0.5, y: 0.4, w: 9, h: 0.6,
    fontSize: 28, fontFace: "Arial", color: COLORS.dark, bold: true, margin: 0
  });

  // Table header
  slide6.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.1, w: 9, h: 0.5, fill: { color: COLORS.primary }
  });
  slide6.addText("你的系统模块", {
    x: 0.5, y: 1.15, w: 2.5, h: 0.45,
    fontSize: 13, fontFace: "Calibri", color: COLORS.white, bold: true, align: "center", margin: 0
  });
  slide6.addText("LangChain 概念", {
    x: 3.0, y: 1.15, w: 2.5, h: 0.45,
    fontSize: 13, fontFace: "Calibri", color: COLORS.white, bold: true, align: "center", margin: 0
  });
  slide6.addText("理解的核心问题", {
    x: 5.5, y: 1.15, w: 4, h: 0.45,
    fontSize: 13, fontFace: "Calibri", color: COLORS.white, bold: true, align: "center", margin: 0
  });

  const concepts = [
    ["13 个 Agent 分工", "Agent / Tool / Persona", "为什么要分工？分到什么粒度？"],
    ["意图识别", "Intent Routing / RouterChain", "怎么让模型选择正确路径？"],
    ["知识库检索", "VectorStore + Retriever", "检索质量怎么评估和改进？"],
    ["共享上下文 (黑板)", "Memory / State", "多轮对话怎么保持上下文？"],
    ["多跳推理", "LangGraph ConditionalEdge", "复杂任务怎么拆解成步骤？"],
    ["Prompt 模板", "LCEL / Chain", "为什么要用管道式组合？"]
  ];

  concepts.forEach((row, i) => {
    const y = 1.6 + i * 0.62;
    const bgColor = i % 2 === 0 ? COLORS.white : COLORS.light;
    slide6.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y, w: 9, h: 0.62, fill: { color: bgColor }
    });
    slide6.addText(row[0], {
      x: 0.6, y: y + 0.08, w: 2.3, h: 0.5,
      fontSize: 12, fontFace: "Calibri", color: COLORS.dark, margin: 0
    });
    slide6.addText(row[1], {
      x: 3.0, y: y + 0.08, w: 2.3, h: 0.5,
      fontSize: 12, fontFace: "Calibri", color: COLORS.primary, bold: true, margin: 0
    });
    slide6.addText(row[2], {
      x: 5.5, y: y + 0.08, w: 3.9, h: 0.5,
      fontSize: 12, fontFace: "Calibri", color: COLORS.gray, margin: 0
    });
  });

  // ========== Slide 7: Learning Milestones ==========
  let slide7 = pres.addSlide();
  slide7.background = { color: COLORS.bg };

  slide7.addText("学习里程碑", {
    x: 0.5, y: 0.4, w: 9, h: 0.6,
    fontSize: 28, fontFace: "Arial", color: COLORS.dark, bold: true, margin: 0
  });

  const milestones = [
    { week: "第 1 周", title: "Embedding 向量化", desc: "文本怎么变成数字？为什么向量能表示语义？" },
    { week: "第 2 周", title: "向量相似度搜索", desc: "怎么知道两个文本'像'？余弦相似度是什么？" },
    { week: "第 3 周", title: "Prompt 工程", desc: "为什么要写 Prompt？模板化 Prompt 的好处？" },
    { week: "第 4 周", title: "意图识别原理", desc: "怎么让模型理解用户想要什么？" },
    { week: "第 5-6 周", title: "Agent 分工设计", desc: "为什么要分工？什么时候该拆，什么时候合？" },
    { week: "第 7-8 周", title: "多跳推理", desc: "复杂问题怎么拆解？Chain-of-Thought 怎么用？" }
  ];

  milestones.forEach((m, i) => {
    const y = 1.1 + i * 0.72;
    // Week badge
    slide7.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y, w: 1.2, h: 0.55, fill: { color: COLORS.primary }
    });
    slide7.addText(m.week, {
      x: 0.5, y: y + 0.08, w: 1.2, h: 0.4,
      fontSize: 11, fontFace: "Calibri", color: COLORS.white, bold: true, align: "center", margin: 0
    });
    // Content
    slide7.addText(m.title, {
      x: 1.9, y: y + 0.02, w: 3, h: 0.3,
      fontSize: 14, fontFace: "Calibri", color: COLORS.dark, bold: true, margin: 0
    });
    slide7.addText(m.desc, {
      x: 1.9, y: y + 0.3, w: 7.5, h: 0.35,
      fontSize: 11, fontFace: "Calibri", color: COLORS.gray, margin: 0
    });
  });

  // ========== Slide 8: Action Plan ==========
  let slide8 = pres.addSlide();
  slide8.background = { color: COLORS.dark };

  slide8.addText("立即行动", {
    x: 0.5, y: 0.4, w: 9, h: 0.6,
    fontSize: 28, fontFace: "Arial", color: COLORS.white, bold: true, margin: 0
  });

  const actions = [
    { step: "01", title: "选定新项目方向", desc: "客服 FAQ / 个人文档助手 / 会议纪要生成器", color: COLORS.primary },
    { step: "02", title: "搭建 LangChain 基础项目", desc: "参考现有系统，一个模块一个模块对照学习", color: COLORS.secondary },
    { step: "03", title: "遇到卡点来找我", desc: "\"为什么要用 XX 而不是直接问？\"", color: COLORS.accent }
  ];

  actions.forEach((a, i) => {
    const y = 1.2 + i * 1.35;
    slide8.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y, w: 9, h: 1.1, fill: { color: a.color, transparency: 20 }
    });
    slide8.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y, w: 0.8, h: 1.1, fill: { color: a.color }
    });
    slide8.addText(a.step, {
      x: 0.5, y: y + 0.3, w: 0.8, h: 0.5,
      fontSize: 20, fontFace: "Arial", color: COLORS.white, bold: true, align: "center", margin: 0
    });
    slide8.addText(a.title, {
      x: 1.5, y: y + 0.15, w: 7.8, h: 0.45,
      fontSize: 16, fontFace: "Calibri", color: COLORS.white, bold: true, margin: 0
    });
    slide8.addText(a.desc, {
      x: 1.5, y: y + 0.6, w: 7.8, h: 0.4,
      fontSize: 13, fontFace: "Calibri", color: COLORS.gray, margin: 0
    });
  });

  // CTA
  slide8.addText("你想做什么方向的项目？我帮你规划第一个月的学习路径", {
    x: 0.5, y: 5.0, w: 9, h: 0.4,
    fontSize: 14, fontFace: "Calibri", color: COLORS.accent, align: "center", margin: 0
  });

  // Save
  await pres.writeFile({ fileName: "C:/Users/51603/langchain-learning-path/LangChain学习路径.pptx" });
  console.log("PPT created: C:/Users/51603/langchain-learning-path/LangChain学习路径.pptx");
}

createPresentation().catch(console.error);
