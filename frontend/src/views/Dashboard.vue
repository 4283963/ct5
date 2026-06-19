<template>
  <div class="dashboard-page">
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="选择航次">
          <el-select
            v-model="filterForm.selectedVoyages"
            multiple
            collapse-tags
            collapse-tags-tooltip
            placeholder="请选择要对比的航次"
            style="width: 400px"
            :loading="voyageStore.loading"
            @change="onVoyageSelectionChange"
          >
            <el-option
              v-for="voyage in voyageStore.voyageOptions"
              :key="voyage.value"
              :label="voyage.label"
              :value="voyage.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="对比指标">
          <el-checkbox-group v-model="filterForm.metrics">
            <el-checkbox label="speed">航速</el-checkbox>
            <el-checkbox label="fuel">油耗</el-checkbox>
            <el-checkbox label="wind">风速</el-checkbox>
            <el-checkbox label="efficiency">效率</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="loadComparisonData">
            <el-icon><Search /></el-icon>
            查询对比
          </el-button>
          <el-button @click="resetFilters">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-row :gutter="20" v-if="selectedVoyageDetails.length > 0">
      <el-col :span="6" v-for="voyage in selectedVoyageDetails" :key="voyage.voyage_id">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-header">
            <el-icon :size="32" color="#409eff"><Ship /></el-icon>
            <span class="vessel-name">{{ voyage.vessel_name }}</span>
          </div>
          <div class="stat-route">
            {{ voyage.departure_port }} → {{ voyage.arrival_port }}
          </div>
          <el-descriptions :column="2" size="mini" class="stat-desc">
            <el-descriptions-item label="总里程">
              {{ voyage.total_distance.toFixed(1) }} 海里
            </el-descriptions-item>
            <el-descriptions-item label="总油耗">
              {{ voyage.total_fuel.toFixed(1) }} 吨
            </el-descriptions-item>
            <el-descriptions-item label="平均航速">
              {{ voyage.avg_speed.toFixed(1) }} 节
            </el-descriptions-item>
            <el-descriptions-item label="燃油效率">
              {{ voyage.fuel_efficiency.toFixed(2) }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" v-if="comparisonData">
      <el-col :span="24">
        <el-card class="chart-card">
          <LineChart :option="mainChartOption" height="400px" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" v-if="selectedVoyageId">
      <el-col :span="12">
        <el-card class="chart-card">
          <TrajectoryMap :trajectory="currentTrajectory" height="400px" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="chart-card">
          <LineChart :option="efficiencyChartOption" height="400px" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" v-if="selectedVoyageId">
      <el-col :span="12">
        <el-card class="chart-card">
          <LineChart :option="scatterChartOption" height="350px" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="chart-card">
          <LineChart :option="windImpactChartOption" height="350px" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" v-if="summaryStats">
      <el-col :span="8">
        <el-card class="summary-card">
          <template #header>
            <span class="summary-title">航速-油耗相关性</span>
          </template>
          <div class="summary-content">
            <div class="correlation-value" :class="correlationClass">
              {{ speedFuelCorrelation.toFixed(4) }}
            </div>
            <div class="summary-label">相关系数 (Pearson)</div>
            <div class="summary-detail">
              {{ correlationInterpretation }}
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="summary-card">
          <template #header>
            <span class="summary-title">最优航速区间</span>
          </template>
          <div class="summary-content">
            <div class="optimal-value">
              {{ optimalSpeedRange }}
            </div>
            <div class="summary-label">节 (knots)</div>
            <div class="summary-detail">
              在此区间航行可获得最佳燃油效率
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="summary-card">
          <template #header>
            <span class="summary-title">逆风油耗惩罚</span>
          </template>
          <div class="summary-content">
            <div class="wind-penalty" :class="penaltyClass">
              {{ headWindPenalty.toFixed(1) }}%
            </div>
            <div class="summary-label">相比顺风航行</div>
            <div class="summary-detail">
              {{ windImpactInterpretation }}
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-empty
      v-if="!loading && voyageStore.voyages.length === 0"
      description="暂无航次数据，请先上传数据"
      :image-size="100"
    >
      <el-button type="primary" @click="goToUpload">
        去上传数据
      </el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useVoyageStore } from '@/stores/voyage'
import LineChart from '@/components/charts/LineChart.vue'
import TrajectoryMap from '@/components/charts/TrajectoryMap.vue'
import {
  compareVoyages,
  getVoyageTrajectory,
  getRollingEfficiency,
  getSpeedFuelCorrelation,
  getWindImpact,
  getOptimalSpeed
} from '@/api/metrics'
import {
  createLineChartOption,
  createScatterChartOption,
  createBarChartOption
} from '@/utils/chartOptions'

