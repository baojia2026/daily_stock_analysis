#!/usr/bin/env python3
"""
策略集成模块
集成：理性投资系统 + Growth-Valuation Map + 短线实战系统
"""

import logging
import yaml
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class Quadrant(Enum):
    """增长-估值图四象限"""
    TOP_RIGHT = "top_right"  # 右上：高增长+高估值
    BOTTOM_RIGHT = "bottom_right"  # 右下：高增长+低估值
    TOP_LEFT = "top_left"  # 左上：低增长+高估值
    BOTTOM_LEFT = "bottom_left"  # 左下：低增长+低估值

class SignalLevel(Enum):
    """信号优先级"""
    LEVEL_1 = 1  # 一级信号：理性评分高且在目标象限
    LEVEL_2 = 2  # 二级信号：在目标象限且满足硬条件
    LEVEL_3 = 3  # 三级信号：仅理性评分高

@dataclass
class RationalInvestmentScore:
    """理性投资系统评分"""
    stock_code: str
    stock_name: str
    total_score: float
    component_scores: Dict[str, float]
    survival_veto: bool = False
    veto_reason: Optional[str] = None
    analysis_date: datetime = field(default_factory=datetime.now)
    
    def is_pass(self, threshold: float = 7.5) -> bool:
        """是否通过筛选"""
        return not self.survival_veto and self.total_score >= threshold

@dataclass
class GrowthValuationPosition:
    """增长-估值图位置"""
    stock_code: str
    stock_name: str
    growth_rate: float  # 增长率 (CAGR)
    valuation: float  # 估值 (PE)
    quadrant: Quadrant
    peg_ratio: Optional[float] = None
    industry_avg_growth: Optional[float] = None
    industry_avg_valuation: Optional[float] = None
    
    def is_in_target_quadrant(self, target: Quadrant = Quadrant.BOTTOM_RIGHT) -> bool:
        """是否在目标象限"""
        return self.quadrant == target
    
    def get_relative_position(self) -> Tuple[float, float]:
        """获取相对位置（相对于行业平均）"""
        if self.industry_avg_growth and self.industry_avg_valuation:
            return (self.growth_rate - self.industry_avg_growth, 
                   self.valuation - self.industry_avg_valuation)
        return (0, 0)

@dataclass
class ShortTermSignal:
    """短线实战信号"""
    stock_code: str
    stock_name: str
    # 三层硬条件
    trend_conditions_met: bool
    sentiment_conditions_met: bool
    structure_conditions_met: bool
    # 软条件计数
    soft_conditions_met: int
    soft_conditions_total: int
    # 价格信息
    current_price: float
    structure_low: float  # 结构低点
    first_target: float  # 第一目标位
    second_target: float  # 第二目标位
    stop_loss: float  # 止损位
    # 时间信息
    signal_date: datetime = field(default_factory=datetime.now)
    
    @property
    def all_hard_conditions_met(self) -> bool:
        """是否满足所有硬条件"""
        return (self.trend_conditions_met and 
                self.sentiment_conditions_met and 
                self.structure_conditions_met)
    
    @property
    def potential_return(self) -> Tuple[float, float]:
        """潜在回报率（第一目标，第二目标）"""
        if self.current_price > 0:
            return ((self.first_target - self.current_price) / self.current_price,
                   (self.second_target - self.current_price) / self.current_price)
        return (0, 0)
    
    @property
    def risk_reward_ratio(self) -> float:
        """风险回报比"""
        potential_gain = self.first_target - self.current_price
        potential_loss = self.current_price - self.stop_loss
        if potential_loss > 0:
            return potential_gain / potential_loss
        return 0

@dataclass
class IntegratedSignal:
    """综合策略信号"""
    stock_code: str
    stock_name: str
    # 各策略状态
    rational_investment: RationalInvestmentScore
    growth_valuation: GrowthValuationPosition
    short_term: ShortTermSignal
    # 综合评估
    signal_level: SignalLevel
    pass_all_strategies: bool
    # 交易建议
    suggested_position: float  # 建议仓位比例
    entry_price_range: Tuple[float, float]  # 入场价格区间
    targets: List[float]  # 目标价位
    stop_loss: float  # 止损价位
    holding_period: Tuple[int, int]  # 建议持有期（最小，最大）
    # 分析信息
    analysis_date: datetime = field(default_factory=datetime.now)
    confidence_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "signal_level": self.signal_level.value,
            "pass_all_strategies": self.pass_all_strategies,
            "rational_score": self.rational_investment.total_score,
            "quadrant": self.growth_valuation.quadrant.value,
            "hard_conditions_met": self.short_term.all_hard_conditions_met,
            "soft_conditions_met": f"{self.short_term.soft_conditions_met}/{self.short_term.soft_conditions_total}",
            "suggested_position": f"{self.suggested_position*100:.1f}%",
            "current_price": self.short_term.current_price,
            "entry_range": f"{self.entry_price_range[0]:.2f}-{self.entry_price_range[1]:.2f}",
            "targets": [f"{t:.2f}" for t in self.targets],
            "stop_loss": self.stop_loss,
            "potential_return": f"{self.short_term.potential_return[0]*100:.1f}%-{self.short_term.potential_return[1]*100:.1f}%",
            "risk_reward": f"{self.short_term.risk_reward_ratio:.2f}",
            "confidence_score": f"{self.confidence_score:.1f}/10",
            "analysis_date": self.analysis_date.strftime("%Y-%m-%d")
        }

