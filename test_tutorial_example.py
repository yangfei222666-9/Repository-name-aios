"""测试 TUTORIAL.md 里的代码示例"""
import sys
sys.path.insert(0, 'C:\\Users\\A\\.openclaw\\workspace\\aios')

from memory import MemoryPalace

# 示例：Store knowledge
mp = MemoryPalace()

mp.store("lesson_timeout", {
    "category": "network",
    "content": "Connection timeouts often resolve with retry + exponential backoff",
    "confidence": 0.9,
    "source": "playbook:retry_on_timeout",
    "verified_count": 0
})

# 示例：Query knowledge
results = mp.query("how to handle connection timeout", top_k=3)

print(f"✓ Stored 1 lesson")
print(f"✓ Query returned {len(results)} results")

if len(results) > 0:
    print(f"✓ First result: {results[0]['content'][:50]}...")
    print("\n✅ Memory Palace API 示例代码运行成功！")
else:
    print("⚠️ Query 没有返回结果")
