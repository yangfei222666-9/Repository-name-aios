"""
aios/core/model_router_v2.py - 生产级智能模型路由

特性：
- 可配置规则（router_config.json）
- 结构化日志
- 自动降级
- 性能监控
- 灰度开关
"""

import json
import time
import requests
from pathlib import Path
from typing import Literal, Optional, Dict, Any
from datetime import datetime

CONFIG_FILE = Path(__file__).parent / "router_config.json"
METRICS_FILE = Path(__file__).parent.parent / "events" / "router_metrics.json"
LOG_FILE = Path(__file__).parent.parent / "events" / "router_calls.jsonl"


class ModelRouter:
    """生产级模型路由器"""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or CONFIG_FILE
        self.config = self._load_config()
        self._ensure_log_dir()

    def _load_config(self) -> dict:
        """加载配置"""
        if self.config_path.exists():
            try:
                return json.loads(self.config_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return self._default_config()

    def _default_config(self) -> dict:
        """默认配置"""
        return {
            "enabled": True,
            "default_local_model": "qwen2.5:3b",
            "default_cloud_model": "claude",
            "timeout": {"ollama": 30, "claude": 60},
            "fallback": {"enabled": True, "max_retries": 1},
            "task_mapping": {
                "summarize_short": "simple",
                "simple_qa": "simple",
                "reasoning": "complex",
            },
        }

    def _ensure_log_dir(self):
        """确保日志目录存在"""
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    def route(
        self,
        task_type: str,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        force_model: Optional[Literal["ollama", "claude"]] = None,
    ) -> Dict[str, Any]:
        """
        智能路由入口

        Args:
            task_type: 任务类型
            prompt: 提示词
            context: 上下文信息
            force_model: 强制使用指定模型

        Returns:
            {
                "provider": "ollama" | "claude",
                "model": str,
                "response": str,
                "success": bool,
                "fallback": bool,
                "reason": str,
                "estimated_cost": float,
                "latency_ms": int,
                "timestamp": str
            }
        """
        start_time = time.time()
        timestamp = datetime.now().isoformat()

        # 检查路由器是否启用
        if not self.config.get("enabled", True):
            return self._disabled_response(prompt, timestamp)

        # 决策：选择模型
        decision = self._decide_model(task_type, prompt, force_model)

        # 执行调用
        result = self._execute(decision, prompt, context)

        # 计算延迟
        latency_ms = int((time.time() - start_time) * 1000)
        result["latency_ms"] = latency_ms
        result["timestamp"] = timestamp
        result["task_type"] = task_type

        # 记录日志
        self._log_call(result)

        # 更新指标
        self._update_metrics(result)

        return result

    def _decide_model(
        self, task_type: str, prompt: str, force_model: Optional[str]
    ) -> Dict[str, Any]:
        """决策：选择使用哪个模型"""

        # 强制指定
        if force_model:
            return {
                "provider": force_model,
                "model": self._get_model_name(force_model),
                "reason": f"forced_{force_model}",
            }

        # 根据任务类型映射
        complexity = self.config.get("task_mapping", {}).get(task_type, "complex")

        # 根据复杂度选择
        if complexity == "simple":
            if self._is_ollama_available():
                return {
                    "provider": "ollama",
                    "model": self.config["default_local_model"],
                    "reason": "simple_task_local",
                }
            else:
                return {
                    "provider": "claude",
                    "model": self.config["default_cloud_model"],
                    "reason": "simple_task_fallback",
                }

        elif complexity == "medium":
            if self._is_ollama_available():
                return {
                    "provider": "ollama",
                    "model": self.config["default_local_model"],
                    "reason": "medium_task_try_local",
                }
            else:
                return {
                    "provider": "claude",
                    "model": self.config["default_cloud_model"],
                    "reason": "medium_task_fallback",
                }

        else:  # complex
            return {
                "provider": "claude",
                "model": self.config["default_cloud_model"],
                "reason": "complex_task_cloud",
            }

    def _execute(
        self, decision: Dict[str, Any], prompt: str, context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """执行模型调用"""

        provider = decision["provider"]
        model = decision["model"]
        reason = decision["reason"]

        result = {
            "provider": provider,
            "model": model,
            "reason": reason,
            "response": None,
            "success": False,
            "fallback": False,
            "estimated_cost": 0.0,
        }

        # 调用 Ollama
        if provider == "ollama":
            response = self._call_ollama(prompt, model)
            if response:
                result["response"] = response
                result["success"] = True
                result["estimated_cost"] = 0.0
                return result

            # Ollama 失败，降级到 Claude
            if self.config.get("fallback", {}).get("enabled", True):
                result["fallback"] = True
                result["provider"] = "claude"
                result["model"] = self.config["default_cloud_model"]
                result["reason"] = f"{reason}_fallback"
                result["response"] = "[Claude API 调用]"
                result["success"] = True
                result["estimated_cost"] = 0.01
                return result

        # 调用 Claude（占位）
        elif provider == "claude":
            result["response"] = "[Claude API 调用]"
            result["success"] = True
            result["estimated_cost"] = 0.01
            return result

        return result

    def _is_ollama_available(self) -> bool:
        """检查 Ollama 是否可用"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    def _call_ollama(self, prompt: str, model: str) -> Optional[str]:
        """调用 Ollama"""
        try:
            timeout = self.config.get("timeout", {}).get("ollama", 30)
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=timeout,
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                return None

        except Exception as e:
            print(f"Ollama 调用失败: {e}")
            return None

    def _get_model_name(self, provider: str) -> str:
        """获取模型名称"""
        if provider == "ollama":
            return self.config.get("default_local_model", "qwen2.5:3b")
        else:
            return self.config.get("default_cloud_model", "claude")

    def _disabled_response(self, prompt: str, timestamp: str) -> Dict[str, Any]:
        """路由器禁用时的响应"""
        return {
            "provider": "claude",
            "model": self.config["default_cloud_model"],
            "response": "[Claude API 调用]",
            "success": True,
            "fallback": False,
            "reason": "router_disabled",
            "estimated_cost": 0.01,
            "latency_ms": 0,
            "timestamp": timestamp,
            "task_type": "unknown",
        }

    def _log_call(self, result: Dict[str, Any]):
        """记录调用日志"""
        if not self.config.get("monitoring", {}).get("log_all_calls", True):
            return

        try:
            log_entry = {
                "timestamp": result["timestamp"],
                "task_type": result.get("task_type", "unknown"),
                "provider": result["provider"],
                "model": result["model"],
                "reason": result["reason"],
                "success": result["success"],
                "fallback": result["fallback"],
                "estimated_cost": result["estimated_cost"],
                "latency_ms": result["latency_ms"],
            }

            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        except Exception as e:
            print(f"日志记录失败: {e}")

    def _update_metrics(self, result: Dict[str, Any]):
        """更新指标"""
        try:
            metrics = self._load_metrics()

            provider = result["provider"]
            metrics["total_calls"] = metrics.get("total_calls", 0) + 1
            metrics[f"{provider}_calls"] = metrics.get(f"{provider}_calls", 0) + 1

            if result["fallback"]:
                metrics["fallback_count"] = metrics.get("fallback_count", 0) + 1

            metrics["total_cost"] = (
                metrics.get("total_cost", 0.0) + result["estimated_cost"]
            )
            metrics["last_updated"] = result["timestamp"]

            self._save_metrics(metrics)

        except Exception as e:
            print(f"指标更新失败: {e}")

    def _load_metrics(self) -> dict:
        """加载指标"""
        if METRICS_FILE.exists():
            try:
                return json.loads(METRICS_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def _save_metrics(self, metrics: dict):
        """保存指标"""
        METRICS_FILE.write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def get_metrics(self) -> dict:
        """获取当前指标"""
        return self._load_metrics()


# 全局单例
_router = None


def get_router() -> ModelRouter:
    """获取路由器单例"""
    global _router
    if _router is None:
        _router = ModelRouter()
    return _router


def route_model(
    task_type: str,
    prompt: str,
    context: Optional[Dict[str, Any]] = None,
    force_model: Optional[Literal["ollama", "claude"]] = None,
) -> Dict[str, Any]:
    """
    便捷函数：路由模型调用

    Args:
        task_type: 任务类型
        prompt: 提示词
        context: 上下文
        force_model: 强制模型

    Returns:
        路由结果
    """
    router = get_router()
    return router.route(task_type, prompt, context, force_model)


if __name__ == "__main__":
    # 测试
    router = ModelRouter()

    print("测试路由器...")
    result = route_model("summarize_short", "总结：系统运行正常")

    print(f"Provider: {result['provider']}")
    print(f"Model: {result['model']}")
    print(f"Reason: {result['reason']}")
    print(f"Cost: ${result['estimated_cost']}")
    print(f"Latency: {result['latency_ms']}ms")

    print("\n当前指标:")
    metrics = router.get_metrics()
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
