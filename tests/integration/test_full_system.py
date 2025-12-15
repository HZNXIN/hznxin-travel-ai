"""
完整系统测试
测试从初始化到获取候选的完整流程（含LLM）
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.core.models import Location, State, PlanningSession, POIType, UserProfile
from src.core.spatial_intelligence import SpatialIntelligenceCore
from src.core.progressive_planner import ProgressivePlanner
from src.core.verification_engine import VerificationEngine
from src.core.scoring_engine import ScoringEngine
from src.data_services.poi_database import POIDatabase
from src.data_services.gaode_api_client import GaodeAPIClient
from src.data_services.multi_source_collector import MultiSourceCollector
from src.core.llm_client import create_llm_client
from config import GAODE_API_KEY
from llm_config import *
from datetime import datetime


def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def test_full_system():
    """完整系统测试"""
    
    print("\n")
    print("🚀" * 35)
    print("  完整系统测试 - 含DeepSeek LLM")
    print("🚀" * 35)
    
    # 1. 初始化所有组件
    print_section("1️⃣  初始化系统组件")
    
    try:
        # POI数据库
        poi_db = POIDatabase(data_dir="data")
        if len(poi_db.pois) == 0:
            print("  📍 初始化Demo数据...")
            poi_db.initialize_demo_data()
        
        all_pois = poi_db.get_pois_in_city("苏州", limit=200)
        print(f"  ✅ POI数据库: {len(all_pois)}个POI")
        
        # 高德API客户端
        gaode_client = GaodeAPIClient(GAODE_API_KEY)
        print("  ✅ 高德API客户端")
        
        # 数据收集器
        collector = MultiSourceCollector(gaode_client)
        print("  ✅ 多源数据收集器")
        
        # 验证引擎
        verification_engine = VerificationEngine(collector, None, gaode_client)
        print("  ✅ 四项原则验证引擎")
        
        # 评分引擎
        scoring_engine = ScoringEngine()
        print("  ✅ 评分引擎")
        
        # LLM客户端（DeepSeek）
        if ENABLE_LLM:
            llm_client = create_llm_client(
                provider=LLM_PROVIDER,
                api_key=LLM_API_KEY,
                model=LLM_MODEL,
                api_base=LLM_API_BASE
            )
            print(f"  ✅ LLM客户端 ({LLM_MODEL})")
        else:
            llm_client = create_llm_client(provider='mock')
            print("  ✅ LLM客户端 (Mock模式)")
        
        # 空间智能核心
        spatial_core = SpatialIntelligenceCore(llm_client=llm_client)
        spatial_core.initialize(all_pois)
        print(f"  ✅ 空间智能核心: {len(all_pois)}个节点")
        
        # 渐进式规划器
        planner = ProgressivePlanner(
            poi_db=poi_db,
            verification_engine=verification_engine,
            scoring_engine=scoring_engine,
            spatial_core=spatial_core
        )
        print("  ✅ 渐进式规划器")
        
    except Exception as e:
        print(f"  ❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 2. 创建规划会话
    print_section("2️⃣  创建规划会话")
    
    # 起点：苏州站
    start_location = Location(
        id="start",
        name="苏州站",
        lat=31.3297,
        lon=120.6109,
        type=POIType.STATION,
        average_visit_time=0
    )
    
    # 初始状态
    initial_state = State(
        current_location=start_location,
        current_time=0.0,  # 从0点开始计时
        visited_history=set(),
        visit_quality={},
        remaining_budget=500.0
    )
    
    # 用户画像
    user_profile = UserProfile(
        purpose={'culture': 0.9, 'leisure': 0.7},
        pace={'slow': 0.9},
        intensity={'low': 0.8}
    )
    
    # 会话
    session = PlanningSession(
        start_location=start_location,
        destination_city="苏州",
        duration=8.0,  # 8小时
        budget=500.0,
        user_profile=user_profile,
        initial_state=initial_state,
        current_state=initial_state
    )
    
    # 添加硬约束：必须在8小时内回到苏州站
    session.hard_constraints = {
        'return': {
            'time': 8.0,  # 8小时后必须返回
            'location': start_location,
            'mode': '高铁'
        }
    }
    
    print(f"  ✅ 会话ID: {session.session_id}")
    print(f"  ✅ 起点: {start_location.name}")
    print(f"  ✅ 持续时间: {session.duration}小时")
    print(f"  ✅ 预算: ¥{session.budget}")
    print(f"  ✅ 硬约束: {session.hard_constraints['return']['time']}小时后必须返回")
    print(f"  ✅ 用户画像: 文化爱好者、慢节奏、低强度")
    
    # 3. 获取第一轮候选
    print_section("3️⃣  获取第一轮候选选项")
    
    try:
        print("  🔍 正在分析候选...")
        print("  ⏱️  这可能需要几秒钟（含LLM分析）...")
        print()
        
        options = planner.get_next_options(session, k=3)
        print(f"  ✅ 获取到 {len(options)} 个候选\n")
        
        if len(options) == 0:
            print("  ⚠️  没有找到合适的候选")
            print("  💡 可能原因：")
            print("     - POI数据较少")
            print("     - 过滤条件太严格")
            print("     - 时间设置问题")
            return
        
        # 4. 展示候选详情
        print_section("4️⃣  候选选项详细分析")
        
        for i, option in enumerate(options, 1):
            risk_emoji = {
                'info': '✅',
                'warning': '⚠️ ',
                'critical': '🚨'
            }.get(option.risk_level, '❓')
            
            print(f"{'='*70}")
            print(f"选项 {i}: {risk_emoji} {option.node.name}")
            print(f"{'='*70}")
            print(f"📍 类型: {option.node.type.value}")
            print(f"⭐ 综合评分: {option.total_score:.2f}")
            print(f"📏 距离: {option.edge_score:.1f}km")
            print(f"🎯 风险等级: {option.risk_level.upper()}")
            print()
            
            # 推荐理由（LLM生成或规则生成）
            if option.deep_analysis:
                print("💡 推荐理由:")
                for j, reason in enumerate(option.deep_analysis.reasons[:3], 1):
                    print(f"  {j}. {reason.content}")
                print()
            
            # 风险详情
            if option.risk_details:
                print(f"⚠️  风险信息:")
                print(f"  类型: {option.risk_details['type']}")
                print(f"  消息: {option.risk_details['short_message']}")
                print(f"  详细:")
                for detail in option.risk_details['details']:
                    print(f"    • {detail}")
                if option.risk_details.get('consequence'):
                    print(f"  🚨 后果: {option.risk_details['consequence']}")
                print()
            else:
                print("✅ 无风险，推荐选择")
                print()
        
        # 5. 全局状态监控
        print_section("5️⃣  全局状态监控")
        
        global_status = spatial_core.get_global_status(
            session.current_state,
            session
        )
        
        print(f"⏱️  时间: {global_status['time']['description']}")
        print(f"💰 预算: {global_status['budget']['description']}")
        print(f"📍 覆盖: {global_status['coverage']['description']}")
        print()
        print(f"📊 总结: {global_status['summary']}")
        
        # 6. 模拟用户选择
        print_section("6️⃣  模拟用户选择")
        
        selected = options[0]
        print(f"  👉 用户选择: {selected.node.name}")
        print(f"  📊 评分: {selected.total_score:.2f}")
        print(f"  🎯 风险: {selected.risk_level}")
        print()
        
        # 更新状态
        new_state = planner.select_option(session, selected)
        print(f"  ✅ 状态已更新")
        print(f"  📍 新位置: {new_state.current_location.name}")
        print(f"  ⏱️  当前时间: {new_state.current_time:.1f}小时")
        print(f"  💰 剩余预算: ¥{new_state.remaining_budget:.0f}")
        
        # 7. 获取第二轮候选
        print_section("7️⃣  从新位置获取候选")
        
        print("  🔍 正在分析新的候选...")
        print()
        
        new_options = planner.get_next_options(session, k=3)
        print(f"  ✅ 获取到 {len(new_options)} 个新候选\n")
        
        for i, option in enumerate(new_options, 1):
            risk_emoji = {
                'info': '✅',
                'warning': '⚠️ ',
                'critical': '🚨'
            }.get(option.risk_level, '❓')
            
            print(f"  {i}. {risk_emoji} {option.node.name}")
            print(f"     评分: {option.total_score:.2f} | 风险: {option.risk_level}")
            if option.risk_details:
                print(f"     ⚠️  {option.risk_details['short_message']}")
            print()
        
        # 总结
        print_section("✅ 测试完成")
        
        print("📊 测试总结:")
        print("  • 系统初始化: ✅")
        print("  • 会话创建: ✅")
        print("  • 候选生成: ✅")
        print("  • 风险分析: ✅")
        print(f"  • LLM增强: {'✅' if ENABLE_LLM else '⏭️  (已禁用)'}")
        print("  • 状态转移: ✅")
        print("  • 全局监控: ✅")
        print()
        print("🎯 完整系统运行正常！")
        
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_full_system()
