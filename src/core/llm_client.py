"""
LLM客户端统一接口
支持多种大模型服务
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class LLMClient(ABC):
    """LLM客户端抽象基类"""
    
    @abstractmethod
    def generate(self, 
                prompt: str, 
                temperature: float = 0.7,
                max_tokens: int = 500,
                **kwargs) -> str:
        """
        生成文本
        
        Args:
            prompt: 提示词
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            生成的文本
        """
        pass
    
    @abstractmethod
    def generate_structured(self,
                          prompt: str,
                          schema: Dict,
                          temperature: float = 0.7,
                          **kwargs) -> Dict:
        """
        生成结构化输出（JSON）
        
        Args:
            prompt: 提示词
            schema: JSON schema
            temperature: 温度参数
            
        Returns:
            解析后的JSON对象
        """
        pass
    
    def batch_reason(self, 
                    prompts: List[str], 
                    temperature: float = 0.5,
                    max_tokens: int = 50,
                    max_workers: int = 10,
                    **kwargs) -> List[Optional[float]]:
        """
        批量推理（并发，性能优化）
        
        Args:
            prompts: 提示词列表
            temperature: 温度参数
            max_tokens: 最大token数
            max_workers: 最大并发数
            
        Returns:
            推理结果列表（数值或None）
        """
        # 默认实现：串行调用
        results = []
        for prompt in prompts:
            try:
                response = self.generate(prompt, temperature, max_tokens, **kwargs)
                # 尝试提取数字
                numbers = re.findall(r'0?\.\d+|1\.0+|1', response)
                results.append(float(numbers[0]) if numbers else None)
            except:
                results.append(None)
        return results


class OpenAIClient(LLMClient):
    """OpenAI GPT客户端"""
    
    def __init__(self, api_key: str, model: str = "gpt-5", api_base: Optional[str] = None):
        """
        初始化OpenAI客户端
        
        Args:
            api_key: OpenAI API密钥
            model: 模型名称
            api_base: 自定义API基础URL（用于第三方代理）
        """
        self.api_key = api_key
        self.model = model
        self.api_base = api_base
        
        try:
            from openai import OpenAI
            
            # 使用新版本的OpenAI客户端
            if api_base:
                self.client = OpenAI(api_key=api_key, base_url=api_base)
                logger.info(f"使用自定义API: {api_base}")
            else:
                self.client = OpenAI(api_key=api_key)
            
            logger.info(f"OpenAI客户端初始化成功，模型: {model}")
        except ImportError:
            logger.error("未安装openai库，请运行: pip install openai")
            raise
    
    def generate(self, 
                prompt: str, 
                temperature: float = 0.7,
                max_tokens: int = 500,
                **kwargs) -> str:
        """生成文本"""
        try:
            # 使用新版本的API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的旅行顾问AI，提供信息性建议，不使用命令式语气。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
            # 降级到规则系统
            return self._fallback_response(prompt)
    
    def generate_structured(self,
                          prompt: str,
                          schema: Dict,
                          temperature: float = 0.7,
                          **kwargs) -> Dict:
        """生成结构化输出"""
        try:
            # 添加JSON格式要求到prompt
            full_prompt = f"{prompt}\n\n请以JSON格式返回，符合以下schema:\n{json.dumps(schema, indent=2)}"
            
            # 使用新版本的API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的旅行顾问AI。请严格按照JSON格式返回。"},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=temperature,
                max_tokens=1000,
                response_format={"type": "json_object"},  # GPT-4/5支持JSON模式
                **kwargs
            )
            
            content = response.choices[0].message.content.strip()
            return json.loads(content)
        
        except Exception as e:
            logger.error(f"OpenAI结构化生成失败: {e}")
            return self._fallback_structured_response(schema)
    
    def _fallback_response(self, prompt: str) -> str:
        """降级响应"""
        return "由于LLM服务暂时不可用，已切换到基础推荐模式。"
    
    def _fallback_structured_response(self, schema: Dict) -> Dict:
        """降级结构化响应"""
        return {}
    
    def batch_reason(self, 
                    prompts: List[str], 
                    temperature: float = 0.5,
                    max_tokens: int = 50,
                    max_workers: int = 10,
                    **kwargs) -> List[Optional[float]]:
        """
        批量推理（并发优化）
        
        核心性能优化：10x提速
        
        Args:
            prompts: 提示词列表
            temperature: 温度参数
            max_tokens: 最大token数
            max_workers: 最大并发数
            
        Returns:
            推理结果列表（数值或None）
        """
        def _single_reason(prompt: str) -> Optional[float]:
            """单次推理"""
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                result = response.choices[0].message.content.strip()
                # 提取数字
                numbers = re.findall(r'0?\.\d+|1\.0+|1', result)
                return float(numbers[0]) if numbers else None
            except Exception as e:
                logger.warning(f"推理失败: {e}")
                return None
        
        # 并发执行
        results = [None] * len(prompts)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_single_reason, prompt): i 
                for i, prompt in enumerate(prompts)
            }
            
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    logger.error(f"并发推理异常: {e}")
                    results[idx] = None
        
        return results


class QwenClient(LLMClient):
    """通义千问客户端"""
    
    def __init__(self, api_key: str, model: str = "qwen-turbo"):
        """
        初始化通义千问客户端
        
        Args:
            api_key: 阿里云API密钥
            model: 模型名称
        """
        self.api_key = api_key
        self.model = model
        
        try:
            from dashscope import Generation
            self.generation = Generation
            logger.info(f"通义千问客户端初始化成功，模型: {model}")
        except ImportError:
            logger.error("未安装dashscope库，请运行: pip install dashscope")
            raise
    
    def generate(self, 
                prompt: str, 
                temperature: float = 0.7,
                max_tokens: int = 500,
                **kwargs) -> str:
        """生成文本"""
        try:
            response = self.generation.call(
                model=self.model,
                prompt=prompt,
                api_key=self.api_key,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            if response.status_code == 200:
                return response.output.text.strip()
            else:
                logger.error(f"通义千问API返回错误: {response.message}")
                return self._fallback_response(prompt)
        
        except Exception as e:
            logger.error(f"通义千问API调用失败: {e}")
            return self._fallback_response(prompt)
    
    def generate_structured(self,
                          prompt: str,
                          schema: Dict,
                          temperature: float = 0.7,
                          **kwargs) -> Dict:
        """生成结构化输出"""
        try:
            full_prompt = f"{prompt}\n\n请以JSON格式返回，符合以下schema:\n{json.dumps(schema, ensure_ascii=False, indent=2)}"
            
            response = self.generation.call(
                model=self.model,
                prompt=full_prompt,
                api_key=self.api_key,
                temperature=temperature,
                result_format='message',
                **kwargs
            )
            
            if response.status_code == 200:
                content = response.output.text.strip()
                # 提取JSON（可能包含在markdown代码块中）
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                return json.loads(content)
            else:
                return self._fallback_structured_response(schema)
        
        except Exception as e:
            logger.error(f"通义千问结构化生成失败: {e}")
            return self._fallback_structured_response(schema)
    
    def _fallback_response(self, prompt: str) -> str:
        """降级响应"""
        return "由于LLM服务暂时不可用，已切换到基础推荐模式。"
    
    def _fallback_structured_response(self, schema: Dict) -> Dict:
        """降级结构化响应"""
        return {}


class MockLLMClient(LLMClient):
    """
    模拟LLM客户端（用于测试）
    不调用真实API，返回模拟数据
    """
    
    def __init__(self):
        logger.info("使用MockLLMClient（测试模式）")
    
    def generate(self, 
                prompt: str, 
                temperature: float = 0.7,
                max_tokens: int = 500,
                **kwargs) -> str:
        """返回模拟文本"""
        return "这是一个很棒的旅行目的地，值得推荐。"
    
    def generate_structured(self,
                          prompt: str,
                          schema: Dict,
                          temperature: float = 0.7,
                          **kwargs) -> Dict:
        """返回模拟结构化数据"""
        return {
            "reasons": ["风景优美", "文化底蕴深厚", "适合当前时间游览"],
            "warnings": [],
            "personalized_tip": "建议慢慢游览，体验当地文化"
        }


def create_llm_client(
    provider: str = "mock",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    api_base: Optional[str] = None
) -> LLMClient:
    """
    创建LLM客户端工厂函数
    
    Args:
        provider: 提供商 ('openai', 'deepseek', 'qwen', 'mock')
        api_key: API密钥
        model: 模型名称
        api_base: 自定义API基础URL（用于第三方代理）
        
    Returns:
        LLM客户端实例
        
    Examples:
        # DeepSeek（推荐，性价比高）
        >>> client = create_llm_client(
        ...     provider="deepseek",
        ...     api_key="sk-xxx",
        ...     model="deepseek-chat"
        ... )
        
        # OpenAI
        >>> client = create_llm_client(
        ...     provider="openai",
        ...     api_key="sk-xxx",
        ...     model="gpt-4"
        ... )
    """
    if provider == "openai":
        if not api_key:
            raise ValueError("OpenAI需要提供api_key")
        return OpenAIClient(
            api_key=api_key,
            model=model or "gpt-4",
            api_base=api_base
        )
    
    elif provider == "deepseek":
        if not api_key:
            raise ValueError("DeepSeek需要提供api_key")
        # DeepSeek使用OpenAI兼容接口
        return OpenAIClient(
            api_key=api_key,
            model=model or "deepseek-chat",
            api_base=api_base or "https://api.deepseek.com/v1"
        )
    
    elif provider == "qwen":
        if not api_key:
            raise ValueError("通义千问需要提供api_key")
        return QwenClient(
            api_key=api_key,
            model=model or "qwen-turbo"
        )
    
    elif provider == "mock":
        return MockLLMClient()
    
    else:
        raise ValueError(f"不支持的provider: {provider}，可选: openai, deepseek, qwen, mock")


# 提示词模板
class PromptTemplates:
    """提示词模板库"""
    
    @staticmethod
    def poi_analysis(poi_info: Dict, user_profile: Dict, context: Dict) -> str:
        """POI深度分析提示词"""
        return f"""分析以下POI的推荐理由：

