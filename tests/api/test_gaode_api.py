"""
测试高德API是否正常工作
"""
import sys
sys.path.insert(0, 'src')

from src.data_services.gaode_api_client import GaodeAPIClient

API_KEY = "c0879532b66de630ce0e0937e828fa12"

print("="*70)
print("Testing Gaode API")
print("="*70)

client = GaodeAPIClient(API_KEY)

print("\nTest 1: Search POI in Suzhou...")
pois = client.search_poi(
    keywords="景点|博物馆|公园",
    city="苏州",
    page=1,
    page_size=10
)

if pois:
    print(f"[OK] Got {len(pois)} POIs")
    for i, poi in enumerate(pois[:5]):
        print(f"   {i+1}. {poi.get('name')}")
        print(f"      Type: {poi.get('type')}")
        print(f"      Location: {poi.get('location')}")
else:
    print("[ERROR] No POIs returned")
    print("   Possible reasons:")
    print("   1. API Key invalid")
    print("   2. Rate limit reached")
    print("   3. Network error")

print("\n" + "="*70)
