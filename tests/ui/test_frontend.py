"""
测试前端完整流程
"""
import requests
import json

API_BASE = "http://localhost:8000"

print("="*70)
print("Testing Complete Frontend Workflow")
print("="*70)

# Step 1: 创建会话
print("\n[Step 1] Create session...")
response = requests.post(f"{API_BASE}/api/session/start", json={
    "user_input": "我想在苏州玩1天，喜欢文化和园林",
    "start_location": "拙政园",
    "city": "苏州"
})

if response.status_code != 200:
    print(f"[ERROR] Failed: {response.status_code}")
    exit(1)

data = response.json()
session_id = data['session_id']
print(f"[OK] Session ID: {session_id}")
print(f"     Start node: {data['start_node']['name']}")

# Step 2: 展开第一层
print("\n[Step 2] Expand from start node...")
response = requests.post(f"{API_BASE}/api/session/next", json={
    "session_id": session_id,
    "selected_poi_id": "start",
    "current_time": 9.0
})

if response.status_code != 200:
    print(f"[ERROR] Failed: {response.status_code}")
    exit(1)

data = response.json()
print(f"[OK] Received {len(data['nodes'])} candidate nodes")
if 'edges' in data:
    print(f"     Received {len(data['edges'])} edges")
else:
    print(f"     (No edges field in response)")

# 显示前5个候选
print("\n[Candidates (top 5)]:")
for i, node in enumerate(data['nodes'][:5], 1):
    print(f"  {i}. {node['name']}")
    print(f"     Score: {node['score']:.3f}")
    print(f"     Type: {node['type']}")
    print(f"     Distance: {node.get('distance_from_prev', 0):.2f} km")
    if 'verification' in node and node['verification']:
        v = node['verification']
        # ✅ 计算overall_trust_score（API返回的是字典，不是对象）
        consistency = v.get('consistency', 0) / 100  # 转回0-1
        fake_rate = v.get('fake_rate', 0) / 100
        spatial = v.get('spatial', 0)
        temporal = v.get('temporal', 0)
        trust = 0.25 * consistency + 0.25 * (1 - fake_rate) + 0.25 * spatial + 0.25 * temporal
        print(f"     Trust: {trust:.2f} (C:{consistency:.2f} F:{fake_rate:.2f} S:{spatial:.2f} T:{temporal:.2f})")
    print()

# 检查是否使用降级策略
scores = [n['score'] for n in data['nodes']]
if len(set(scores)) == 1 and 0.75 in scores:
    print("[WARNING] All scores are 0.75 - fallback strategy used!")
else:
    print(f"[SUCCESS] Score range: {min(scores):.3f} - {max(scores):.3f}")
    print("[SUCCESS] ProgressivePlanner working correctly!")

# Step 3: 选择一个节点继续展开
if data['nodes']:
    selected = data['nodes'][0]
    print(f"\n[Step 3] Select node: {selected['name']}")
    
    response = requests.post(f"{API_BASE}/api/session/next", json={
        "session_id": session_id,
        "selected_poi_id": selected['id'],
        "current_time": 11.0
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Expanded to {len(data['nodes'])} new candidates")
        print(f"     Total nodes in graph: {len(data['nodes'])}")
    else:
        print(f"[ERROR] Failed to expand: {response.status_code}")

print("\n" + "="*70)
print("Frontend workflow test complete!")
print("="*70)
print("\nNext: Open http://localhost:8000/static/progressive.html in browser")
