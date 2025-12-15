"""
解释层（Explanation Layer）

核心功能：将技术决策转换为人类语言

设计理念：
- 用户是朋友，不是客户
- 说人话，不说技术术语
- 解释"为什么舒服"，而非"为什么高分"
- 自然合理化回访、等待等"不完美"决策

Author: GAODE Team
Date: 2024-12
"""

from typing import Dict, Optional
from .models import Location, CandidateOption, POIType
import logging

logger = logging.getLogger(__name__)


class ExplanationLayer:
    """
    解释层：技术→人类语言
    
    核心方法：
    1. explain_choice() - 解释为什么选择这个地方
    2. explain_region_revisit() - 解释为什么回访同一区域
    3. explain_timing() - 解释为什么现在去合适
    
    输出风格：
    - 朋友式："咱们"、"走"、"我觉得"
    - 1-2句话，30字内
    - 不提C_causal、评分等技术指标
    - 融入时间、天气、距离等现实因素
    """
    
    def __init__(self, llm_client=None):
        """
        Args:
            llm_client: LLM客户端（可选）
                - 有LLM：AI生成自然解释
                - 无LLM：使用规则模板
        """
        self.llm_client = llm_client
        
    def explain_choice(self, 
                      option: CandidateOption,
                      context: Dict,
                      rank: int = 1,
                      alternatives: list = None) -> str:
        """
        解释为什么选择这个地方（🔥 修复：敢犹豫、敢质疑）
        
        Args:
            option: 候选选项
            context: 上下文信息
            rank: 排名（1=第一，2=第二...）🔥
            alternatives: 其他备选（用于对比）🔥
                
        Returns:
            朋友式解释 - 可能是支持，也可能是质疑
        """
        # 🔥 检测"需要质疑"的情况
        region = self._get_region(option.node)
        visit_count = context.get('visited_regions', {}).get(region, 0)
        
        # 情况1：区域连续访问≥2次 → 强制生成反方向建议
        if visit_count >= 2 and rank == 1:
            return self._generate_counter_suggestion(option, context, alternatives)
        
        # 情况2：第二名的不甘心
        if rank == 2:
            return self._generate_second_choice_appeal(option, context)
        
        # 情况3：正常解释
        if self.llm_client:
            try:
                return self._llm_explain(option, context, rank)
            except Exception as e:
                logger.warning(f"LLM解释失败，降级到规则: {e}")
                return self._rule_explain(option, context)
        else:
            return self._rule_explain(option, context)
    
    def _llm_explain(self, option: CandidateOption, context: Dict, rank: int = 1) -> str:
        """
        用LLM生成自然解释（🔥 修复：呈现冲突和犹豫）
        """
        poi = option.node
        
        # 提取关键信息
        region = self._get_region(poi)
        visit_count = context.get('visited_regions', {}).get(region, 0)
        time = context.get('time', '10:00')
        weather = context.get('weather', '晴天')
        c_causal = context.get('c_causal', 0.5)
        
        # 🔥 提取张力信息
        tensions = context.get('tensions', {})
        novelty = tensions.get('novelty', 0)
        continuity = tensions.get('continuity', 0)
        energy = tensions.get('energy', 0)
        conflict = tensions.get('conflict', 0)
        
        # 提取交通信息
        transport = {}
        if option.edges:
            edge = option.edges[0]
            transport = {
                'mode': edge.mode.value if hasattr(edge.mode, 'value') else str(edge.mode),
                'time': int(edge.time * 60) if edge.time else 10,
                'cost': int(edge.cost) if edge.cost else 0
            }
        
        # 🔥 构建prompt（呈现冲突和犹豫）
        prompt = f"""你是旅行伙伴，用朋友的口吻解释为什么选择这个地方。但你要呈现"犹豫"，而不是总是完美合理。

地点：{poi.name}
区域：{region}（{"第"+str(visit_count)+"次" if visit_count > 0 else "首次"}）
时间：{time} | 天气：{weather}
交通：{transport.get('mode', '步行')} {transport.get('time', 10)}分钟

🔥 核心张力（决定你的语气）：
- 新鲜感张力：{novelty:.1f}（{"想去新地方" if novelty > 0 else "重复区域"}）
- 体力张力：{energy:.1f}（{"精力充沛" if energy > 0 else "有点累了"}）
- 连续性张力：{continuity:.1f}（{"体验丰富" if continuity > 0 else "重复类型"}）
- 冲突度：{conflict:.1f}（{"矛盾明显" if conflict > 0.3 else "比较一致"}）

🔥 关键要求（必须遵守）：
1. 如果冲突度>0.3，必须呈现矛盾："虽然...但是..."或"一方面...一方面..."
2. 如果冲突度<0.3，可以单一理由，但不要太肯定，用"我觉得"、"可能"
3. 绝对不要每次都说"正好"、"刚好"、"正合适"（这太完美了）
4. 允许犹豫："不知道是不是..."、"要不..."、"也行"
5. 1-2句话，30-40字

🔥 好的例子（呈现冲突）：
- 冲突高："虽然这边去过了，但也不用赶，随便转转也行"
- 冲突高："新地方是挺吸引人，不过有点远，要不就近走走？"
- 冲突低："我觉得可以去新地方透透气"
- 冲突低："有点累了，回熟悉的地方歇会儿"

❌ 避免的例子（太完美）：
- "这会儿阳光正好，走过去就10分钟"（太完美）
- "正好到饭点儿了"（总是正好）
- "人少又凉快，正好去逛逛"（总是理由齐全）

直接输出解释，不要任何前缀："""

        response = self.llm_client.generate(
            prompt,
            temperature=0.8,  # 提高温度，更自然
            max_tokens=60
        )
        
        return response.strip()
    
    def _rule_explain(self, option: CandidateOption, context: Dict) -> str:
        """规则生成解释（后备方案）"""
        poi = option.node
        region = self._get_region(poi)
        visit_count = context.get('visited_regions', {}).get(region, 0)
        time = context.get('time', '10:00')
        
        hour = int(time.split(':')[0]) if ':' in time else 10
        
        # 提取交通信息
        transport_mode = '步行'
        transport_time = 10
        if option.edges:
            edge = option.edges[0]
            transport_mode = edge.mode.value if hasattr(edge.mode, 'value') else str(edge.mode)
            transport_time = int(edge.time * 60) if edge.time else 10
        
        # 策略1：重复区域（优先）
        if visit_count > 0:
            templates = [
                "这会儿有点累了，回熟悉的地方随便走走反而更放松",
                "时间还早，再逛逛这边也不错，不用赶路",
                "上次没逛够吧？正好再来补上"
            ]
            return templates[min(visit_count - 1, len(templates) - 1)]
        
        # 策略2：餐厅
        if poi.type == POIType.RESTAURANT:
            if 11 <= hour <= 13:
                return "正好到饭点儿了，这家看着不错，试试"
            else:
                return "提前找个地方吃点东西，免得一会儿饿"
        
        # 策略3：知名景点
        famous = ["厦大", "鼓浪屿", "环岛路", "曾厝垵", "中山路", 
                  "苏州博物馆", "拙政园", "虎丘", "平江路"]
        if any(f in poi.name for f in famous):
            return f"走，去{region}看看，这是必打卡的地方"
        
        # 策略4：交通便利
        if transport_mode == '步行':
            return "就在附近，走过去就行，顺便消消食"
        elif transport_time < 15:
            return "离得很近，过去看看正好"
        
        # 策略5：天气相关
        weather = context.get('weather', '')
        if '雨' in weather or 'rain' in weather.lower():
            if poi.type in [POIType.SHOPPING, POIType.RESTAURANT, POIType.ENTERTAINMENT]:
                return "下雨天，去室内逛逛最舒服"
        
        # 默认策略
        return f"换个地方透透气，去{region}逛逛"
    
    def explain_region_revisit(self, region: str, visit_count: int, reason: str = None) -> str:
        """
        专门解释区域回访
        
        Args:
            region: 区域名称
            visit_count: 访问次数
            reason: 回访原因（可选）
            
        Returns:
            自然解释
        """
        if reason:
            return reason
        
        templates = {
            1: f"{region}还有些地方没逛完，顺便再看看",
            2: f"这边挺好的，再转转也不亏",
            3: f"反正时间充足，{region}多逛几次也行"
        }
        
        return templates.get(visit_count, templates[3])
    
    def explain_timing(self, poi: Location, time_hour: int, weather: str = None) -> str:
        """
        解释为什么现在去合适
        
        Args:
            poi: POI
            time_hour: 当前小时数（如10表示10点）
            weather: 天气（可选）
            
        Returns:
            时机解释
        """
        # 餐饮时机
        if poi.type == POIType.RESTAURANT:
            if 11 <= time_hour <= 13:
                return "正好饭点，去吃饭最合适"
            elif 17 <= time_hour <= 19:
                return "晚饭时间到了，该吃饭啦"
            else:
                return "现在人少，不用排队"
        
        # 景点时机
        if poi.type == POIType.ATTRACTION:
            if 9 <= time_hour <= 11:
                return "早上人少景美，最佳游览时间"
            elif 14 <= time_hour <= 16:
                return "下午阳光正好，适合拍照"
            elif time_hour >= 17:
                return "傍晚光线柔和，景色更美"
        
        # 天气因素
        if weather:
            if '雨' in weather:
                if poi.type in [POIType.SHOPPING, POIType.ENTERTAINMENT]:
                    return "雨天正好去室内，不受影响"
            elif '晴' in weather:
                if poi.type == POIType.ATTRACTION and '公园' in poi.name:
                    return "天气这么好，正适合逛公园"
        
        return "现在去正合适"
    
    def _get_region(self, poi: Location) -> str:
        """获取POI所属区域"""
        # 通用区域识别
        regions = ["鼓浪屿", "厦大", "曾厝垵", "中山路", "环岛路",
                   "姑苏", "虎丘", "金鸡湖", "平江路", "山塘街"]
        
        for region in regions:
            if region in poi.name or region in poi.address:
                return region
        
        return "其他"
    
    def _generate_counter_suggestion(self, option: CandidateOption, context: Dict, alternatives: list = None) -> str:
        """
        生成反方向建议（🔥 核心创新：敢质疑）
        
        当区域连续访问≥2次时，不再"合理化"，而是提出质疑
        
        Args:
            option: 当前选项（第一名）
            context: 上下文
            alternatives: 其他选项
            
        Returns:
            质疑性解释
        """
        region = self._get_region(option.node)
        visit_count = context.get('visited_regions', {}).get(region, 0)
        
        # 如果有备选，提及备选
        alternative_text = ""
        if alternatives and len(alternatives) > 0:
            alt_option = alternatives[0]
            alt_region = self._get_region(alt_option.node)
            alt_visit = context.get('visited_regions', {}).get(alt_region, 0)
            
            if alt_visit < visit_count:
                alternative_text = f"或者{alt_region}那边还没怎么去过，"
        
        # 反向质疑模板
        templates = [
            f"{region}又去？{alternative_text}要不换个地方透透气？",
            f"虽然{region}还不错，但去了{visit_count}次了，{alternative_text}换个区域会不会更新鲜？",
            f"我感觉{region}有点去腻了...{alternative_text}要不要考虑别的地方？",
            f"{region}确实挺好，可是去太多次会不会单调？{alternative_text}换个方向走走？"
        ]
        
        import random
        return random.choice(templates)
    
    def _generate_second_choice_appeal(self, option: CandidateOption, context: Dict) -> str:
        """
        生成第二名的"不甘心"（🔥 核心创新：放大第二名的价值）
        
        不让第一名独大，而是突出第二名的独特优势
        
        Args:
            option: 第二名选项
            context: 上下文
            
        Returns:
            突出第二名价值的解释
        """
        region = self._get_region(option.node)
        visit_count = context.get('visited_regions', {}).get(region, 0)
        
        # 提取张力
        tensions = context.get('tensions', {})
        novelty = tensions.get('novelty', 0)
        energy = tensions.get('energy', 0)
        
        # 强调第二名的优势
        if visit_count == 0 and novelty > 0.5:
            # 新鲜感优势
            return f"虽然排第二，但{region}是新地方，说不定更有惊喜"
        elif energy < 0:
            # 省力优势
            return f"第二选择也不错，而且更近，省点力气"
        else:
            # 通用不甘心
            templates = [
                f"其实{region}也挺值得去的，不一定非要选第一",
                f"第二名也有它的道理，{region}可能更适合你",
                f"要不考虑一下这个？{region}也许是个惊喜"
            ]
            import random
            return random.choice(templates)


# 便捷函数
def create_explanation_layer(llm_client=None) -> ExplanationLayer:
    """
    创建解释层（工厂函数）
    
    Args:
        llm_client: LLM客户端（可选）
        
    Returns:
        ExplanationLayer实例
        
    Example:
        >>> from src.core.llm_client import create_llm_client
        >>> llm = create_llm_client(provider="deepseek", api_key="sk-xxx")
        >>> explainer = create_explanation_layer(llm)
    """
    return ExplanationLayer(llm_client=llm_client)
