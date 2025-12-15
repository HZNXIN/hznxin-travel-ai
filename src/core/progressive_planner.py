"""
渐进式规划引擎
实现核心的渐进式拓扑决策算法
"""

from typing import List, Dict, Optional, Tuple, Set
import math
from dataclasses import dataclass

from .models import (
    Location, Edge, State, Action, CandidateOption,
    UserProfile, PlanningSession, TransportMode, POIType,
    NodeVerification
)
from .poi_quality_filter import POIQualityFilter, get_poi_quality_explanation
from .semantic_causal_flow import SemanticCausalFlow  # 🔥 新增：W轴
from .explanation_layer import ExplanationLayer  # 🔥 新增：解释层


class ProgressivePlanner:
    """
    渐进式规划引擎
    
    核心算法:
    1. 动态构建图 G(σ) = (V(σ), E(σ))
    2. 渐进式展开候选节点
    3. 用户选择后状态转移 δ(σ, a) → σ'
    
    数学模型:
    - 状态空间 Σ
    - 动作空间 A(σ)
    - 状态转移函数 δ: Σ × A → Σ
    """
    
    def __init__(self,
                 poi_db,
                 verification_engine,
                 scoring_engine,
                 quality_filter=None,
                 deep_analyzer=None,
                 neural_net_service=None,
                 spatial_core=None,
                 w_axis=None,
                 explainer=None):
        """
        初始化规划器
        
        Args:
            poi_db: POI数据库
            verification_engine: 验证引擎（四项原则）
            scoring_engine: 评分引擎
            quality_filter: 质量过滤器
            deep_analyzer: 深度分析器
            neural_net_service: 神经网络服务（可选）
            spatial_core: 空间智能核心（可选）
            w_axis: W轴因果流（可选）🔥
            explainer: 解释层（可选）🔥
        """
        self.poi_db = poi_db
        self.verification_engine = verification_engine
        self.scoring_engine = scoring_engine
        self.nn_service = neural_net_service
        self.spatial_core = spatial_core  # 空间智能核心
        self.w_axis = w_axis  # 🔥 W轴（四维空间智能）
        self.explainer = explainer  # 🔥 解释层（人性化表达）
        
        # 注意：region_visit_counts现在存储在session中，不再是实例变量
        
        # POI质量过滤器
        from .poi_quality_filter import POIQualityFilter
        self.quality_filter = quality_filter or POIQualityFilter()
        
        # 深度分析器
        from .poi_deep_analyzer import POIDeepAnalyzer
        self.deep_analyzer = deep_analyzer or POIDeepAnalyzer()
        
        # 配置参数
        self.config = {
            'max_candidates': 10,  # 最多返回候选数
            'max_distance_km': 50,  # 最大距离（km）
            'max_detour_rate': 0.5,  # 最大绕路率
            'min_consistency_score': 0.7,  # 最小一致性分数
            'min_trust_score': 0.6,  # 最小可信度
            'crowd_threshold': 0.7,  # 拥挤度阈值
            'enable_quality_filter': True,  # 启用质量过滤
        }
    
    def initialize_session(self,
                          user_input: str,
                          start: Location,
                          destination_city: str,
                          duration: float,
                          budget: float) -> PlanningSession:
        """
        初始化规划会话
        
        Args:
            user_input: 用户输入的自然语言
            start: 起点
            destination_city: 目的地城市
            duration: 持续时间（小时）
            budget: 预算
            
        Returns:
            规划会话
        """
        # 1. 提取用户画像（使用神经网络）
        if self.nn_service:
            user_profile = self.nn_service.extract_user_profile(
                user_input, []
            )
        else:
            user_profile = self._default_user_profile()
        
        # 2. 创建初始状态
        initial_state = State(
            current_location=start,
            current_time=0.0,
            visited_history=set(),
            visit_quality={},
            remaining_budget=budget
        )
        
        # 3. 创建会话
        session = PlanningSession(
            start_location=start,
            destination_city=destination_city,
            duration=duration,
            budget=budget,
            user_profile=user_profile,
            current_state=initial_state
        )
        
        return session
    
    def get_next_options(self,
                        session: PlanningSession,
                        k: Optional[int] = None) -> List[CandidateOption]:
        """
        获取下一步的候选选项（核心算法）
        
        算法流程:
        1. 计算候选节点 Candidates(σ) = {v | Reachable(v, σ) ∧ Verified(v)}
        2. 为每个候选节点计算所有可达边
        3. 验证每个节点（四项原则）
        4. 计算综合评分
        5. 排序并返回 top-k
        
        数学定义:
        Candidates(σ) = {v ∈ Location | 
            Reachable(v, σ) ∧
            Spatial_Score(σ.l, v) ≥ θ_spatial ∧
            Temporal_Score(v, σ.t) ≥ θ_temporal ∧
            Consistency(v) ≥ θ_consistency
        }
        
        Args:
            session: 当前会话
            k: 返回的候选数量
            
        Returns:
            候选选项列表
        """
        if k is None:
            k = self.config['max_candidates']
        
        state = session.current_state
        profile = session.user_profile
        
        # 1. 计算候选节点
        candidates = self._compute_candidates(session)
        print(f"   [ProgressivePlanner] 计算候选: {len(candidates)} 个初始候选")
        
        # 2. 为每个候选节点构建完整信息
        options = []
        for idx, node in enumerate(candidates):
            print(f"   [ProgressivePlanner] 处理候选 {idx+1}/{len(candidates)}: {node.name}")
            try:
                # 2.1 计算所有可达边
                edges = self._compute_edges(state, node)
                print(f"      边数: {len(edges)}")
                
                if not edges:
                    print(f"      ❌ 跳过: 无可达边")
                    continue
                
                # 2.2 验证节点（四项原则）
                verification = self.verification_engine.verify(
                    node, state, session
                )
                if verification is None:
                    print(f"      ❌ 跳过: verification返回None")
                    continue
                print(f"      验证: Trust={verification.overall_trust_score:.2f}")
                
                # 2.3 计算综合评分
                score = self.scoring_engine.compute_score(
                    node, edges, verification, profile, state
                )
                print(f"      评分: {score:.3f}")
                
                # 2.4 计算匹配度
                match_score = self.scoring_engine.compute_match_score(
                    node, profile
                )
                
                # 2.5 预览未来可能
                future_preview = self._preview_future(node, state, session)
                
                # 2.6 质量过滤（关键！不推荐低质量POI）
                quality_score = None
                if self.config['enable_quality_filter']:
                    # 评估质量
                    quality_score = self.quality_filter.evaluate_quality(node, verification)
                    # 检查是否值得推荐
                    is_recommended = self.quality_filter.is_worth_recommending(node, verification)
                    if not is_recommended:
                        # 跳过低质量POI：评论少、评分低、可玩性差
                        print(f"      ❌ 跳过: 未通过质量过滤")
                        continue
                
                # 2.7 深度分析
                context = {
                    'distance_km': min(e.distance for e in edges),
                    'travel_time': min(e.time for e in edges),
                    'current_time': state.current_time
                }
                deep_analysis = self.deep_analyzer.analyze(
                    poi=node,
                    verification=verification,
                    quality_score=quality_score,
                    user_profile=profile,
                    context=context
                )
                
                # ✅ 检查deep_analysis是否为None
                if deep_analysis is None:
                    print(f"      ❌ 跳过: deep_analysis返回None")
                    continue
                
                # 2.8 构建选项
                option = CandidateOption(
                    node=node,
                    edges=edges,
                    verification=verification,
                    score=score,
                    match_score=match_score,
                    future_preview=future_preview
                )
                # 添加扩展字段
                option.quality_score = quality_score
                option.deep_analysis = deep_analysis
                option.edge_score = min(e.distance for e in edges)  # 最短距离
                option.total_score = deep_analysis.overall_score
                
                options.append(option)
                print(f"      ✅ 添加成功")
                
            except Exception as e:
                # 记录错误但继续处理其他候选
                import traceback
                print(f"      ❌ 异常: {e}")
                print(f"      详情: {traceback.format_exc()[:200]}")
                continue
        
        # 3. 🔥 W轴批量推理（四维空间智能）
        print(f"   ✅ 最终候选数: {len(options)}")
        
        if options and self.w_axis:
            try:
                print(f"   🌌 W轴批量推理...")
                import time
                start_time = time.time()
                
                # 构建批量推理任务
                tasks = []
                for option in options:
                    context = {
                        'weather': 'sunny',  # TODO: 从session获取
                        'time_of_day': int(state.current_time),
                        'visited_regions': dict(session.region_visit_counts)
                    }
                    tasks.append({
                        'current': state.current_location,
                        'next': option.node,
                        'context': context
                    })
                
                # 批量并发推理（🔥 现在返回结构化张力）
                w_results = self.w_axis.batch_compute_causal_flow(tasks)
                
                elapsed = time.time() - start_time
                c_causals = [r['c_causal'] for r in w_results]
                print(f"   ✅ W轴推理完成: {len(w_results)}个 ({elapsed:.2f}秒)")
                print(f"      C_causal范围: {min(c_causals):.3f} - {max(c_causals):.3f}")
                
                # 🔥 提取张力统计
                avg_conflict = sum(r['tensions']['conflict'] for r in w_results) / len(w_results)
                print(f"      平均冲突度: {avg_conflict:.3f}（{"高冲突" if avg_conflict > 0.3 else "低冲突"}）")
                
                # 设置W轴相关字段
                for option, w_result in zip(options, w_results):
                    option.c_causal = w_result['c_causal']
                    option.region = self._get_region(option.node)
                    option.visit_count = session.region_visit_counts.get(option.region, 0)
                    
                    # 🔥 保存完整张力信息
                    option.w_axis_details = {
                        'c_causal': w_result['c_causal'],
                        'tensions': w_result['tensions'],
                        'region': option.region,
                        'visit_count': option.visit_count
                    }
                    
            except Exception as e:
                print(f"   ⚠️  W轴推理失败，继续使用基础评分: {e}")
                # 降级：设置默认值
                for option in options:
                    option.c_causal = 0.5
                    option.region = self._get_region(option.node)
                    option.visit_count = session.region_visit_counts.get(option.region, 0)
        
        elif options:
            # 没有W轴时，设置基本字段
            for option in options:
                option.c_causal = None
                option.region = self._get_region(option.node)
                option.visit_count = session.region_visit_counts.get(option.region, 0)
        
        # 4. 排序（按综合评分）
        options.sort(key=lambda x: x.score, reverse=True)
        
        # 3.5 风险分析（使用SpatialIntelligenceCore）
        if self.spatial_core:
            for option in options:
                try:
                    # 分析风险等级
                    risk_analysis = self.spatial_core.analyze_with_risk_level(
                        option.node,
                        state,
                        session
                    )
                    
                    # 设置风险等级
                    option.risk_level = risk_analysis.risk_level
                    
                    # 设置风险详情（如果有）
                    if risk_analysis.risk_level != 'info':
                        option.risk_details = {
                            'type': risk_analysis.risk_type,
                            'short_message': self._get_risk_message(risk_analysis),
                            'details': self._format_risk_details(risk_analysis),
                            'consequence': self._get_consequence(risk_analysis)
                        }
                except Exception as e:
                    print(f"Risk analysis error for {option.node.name}: {e}")
                    # 降级：保持默认的info级别
                    option.risk_level = 'info'
        
        # 4. 🔥 生成人性化解释（解释层 - 敢质疑、敢犹豫）
        top_options = options[:k]
        
        if top_options and self.explainer:
            try:
                print(f"   💭 生成人性化解释...")
                
                for rank, option in enumerate(top_options, 1):
                    # 🔥 构建上下文（包含张力信息）
                    context = {
                        'time': self._format_time(state.current_time),
                        'weather': 'sunny',  # TODO: 从session获取
                        'visited_regions': dict(session.region_visit_counts),
                        'c_causal': option.c_causal if option.c_causal else 0.5,
                        'tensions': option.w_axis_details.get('tensions', {}) if option.w_axis_details else {}
                    }
                    
                    # 🔥 传递rank和alternatives（让系统敢质疑）
                    alternatives = top_options[1:3] if rank == 1 and len(top_options) > 1 else None
                    
                    # 生成解释
                    explanation = self.explainer.explain_choice(
                        option, 
                        context, 
                        rank=rank,  # 🔥 传递排名
                        alternatives=alternatives  # 🔥 传递备选
                    )
                    option.explanation = explanation
                
                print(f"   ✅ 解释生成完成")
                
            except Exception as e:
                print(f"   ⚠️  解释生成失败: {e}")
                # 降级：不设置explanation（保持None）
        
        # 5. 返回 top-k
        return top_options
    
    def user_select(self,
                   session: PlanningSession,
                   selected_option: CandidateOption,
                   selected_edge: Edge) -> State:
        """
        用户选择后，执行状态转移
        
        数学定义:
        δ(σ, a) = σ' where σ' = (l', t', H', V', budget')
        
        Args:
            session: 当前会话
            selected_option: 用户选择的选项
            selected_edge: 用户选择的边（交通方式）
            
        Returns:
            新状态
        """
        old_state = session.current_state
        node = selected_option.node
        
        # 构建动作
        action = Action(
            target_node=node,
            transport_mode=selected_edge.mode,
            selected_edge=selected_edge,
            estimated_time=selected_edge.time + node.average_visit_time,
            estimated_cost=selected_edge.cost + node.ticket_price
        )
        
        # 状态转移 δ(σ, a) → σ'
        new_state = self._state_transition(old_state, action, selected_edge)
        
        # 🔥 更新区域访问计数（四维空间智能）
        region = self._get_region(node)
        session.region_visit_counts[region] = session.region_visit_counts.get(region, 0) + 1
        
        # 更新会话
        session.current_state = new_state
        session.add_history(action, old_state, new_state)
        
        return new_state
    
    def _compute_candidates(self, session: PlanningSession) -> List[Location]:
        """
        计算候选节点
        
        算法:
        1. 从POI数据库获取目的地城市的所有POI
        2. 空间过滤（距离合理）
        3. 时间过滤（时间充足）
        4. 逻辑过滤（上下文相关）
        5. 去重（避免重复访问）
        
        返回:
            候选节点列表
        """
        state = session.current_state
        current = state.current_location
        
        # 1. 获取所有POI
        all_pois = self.poi_db.get_pois_in_city(session.destination_city)
        
        candidates = []
        
        for poi in all_pois:
            # 2. 空间过滤
            if not self._spatial_filter(current, poi, state):
                continue
            
            # 3. 时间过滤
            if not self._temporal_filter(poi, state, session.duration):
                continue
            
            # 4. 逻辑过滤（上下文）
            if not self._contextual_filter(poi, state, session):
                continue
            
            # 5. 去重
            if poi.id in state.visited_history:
                continue
            
            candidates.append(poi)
        
        return candidates
    
    def _spatial_filter(self,
                       current: Location,
                       target: Location,
                       state: State) -> bool:
        """
        空间可行性过滤
        
        条件:
        1. distance(current, target) ≤ θ_max_dist
        2. 连通（存在路径）
        
        Args:
            current: 当前位置
            target: 目标位置
            state: 当前状态
            
        Returns:
            是否通过过滤
        """
        # 计算直线距离
        distance = self._haversine_distance(current, target)
        
        # 距离过滤
        if distance > self.config['max_distance_km']:
            return False
        
        # 检查连通性（简化：假设都连通）
        # 实际应该调用高德API检查是否有路径
        return True
    
    def _temporal_filter(self,
                        poi: Location,
                        state: State,
                        total_duration: float) -> bool:
        """
        时间可行性过滤
        
        条件:
        1. 营业时间内
        2. 剩余时间充足
        
        Args:
            poi: POI
            state: 当前状态
            total_duration: 总持续时间
            
        Returns:
            是否通过过滤
        """
        # 检查配置是否禁用时间过滤
        if not self.config.get('enable_temporal_filter', True):
            return True  # 禁用时间过滤，全部通过
        
        # 1. 检查营业时间
        if not poi.is_open(state.current_time):
            return False
        
        # 2. 检查剩余时间
        remaining = total_duration - state.current_time
        required = poi.average_visit_time + 1.0  # 加上预估交通时间
        
        if remaining < required:
            return False
        
        return True
    
    def _contextual_filter(self,
                          poi: Location,
                          state: State,
                          session: PlanningSession) -> bool:
        """
        上下文逻辑过滤
        
        根据当前时间、位置、已访问节点等，判断POI是否合适
        
        Args:
            poi: POI
            state: 当前状态
            session: 会话
            
        Returns:
            是否通过过滤
        """
        # 当前时间（小时）
        # 注意：current_time是从开始的累计小时数，需要转换为一天中的小时
        # 假设从上午9点开始
        start_hour = 9  # 假设从上午9点开始旅行
        elapsed_hours = state.current_time
        hour = (start_hour + elapsed_hours) % 24
        
        # 凌晨（0:00-6:00）只推荐酒店
        if 0 <= hour < 6:
            if poi.type != POIType.HOTEL:
                return False
        
        # 清晨（6:00-9:00）推荐餐厅或景点
        if 6 <= hour < 9:
            if poi.type not in [POIType.RESTAURANT, POIType.ATTRACTION, POIType.HOTEL]:
                return False
        
        # 晚上（21:00-24:00）主要推荐餐厅、酒店
        if 21 <= hour < 24:
            if poi.type not in [POIType.RESTAURANT, POIType.HOTEL, 
                               POIType.ENTERTAINMENT]:
                return False
        
        # 其他时间（9:00-21:00）所有类型都可以
        return True
    
    def _compute_edges(self,
                      state: State,
                      target: Location) -> List[Edge]:
        """
        计算从当前位置到目标的所有可达边
        
        算法:
        1. 步行（distance < 2km）
        2. 打车
        3. 公交（如果可用）
        4. 地铁（如果可用）
        
        Args:
            state: 当前状态
            target: 目标位置
            
        Returns:
            边列表
        """
        current = state.current_location
        edges = []
        
        # 1. 步行
        walk_edge = self._compute_walk_edge(current, target)
        if walk_edge and walk_edge.distance < 2.0:  # 2km内才考虑步行
            edges.append(walk_edge)
        
        # 2. 打车
        taxi_edge = self._compute_taxi_edge(current, target)
        if taxi_edge:
            edges.append(taxi_edge)
        
        # 3. 公交（基于高德API）
        try:
            bus_edge = self._compute_bus_edge(current, target)
            if bus_edge:
                edges.append(bus_edge)
        except Exception as e:
            # 公交路线获取失败，降级跳过
            print(f"公交路线计算失败: {e}")
        
        # 4. 地铁（简化实现：基于距离估算）
        try:
            subway_edge = self._compute_subway_edge(current, target)
            if subway_edge:
                edges.append(subway_edge)
        except Exception as e:
            # 地铁路线获取失败，降级跳过
            print(f"地铁路线计算失败: {e}")
        
        return edges
    
    def _compute_walk_edge(self,
                          from_loc: Location,
                          to_loc: Location) -> Optional[Edge]:
        """
        计算步行边
        
        算法:
        distance = haversine(from, to)
        time = distance / walking_speed  (假设 4 km/h)
        cost = 0
        """
        distance = self._haversine_distance(from_loc, to_loc)
        
        # 步行速度 4 km/h
        time = distance / 4.0
        
        edge = Edge(
            id=f"walk_{from_loc.id}_{to_loc.id}",
            from_loc=from_loc,
            to_loc=to_loc,
            mode=TransportMode.WALK,
            distance=distance,
            time=time,
            cost=0.0
        )
        
        return edge
    
    def _compute_taxi_edge(self,
                          from_loc: Location,
                          to_loc: Location) -> Optional[Edge]:
        """
        计算打车边
        
        算法:
        distance = route_distance(from, to)  # 高德API
        time = distance / avg_speed + traffic_delay
        cost = base_fare + price_per_km * distance
        """
        # 调用高德API获取实际路径距离
        # 这里简化：使用直线距离 * 1.3
        straight_distance = self._haversine_distance(from_loc, to_loc)
        distance = straight_distance * 1.3
        
        # 平均速度30km/h（考虑市区路况）
        time = distance / 30.0
        
        # 打车费用：起步价13元 + 2.5元/km
        cost = 13.0 + 2.5 * distance
        
        edge = Edge(
            id=f"taxi_{from_loc.id}_{to_loc.id}",
            from_loc=from_loc,
            to_loc=to_loc,
            mode=TransportMode.TAXI,
            distance=distance,
            time=time,
            cost=cost
        )
        
        return edge
    
    def _compute_bus_edge(self,
                         from_loc: Location,
                         to_loc: Location) -> Optional[Edge]:
        """
        计算公交边
        
        基于高德API的公交路径规划
        如果距离太近（<1km）或太远（>20km），不推荐公交
        """
        straight_distance = self._haversine_distance(from_loc, to_loc)
        
        # 距离过滤
        if straight_distance < 1.0 or straight_distance > 20.0:
            return None
        
        # 简化实现：估算公交时间和费用
        # 实际应调用高德API: gaode_api.get_route_transit()
        distance = straight_distance * 1.4  # 公交实际距离约为直线距离的1.4倍
        time = distance / 15.0 + 0.3  # 平均速度15km/h + 等待时间0.3h
        cost = 2.0  # 公交票价通常2元
        
        edge = Edge(
            id=f"bus_{from_loc.id}_{to_loc.id}",
            from_loc=from_loc,
            to_loc=to_loc,
            mode=TransportMode.BUS,
            distance=distance,
            time=time,
            cost=cost
        )
        
        return edge
    
    def _compute_subway_edge(self,
                            from_loc: Location,
                            to_loc: Location) -> Optional[Edge]:
        """
        计算地铁边
        
        简化实现：仅在有地铁的城市（如苏州、上海）且距离适中时提供
        距离范围：3-30km
        """
        straight_distance = self._haversine_distance(from_loc, to_loc)
        
        # 距离过滤（地铁适合中长距离）
        if straight_distance < 3.0 or straight_distance > 30.0:
            return None
        
        # 简化实现：估算地铁时间和费用
        # 实际应调用高德API并检查地铁线路
        distance = straight_distance * 1.2  # 地铁实际距离约为直线距离的1.2倍
        time = distance / 35.0 + 0.25  # 平均速度35km/h + 换乘等待0.25h
        cost = min(2.0 + (distance / 10) * 1.0, 8.0)  # 起步2元，每10km加1元，最高8元
        
        edge = Edge(
            id=f"subway_{from_loc.id}_{to_loc.id}",
            from_loc=from_loc,
            to_loc=to_loc,
            mode=TransportMode.SUBWAY,
            distance=distance,
            time=time,
            cost=cost
        )
        
        return edge
    
    def _state_transition(self,
                         state: State,
                         action: Action,
                         edge: Edge) -> State:
        """
        状态转移函数 δ(σ, a) → σ'
        
        数学定义:
        δ(σ, a) = (l', t', H', V', budget') where:
            l' = a.n
            t' = t + travel_time + visit_time
            H' = H ∪ {a.n}
            V'[a.n] = visit_quality
            budget' = budget - cost
        
        Args:
            state: 当前状态 σ
            action: 动作 a
            edge: 选择的边
            
        Returns:
            新状态 σ'
        """
        node = action.target_node
        
        # 计算新时间
        new_time = (state.current_time + 
                   edge.time + 
                   node.average_visit_time)
        
        # 更新历史
        new_history = state.visited_history | {node.id}
        
        # 更新访问质量（TODO: 基于实际体验）
        new_quality = state.visit_quality.copy()
        new_quality[node.id] = 0.8  # 默认质量分数
        
        # 更新预算
        new_budget = state.remaining_budget - edge.cost - node.ticket_price
        
        # 构建新状态
        new_state = State(
            current_location=node,
            current_time=new_time,
            visited_history=new_history,
            visit_quality=new_quality,
            remaining_budget=new_budget
        )
        
        return new_state
    
    def _preview_future(self,
                       node: Location,
                       state: State,
                       session: PlanningSession,
                       k: int = 3) -> List[Location]:
        """
        预览选择此节点后的可能下一步
        
        算法:
        1. 假设选择了此节点
        2. 计算从此节点出发的候选
        3. 返回 top-k 候选
        
        Args:
            node: 待选择的节点
            state: 当前状态
            session: 会话
            k: 预览数量
            
        Returns:
            未来可能的节点列表
        """
        # 创建假设状态
        hypothetical_state = State(
            current_location=node,
            current_time=state.current_time + 2.0,  # 假设2小时后
            visited_history=state.visited_history | {node.id},
            visit_quality=state.visit_quality.copy(),
            remaining_budget=state.remaining_budget
        )
        
        # 创建临时会话
        temp_session = PlanningSession(
            start_location=session.start_location,
            destination_city=session.destination_city,
            duration=session.duration,
            budget=session.budget,
            user_profile=session.user_profile,
            current_state=hypothetical_state
        )
        
        # 计算候选
        candidates = self._compute_candidates(temp_session)
        
        # 返回前k个
        return candidates[:k]
    
    def _haversine_distance(self, loc1: Location, loc2: Location) -> float:
        """
        计算两点间的球面距离（Haversine公式）
        
        Args:
            loc1: 位置1
            loc2: 位置2
            
        Returns:
            距离（km）
        """
        R = 6371  # 地球半径（km）
        
        lat1, lon1 = math.radians(loc1.lat), math.radians(loc1.lon)
        lat2, lon2 = math.radians(loc2.lat), math.radians(loc2.lon)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def _default_user_profile(self) -> UserProfile:
        """默认用户画像"""
        return UserProfile(
            purpose={'leisure': 0.7, 'culture': 0.5},
            intensity={'low': 0.7, 'medium': 0.3},
            pace={'slow': 0.8, 'medium': 0.2},
            food_preference={},
            budget_level='medium',
            avoid_crowd_preference=0.5
        )
    
    def select_option(self, session: PlanningSession, option: CandidateOption):
        """
        选择一个选项，更新会话状态
        
        Args:
            session: 当前会话
            option: 选择的选项
            
        Returns:
            新状态
        """
        from .models import State
        
        # 选择最优边（最短时间）
        best_edge = min(option.edges, key=lambda e: e.time)
        
        # 调用user_select更新状态
        new_state = self.user_select(session, option, best_edge)
        
        return new_state
    
    def _get_risk_message(self, risk_analysis) -> str:
        """获取风险简短消息"""
        if risk_analysis.risk_type == 'return':
            return "会错过回程"
        elif risk_analysis.risk_type == 'budget':
            if risk_analysis.risk_level == 'critical':
                return "预算即将耗尽"
            else:
                return "预算紧张"
        elif risk_analysis.risk_type == 'time':
            if risk_analysis.risk_level == 'critical':
                return "时间不足"
            else:
                return "时间紧张"
        else:
            return "需要注意"
    
    def _format_risk_details(self, risk_analysis) -> List[str]:
        """格式化风险详情"""
        details = []
        
        if risk_analysis.constraint_violations:
            # 硬约束违反
            violation = risk_analysis.constraint_violations[0]
            v_details = violation.get('details', {})
            
            details.append(f"游玩结束: {v_details.get('finish_time', 'N/A')}")
            details.append(f"返程耗时: {v_details.get('return_travel_time', 0):.1f}小时")
            details.append(f"预计到达: {v_details.get('arrive_time', 'N/A')}")
            details.append(f"必须到达: {v_details.get('deadline', 'N/A')}")
        else:
            # 软约束警告
            impact = risk_analysis.impact
            
            if risk_analysis.risk_type == 'budget':
                remaining = impact.budget_impact.get('remaining_after', 0)
                details.append(f"选择后剩余预算: ¥{remaining:.0f}")
                if remaining < 50:
                    details.append("后续选择将严重受限")
                else:
                    details.append("后续仅够1-2个免费景点")
            
            elif risk_analysis.risk_type == 'time':
                remaining = impact.time_impact.get('remaining_after', 0)
                details.append(f"选择后剩余时间: {remaining:.1f}小时")
                if remaining < 0.5:
                    details.append("之后必须立即返回")
                else:
                    details.append("之后仅够游览短景点")
        
        return details
    
    def _get_consequence(self, risk_analysis) -> Optional[str]:
        """获取风险后果"""
        if risk_analysis.constraint_violations:
            violation = risk_analysis.constraint_violations[0]
            return violation.get('details', {}).get('consequence')
        return None
    
    # 🔥 新增：四维空间智能辅助方法
    
    def _get_region(self, poi: Location) -> str:
        """
        获取POI所属区域
        
        用于区域软约束和访问计数
        
        Args:
            poi: POI
            
        Returns:
            区域名称（如"鼓浪屿"）
        """
        # 常见区域列表（可扩展）
        regions = [
            "鼓浪屿", "厦大", "曾厝垵", "中山路", "环岛路",  # 厦门
            "姑苏", "虎丘", "金鸡湖", "平江路", "山塘街",  # 苏州
            "西湖", "灵隐", "河坊街", "钱塘江",  # 杭州
            "外滩", "陆家嘴", "南京路", "豫园"  # 上海
        ]
        
        for region in regions:
            if region in poi.name or region in poi.address:
                return region
        
        return "其他"
    
    def _format_time(self, hour: float) -> str:
        """
        将小时数转换为时间字符串
        
        Args:
            hour: 小时数（如10.5）
            
        Returns:
            时间字符串（如"10:30"）
        """
        h = int(hour)
        m = int((hour - h) * 60)
        return f"{h:02d}:{m:02d}"
