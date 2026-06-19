#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    print('=== 1. 测试健康检查 ===')
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'
    print('  OK!')


def test_fuel_types_api():
    print('\n=== 2. 测试燃油类型 API ===')
    response = client.get('/api/metrics/carbon/fuel-types')
    assert response.status_code == 200
    data = response.json()
    print(f'  获取到 {len(data["fuel_types"])} 种燃油类型')
    for ft in data['fuel_types']:
        print(f'    {ft["code"]}: {ft["name"]}, 碳排放因子: {ft["carbon_factor"]}')
    assert len(data['fuel_types']) == 4
    print('  OK!')


def test_carbon_predict_api():
    print('\n=== 3. 测试碳排放预测 API ===')
    payload = {
        'distance': 5000,
        'avg_speed': 15,
        'fuel_type': 'HFO'
    }
    response = client.post('/api/metrics/carbon/predict', json=payload)
    assert response.status_code == 200
    data = response.json()
    print(f'  总碳排放: {data["total_carbon_emission"]} 吨 CO₂')
    print(f'  总油耗: {data["total_fuel_consumption"]} 吨')
    print(f'  燃油类型: {data["fuel_type_name"]}')
    print(f'  航行时间: {data["duration_hours"]} 小时')
    print(f'  能效系数: {data["efficiency_coefficient"]}')
    print(f'  能效等级: {data["efficiency_level"]}')
    print(f'  CO₂当量: {data["emission_breakdown"]["co2_equivalent"]}')
    print(f'  建议数: {len(data["recommendations"])}')
    assert data['total_carbon_emission'] > 0
    assert data['total_fuel_consumption'] > 0
    assert data['efficiency_level'] in ['excellent', 'good', 'fair', 'poor']
    print('  OK!')


def test_carbon_predict_invalid_fuel():
    print('\n=== 4. 测试无效燃油类型 API ===')
    payload = {
        'distance': 5000,
        'avg_speed': 15,
        'fuel_type': 'INVALID'
    }
    response = client.post('/api/metrics/carbon/predict', json=payload)
    assert response.status_code == 400
    print(f'  正确返回 400 错误: {response.json()["detail"]}')
    print('  OK!')


def test_carbon_predict_validation():
    print('\n=== 5. 测试参数验证 ===')
    payload = {
        'distance': -100,
        'avg_speed': 15,
        'fuel_type': 'HFO'
    }
    response = client.post('/api/metrics/carbon/predict', json=payload)
    assert response.status_code == 422
    print(f'  正确返回 422 验证错误')
    print('  OK!')


def test_carbon_predict_with_lng():
    print('\n=== 6. 测试 LNG 燃油 (验证低碳排放) ===')
    payload_hfo = {
        'distance': 5000,
        'avg_speed': 15,
        'fuel_type': 'HFO'
    }
    payload_lng = {
        'distance': 5000,
        'avg_speed': 15,
        'fuel_type': 'LNG'
    }
    hfo_result = client.post('/api/metrics/carbon/predict', json=payload_hfo).json()
    lng_result = client.post('/api/metrics/carbon/predict', json=payload_lng).json()

    print(f'  HFO 碳排放: {hfo_result["total_carbon_emission"]} 吨')
    print(f'  LNG 碳排放: {lng_result["total_carbon_emission"]} 吨')
    assert lng_result['total_carbon_emission'] < hfo_result['total_carbon_emission']
    print('  OK! (LNG碳排放低于HFO)')


if __name__ == '__main__':
    print('开始碳排放 API 端到端测试...\n')
    try:
        test_health_check()
        test_fuel_types_api()
        test_carbon_predict_api()
        test_carbon_predict_invalid_fuel()
        test_carbon_predict_validation()
        test_carbon_predict_with_lng()
        print('\n' + '=' * 50)
        print('所有 API 测试通过！')
        print('=' * 50)
    except Exception as e:
        print(f'\n测试失败: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