POI信息：
- 名称：{poi_info.get('name')}
- 类型：{poi_info.get('type')}
- 评分：{poi_info.get('rating')}
- 评论数：{poi_info.get('review_count')}
- 特色标签：{', '.join(poi_info.get('tags', []))}

用户画像：
- 旅行目的：{user_profile.get('purpose', {})}
- 节奏偏好：{user_profile.get('pace', {})}

当前上下文：
- 已访问：{context.get('visited', [])}
- 疲劳度：{context.get('fatigue', 0)}

请生成：
1. 3-5个吸引人的推荐理由（简洁、自然）
2. 1-2个注意事项（如果有）
3. 1句个性化建议

要求：语气友好、信息性、不命令式"""
    
    @staticmethod
    def risk_explanation(risk_info: Dict) -> str:
        """风险解释提示词"""
        return f"""解释以下旅行风险：

选择：{risk_info.get('choice_name')}
风险类型：{risk_info.get('risk_type')}

时间分析：
- 游玩预计结束：{risk_info.get('finish_time')}
- 返程耗时：{risk_info.get('return_time')}小时
- 预计到达：{risk_info.get('arrive_time')}
- 必须到达时间：{risk_info.get('deadline')}
- 差距：晚{risk_info.get('late_by')}小时

请用自然、友好的语言解释：
1. 为什么会产生这个风险
2. 具体会导致什么后果
3. 有什么补救方案（如果有）

要求：简洁、客观、不说教"""
    
    @staticmethod
    def global_insight(session_info: Dict, candidates: List[Dict]) -> str:
        """全局洞察提示词"""
        return f"""作为全知的旅行顾问，分析当前状况：

当前状态：
- 时间：已用{session_info.get('time_used')}h / 总共{session_info.get('total_duration')}h
- 预算：已用¥{session_info.get('budget_used')} / 总共¥{session_info.get('total_budget')}
- 已访问：{session_info.get('visited_pois', [])}
- 回程约束：{session_info.get('return_constraint', '无')}

候选选项：
{json.dumps(candidates, ensure_ascii=False, indent=2)}

请生成：
1. 全局概览（1句话评价当前进度）
2. 关键洞察（2-3个要点）
3. 前瞻建议（如果有重要提醒）

要求：信息性、简洁、友好、不命令式"""
