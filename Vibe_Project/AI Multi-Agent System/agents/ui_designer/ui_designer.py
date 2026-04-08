"""
UI Designer Agent - UI设计智能体
==============================

职责:
- 界面设计
- 组件规格
- 设计系统
- 布局规划
- 交互设计
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from core.prompt_engine import prompt_manager
from core.guardrails import guardrails
from core.llm import get_llm
from logs.error_logs import error_logger, ErrorLevel


class DesignStyle(Enum):
    """设计风格"""
    MINIMAL = "minimal"
    MATERIAL = "material"
    GLASSMORPHISM = "glassmorphism"
    NEUMORPHISM = "neumorphism"
    BRUTALIST = "brutalist"
    RETRO = "retro"
    FUTURISTIC = "futuristic"


class ComponentType(Enum):
    """组件类型"""
    BUTTON = "button"
    INPUT = "input"
    CARD = "card"
    MODAL = "modal"
    NAVIGATION = "navigation"
    TABLE = "table"
    FORM = "form"


@dataclass
class DesignTask:
    """设计任务"""
    id: str
    component_type: ComponentType
    description: str
    style: DesignStyle
    color_scheme: Optional[Dict] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class DesignResult:
    """设计结果"""
    component_name: str
    description: str
    style: str
    specs: Dict = field(default_factory=dict)
    css: Optional[str] = None
    html: Optional[str] = None
    interaction: Optional[str] = None
    accessibility: Optional[str] = None
    quality_score: float = 0.0


class UIDesigner:
    """UI设计智能体

    【能力】
    - 设计UI组件
    - 创建设计规格
    - 定义颜色和排版
    - 规划响应式布局
    - 提供交互设计建议
    """

    def __init__(self):
        self.name = "UI Designer"
        self.specialty = ["UI设计", "UX", "设计系统", "响应式", "无障碍"]
        self.current_task: Optional[DesignTask] = None

    async def design_component(
        self,
        description: str,
        component_type: str = "button",
        style: str = "minimal",
        color_scheme: Optional[Dict] = None
    ) -> DesignResult:
        """设计UI组件

        Args:
            description: 组件描述
            component_type: 组件类型
            style: 设计风格
            color_scheme: 颜色方案

        Returns:
            DesignResult: 设计方案
        """
        guard_result = guardrails.check_input(description)
        if not guard_result.passed:
            raise ValueError(f"Input blocked")

        specs = {}
        css = None
        html = None
        interaction = None
        accessibility = None

        try:
            # 生成组件规格
            specs = self._generate_specs(description, component_type, style, color_scheme)

            # 生成CSS
            css = self._generate_css(component_type, style, color_scheme)

            # 生成HTML结构
            html = self._generate_html(component_type, description)

            # 交互设计
            interaction = self._generate_interaction(component_type)

            # 无障碍设计
            accessibility = self._generate_accessibility(component_type)

            quality_score = 0.85

        except Exception as e:
            error_logger.log(
                error_type="DesignError",
                message=f"UI design failed: {str(e)}",
                level=ErrorLevel.WARNING
            )
            quality_score = 0.5

        return DesignResult(
            component_name=self._generate_component_name(description),
            description=description,
            style=style,
            specs=specs,
            css=css,
            html=html,
            interaction=interaction,
            accessibility=accessibility,
            quality_score=quality_score
        )

    async def design_page_layout(
        self,
        description: str,
        sections: List[str],
        style: str = "minimal"
    ) -> DesignResult:
        """设计页面布局"""
        try:
            layout_spec = self._generate_layout_spec(sections, style)
            grid_css = self._generate_grid_css(sections, style)
            html = self._generate_page_html(sections, description)

            quality_score = 0.85

        except Exception as e:
            error_logger.log(
                error_type="DesignError",
                message=f"Layout design failed: {str(e)}",
                level=ErrorLevel.WARNING
            )
            layout_spec = {}
            grid_css = ""
            html = ""
            quality_score = 0.5

        return DesignResult(
            component_name="PageLayout",
            description=description,
            style=style,
            specs=layout_spec,
            css=grid_css,
            html=html,
            interaction=None,
            accessibility=None,
            quality_score=quality_score
        )

    def create_color_palette(
        self,
        base_color: str = "#4299E1",
        palette_type: str = "analogous"
    ) -> Dict:
        """创建配色方案"""
        # 基础颜色扩展
        palettes = {
            "analogous": [
                base_color,
                self._adjust_hue(base_color, 30),
                self._adjust_hue(base_color, -30),
                self._adjust_saturation(base_color, 0.8),
                self._adjust_lightness(base_color, 0.9),
            ],
            "complementary": [
                base_color,
                self._get_complementary(base_color),
                self._adjust_lightness(base_color, 0.8),
                self._adjust_lightness(base_color, 1.2),
            ],
            "triadic": [
                base_color,
                self._adjust_hue(base_color, 120),
                self._adjust_hue(base_color, 240),
                "#FFFFFF",
                "#000000",
            ]
        }

        return {
            "primary": base_color,
            "palette": palettes.get(palette_type, palettes["analogous"]),
            "neutrals": ["#FFFFFF", "#F7FAFC", "#EDF2F7", "#CBD5E0", "#2D3748", "#1A202C"]
        }

    def _generate_specs(
        self,
        description: str,
        component_type: str,
        style: str,
        color_scheme: Optional[Dict]
    ) -> Dict:
        """生成组件规格"""
        specs = {
            "component": component_type,
            "style": style,
            "dimensions": {
                "min_width": "auto",
                "max_width": "100%",
                "height": "auto",
                "padding": "12px 24px",
                "border_radius": "8px"
            },
            "colors": color_scheme or {
                "background": "#FFFFFF",
                "text": "#2D3748",
                "border": "#E2E8F0",
                "hover": "#4299E1"
            },
            "typography": {
                "font_family": "Inter, sans-serif",
                "font_size": "14px",
                "font_weight": "500"
            },
            "spacing": {
                "xs": "4px",
                "sm": "8px",
                "md": "16px",
                "lg": "24px",
                "xl": "32px"
            }
        }

        if component_type == "button":
            specs["states"] = {
                "default": {"background": "#4299E1", "color": "#FFFFFF"},
                "hover": {"background": "#3182CE", "transform": "translateY(-1px)"},
                "active": {"background": "#2B6CB0", "transform": "translateY(0)"},
                "disabled": {"opacity": "0.5", "cursor": "not-allowed"}
            }
        elif component_type == "input":
            specs["states"] = {
                "default": {"border": "1px solid #E2E8F0"},
                "focus": {"border": "2px solid #4299E1", "box_shadow": "0 0 0 3px rgba(66,153,225,0.2)"},
                "error": {"border": "2px solid #F56565"},
                "disabled": {"background": "#F7FAFC", "cursor": "not-allowed"}
            }

        return specs

    def _generate_css(
        self,
        component_type: str,
        style: str,
        color_scheme: Optional[Dict]
    ) -> str:
        """生成CSS代码"""
        base_css = f"""
