#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from app.config import settings
from app.models.schemas import (
    CarbonEmissionRequest, CarbonEmissionResponse,
    FuelTypeInfo, FuelTypesResponse
)
from app.services.metrics_calculator import metrics_calculator


def test_config():
    print('=== 1. 测试配置加载 ===')
    print(f'燃油类型: {list(settings.FUEL_TYPES.keys())}')
    for code, info in settings.FUEL_TYPES.items():
        print(f'  {code}: {info["name"]}, 碳排放因子: {info["carbon_factor"]}')
    print('  OK!')


def test_fuel_types():
    print('\n=== 2. 测试获取燃油类型列表 ===')
    fuel_types = metrics_calculator.get_available_fuel_types()
    print(f'获取到 {len(fuel_types.fuel_types)} 种燃油类型')
    for ft in fuel_types.fuel_types:
        print(f'  {ft.code}: {ft.name}')
    assert len(fuel_types.fuel_types) == 4
    print('  OK!')


def test_carbon_calculation_basic():
    print('\n=== 3. 测试碳排放计算 (无参考航次) ===')
    result = metrics_calculator.calculate_carbon_emission(
        distance=5000,
        avg_speed=15,
        fuel_type='HFO'
    )
    print(f'  总碳排放: {result.total_carbon_emission} 吨 CO₂')
    print(f'  总油耗: {result.total_fuel_consumption} 吨')
    print(f'  燃油类型: {result.fuel_type_name}')
    print(f'  航行时间: {result.duration_hours} 小时')
    print(f'  能效系数: {result.efficiency_coefficient}')
    print(f'  能效等级: {result.efficiency_level}')
    print(f'  硫排放: {result.sulfur_emission} 吨')
    print(f'  排放明细: {result.emission_breakdown}')
    print(f'  优化建议数: {len(result.recommendations)}')
    for rec in result.recommendations:
        print(f'    - {rec}')
    assert result.total_carbon_emission > 0
    assert result.total_fuel_consumption > 0
    print('  OK!')


def test_different_fuels():
    print('\n=== 4. 测试不同燃油类型 ===')
    results = {}
    for fuel in ['HFO', 'MGO', 'LNG', 'VLSFO']:
        r = metrics_calculator.calculate_carbon_emission(
            distance=5000, avg_speed=15, fuel_type=fuel
        )
        results[fuel] = r.total_carbon_emission
        print(f'  {fuel}: {r.total_carbon_emission} 吨 CO₂')
    assert results['LNG'] < results['HFO']
    assert results['LNG'] < results['MGO']
    print('  OK! (LNG碳排放最低)')


def test_different_speeds():
    print('\n=== 5. 测试不同航速 (验证速度惩罚) ===')
    results = {}
    for speed in [10, 14, 15, 16, 20, 25]:
        r = metrics_calculator.calculate_carbon_emission(
            distance=5000, avg_speed=speed, fuel_type='HFO'
        )
        results[speed] = r.total_carbon_emission
        print(f'  {speed}节: {r.total_carbon_emission} 吨 CO₂')
    assert results[20] > results[15]
    assert results[25] > results[20]
    print('  OK! (航速越高碳排放越高)')


def test_invalid_fuel():
    print('\n=== 6. 测试无效燃油类型 ===')
    try:
        metrics_calculator.calculate_carbon_emission(
            distance=5000, avg_speed=15, fuel_type='INVALID'
        )
        print('  FAIL: 应该抛出异常')
    except ValueError as e:
        print(f'  正确捕获异常: {e}')
        print('  OK!')


if __name__ == '__main__':
    print('开始碳排放计算模块测试...\n')
    try:
        test_config()
        test_fuel_types()
        test_carbon_calculation_basic()
        test_different_fuels()
        test_different_speeds()
        test_invalid_fuel()
        print('\n' + '=' * 50)
        print('所有测试通过！')
        print('=' * 50)
    except Exception as e:
        print(f'\n测试失败: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
