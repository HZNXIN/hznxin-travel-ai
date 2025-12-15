"""
测试LLM接入
使用GPT-5通过第三方代理
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.core.llm_client import create_llm_client, PromptTemplates


def test_llm_connection():
    """测试LLM连接"""
    
    print("="*70)
    print("  测试DeepSeek接入")
    print("="*70)
    print()
    
    # 配置
    API_KEY = "sk-c04296145c2545588fee614c8e9ac3fb"
    API_BASE = "https://api.deepseek.com/v1"  # DeepSeek官方API
    MODEL = "deepseek-chat"  # DeepSeek Chat模型
    
    print(f"📡 配置信息:")
    print(f"  API Key: {API_KEY[:20]}...")
    print(f"  API Base: {API_BASE}")
    print(f"  模型: {MODEL}")
    print()
    
    try:
        # 1. 创建客户端
        print("1️⃣  创建LLM客户端...")
        llm_client = create_llm_client(
            provider='openai',
            api_key=API_KEY,
            model=MODEL,
            api_base=API_BASE
        )
        print("  ✅ 客户端创建成功")
        print()
        
        # 2. 测试简单生成
        print("2️⃣  测试简单文本生成...")
        prompt = "请用一句话介绍苏州拙政园的特色。"
        print(f"  提示词: {prompt}")
        print()
        
        response = llm_client.generate(
            prompt=prompt,
            temperature=0.7,
            max_tokens=100
        )
        
        print("  响应:")
        print(f"  {response}")
        print()
        print("  ✅ 简单生成测试成功！")
        print()
        
        # 3. 测试POI分析（结构化）
        print("3️⃣  测试POI深度分析...")
        
        poi_info = {
            'name': '拙政园',
            'type': 'attraction',
            'rating': 4.7,
            'review_count': 25000,
            'tags': ['江南园林', '世界文化遗产', '明代建筑']
        }
        
        user_profile = {
            'purpose': {'culture': 0.9, 'leisure': 0.7},
            'pace': {'slow': 0.9}
        }
        
        context = {
            'visited': [],
            'fatigue': 0.0
        }
        
        prompt = PromptTemplates.poi_analysis(poi_info, user_profile, context)
        
        print("  生成POI推荐理由...")
        response = llm_client.generate(
            prompt=prompt,
            temperature=0.7,
            max_tokens=300
        )
        
        print()
        print("  GPT-5分析结果:")
        print("  " + "-"*60)
        print(f"  {response}")
        print("  " + "-"*60)
        print()
        print("  ✅ POI分析测试成功！")
        print()
        
        # 4. 测试风险解释
        print("4️⃣  测试风险解释...")
        
        risk_info = {
            'choice_name': '太湖湿地公园',
            'risk_type': 'return',
            'finish_time': '17:30',
            'return_time': 1.0,
            'arrive_time': '18:30',
            'deadline': '18:00',
            'late_by': 0.5
        }
        
        prompt = PromptTemplates.risk_explanation(risk_info)
        
        print("  生成风险解释...")
        response = llm_client.generate(
            prompt=prompt,
            temperature=0.7,
            max_tokens=200
        )
        
        print()
        print("  GPT-5风险解释:")
        print("  " + "-"*60)
        print(f"  {response}")
        print("  " + "-"*60)
        print()
        print("  ✅ 风险解释测试成功！")
        print()
        
        # 总结
        print("="*70)
        print("  ✅ 所有测试通过！GPT-5接入成功！")
        print("="*70)
        print()
        print("📊 测试结果:")
        print("  • 客户端连接: ✅")
        print("  • 简单文本生成: ✅")
        print("  • POI深度分析: ✅")
        print("  • 风险解释: ✅")
        print()
        print("🎯 LLM已就绪，可以集成到系统中！")
        
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("💡 可能的问题:")
        print("  1. 检查API Key是否正确")
        print("  2. 检查API Base URL是否正确")
        print("  3. 检查网络连接")
        print("  4. 确认已安装openai库: pip install openai")


if __name__ == "__main__":
    test_llm_connection()
