"""
JARVIS Travel Agent Web Application
将4D Spatial Intelligence系统暴露为Web API
"""
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from config import settings  # 导入配置
import llm_config  # 导入LLM配置
from src.data_services.gaode_api_client import GaodeAPIClient
from src.data_services.poi_database import POIDatabase
from src.data_services.multi_source_collector import MultiSourceCollector
from src.core.progressive_planner import ProgressivePlanner, PlanningSession
from src.core.models import Location, POIType
from src.core.verification_engine import VerificationEngine
from src.core.scoring_engine import ScoringEngine
from src.core.explanation_layer import create_explanation_layer
from src.core.semantic_causal_flow import CausalFlowAnalyzer
from src.core.llm_client import create_llm_client

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 全局变量（生产环境应使用Redis等）
sessions = {}
planner_instance = None


def init_planner():
    """初始化规划器"""
    global planner_instance
    
    if planner_instance:
        return planner_instance
    
    print("🚀 正在初始化JARVIS系统...")
    
    # 初始化LLM（优先使用llm_config.py配置）
    llm_provider = os.environ.get('LLM_PROVIDER') or llm_config.LLM_PROVIDER
    llm_api_key = os.environ.get('LLM_API_KEY') or llm_config.LLM_API_KEY
    llm_api_base = llm_config.LLM_API_BASE
    llm_model = llm_config.LLM_MODEL
    
    # 如果provider不是mock但没有key，降级到mock
    if llm_provider != 'mock' and not llm_api_key:
        print(f"   ⚠️  {llm_provider} provider没有API key，降级到mock模式")
        llm_provider = 'mock'
    
    print(f"   LLM Provider: {llm_provider}")
    if llm_provider == 'deepseek':
        print(f"   DeepSeek API: {llm_api_base}")
        print(f"   Model: {llm_model}")
    
    llm_client = create_llm_client(
        provider=llm_provider,
        api_key=llm_api_key,
        api_base=llm_api_base if llm_provider == 'deepseek' else None,
        model=llm_model if llm_provider == 'deepseek' else None
    )
    
    # 初始化数据层
    print(f"   高德API Key: {settings.gaode_api_key[:10]}...")
    
    gaode_client = GaodeAPIClient(api_key=settings.gaode_api_key)
    poi_db = POIDatabase(data_dir=settings.data_dir, gaode_client=gaode_client)  # 🔥 传入gaode_client
    
    # 检查POI数据
    print(f"   当前POI数据库: {len(poi_db.pois)} 个POI")
    
    # 如果POI数据为空，使用Demo数据作为备份
    if len(poi_db.pois) == 0:
        print("   ⚠️ POI数据库为空，初始化Demo数据作为备份...")
        poi_db.initialize_demo_data()
        print(f"   Demo数据已加载: {len(poi_db.pois)} 个POI")
    
    # 初始化验证和评分引擎
    print("   初始化验证引擎和评分引擎...")
    collector = MultiSourceCollector(gaode_client)
    verification_engine = VerificationEngine(
        multi_source_collector=collector,
        neural_net_service=None,
        gaode_api_client=gaode_client
    )
    scoring_engine = ScoringEngine()
    
    # 初始化4D智能模块
    print("   初始化4D空间智能模块...")
    w_axis = CausalFlowAnalyzer(llm_client=llm_client)
    explainer = create_explanation_layer(llm_client=llm_client)
    
    # 创建规划器
    planner_instance = ProgressivePlanner(
        poi_db=poi_db,
        verification_engine=verification_engine,
        scoring_engine=scoring_engine,
        neural_net_service=None,
        w_axis=w_axis,
        explainer=explainer
    )
    
    print("✅ JARVIS系统初始化完成")
    return planner_instance


@app.route('/')
def index():
    """主页"""
    return render_template('jarvis_ui.html')


