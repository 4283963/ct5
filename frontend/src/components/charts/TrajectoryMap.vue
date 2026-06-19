<template>
  <div ref="chartRef" class="chart-container"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  trajectory: {
    type: Array,
    default: () => []
  },
  height: {
    type: String,
    default: '400px'
  }
})

const chartRef = ref(null)
let chartInstance = null

const chartOption = computed(() => {
  if (!props.trajectory || props.trajectory.length === 0) {
    return {
      title: {
        text: '航线轨迹图',
        left: 'center',
        textStyle: { fontSize: 16, fontWeight: 'normal' }
      },
      tooltip: { trigger: 'item' },
      grid: { left: '3%', right: '3%', bottom: '10%', top: '15%' },
      xAxis: {
        type: 'value',
        name: '经度',
        min: 100,
        max: 140,
        splitLine: { lineStyle: { color: '#f0f2f5' } }
      },
      yAxis: {
        type: 'value',
        name: '纬度',
        min: 0,
        max: 45,
        splitLine: { lineStyle: { color: '#f0f2f5' } }
      },
      series: []
    }
  }

  const coords = props.trajectory.map(p => [p.longitude, p.latitude])
  const speeds = props.trajectory.map(p => p.speed)
  const fuels = props.trajectory.map(p => p.fuel_consumption)

  const minLon = Math.min(...coords.map(c => c[0])) - 2
  const maxLon = Math.max(...coords.map(c => c[0])) + 2
  const minLat = Math.min(...coords.map(c => c[1])) - 2
  const maxLat = Math.max(...coords.map(c => c[1])) + 2

  return {
    title: {
      text: '航线轨迹图',
      left: 'center',
      textStyle: { fontSize: 16, fontWeight: 'normal' }
    },
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const idx = params.dataIndex
        if (idx !== undefined && props.trajectory[idx]) {
          const p = props.trajectory[idx]
          return `时间: ${p.timestamp}<br/>
                  经度: ${p.longitude.toFixed(4)}<br/>
                  纬度: ${p.latitude.toFixed(4)}<br/>
                  航速: ${p.speed.toFixed(2)} 节<br/>
                  油耗: ${p.fuel_consumption.toFixed(2)} 吨/时`
        }
        return ''
      }
    },
    visualMap: {
      show: true,
      min: Math.min(...speeds),
      max: Math.max(...speeds),
      left: 'left',
      top: 'center',
      calculable: true,
      inRange: {
        color: ['#67c23a', '#e6a23c', '#f56c6c']
      },
      text: ['高航速', '低航速'],
      textStyle: {
        color: '#333'
      }
    },
    grid: {
      left: '10%',
      right: '5%',
      bottom: '10%',
      top: '15%'
    },
    xAxis: {
      type: 'value',
      name: '经度',
      min: minLon,
      max: maxLon,
      splitLine: { lineStyle: { color: '#f0f2f5' } }
    },
    yAxis: {
      type: 'value',
      name: '纬度',
      min: minLat,
      max: maxLat,
      splitLine: { lineStyle: { color: '#f0f2f5' } }
    },
    series: [
      {
        name: '轨迹',
        type: 'line',
        data: coords,
        smooth: true,
        lineStyle: {
          width: 3,
          color: '#409eff'
        },
        symbol: 'none'
      },
      {
        name: '航点',
        type: 'scatter',
        data: coords.map((coord, i) => ({
          value: coord,
          symbolSize: Math.max(6, speeds[i] / 2)
        })),
        itemStyle: {
          color: (params) => {
            const val = params.value
            return params.data.color || '#409eff'
          }
        },
        encode: {
          tooltip: [0, 1]
        }
      }
    ]
  }
})

const initChart = () => {
  if (!chartRef.value) return

  if (chartInstance) {
    chartInstance.dispose()
  }

  chartInstance = echarts.init(chartRef.value)
  chartInstance.setOption(chartOption.value)
}

const resizeHandler = () => {
  chartInstance?.resize()
}

watch(() => props.trajectory, () => {
  if (chartInstance) {
    chartInstance.setOption(chartOption.value)
  }
}, { deep: true })

onMounted(() => {
  initChart()
  window.addEventListener('resize', resizeHandler)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeHandler)
  chartInstance?.dispose()
})
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: v-bind(height);
}
</style>