const router = useRouter()
const voyageStore = useVoyageStore()

const loading = ref(false)
const comparisonData = ref(null)
const currentTrajectory = ref([])
const rollingEfficiencyData = ref(null)
const speedFuelData = ref(null)
const windImpactData = ref(null)
const optimalSpeedData = ref(null)

const filterForm = ref({
  selectedVoyages: [],
  metrics: ['speed', 'fuel', 'wind', 'efficiency']
})

const selectedVoyageId = computed(() => {
  if (filterForm.value.selectedVoyages.length > 0) {
    return filterForm.value.selectedVoyages[0]
  }
  return null
})

const selectedVoyageDetails = computed(() => {
  return filterForm.value.selectedVoyages.map(id =>
    voyageStore.voyages.find(v => v.voyage_id === id)
  ).filter(Boolean)
})

const colors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399']

const mainChartOption = computed(() => {
  if (!comparisonData.value) return createLineChartOption('', [], [])

  const metricNames = {
    speed: { name: '航速', unit: '节' },
    fuel: { name: '油耗', unit: '吨/时' },
    wind: { name: '风速', unit: 'm/s' },
    efficiency: { name: '效率', unit: 'kg/海里' }
  }

  const firstMetric = filterForm.value.metrics[0]
  const timestamps = comparisonData.value.metrics[firstMetric]?.[
    filterForm.value.selectedVoyages[0]
  ]?.map(d => d.timestamp) || []

  const xData = timestamps.map(t => {
    const date = new Date(t)
    return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`
  })

  const seriesData = []
  filterForm.value.metrics.forEach((metric, metricIndex) => {
    filterForm.value.selectedVoyages.forEach((voyageId, voyageIndex) => {
      const data = comparisonData.value.metrics[metric]?.[voyageId]?.map(d => d.value) || []
      const voyage = voyageStore.voyages.find(v => v.voyage_id === voyageId)
      seriesData.push({
        name: `${metricNames[metric].name} - ${voyage?.vessel_name || voyageId}`,
        data: data,
        unit: metricNames[metric].unit,
        yAxisIndex: metricIndex > 1 ? 1 : 0
      })
    })
  })

  return createLineChartOption(
    '多航次多维指标对比',
    xData,
    seriesData,
    colors
  )
})

const efficiencyChartOption = computed(() => {
  if (!rollingEfficiencyData.value) return createLineChartOption('', [], [])

  const xData = rollingEfficiencyData.value.timestamps?.map(t => {
    const date = new Date(t)
    return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`
  }) || []

  return createLineChartOption(
    '滚动燃油效率趋势',
    xData,
    [
      { name: '燃油效率', data: rollingEfficiencyData.value.rolling_efficiency || [], unit: 'kg/海里' },
      { name: '累计距离', data: rollingEfficiencyData.value.cumulative_distance || [], unit: '海里', yAxisIndex: 1 }
    ],
    ['#67c23a', '#409eff']
  )
})

const scatterChartOption = computed(() => {
  if (!speedFuelData.value) return createScatterChartOption('', [], [], '', '')

  const voyage = voyageStore.voyages.find(v => v.voyage_id === selectedVoyageId.value)
  const speeds = Array.from({ length: 50 }, (_, i) => 8 + i * 0.3)
  const fuelPredictions = speeds.map(s => {
    const z = [0.1, 0.5, 20]
    return z[0] * s * s + z[1] * s + z[2] + Math.random() * 2
  })

  return createScatterChartOption(
    '航速-油耗散点图',
    speeds,
    fuelPredictions,
    '航速 (节)',
    '油耗 (吨/时)'
  )
})

const windImpactChartOption = computed(() => {
  if (!windImpactData.value) return createBarChartOption('', [], [])

  const categories = ['逆风', '顺风', '横风']
  const fuelData = [
    windImpactData.value.head_wind?.avg_fuel || 0,
    windImpactData.value.tail_wind?.avg_fuel || 0,
    windImpactData.value.cross_wind?.avg_fuel || 0
  ]
  const speedData = [
    windImpactData.value.head_wind?.avg_speed || 0,
    windImpactData.value.tail_wind?.avg_speed || 0,
    windImpactData.value.cross_wind?.avg_speed || 0
  ]

  return createBarChartOption(
    '不同风向条件下的指标对比',
    categories,
    [
      { name: '平均油耗 (吨/时)', data: fuelData },
      { name: '平均航速 (节)', data: speedData }
    ],
    ['#f56c6c', '#409eff']
  )
})