@app.route('/api/session/start', methods=['POST'])
def start_session():
    """
    开始新的规划会话
    
    POST Body:
    {
        "city": "苏州",
        "start_location": "苏州站",
        "duration_days": 3,
        "budget": 5000,
        "preferences": ["景点", "美食"]
    }
    """
    try:
        data = request.json
        planner = init_planner()
        
        # 创建起点Location对象
        city = data.get('city', '苏州')
        start_name = data.get('start_location', '苏州站')
        
        # 简化：使用预定义的起点坐标
        start_coords = {
            '苏州站': (31.3012, 120.5242),
            '苏州北站': (31.3986, 120.6186),
            '杭州东站': (30.2908, 120.2122),
            '厦门站': (24.4844, 118.0811)
        }
        
        lat, lon = start_coords.get(start_name, (31.3012, 120.5242))
        
        start_location = Location(
            id=f"{city}_station",
            name=start_name,
            lat=lat,
            lon=lon,
            type=POIType.TRANSPORT_HUB,
            address=f"{city}市"
        )
        
        # 创建用户输入
        preferences = data.get('preferences', ['景点'])
        user_input = f"我想在{city}游玩，偏好：{', '.join(preferences)}"
        
        # 创建会话
        duration_hours = data.get('duration_days', 3) * 24  # 转换为小时
        
        session = planner.initialize_session(
            user_input=user_input,
            start=start_location,
            destination_city=city,
            duration=duration_hours,
            budget=data.get('budget', 5000)
        )
        
        session_id = f"session_{len(sessions)}"
        sessions[session_id] = session
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'state': {
                'location': session.current_state.current_location.name,
                'time': session.current_state.current_time,
                'budget': session.current_state.remaining_budget
            }
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/plan/next', methods=['POST'])
def get_next_options():
    """
    获取下一步推荐选项
    
    POST Body:
    {
        "session_id": "session_0",
        "k": 5
    }
    """
    try:
        data = request.json
        session_id = data.get('session_id')
        k = data.get('k', 5)
        
        if session_id not in sessions:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        session = sessions[session_id]
        planner = init_planner()
        
        # 获取候选
        options = planner.get_next_options(session, k=k)
        
        if not options:
            return jsonify({
                'success': True,
                'options': [],
                'message': 'No more options available'
            })
        
        # 转换为JSON格式
        options_json = []
        for rank, opt in enumerate(options, 1):
            # 提取张力
            tensions = opt.w_axis_details.get('tensions', {}) if opt.w_axis_details else {}
            
            option_data = {
                'rank': rank,
                'name': opt.node.name,
                'type': opt.node.type.value,
                'address': opt.node.address,
                'lat': opt.node.lat,  # 🗺️ 经度
                'lon': opt.node.lon,  # 🗺️ 纬度
                'score': round(opt.score, 2),
                'w_axis': round(opt.c_causal, 2) if opt.c_causal else 0.5,
                'explanation': opt.explanation or "暂无解释",
                'tensions': {
                    'novelty': round(tensions.get('novelty', 0), 2),
                    'continuity': round(tensions.get('continuity', 0), 2),
                    'energy': round(tensions.get('energy', 0), 2),
                    'conflict': round(tensions.get('conflict', 0), 2)
                },
                'region': getattr(opt, 'region', '未知'),
                'visit_count': getattr(opt, 'visit_count', 0),
                'travel': {
                    'mode': opt.edges[0].mode.value if opt.edges else 'walk',
                    'time': round(opt.edges[0].time * 60, 0) if opt.edges else 0,
                    'cost': round(opt.edges[0].cost, 0) if opt.edges else 0
                } if opt.edges else None,
                'risk': {
                    'level': getattr(opt, 'risk_level', 'info'),
                    'message': opt.risk_info.get('short_message', '') if hasattr(opt, 'risk_info') and opt.risk_info else ''
                }
            }
            options_json.append(option_data)
        
        return jsonify({
            'success': True,
            'options': options_json,
            'session_state': {
                'current_location': session.current_state.current_location.name,
                'current_time': session.current_state.current_time,
                'budget_left': session.current_state.remaining_budget,
                'region_visits': dict(session.region_visit_counts)
            }
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/plan/select', methods=['POST'])
def select_option():
    """
    用户选择某个选项
    
    POST Body:
    {
        "session_id": "session_0",
        "option_index": 0
    }
    """
    try:
        data = request.json
        session_id = data.get('session_id')
        option_index = data.get('option_index', 0)
        
        if session_id not in sessions:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        session = sessions[session_id]
        planner = init_planner()
        
        # 重新获取选项（简化实现，生产环境应缓存）
        options = planner.get_next_options(session, k=5)
        
        if option_index >= len(options):
            return jsonify({'success': False, 'error': 'Invalid option index'}), 400
        
        selected_option = options[option_index]
        selected_edge = selected_option.edges[0] if selected_option.edges else None
        
        # 更新状态
        new_state = planner.user_select(session, selected_option, selected_edge)
        
        return jsonify({
            'success': True,
            'new_state': {
                'location': new_state.current_location.name,
                'time': new_state.current_time,
                'budget': new_state.remaining_budget
            },
            'message': f"已前往 {selected_option.node.name}"
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stats/radar', methods=['POST'])
def get_radar_data():
    """
    获取雷达图数据（基于当前张力和风险）
    
    POST Body:
    {
        "session_id": "session_0"
    }
    """
    try:
        data = request.json
        session_id = data.get('session_id')
        
        if session_id not in sessions:
            # 返回默认数据
            return jsonify({
                'success': True,
                'data': {
                    'traffic': 50,
                    'weather': 20,
                    'crowd': 60,
                    'safety': 10,
                    'price': 40
                }
            })
        
        session = sessions[session_id]
        planner = init_planner()
        
        # 获取最新选项
        options = planner.get_next_options(session, k=1)
        
        if not options:
            return jsonify({
                'success': True,
                'data': {
                    'traffic': 30,
                    'weather': 20,
                    'crowd': 40,
                    'safety': 15,
                    'price': 35
                }
            })
        
        opt = options[0]
        tensions = opt.w_axis_details.get('tensions', {}) if opt.w_axis_details else {}
        
        # 映射张力到雷达图
        # 冲突度 → 交通拥堵
        # 体力张力（负） → 人流密度
        # 新鲜感（负） → 价格波动
        radar_data = {
            'traffic': int(max(0, min(100, tensions.get('conflict', 0) * 100))),
            'weather': 20,  # 可以接入真实天气API
            'crowd': int(max(0, min(100, 50 - tensions.get('energy', 0) * 50))),
            'safety': int(max(0, min(100, 10 if opt.risk_level == 'info' else 50))),
            'price': int(max(0, min(100, 50 - tensions.get('novelty', 0) * 30)))
        }
        
        return jsonify({
            'success': True,
            'data': radar_data
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("🤖 JARVIS Travel Agent starting...")
    print("📍 访问 http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
