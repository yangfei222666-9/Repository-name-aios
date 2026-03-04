"""
优化的卦象匹配算法
增加加权匹配和模糊逻辑
"""
from typing import Dict, Tuple, List
from hexagram_patterns import HexagramPattern, HEXAGRAM_PATTERNS


class ImprovedHexagramMatcher:
    """改进的卦象匹配器 - 加权匹配 + 模糊逻辑"""
    
    def __init__(self):
        self.patterns = HEXAGRAM_PATTERNS
        
        # 指标权重（可调整）
        self.weights = {
            "success_rate": 0.40,      # 成功率最重要
            "growth_rate": 0.25,       # 增长率次之
            "stability": 0.20,         # 稳定性
            "resource_usage": 0.15,    # 资源使用
        }
    
    def match(self, system_metrics: Dict) -> Tuple[HexagramPattern, float]:
        """
        加权匹配最接近的卦象
        
        Args:
            system_metrics: 系统指标字典
        
        Returns:
            (pattern, confidence) - 最匹配的卦象和置信度
        """
        best_match = None
        best_score = -1
        
        for pattern in self.patterns.values():
            score = self._calculate_weighted_score(system_metrics, pattern)
            if score > best_score:
                best_score = score
                best_match = pattern
        
        return best_match, best_score
    
    def _calculate_weighted_score(self, metrics: Dict, pattern: HexagramPattern) -> float:
        """计算加权匹配分数"""
        scores = {}
        
        for key, value_range in pattern.system_state.items():
            if key not in metrics:
                continue
            
            metric_value = metrics[key]
            
            # 布尔值匹配
            if isinstance(value_range, bool):
                scores[key] = 1.0 if metric_value == value_range else 0.0
                continue
            
            # 范围匹配（使用模糊逻辑）
            if isinstance(value_range, tuple):
                scores[key] = self._fuzzy_match(metric_value, value_range)
        
        # 加权平均
        weighted_score = 0.0
        total_weight = 0.0
        
        for key, score in scores.items():
            weight = self.weights.get(key, 0.1)  # 默认权重0.1
            weighted_score += score * weight
            total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _fuzzy_match(self, value: float, value_range: Tuple[float, float]) -> float:
        """
        模糊匹配 - 使用梯形隶属函数
        
        返回值在0-1之间：
        - 1.0: 完全在范围内
        - 0.5-1.0: 接近范围
        - 0.0-0.5: 远离范围
        """
        min_val, max_val = value_range
        center = (min_val + max_val) / 2
        range_size = (max_val - min_val) / 2
        
        if range_size == 0:
            return 1.0 if value == center else 0.0
        
        # 在范围内
        if min_val <= value <= max_val:
            # 距离中心越近，分数越高
            distance = abs(value - center)
            return 1.0 - (distance / range_size) * 0.2  # 最低0.8
        
        # 在范围外
        if value < min_val:
            distance = min_val - value
        else:
            distance = value - max_val
        
        # 使用指数衰减
        decay_rate = 2.0  # 衰减速度
        score = max(0, 1.0 - (distance / range_size) * decay_rate)
        
        return score
    
    def get_top_matches(self, system_metrics: Dict, top_n: int = 3) -> List[Tuple[HexagramPattern, float]]:
        """获取前N个最匹配的卦象"""
        matches = []
        for pattern in self.patterns.values():
            score = self._calculate_weighted_score(system_metrics, pattern)
            matches.append((pattern, score))
        
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:top_n]
    
    def set_weights(self, weights: Dict[str, float]):
        """
        自定义指标权重
        
        Args:
            weights: 权重字典，如 {"success_rate": 0.5, "growth_rate": 0.3}
        """
        # 归一化权重
        total = sum(weights.values())
        if total > 0:
            self.weights.update({k: v/total for k, v in weights.items()})


def compare_matchers():
    """对比原始匹配器和改进匹配器"""
    from hexagram_patterns import HexagramMatcher
    from hexagram_patterns_extended import extend_hexagram_patterns
    
    extend_hexagram_patterns()
    
    # 测试场景
    test_cases = [
        {
            "name": "顺利期",
            "metrics": {"success_rate": 0.9, "growth_rate": 0.3, "stability": 0.8, "resource_usage": 0.4}
        },
        {
            "name": "危机期",
            "metrics": {"success_rate": 0.2, "growth_rate": -0.3, "stability": 0.3, "resource_usage": 0.8}
        },
        {
            "name": "边界情况",
            "metrics": {"success_rate": 0.75, "growth_rate": 0.05, "stability": 0.65, "resource_usage": 0.5}
        },
    ]
    
    original_matcher = HexagramMatcher()
    improved_matcher = ImprovedHexagramMatcher()
    
    print("=== 匹配算法对比 ===\n")
    
    for case in test_cases:
        print(f"【{case['name']}】")
        metrics = case['metrics']
        print(f"  成功率: {metrics['success_rate']:.1%}")
        print(f"  增长率: {metrics['growth_rate']:+.1%}")
        print(f"  稳定性: {metrics['stability']:.1%}")
        print(f"  资源使用: {metrics['resource_usage']:.1%}")
        
        # 原始匹配器
        pattern1, conf1 = original_matcher.match(metrics)
        print(f"\n  原始匹配器:")
        print(f"    卦象: {pattern1.name} (第{pattern1.number}卦)")
        print(f"    置信度: {conf1:.1%}")
        
        # 改进匹配器
        pattern2, conf2 = improved_matcher.match(metrics)
        print(f"\n  改进匹配器:")
        print(f"    卦象: {pattern2.name} (第{pattern2.number}卦)")
        print(f"    置信度: {conf2:.1%}")
        
        if pattern1.name != pattern2.name:
            print(f"\n  [!] 匹配结果不同")
        
        print()


if __name__ == "__main__":
    compare_matchers()