class StrategyIntegrator:
    """策略集成器"""
    
    def __init__(self, config_path: str = "config/strategies.yaml"):
        """初始化策略集成器"""
        self.config = self._load_config(config_path)
        self.rational_threshold = self.config["rational_investment"]["score_threshold"]
        self.target_quadrant = Quadrant(self.config["growth_valuation_map"]["target_quadrant"])
        
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # 使用默认配置
            logger.warning(f"配置文件 {config_path} 未找到，使用默认配置")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "rational_investment": {
                "score_threshold": 7.5
            },
            "growth_valuation_map": {
                "target_quadrant": "bottom_right"
            },
            "short_term_trading": {
                "hard_conditions": {
                    "trend_filter": {},
                    "sentiment_filter": {},
                    "structure_filter": {}
                }
            },
            "integrated_strategy": {
                "requirements": {
                    "phase1_rational_investment": {"must_pass": True, "min_score": 7.5},
                    "phase2_growth_valuation": {"must_pass": True, "target_quadrant": "bottom_right"},
                    "phase3_short_term": {"must_pass": True, "hard_conditions_all": True}
                }
            }
        }
    
    def integrate_strategies(
        self,
        rational_scores: List[RationalInvestmentScore],
        growth_positions: List[GrowthValuationPosition],
        short_term_signals: List[ShortTermSignal]
    ) -> List[IntegratedSignal]:
        """集成三个策略的信号"""
        
        integrated_signals = []
        
        # 创建查找字典
        rational_dict = {s.stock_code: s for s in rational_scores}
        growth_dict = {g.stock_code: g for g in growth_positions}
        short_term_dict = {s.stock_code: s for s in short_term_signals}
        
        # 获取所有股票代码
        all_codes = set(rational_dict.keys()) | set(growth_dict.keys()) | set(short_term_dict.keys())
        
        for code in all_codes:
            rational = rational_dict.get(code)
            growth = growth_dict.get(code)
            short_term = short_term_dict.get(code)
            
            if not rational or not growth or not short_term:
                continue  # 缺少任一策略数据
            
            # 检查是否通过各策略
            pass_rational = rational.is_pass(self.rational_threshold)
            pass_growth = growth.is_in_target_quadrant(self.target_quadrant)
            pass_short_term = short_term.all_hard_conditions_met
            
            # 确定信号级别
            signal_level = self._determine_signal_level(pass_rational, pass_growth, pass_short_term)
            
            # 是否通过所有策略
            pass_all = pass_rational and pass_growth and pass_short_term
            
            # 计算置信度评分
            confidence_score = self._calculate_confidence_score(
                rational, growth, short_term, pass_all
            )
            
            # 确定建议仓位
            suggested_position = self._calculate_position_size(
                signal_level, confidence_score, short_term.risk_reward_ratio
            )
            
            # 生成综合信号
            integrated_signal = IntegratedSignal(
                stock_code=code,
                stock_name=rational.stock_name,
                rational_investment=rational,
                growth_valuation=growth,
                short_term=short_term,
                signal_level=signal_level,
                pass_all_strategies=pass_all,
                suggested_position=suggested_position,
                entry_price_range=(short_term.current_price * 0.98, short_term.current_price * 1.02),
                targets=[short_term.first_target, short_term.second_target],
                stop_loss=short_term.stop_loss,
                holding_period=(5, 20),  # 5-20个交易日
                confidence_score=confidence_score
            )
            
            integrated_signals.append(integrated_signal)
        
        # 按信号级别和置信度排序
        integrated_signals.sort(
            key=lambda x: (x.signal_level.value, x.confidence_score),
            reverse=True
        )
        
        return integrated_signals
    
    def _determine_signal_level(
        self, 
        pass_rational: bool, 
        pass_growth: bool, 
        pass_short_term: bool
    ) -> SignalLevel:
        """确定信号级别"""
        if pass_rational and pass_growth and pass_short_term:
            return SignalLevel.LEVEL_1
        elif pass_growth and pass_short_term:
            return SignalLevel.LEVEL_2
        elif pass_rational:
            return SignalLevel.LEVEL_3
        else:
            return SignalLevel.LEVEL_3  # 默认最低级别
    
    def _calculate_confidence_score(
        self,
        rational: RationalInvestmentScore,
        growth: GrowthValuationPosition,
        short_term: ShortTermSignal,
        pass_all: bool
    ) -> float:
        """计算置信度评分（0-10）"""
        score = 0.0
        
        # 理性投资评分贡献（0-4分）
        rational_score_norm = min(rational.total_score / 10.0, 1.0)
        score += rational_score_norm * 4.0
        
        # 增长-估值位置贡献（0-3分）
        if growth.quadrant == self.target_quadrant:
            score += 3.0
        elif growth.peg_ratio and growth.peg_ratio < 1.0:
            score += 2.0
        else:
            score += 1.0
        
        # 短线信号强度贡献（0-3分）
        if short_term.all_hard_conditions_met:
            score += 2.0
        if short_term.soft_conditions_met >= 3:
            score += 1.0
        
        # 通过所有策略加成
        if pass_all:
            score += 1.0
        
        return min(score, 10.0)
    
    def _calculate_position_size(
        self, 
        signal_level: SignalLevel, 
        confidence_score: float,
        risk_reward_ratio: float
    ) -> float:
        """计算建议仓位大小"""
        
        # 基础仓位
        if signal_level == SignalLevel.LEVEL_1:
            base_position = 0.04  # 4%
        elif signal_level == SignalLevel.LEVEL_2:
            base_position = 0.02  # 2%
        else:
            base_position = 0.01  # 1%
        
        # 根据置信度调整
        confidence_multiplier = confidence_score / 10.0
        
        # 根据风险回报比调整
        if risk_reward_ratio > 2.0:
            rr_multiplier = 1.2
        elif risk_reward_ratio > 1.5:
            rr_multiplier = 1.0
        else:
            rr_multiplier = 0.8
        
        # 计算最终仓位
        final_position = base_position * confidence_multiplier * rr_multiplier
        
        # 限制最大仓位
        max_position = 0.08  # 最大8%
        return min(final_position, max_position)
    
    def generate_report(self, signals: List[IntegratedSignal]) -> str:
        """生成策略报告"""
        
        if not signals:
            return "【策略集成报告】\n当前无符合条件的股票信号。"
        
        # 分类统计
        level1_count = sum(1 for s in signals if s.signal_level == SignalLevel.LEVEL_1)
        level2_count = sum(1 for s in signals if s.signal_level == SignalLevel.LEVEL_2)
        level3_count = sum(1 for s in signals if s.signal_level == SignalLevel.LEVEL_3)
        
        pass_all_count = sum(1 for s in signals if s.pass_all_strategies)
        
        report_lines = [
            "=" * 60,
            "【策略集成报告】",
            "=" * 60,
            f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"筛选股票数量: {len(signals)}",
            f"一级信号(全策略通过): {level1_count}",
            f"二级信号(增长+短线): {level2_count}",
            f"三级信号(仅理性评分): {level3_count}",
            f"全策略通过: {pass_all_count}",
            "",
            "【推荐股票列表】"
        ]
        
        # 添加股票详情
        for i, signal in enumerate(signals[:10], 1):  # 最多显示10只
            data = signal.to_dict()
            report_lines.extend([
                f"\n{i}. {data['stock_name']}({data['stock_code']})",
                f"   信号级别: {data['signal_level']} | 置信度: {data['confidence_score']}",
                f"   理性评分: {data['rational_score']} | 象限: {data['quadrant']}",
                f"   硬条件: {data['hard_conditions_met']} | 软条件: {data['soft_conditions_met']}",
                f"   当前价: {data['current_price']} | 目标位: {data['targets']}",
                f"   止损: {data['stop_loss']} | 风报比: {data['risk_reward']}",
                f"   建议仓位: {data['suggested_position']} | 潜在收益: {data['potential_return']}"
            ])
        
        # 添加策略统计
        report_lines.extend([
            "\n" + "=" * 60,
            "【策略统计】"
        ])
        
        if signals:
            avg_rational_score = sum(s.rational_investment.total_score for s in signals) / len(signals)
            avg_confidence = sum(s.confidence_score for s in signals) / len(signals)
            report_lines.extend([
                f"平均理性评分: {avg_rational_score:.2f}",
                f"平均置信度: {avg_confidence:.2f}",
                f"最高置信度: {max(s.confidence_score for s in signals):.2f}"
            ])
        
        # 添加风险提示
        report_lines.extend([
            "\n" + "=" * 60,
            "【风险提示】",
            "1. 所有策略基于历史数据和模型计算，不保证未来收益",
            "2. 建议仓位仅供参考，请根据个人风险承受能力调整",
            "3. 短线信号具有时效性，请及时执行交易计划",
            "4. 严格执行止损纪律，控制单笔损失",
            "=" * 60
        ])
        
        return "\n".join(report_lines)

# ============= 简易数据适配器 =============

class DataAdapter:
    """简易数据适配器"""
    
    @staticmethod
    def create_sample_data() -> Tuple[
        List[RationalInvestmentScore],
        List[GrowthValuationPosition],
        List[ShortTermSignal]
    ]:
        """创建示例数据
