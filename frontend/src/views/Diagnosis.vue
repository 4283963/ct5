<template>
  <div class="diagnosis-page">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card class="ranking-card">
          <template #header>
            <div class="card-header">
              <el-icon><Trophy /></el-icon>
              <span>效益排名</span>
              <el-button
                type="primary"
                link
                @click="loadRanking"
                :loading="rankingLoading"
              >
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </template>
          <div class="ranking-stats" v-if="rankingData">
            <el-descriptions :column="1" size="small" border>
              <el-descriptions-item label="总航次数">
                {{ rankingData.total_voyages }}
              </el-descriptions-item>
              <el-descriptions-item label="平均效益得分">
                <span :class="getScoreClass(rankingData.average_score)">
                  {{ rankingData.average_score }}
                </span>
              </el-descriptions-item>
            </el-descriptions>
          </div>
          <el-table
            :data="rankingData?.ranking || []"
            size="small"
            style="margin-top: 16px"
            v-loading="rankingLoading"
            @row-click="selectVoyage"
            highlight-current-row
          >
            <el-table-column label="排名" width="50" align="center">
              <template #default="{ $index }">
                <el-tag
                  size="small"
                  :type="$index < 3 ? 'warning' : 'info'"
                  effect="dark"
                >
                  {{ $index + 1 }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="船舶" show-overflow-tooltip>
              <template #default="{ row }">
                {{ row.vessel_name }}
              </template>
            </el-table-column>
            <el-table-column label="效益得分" width="80" align="center">
              <template #default="{ row }">
                <span :class="getScoreClass(row.efficiency_score)">
                  {{ row.efficiency_score.toFixed(1) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="问题数" width="60" align="center">
              <template #default="{ row }">
                <el-tag
                  size="small"
                  :type="row.issues_count > 3 ? 'danger' : row.issues_count > 0 ? 'warning' : 'success'"
                >
                  {{ row.issues_count }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card class="statistics-card">
          <template #header>
            <div class="card-header">
              <el-icon><DataLine /></el-icon>
              <span>整体统计</span>
            </div>
          </template>
          <div v-if="statisticsData" class="statistics-content">
            <LineChart :option="efficiencyDistributionChart" height="250px" />
            <el-divider />
            <LineChart :option="issueTypeChart" height="200px" />
            <el-divider />
            <div class="total-saving">
              <el-icon :size="24" color="#67c23a"><Money /></el-icon>
              <div>
                <div class="saving-value">
                  {{ statisticsData.total_potential_saving.toFixed(1) }} 吨
                </div>
                <div class="saving-label">潜在节油总量</div>
              </div>
            </div>
          </div>
          <el-skeleton v-else :rows="8" animated />
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card class="detail-card" v-if="selectedVoyage">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <el-icon :size="24" color="#409eff"><Ship /></el-icon>
                <span class="voyage-title">
                  {{ selectedVoyage.vessel_name }} -
                  {{ selectedVoyage.departure_port }} → {{ selectedVoyage.arrival_port }}
                </span>
              </div>
              <el-button-group>
                <el-button
                  type="primary"
                  size="small"
                  :loading="diagnosisLoading"
                  @click="loadDiagnosis"
                >
                  <el-icon><View /></el-icon>
                  诊断分析
                </el-button>
                <el-button
                  type="success"
                  size="small"
                  :loading="planLoading"
                  @click="loadOptimizationPlan"
                >
                  <el-icon><Promotion /></el-icon>
                  优化方案
                </el-button>
              </el-button-group>
            </div>
          </template>

          <el-row :gutter="20" v-if="diagnosisData">
            <el-col :span="6">
              <div class="score-gauge">
                <LineChart :option="scoreGaugeOption" height="200px" />
              </div>
            </el-col>
            <el-col :span="18">
              <el-descriptions :column="3" border size="small">
                <el-descriptions-item label="总里程">
                  {{ selectedVoyage.total_distance.toFixed(1) }} 海里
                </el-descriptions-item>
                <el-descriptions-item label="总油耗">
                  {{ selectedVoyage.total_fuel.toFixed(1) }} 吨
                </el-descriptions-item>
                <el-descriptions-item label="燃油效率">
                  {{ selectedVoyage.fuel_efficiency.toFixed(2) }} kg/海里
                </el-descriptions-item>
                <el-descriptions-item label="问题总数">
                  <el-tag type="danger">
                    {{ diagnosisData.issues.length }} 个
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="潜在节油">
                  <span class="saving-text">
                    {{ diagnosisData.total_potential_saving.toFixed(1) }} 吨
                  </span>
                </el-descriptions-item>
                <el-descriptions-item label="航行时间">
                  {{ calculateDuration(selectedVoyage.start_time, selectedVoyage.end_time) }}
                </el-descriptions-item>
              </el-descriptions>
            </el-col>
          </el-row>

          <el-tabs v-model="activeTab" v-if="diagnosisData" style="margin-top: 20px">
            <el-tab-pane label="问题清单" name="issues">
              <el-table
                :data="diagnosisData.issues"
                size="small"
                stripe
                style="width: 100%"
              >
                <el-table-column label="严重程度" width="100">
                  <template #default="{ row }">
                    <el-tag
                      :type="row.severity === 'high' ? 'danger' : row.severity === 'medium' ? 'warning' : 'info'"
                      effect="dark"
                    >
                      {{ getSeverityText(row.severity) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="问题类型" width="140">
                  <template #default="{ row }">
                    {{ getIssueTypeText(row.issue_type) }}
                  </template>
                </el-table-column>
                <el-table-column label="描述" show-overflow-tooltip>
                  <template #default="{ row }">
                    {{ row.description }}
                  </template>
                </el-table-column>
                <el-table-column label="建议措施" width="200" show-overflow-tooltip>
                  <template #default="{ row }">
                    {{ row.suggested_action }}
                  </template>
                </el-table-column>
                <el-table-column label="潜在节油" width="100" align="right">
                  <template #default="{ row }">
                    <span class="saving-text">
                      {{ row.potential_saving.toFixed(1) }} 吨
                    </span>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>

            <el-tab-pane label="优化方案" name="plan" v-if="optimizationPlan">
              <div class="optimization-header">
                <div class="optimization-stat">
                  <div class="stat-label">基准效益</div>
                  <div class="stat-value baseline">
                    {{ optimizationPlan.baseline_efficiency.toFixed(1) }}
                  </div>
                </div>
                <div class="optimization-arrow">
                  <el-icon :size="32" color="#67c23a"><Right /></el-icon>
                </div>
                <div class="optimization-stat">
                  <div class="stat-label">目标效益</div>
                  <div class="stat-value target">
                    {{ optimizationPlan.target_efficiency.toFixed(1) }}
                  </div>
                </div>
                <div class="optimization-stat">
                  <div class="stat-label">预期提升</div>
                  <div class="stat-value improvement">
                    +{{ (optimizationPlan.target_efficiency - optimizationPlan.baseline_efficiency).toFixed(1) }}
                  </div>
                </div>
                <div class="optimization-stat">
                  <div class="stat-label">投资回报</div>
                  <div class="stat-value payback">
                    {{ optimizationPlan.estimated_payback_period }}
                  </div>
                </div>
              </div>

              <el-divider />

              <el-table
                :data="optimizationPlan.suggestions"
                size="small"
                stripe
                style="width: 100%"
              >
                <el-table-column label="优先级" width="90">
                  <template #default="{ row }">
                    <el-tag
                      :type="row.priority === 'high' ? 'danger' : row.priority === 'medium' ? 'warning' : 'info'"
                      effect="dark"
                      size="small"
                    >
                      {{ getPriorityText(row.priority) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="类别" width="120">
                  <template #default="{ row }">
                    {{ getCategoryText(row.category) }}
                  </template>
                </el-table-column>
                <el-table-column label="优化建议" show-overflow-tooltip>
                  <template #default="{ row }">
                    {{ row.description }}
                  </template>
                </el-table-column>
                <el-table-column label="预期节油" width="100" align="center">
                  <template #default="{ row }">
                    <span class="saving-text">
                      {{ row.expected_saving_percent.toFixed(1) }}%
                    </span>
                  </template>
                </el-table-column>
                <el-table-column label="实施难度" width="100" align="center">
                  <template #default="{ row }">
                    {{ getDifficultyText(row.implementation_difficulty) }}
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>

            <el-tab-pane label="问题分布" name="distribution">
              <el-row :gutter="20">
                <el-col :span="12">
                  <LineChart :option="severityDistributionChart" height="300px" />
                </el-col>
                <el-col :span="12">
                  <LineChart :option="savingPotentialChart" height="300px" />
                </el-col>
              </el-row>
            </el-tab-pane>
          </el-tabs>

          <el-empty
            v-if="!diagnosisData && !diagnosisLoading"
            description="请选择一个航次并点击诊断分析"
            :image-size="100"
          />
        </el-card>

        <el-empty
          v-if="!selectedVoyage"
          description="请从左侧列表选择一个航次进行诊断分析"
          :image-size="120"
        />
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useVoyageStore } from '@/stores/voyage'
import LineChart from '@/components/charts/LineChart.vue'
import {
  getEfficiencyRanking,
  getDiagnosisStatistics,
  getVoyageDiagnosis,
  getOptimizationPlan
} from '@/api/diagnosis'
import {
  createGaugeChartOption,
  createPieChartOption,
  createBarChartOption
} from '@/utils/chartOptions'

const voyageStore = useVoyageStore()

const rankingLoading = ref(false)
const diagnosisLoading = ref(false)
const planLoading = ref(false)

const rankingData = ref(null)
const statisticsData = ref(null)
const diagnosisData = ref(null)
const optimizationPlan = ref(null)

const selectedVoyage = ref(null)
const activeTab = ref('issues')

const loadRanking = async () => {
  rankingLoading.value = true
  try {
    rankingData.value = await getEfficiencyRanking(20)
    await loadStatistics()
  } catch (error) {
    console.error('Failed to load ranking:', error)
    ElMessage.error('加载排名数据失败')
  } finally {
    rankingLoading.value = false
  }
}

const loadStatistics = async () => {
  try {
    statisticsData.value = await getDiagnosisStatistics()
  } catch (error) {
    console.error('Failed to load statistics:', error)
  }
}

const selectVoyage = (row) => {
  const voyage = voyageStore.voyages.find(v => v.voyage_id === row.voyage_id)
  selectedVoyage.value = voyage || row
  diagnosisData.value = null
  optimizationPlan.value = null
}

const loadDiagnosis = async () => {
  if (!selectedVoyage.value) {
    ElMessage.warning('请先选择一个航次')
    return
  }

  diagnosisLoading.value = true
  try {
    diagnosisData.value = await getVoyageDiagnosis(selectedVoyage.value.voyage_id)
    activeTab.value = 'issues'
    ElMessage.success('诊断分析完成')
  } catch (error) {
    console.error('Failed to load diagnosis:', error)
    ElMessage.error('诊断分析失败')
  } finally {
    diagnosisLoading.value = false
  }
}

const loadOptimizationPlan = async () => {
  if (!selectedVoyage.value) {
    ElMessage.warning('请先选择一个航次')
    return
  }

  planLoading.value = true
  try {
    optimizationPlan.value = await getOptimizationPlan(selectedVoyage.value.voyage_id)
    if (!diagnosisData.value) {
      await loadDiagnosis()
    }
    activeTab.value = 'plan'
    ElMessage.success('优化方案已生成')
  } catch (error) {
    console.error('Failed to load optimization plan:', error)
    ElMessage.error('生成优化方案失败')
  } finally {
    planLoading.value = false
  }
}

const scoreGaugeOption = computed(() => {
  if (!diagnosisData.value) return createGaugeChartOption('', 0)
  return createGaugeChartOption('综合效益得分', diagnosisData.value.overall_efficiency_score)
})

const efficiencyDistributionChart = computed(() => {
  if (!statisticsData.value) return createPieChartOption('', [])

  const dist = statisticsData.value.efficiency_distribution || {}
  const data = Object.entries(dist).map(([name, value]) => ({
    name,
    value,
    itemStyle: {
      color: name.includes('excellent') ? '#67c23a' :
             name.includes('good') ? '#409eff' :
             name.includes('fair') ? '#e6a23c' : '#f56c6c'
    }
  }))

  return createPieChartOption('效益等级分布', data)
})

const issueTypeChart = computed(() => {
  if (!statisticsData.value) return createBarChartOption('', [], [])

  const types = statisticsData.value.issue_type_breakdown || {}
  const categories = Object.keys(types).map(getIssueTypeText)
  const values = Object.values(types)

  return createBarChartOption(
    '问题类型分布',
    categories,
    [{ name: '问题数量', data: values }],
    ['#409eff']
  )
})

const severityDistributionChart = computed(() => {
  if (!diagnosisData.value) return createPieChartOption('', [])

  const severityCount = {
    high: 0,
    medium: 0,
    low: 0
  }

  diagnosisData.value.issues.forEach(issue => {
    severityCount[issue.severity]++
  })

  const data = [
    { name: '高', value: severityCount.high, itemStyle: { color: '#f56c6c' } },
    { name: '中', value: severityCount.medium, itemStyle: { color: '#e6a23c' } },
    { name: '低', value: severityCount.low, itemStyle: { color: '#909399' } }
  ]

  return createPieChartOption('问题严重程度分布', data)
})

const savingPotentialChart = computed(() => {
  if (!diagnosisData.value) return createBarChartOption('', [], [])

  const issueTypes = {}
  diagnosisData.value.issues.forEach(issue => {
    const type = getIssueTypeText(issue.issue_type)
    if (!issueTypes[type]) {
      issueTypes[type] = 0
    }
    issueTypes[type] += issue.potential_saving
  })

  const categories = Object.keys(issueTypes)
  const values = Object.values(issueTypes).map(v => Number(v.toFixed(1)))

  return createBarChartOption(
    '各类问题节油潜力',
    categories,
    [{ name: '节油潜力 (吨)', data: values }],
    ['#67c23a']
  )
})

const getScoreClass = (score) => {
  if (score >= 90) return 'score-excellent'
  if (score >= 75) return 'score-good'
  if (score >= 60) return 'score-fair'
  return 'score-poor'
}

const getSeverityText = (severity) => {
  const map = { high: '高', medium: '中', low: '低' }
  return map[severity] || severity
}

const getIssueTypeText = (type) => {
  const map = {
    speed_too_low: '航速过低',
    speed_too_high: '航速过高',
    low_fuel_efficiency: '燃油效率低',
    high_wind_impact: '风阻影响大',
    data_anomaly: '数据异常',
    frequent_course_changes: '频繁转向'
  }
  return map[type] || type
}

const getPriorityText = (priority) => {
  const map = { high: '高', medium: '中', low: '低' }
  return map[priority] || priority
}

const getCategoryText = (category) => {
  const map = {
    speed_optimization: '航速优化',
    fuel_efficiency: '设备维护',
    weather_routeing: '气象导航',
    route_optimization: '航线规划',
    crew_training: '船员培训'
  }
  return map[category] || category
}

const getDifficultyText = (difficulty) => {
  const map = { low: '低', medium: '中', high: '高' }
  return map[difficulty] || difficulty
}

const calculateDuration = (start, end) => {
  const diff = new Date(end) - new Date(start)
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(hours / 24)
  const remainingHours = hours % 24
  return `${days}天 ${remainingHours}小时`
}

onMounted(() => {
  voyageStore.fetchVoyages()
  loadRanking()
})
</script>

<style scoped>
.diagnosis-page {
  min-height: 100%;
}

.ranking-card,
.statistics-card,
.detail-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  justify-content: space-between;
}

.card-header > div {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ranking-stats {
  margin-bottom: 12px;
}

.statistics-content {
  padding: 0;
}

.total-saving {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #f0f9eb;
  border-radius: 8px;
}

.saving-value {
  font-size: 24px;
  font-weight: bold;
  color: #67c23a;
}

.saving-label {
  font-size: 12px;
  color: #67c23a;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.voyage-title {
  font-size: 16px;
  font-weight: 600;
}

.score-gauge {
  display: flex;
  align-items: center;
  justify-content: center;
}

.saving-text {
  color: #67c23a;
  font-weight: 600;
}

.optimization-header {
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
}

.optimization-stat {
  text-align: center;
}

.stat-label {
  font-size: 12px;
  opacity: 0.9;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
}

.stat-value.baseline { color: #ffd700; }
.stat-value.target { color: #00ff88; }
.stat-value.improvement { color: #00ff88; }
.stat-value.payback { color: #87ceeb; font-size: 18px; }

.optimization-arrow {
  display: flex;
  align-items: center;
}

.score-excellent { color: #67c23a; font-weight: bold; }
.score-good { color: #409eff; font-weight: bold; }
.score-fair { color: #e6a23c; font-weight: bold; }
.score-poor { color: #f56c6c; font-weight: bold; }
</style>
