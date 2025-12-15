"""
会话管理器
管理用户的旅行规划会话
"""

import uuid
from typing import Dict, Optional
from datetime import datetime, timedelta
from dataclasses import asdict

from ..core.models import (
    PlanningSession, UserProfile, State, Location, POIType
)
from ..core.progressive_planner import ProgressivePlanner


class SessionManager:
    """
    会话管理器
    
    功能：
    1. 创建和管理旅行规划会话
    2. 存储会话状态
    3. 清理过期会话
    """
    
    def __init__(self, planner: ProgressivePlanner):
        """
        初始化会话管理器
        
        Args:
            planner: 渐进式规划器实例
        """
        self.planner = planner
        self.sessions: Dict[str, PlanningSession] = {}
        self.session_timeout = timedelta(hours=24)  # 会话24小时后过期
    
    def create_session(self,
                      user_id: str,
                      starting_location: Location,
                      purpose: Optional[str] = None,
                      pace: str = "medium",
                      intensity: str = "medium",
                      time_budget: Optional[float] = None,
                      money_budget: Optional[float] = None) -> PlanningSession:
        """
        创建新会话
        
        Args:
            user_id: 用户ID
            starting_location: 起始位置
            purpose: 旅行目的
            pace: 旅行节奏
            intensity: 体力强度
            time_budget: 时间预算（小时）
            money_budget: 金钱预算（元）
            
        Returns:
            新创建的会话
        """
        # 生成会话ID
        session_id = str(uuid.uuid4())
        
        # 创建用户画像
        purpose_dict = {}
        if purpose:
            # 简化：根据关键词设置偏好
            if '文化' in purpose or '历史' in purpose:
                purpose_dict['culture'] = 0.9
            if '美食' in purpose:
                purpose_dict['food'] = 0.9
            if '自然' in purpose or '风景' in purpose:
                purpose_dict['nature'] = 0.9
            if '休闲' in purpose:
                purpose_dict['leisure'] = 0.8
        
        pace_dict = {pace: 0.9} if pace else {'medium': 0.7}
        intensity_dict = {intensity: 0.8} if intensity else {'medium': 0.7}
        
        user_profile = UserProfile(
            purpose=purpose_dict or {'general': 0.7},
            pace=pace_dict,
            intensity=intensity_dict
        )
        
        # 创建初始状态
        initial_state = State(
            current_location=starting_location,
            current_time=0.0,
            visited_history=set(),  # 空集合，开始时没有访问过任何地点
            visit_quality={},  # 空字典
            remaining_budget=money_budget if money_budget else 10000.0  # 默认10000元
        )
        
        # 从地址提取城市名（简化实现）
        destination_city = self._extract_city(starting_location.address)
        
        # 创建会话
        session = PlanningSession(
            session_id=session_id,
            user_id=user_id,
            start_location=starting_location,  # 起始位置
            destination_city=destination_city,  # 目的地城市
            duration=time_budget if time_budget else 72.0,  # 时长，默认72小时
            budget=money_budget if money_budget else 5000.0,  # 预算，默认5000元
            user_profile=user_profile,
            initial_state=initial_state,  # 初始状态
            current_state=initial_state,  # 当前状态（初始时与初始状态相同）
            created_at=datetime.now(),
            last_active=datetime.now()
        )
        
        # 存储会话
        self.sessions[session_id] = session
        
        return session
    
    def get_session(self, session_id: str) -> Optional[PlanningSession]:
        """
        获取会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话对象，如果不存在或已过期则返回None
        """
        session = self.sessions.get(session_id)
        
        if not session:
            return None
        
        # 检查是否过期
        if datetime.now() - session.last_active > self.session_timeout:
            del self.sessions[session_id]
            return None
        
        # 更新最后活跃时间
        session.last_active = datetime.now()
        
        return session
    
    def update_session(self, session: PlanningSession):
        """
        更新会话
        
        Args:
            session: 会话对象
        """
        session.last_active = datetime.now()
        self.sessions[session.session_id] = session
    
    def delete_session(self, session_id: str):
        """
        删除会话
        
        Args:
            session_id: 会话ID
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def cleanup_expired_sessions(self):
        """清理过期会话"""
        now = datetime.now()
        expired_ids = [
            sid for sid, session in self.sessions.items()
            if now - session.last_active > self.session_timeout
        ]
        
        for sid in expired_ids:
            del self.sessions[sid]
        
        return len(expired_ids)
    
    def get_active_session_count(self) -> int:
        """获取活跃会话数"""
        return len(self.sessions)
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """
        获取会话信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话信息字典
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        return {
            'session_id': session.session_id,
            'user_id': session.user_id,
            'created_at': session.created_at.isoformat(),
            'last_active': session.last_active.isoformat(),
            'visited_count': len(session.history),
            'current_location': session.current_state.current_location.name,
            'total_cost': session.budget - session.current_state.remaining_budget,
            'total_time': session.current_state.current_time
        }
    
    def _extract_city(self, address: str) -> str:
        """
        从地址中提取城市名
        
        Args:
            address: 地址字符串
            
        Returns:
            城市名
        """
        # 简化实现：检查常见城市名
        cities = ['苏州', '厦门', '深圳', '杭州', '上海', '北京', '广州', '南京', '成都', '西安']
        for city in cities:
            if city in address:
                return city
        return "苏州"  # 默认返回苏州