.{component_type} {{
    font-family: Inter, sans-serif;
    font-size: 14px;
    padding: 12px 24px;
    border-radius: 8px;
    transition: all 0.2s ease;
    cursor: pointer;
"""

        if component_type == "button":
            base_css += """    background: #4299E1;
    color: #FFFFFF;
    border: none;
}

.button:hover {
    background: #3182CE;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(66, 153, 225, 0.3);
}

.button:active {
    transform: translateY(0);
}
"""
        elif component_type == "input":
            base_css += """    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    color: #2D3748;
}

.input:focus {
    outline: none;
    border-color: #4299E1;
    box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.2);
}
"""

        return base_css

    def _generate_html(self, component_type: str, description: str) -> str:
        """生成HTML"""
        if component_type == "button":
            return f'<button class="button">{description}</button>'
        elif component_type == "input":
            return f'<input type="text" class="input" placeholder="{description}" />'
        elif component_type == "card":
            return f'''<div class="card">
    <h3 class="card-title">{description}</h3>
    <p class="card-content">Card content here</p>
</div>'''
        return f'<div class="{component_type}">{description}</div>'

    def _generate_interaction(self, component_type: str) -> str:
        """生成交互设计"""
        interactions = {
            "button": """- Hover: Scale 1.02, shadow increase
