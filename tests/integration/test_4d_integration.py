"""
四维空间智能系统 - 完整集成测试
测试W轴、解释层等新功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.progressive_planner import ProgressivePlanner
from src.core.verification_engine import VerificationEngine
from src.core.scoring_engine import ScoringEngine
from src.data_services.gaode_api_client import GaodeAPIClient
from src.data_services.multi_source_collector import MultiSourceCollector
from src.data_services.poi_database import POIDatabase
from src.core.models import Location, POIType

# 🔥 新增：四维空间智能组件
from src.core.llm_client import create_llm_client
from src.core.semantic_causal_flow import SemanticCausalFlow
from src.core.explanation_layer import ExplanationLayer
from llm_config import LLM_API_KEY, LLM_API_BASE, LLM_MODEL


def initialize_4d_system():
    """初始化四维空间智能系统"""
    print("🌌 正在初始化四维空间智能系统...")
    
    try:
        # 1. 基础组件
        from config import GAODE_API_KEY
        gaode_client = GaodeAPIClient(api_key=GAODE_API_KEY)
        poi_db = POIDatabase(data_dir="data")
        
        if len(poi_db.pois) == 0:
            print("初始化Demo POI数据...")
            poi_db.initialize_demo_data()
        
        collector = MultiSourceCollector(gaode_client)
        verification_engine = VerificationEngine(
            multi_source_collector=collector,
            neural_net_service=None,
            gaode_api_client=gaode_client
        )
        scoring_engine = ScoringEngine()
        
        # 2. 🔥 四维空间智能组件
        print("   ✅ 初始化LLM客户端（DeepSeek）...")
        llm_client = create_llm_client(
            provider="deepseek",
            api_key=LLM_API_KEY,
            model=LLM_MODEL
        )
        
        print("   ✅ 初始化W轴（语义-因果流）...")
        w_axis = SemanticCausalFlow(
            llm_client=llm_client,
            delta=0.1,
            epsilon=0.1,
            enable_concurrent=True  # 🔥 启用并发
        )
        
        print("   ✅ 初始化解释层（人性化表达）...")
        explainer = ExplanationLayer(llm_client=llm_client)
        
        # 3. 创建增强版Planner
        print("   ✅ 创建增强版Planner...")
        planner = ProgressivePlanner(
            poi_db=poi_db,
            verification_engine=verification_engine,
            scoring_engine=scoring_engine,
            neural_net_service=None,
            w_axis=w_axis,          # 🔥 集成W轴
            explainer=explainer      # 🔥 集成解释层
        )
        
        print("🎉 四维空间智能系统初始化成功！\n")
        return planner, poi_db
        
    except Exception as e:
        print(f"❌ 系统初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def create_test_session(planner):
    """创建测试会话"""
    print("创建测试会话...")
    print("场景: 从苏州站出发，游玩苏州3天\n")
    
    start = Location(
        id="suzhou_station",
        name="苏州站",
        lat=31.3012,
        lon=120.5242,
        type=POIType.TRANSPORT_HUB,
        address="苏州市姑苏区苏站路"
    )
    
    session = planner.initialize_session(
        user_input="我想去苏州玩3天，喜欢休闲慢节奏，不要太累",
        start=start,
        destination_city="苏州",
        duration=72.0,
        budget=5000.0
    )
    
    print(f"✅ 会话创建成功")
    print(f"会话ID: {session.session_id}")
    print(f"起点: {session.start_location.name}")
    print(f"持续时间: {session.duration/24:.0f}天")
    print(f"预算: ¥{session.budget:.0f}\n")
    
    return session


def display_4d_options(options):
    """展示四维空间智能增强的候选选项"""
    print(f"\n🌌 找到 {len(options)} 个候选选项（四维空间智能增强）:\n")
    print("="*80)
    
    for i, option in enumerate(options, 1):
        print(f"\n【选项{i}】{option.node.name}")
        print("-"*80)
        
        # 🔥 人性化解释（最重要！）
        if hasattr(option, 'explanation') and option.explanation:
            print(f"💭 {option.explanation}")
            print()
        
        # 基本信息
        print(f"📍 位置: {option.node.address}")
        print(f"🏷️  类型: {option.node.type.value}")
        
        # 评分信息
        score_text = f"⭐ 综合评分: {option.score:.2f}"
        if hasattr(option, 'c_causal') and option.c_causal is not None:
            score_text += f" | 🌌 W轴: {option.c_causal:.2f}"
        print(score_text)
        
        print(f"💝 匹配度: {option.match_score:.2f}")
        print(f"🔍 可信度: {option.verification.overall_trust_score:.2f}")
        
        # 🔥 张力信息（新增）
        if hasattr(option, 'w_axis_details') and option.w_axis_details:
            tensions = option.w_axis_details.get('tensions', {})
            if tensions:
                print(f"⚡ 张力:")
                novelty = tensions.get('novelty', 0)
                continuity = tensions.get('continuity', 0)
                energy = tensions.get('energy', 0)
                conflict = tensions.get('conflict', 0)
                
                novelty_emoji = "✨" if novelty > 0 else "🔄"
                energy_emoji = "💪" if energy > 0 else "😴"
                conflict_emoji = "⚔️" if conflict > 0.3 else "✅"
                
                print(f"   {novelty_emoji} 新鲜感: {novelty:+.2f} | {energy_emoji} 体力: {energy:+.2f}")
                print(f"   🔗 连续性: {continuity:+.2f} | {conflict_emoji} 冲突: {conflict:.2f}")
        
        # 🔥 区域信息
        if hasattr(option, 'region') and option.region:
            if hasattr(option, 'visit_count') and option.visit_count is not None:
                if option.visit_count == 0:
                    visit_text = "✨ 首次访问"
                else:
                    visit_text = f"🔄 第{option.visit_count+1}次访问"
                print(f"🗺️  区域: {option.region}（{visit_text}）")
        
        # 交通方式
        if option.edges:
            edge = option.edges[0]
            time_min = edge.time * 60
            print(f"🚶 {edge.mode.value}: {time_min:.0f}分钟, ¥{edge.cost:.0f}")
    
    print("\n" + "="*80)


def test_single_step(planner, session):
    """测试单步推荐"""
    print("\n" + "="*80)
    print(f"📍 当前位置: {session.current_state.current_location.name}")
    print(f"⏰ 当前时间: {session.current_state.current_time:.1f}小时")
    print(f"💰 剩余预算: ¥{session.current_state.remaining_budget:.0f}")
    print("="*80)
    
    # 获取候选选项
    print("\n🔍 正在获取候选选项...")
    options = planner.get_next_options(session, k=5)
    
    if not options:
        print("❌ 没有找到候选选项")
        return False
    
    # 显示选项
    display_4d_options(options)
    
    # 🔥 修复：不自动选择，提示用户思考
    print(f"\n" + "="*80)
    print("❓ 你会怎么选？")
    print("   1️⃣ {:<30}".format(options[0].node.name[:28]))
    if len(options) > 1:
        print("   2️⃣ {:<30} ← 也许更好？".format(options[1].node.name[:28]))
    print("="*80)
    
    # 为演示，自动选择第一个（实际应该等用户输入）
    print(f"\n💭 系统建议: {options[0].explanation}")
    if len(options) > 1 and options[1].explanation:
        print(f"💭 但第二选择说: {options[1].explanation}")
    
    print(f"\n🎯 暂且选择: {options[0].node.name}（实际应该让用户决定）")
    selected_edge = options[0].edges[0]
    new_state = planner.user_select(session, options[0], selected_edge)
    
    print(f"✅ 已前往 {options[0].node.name}")
    print(f"   耗时: {selected_edge.time*60:.0f}分钟")
    print(f"   花费: ¥{selected_edge.cost:.0f}")
    
    # 显示区域访问统计
    if session.region_visit_counts:
        print(f"\n📊 区域访问统计:")
        for region, count in session.region_visit_counts.items():
            print(f"   - {region}: {count}次")
    
    return True


def test_region_soft_constraint(planner, session):
    """测试区域软约束"""
    print("\n" + "="*80)
    print("🧪 测试区域软约束（连续访问同一区域）")
    print("="*80)
    
    steps = 3
    for i in range(steps):
        print(f"\n--- 第{i+1}步 ---")
        success = test_single_step(planner, session)
        if not success:
            break
        
        if i < steps - 1:
            input("\n按Enter继续下一步...")


def main():
    """主函数"""
    print("\n" + "="*80)
    print("🌌 四维空间智能旅行规划系统 - 集成测试")
    print("="*80 + "\n")
    
    # 1. 初始化系统
    planner, poi_db = initialize_4d_system()
    if not planner:
        return
    
    # 2. 创建会话
    session = create_test_session(planner)
    
    # 3. 测试区域软约束
    test_region_soft_constraint(planner, session)
    
    print("\n" + "="*80)
    print("✅ 测试完成！")
    print("="*80)
    
    # 显示最终统计
    print("\n📊 最终统计:")
    print(f"   - 访问景点数: {len(session.current_state.visited_history)}")
    print(f"   - 总耗时: {session.current_state.current_time:.1f}小时")
    print(f"   - 总花费: ¥{session.budget - session.current_state.remaining_budget:.0f}")
    print(f"   - 区域访问: {dict(session.region_visit_counts)}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 测试中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