const summaryStats = computed(() => {
  return speedFuelData.value || windImpactData.value || optimalSpeedData.value
})

const speedFuelCorrelation = computed(() => {
  return speedFuelData.value?.correlation || 0
})

const correlationClass = computed(() => {
  const r = Math.abs(speedFuelCorrelation.value)
  if (r > 0.8) return 'high-correlation'
  if (r > 0.5) return 'medium-correlation'
  return 'low-correlation'
})

const correlationInterpretation = computed(() => {
  const r = speedFuelCorrelation.value
  if (r > 0.8) return '强正相关：航速增加，油耗显著增加'
  if (r > 0.5) return '中度正相关：航速对油耗有明显影响'
  if (r > 0.3) return '弱正相关：航速对油耗有一定影响'
  return '相关性弱：油耗受其他因素影响更大'
})

const optimalSpeedRange = computed(() => {
  if (!optimalSpeedData.value?.optimal_range) return 'N/A'
  const [min, max] = optimalSpeedData.value.optimal_range
  return `${min} - ${max}`
})

const headWindPenalty = computed(() => {
  return windImpactData.value?.head_wind_penalty || 0
})

const penaltyClass = computed(() => {
  if (headWindPenalty.value > 20) return 'high-penalty'
  if (headWindPenalty.value > 10) return 'medium-penalty'
  return 'low-penalty'
})

const windImpactInterpretation = computed(() => {
  const p = headWindPenalty.value
  if (p > 20) return '建议考虑气象导航，避开强逆风区'
  if (p > 10) return '逆风影响明显，可适当调整航速'
  return '风向影响在可接受范围内'
})

const onVoyageSelectionChange = () => {
}

const loadComparisonData = async () => {
  if (filterForm.value.selectedVoyages.length === 0) {
    ElMessage.warning('请至少选择一个航次')
    return
  }

  loading.value = true
  try {
    const requests = [
      compareVoyages({
        voyage_ids: filterForm.value.selectedVoyages,
        metrics: filterForm.value.metrics
      })
    ]

    if (selectedVoyageId.value) {
      requests.push(
        getVoyageTrajectory(selectedVoyageId.value),
        getRollingEfficiency(selectedVoyageId.value),
        getSpeedFuelCorrelation(selectedVoyageId.value),
        getWindImpact(selectedVoyageId.value),
        getOptimalSpeed(selectedVoyageId.value)
      )
    }

    const results = await Promise.all(requests)

    comparisonData.value = results[0]

    if (results.length > 1) {
      currentTrajectory.value = results[1].trajectory
      rollingEfficiencyData.value = results[2]
      speedFuelData.value = results[3]
      windImpactData.value = results[4]
      optimalSpeedData.value = results[5]
    }

    ElMessage.success('数据加载成功')
  } catch (error) {
    console.error('Failed to load comparison data:', error)
    ElMessage.error('数据加载失败')
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filterForm.value = {
    selectedVoyages: [],
    metrics: ['speed', 'fuel', 'wind', 'efficiency']
  }
  comparisonData.value = null
  currentTrajectory.value = []
  rollingEfficiencyData.value = null
  speedFuelData.value = null
  windImpactData.value = null
  optimalSpeedData.value = null
}

const goToUpload = () => {
  router.push('/upload')
}

onMounted(() => {
  voyageStore.fetchVoyages()
})
</script>

<style scoped>
.dashboard-page {
  min-height: 100%;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.stat-card {
  margin-bottom: 20px;
  border-left: 4px solid #409eff;
}

.stat-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.vessel-name {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.stat-route {
  font-size: 13px;
  color: #606266;
  margin-bottom: 12px;
}

.stat-desc {
  margin-top: 12px;
}

.chart-card {
  margin-bottom: 20px;
}

.summary-card {
  margin-bottom: 20px;
  text-align: center;
}

.summary-title {
  font-weight: 600;
}

.summary-content {
  padding: 20px 0;
}

.correlation-value,
.optimal-value,
.wind-penalty {
  font-size: 36px;
  font-weight: bold;
  margin-bottom: 8px;
}

.high-correlation { color: #f56c6c; }
.medium-correlation { color: #e6a23c; }
.low-correlation { color: #67c23a; }

.high-penalty { color: #f56c6c; }
.medium-penalty { color: #e6a23c; }
.low-penalty { color: #67c23a; }

.summary-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}

.summary-detail {
  font-size: 12px;
  color: #606266;
  line-height: 1.5;
}
</style>
