"""
AIOS LLM 集成模块 v1.0

支持多种 LLM 后端：
1. Ollama（本地模型）- 免费、快速
2. DeepSeek API - 便宜、强大
3. Claude API - 最强、但贵

使用方式：
    llm = LLM(provider="ollama", model="llama3.1:8b")
    response = llm.generate("你好")
"""

import json
import subprocess
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path
import os

@dataclass
class LLMResponse:
    """LLM 响应"""
    content: str
    model: str
    provider: str
    tokens_used: int = 0
    cost: float = 0.0
    error: Optional[str] = None

class LLM:
    """统一的 LLM 接口"""
    
    def __init__(self, 
                 provider: str = "ollama",
                 model: str = "llama3.1:8b",
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None):
        """
        初始化 LLM
        
        Args:
            provider: 提供商（ollama/deepseek/claude）
            model: 模型名称
            api_key: API 密钥（云端模型需要）
            base_url: API 基础 URL（可选）
        """
        self.provider = provider.lower()
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        
        # 验证配置
        if self.provider == "ollama":
            self._check_ollama()
        elif self.provider in ["deepseek", "claude", "pgt"]:
            if not self._resolved_api_key():
                raise ValueError(f"{provider} 需要 API Key")
    
    def _check_ollama(self):
        """检查 Ollama 是否可用"""
        # 直接使用完整路径
        ollama_path = Path.home() / "AppData/Local/Programs/Ollama/ollama.exe"
        if ollama_path.exists():
            self.ollama_path = str(ollama_path)
        else:
            raise RuntimeError("Ollama 未安装（路径不存在）")
    
    def generate(self, 
                 prompt: str,
                 system: Optional[str] = None,
                 temperature: float = 0.7,
                 max_tokens: int = 2000) -> LLMResponse:
        """
        生成文本
        
        Args:
            prompt: 用户输入
            system: 系统提示（可选）
            temperature: 温度（0-1）
            max_tokens: 最大 token 数
        
        Returns:
            LLMResponse: 响应对象
        """
        if self.provider == "ollama":
            return self._generate_ollama(prompt, system, temperature, max_tokens)
        elif self.provider == "deepseek":
            return self._generate_deepseek(prompt, system, temperature, max_tokens)
        elif self.provider == "claude":
            return self._generate_claude(prompt, system, temperature, max_tokens)
        elif self.provider == "pgt":
            return self._generate_pgt(prompt, system, temperature, max_tokens)
        else:
            raise ValueError(f"不支持的提供商: {self.provider}")

    def _resolved_api_key(self) -> Optional[str]:
        if self.api_key:
            return self.api_key
        if self.provider == "pgt":
            k = os.getenv("PGT_RELAY_API_KEY", "").strip()
            return k or None
        return None

    def _resolved_base_url(self) -> Optional[str]:
        if self.base_url:
            return self.base_url
        if self.provider == "pgt":
            full = os.getenv("PGT_RELAY_URL", "").strip()
            if full:
                return full
            base = os.getenv("PGT_RELAY_BASE_URL", "").strip().rstrip("/")
            if not base:
                return None
            path = os.getenv("PGT_RELAY_CHAT_PATH", "/v1/chat/completions").strip().lstrip("/")
            return f"{base}/{path}"
        return None
    
    def _generate_ollama(self, prompt: str, system: Optional[str], 
                        temperature: float, max_tokens: int) -> LLMResponse:
        """Ollama 生成"""
        try:
            # 构建消息
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            
            # 调用 Ollama
            cmd = [
                self.ollama_path, "run", self.model,
                "--format", "json"
            ]
            
            # 构建完整的 prompt
            full_prompt = ""
            if system:
                full_prompt += f"System: {system}\n\n"
            full_prompt += f"User: {prompt}\n\nAssistant:"
            
            result = subprocess.run(
                [self.ollama_path, "run", self.model, full_prompt],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                return LLMResponse(
                    content="",
                    model=self.model,
                    provider=self.provider,
                    error=result.stderr
                )
            
            # 解析响应
            content = result.stdout.strip()
            
            return LLMResponse(
                content=content,
                model=self.model,
                provider=self.provider,
                tokens_used=len(content.split()),  # 粗略估计
                cost=0.0  # 本地模型免费
            )
        
        except Exception as e:
            return LLMResponse(
                content="",
                model=self.model,
                provider=self.provider,
                error=str(e)
            )
    
    def _generate_deepseek(self, prompt: str, system: Optional[str],
                          temperature: float, max_tokens: int) -> LLMResponse:
        """DeepSeek API 生成"""
        try:
            import requests
            
            url = self.base_url or "https://api.deepseek.com/v1/chat/completions"
            
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            
            response = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=60
            )
            
            if response.status_code != 200:
                return LLMResponse(
                    content="",
                    model=self.model,
                    provider=self.provider,
                    error=f"API 错误: {response.status_code}"
                )
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            tokens_used = data["usage"]["total_tokens"]
            
            # DeepSeek 定价：¥1/百万 tokens（输入），¥2/百万 tokens（输出）
            cost = tokens_used / 1_000_000 * 1.5  # 平均成本
            
            return LLMResponse(
                content=content,
                model=self.model,
                provider=self.provider,
                tokens_used=tokens_used,
                cost=cost
            )
        
        except Exception as e:
            return LLMResponse(
                content="",
                model=self.model,
                provider=self.provider,
                error=str(e)
            )

    def _generate_pgt(self, prompt: str, system: Optional[str],
                     temperature: float, max_tokens: int) -> LLMResponse:
        try:
            import requests

            url = self._resolved_base_url()
            if not url:
                return LLMResponse(
                    content="",
                    model=self.model,
                    provider=self.provider,
                    error="PGT_RELAY_URL/PGT_RELAY_BASE_URL 未配置"
                )

            api_key = self._resolved_api_key()
            if not api_key:
                return LLMResponse(
                    content="",
                    model=self.model,
                    provider=self.provider,
                    error="PGT_RELAY_API_KEY 未配置"
                )
            if not api_key.isascii():
                return LLMResponse(
                    content="",
                    model=self.model,
                    provider=self.provider,
                    error="PGT_RELAY_API_KEY 包含非 ASCII 字符，请只粘贴纯 key（不要带中文说明/引号内容）"
                )

            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            timeout_s = float(os.getenv("PGT_TIMEOUT_S", "60"))
            response = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=timeout_s
            )

            if response.status_code != 200:
                return LLMResponse(
                    content="",
                    model=self.model,
                    provider=self.provider,
                    error=f"API 错误: {response.status_code}"
                )

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage") or {}
            tokens_used = int(usage.get("total_tokens") or 0)

            return LLMResponse(
                content=content,
                model=self.model,
                provider=self.provider,
                tokens_used=tokens_used,
                cost=0.0
            )

        except Exception as e:
            return LLMResponse(
                content="",
                model=self.model,
                provider=self.provider,
                error=str(e)
            )
    
    def _generate_claude(self, prompt: str, system: Optional[str],
                        temperature: float, max_tokens: int) -> LLMResponse:
        """Claude API 生成（通过 OpenClaw）"""
        # TODO: 实现 Claude API 调用
        return LLMResponse(
            content="",
            model=self.model,
            provider=self.provider,
            error="Claude API 暂未实现"
        )

# 便捷函数
def create_llm(provider: str = "ollama", model: Optional[str] = None) -> LLM:
    """
    创建 LLM 实例
    
    Args:
        provider: 提供商（ollama/deepseek/claude）
        model: 模型名称（可选，使用默认值）
    
    Returns:
        LLM 实例
    """
    default_models = {
        "ollama": "llama3.1:8b",
        "deepseek": "deepseek-chat",
        "claude": "claude-sonnet-4-6"
    }
    
    if model is None:
        model = default_models.get(provider, "llama3.1:8b")
    
    return LLM(provider=provider, model=model)

if __name__ == "__main__":
    # 测试
    print("测试 Ollama...")
    llm = create_llm("ollama", "qwen2.5:3b")  # 使用已有的模型
    response = llm.generate("你好，请用一句话介绍你自己")
    print(f"响应: {response.content}")
    print(f"Tokens: {response.tokens_used}")
    print(f"成本: ¥{response.cost:.4f}")
