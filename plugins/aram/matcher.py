# aios/plugins/aram/matcher.py - 英雄模糊搜索 v0.2（可解释性）
import json, sys
from pathlib import Path
from difflib import SequenceMatcher

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from core.config import get_path
from plugins.aram.data_adapter import load_champions, load_aliases, save_aliases

LOW_SCORE = 0.5


def _sim(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _matched_keywords(query: str, target: str) -> list:
    """提取 query 和 target 之间的重叠字符/词"""
    q_chars = set(query.lower())
    t_chars = set(target.lower())
    # 中文按字符匹配，英文按 token
    overlap = q_chars & t_chars - {" ", ",", "."}
    return sorted(overlap) if overlap else []


def match(query: str, top_n: int = 3) -> list:
    """输入 → 匹配 → 输出 JSON + 事件"""
    data = load_champions()
    if not data:
        return []

    query = query.strip()
    results = []
    aliases = load_aliases()

    # 0. learned aliases
    if query in aliases:
        cid = aliases[query]
        if cid in data:
            info = data[cid]
            results.append(
                _result(
                    cid,
                    info,
                    1.0,
                    "learned",
                    f"learned: {query} → {info.get('title','')}",
                    query,
                )
            )
            _emit(query, results[0])
            return results

    # 1. builtin aliases (from rules)
    from plugins.aram.rules import BUILTIN_ALIASES

    if query in BUILTIN_ALIASES:
        cid = BUILTIN_ALIASES[query]
        if cid in data:
            info = data[cid]
            results.append(
                _result(
                    cid,
                    info,
                    1.0,
                    "alias_exact",
                    f"alias: {query} → {info.get('title','')}",
                    query,
                )
            )
            _emit(query, results[0])
            return results

    # 2. name/title contains
    for cid, info in data.items():
        name = info.get("name", "")
        title = info.get("title", "")
        if query in name or query in title:
            score = 0.95 if query == title else 0.90
            results.append(
                _result(
                    cid,
                    info,
                    score,
                    "contains",
                    f"contains: '{query}' in '{title}/{name}'",
                    query,
                )
            )

    # 3. fuzzy
    for cid, info in data.items():
        if any(r["champion_id"] == cid for r in results):
            continue
        name = info.get("name", "")
        title = info.get("title", "")
        best = max(_sim(query, name), _sim(query, title))
        if best >= LOW_SCORE:
            results.append(
                _result(cid, info, round(best, 2), "fuzzy", f"fuzzy: {best:.2f}", query)
            )

    # dedup + sort
    seen = {}
    for r in results:
        cid = r["champion_id"]
        if cid not in seen or r["score"] > seen[cid]["score"]:
            seen[cid] = r
    final = sorted(seen.values(), key=lambda x: x["score"], reverse=True)[:top_n]

    if final:
        _emit(query, final[0], alternatives=final[1:])
    return final


def feedback(query: str, correct_id: str):
    """用户纠正"""
    data = load_champions()
    prev = match(query, top_n=1)
    wrong_title = prev[0]["title"] if prev else ""
    correct_title = data.get(correct_id, {}).get("title", "")

    # 写入 learned aliases
    aliases = load_aliases()
    aliases[query] = correct_id
    save_aliases(aliases)

    # 事件
    from core.engine import log_mem

    log_mem(
        "correction",
        status="err",
        source="aram.matcher",
        query=query,
        wrong=wrong_title,
        correct=correct_title,
        correct_id=correct_id,
    )

    return {
        "input": query,
        "matched": wrong_title,
        "corrected": True,
        "correct_target": correct_title,
    }


def _result(cid, info, score, match_type, reason, query=""):
    title = info.get("title", "")
    name = info.get("name", "")
    keywords = _matched_keywords(query, title) if query else []
    return {
        "champion_id": cid,
        "name": name,
        "title": title,
        "score": score,
        "match_type": match_type,
        "reason": reason,
        "matched_keywords": keywords,
        "confidence": "HIGH" if score >= 0.8 else "MEDIUM" if score >= 0.6 else "LOW",
    }


def _emit(query, top, alternatives=None):
    from core.engine import log_mem

    alt_names = [a["title"] for a in (alternatives or [])[:3]]
    log_mem(
        "memory_recall",
        source="aram.matcher",
        query=query,
        hit_count=1 + len(alt_names),
        matched=top["title"],
        matched_id=top["champion_id"],
        score=top["score"],
        match_type=top["match_type"],
        matched_keywords=top.get("matched_keywords", []),
        confidence=top.get("confidence", ""),
        alternatives=alt_names,
    )


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "凯隐"
    if len(sys.argv) >= 3 and sys.argv[1] == "feedback":
        print(json.dumps(feedback(sys.argv[2], sys.argv[3]), ensure_ascii=False))
    else:
        for r in match(q):
            print(
                json.dumps(
                    {
                        "input": q,
                        "matched": r["title"],
                        "champion_id": r["champion_id"],
                        "score": r["score"],
                        "reasons": [r["match_type"]],
                    },
                    ensure_ascii=False,
                )
            )