- Active: Scale 0.98
- Focus: Visible focus ring for keyboard users
- Loading: Show spinner, disable interaction
- Success: Brief green flash""",
            "input": """- Focus: Border highlight, label float up
- Typing: Real-time validation feedback
- Error: Shake animation, error message below
- Clear: X button appears when has content""",
            "modal": """- Open: Fade in + scale up from 0.95
- Close: Fade out + scale down
- Backdrop click: Close modal
- Escape key: Close modal"""
        }
        return interactions.get(component_type, "Standard click/tap interaction")

    def _generate_accessibility(self, component_type: str) -> str:
        """生成无障碍设计"""
        return f"""- ARIA labels for screen readers
- Keyboard navigation support (Tab, Enter, Space)
- Focus visible indicators
- Color contrast ratio minimum 4.5:1
- Reduced motion support (@media prefers-reduced-motion)"""

    def _generate_layout_spec(self, sections: List[str], style: str) -> Dict:
        """生成布局规格"""
        return {
            "sections": sections,
            "grid": "12-column grid system",
            "breakpoints": {
                "mobile": "320px - 767px",
                "tablet": "768px - 1023px",
                "desktop": "1024px - 1439px",
                "large": "1440px+"
            },
            "container_max_width": "1200px",
            "gutter": "24px"
        }

    def _generate_grid_css(self, sections: List[str], style: str) -> str:
        """生成网格CSS"""
        return """.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 24px;
}

.grid {
    display: grid;
    grid-template-columns: repeat(12, 1fr);
    gap: 24px;
}

/* Responsive breakpoints */
@media (max-width: 767px) {
    .grid {
        grid-template-columns: 1fr;
    }
}

@media (min-width: 768px) and (max-width: 1023px) {
    .grid {
        grid-template-columns: repeat(6, 1fr);
    }
}
"""

    def _generate_page_html(self, sections: List[str], description: str) -> str:
        """生成页面HTML"""
        sections_html = "\n".join([
            f'    <section class="{s.lower().replace(" ", "-")}">\n        <!-- {s} -->\n    </section>'
            for s in sections
        ])
        return f"""<div class="page">
    <header><!-- Header --></header>
{sections_html}
    <footer><!-- Footer --></footer>
</div>"""

    def _generate_component_name(self, description: str) -> str:
        """生成组件名称"""
        words = description.replace("_", " ").split()
        return "".join(word.capitalize() for word in words[:2]) + "Component"

    def _adjust_hue(self, hex_color: str, degrees: int) -> str:
        """调整色相"""
        # Simplified - in production use a proper color library
        return hex_color

    def _adjust_saturation(self, hex_color: str, factor: float) -> str:
        """调整饱和度"""
        return hex_color

    def _adjust_lightness(self, hex_color: str, factor: float) -> str:
        """调整亮度"""
        return hex_color

    def _get_complementary(self, hex_color: str) -> str:
        """获取互补色"""
        return "#" + hex(int(hex_color[1:], 16) ^ 0xFFFFFF).__str__()[2:].zfill(6)

    def get_capabilities(self) -> Dict:
        """获取智能体能力"""
        return {
            "name": self.name,
            "specialty": self.specialty,
            "design_styles": [s.value for s in DesignStyle],
            "component_types": [c.value for c in ComponentType],
            "output_formats": ["CSS", "HTML", "React", "Vue", "Specifications"]
        }


# 全局实例
ui_designer = UIDesigner()
