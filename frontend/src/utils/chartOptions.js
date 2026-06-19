export const createLineChartOption = (title, xData, seriesData, colors = null) => {
  const series = seriesData.map((item, index) => ({
    name: item.name,
    type: 'line',
    smooth: true,
    symbol: 'circle',
    symbolSize: 6,
    data: item.data,
    yAxisIndex: item.yAxisIndex || 0,
    lineStyle: {
      width: 2,
      color: colors ? colors[index] : undefined
    },
    itemStyle: {
      color: colors ? colors[index] : undefined
    }
  }))

  const hasDualAxis = seriesData.some(item => item.yAxisIndex === 1)

  const option = {
    title: {
      text: title,
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e4e7ed',
      borderWidth: 1,
      textStyle: {
        color: '#303133'
      }
    },
    legend: {
      data: seriesData.map(item => item.name),
      bottom: 0,
      textStyle: {
        fontSize: 12
      }
    },
    grid: {
      left: '3%',
      right: hasDualAxis ? '10%' : '3%',
      bottom: '15%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: xData,
      axisLabel: {
        rotate: 30,
        fontSize: 10,
        interval: Math.floor(xData.length / 8)
      },
      axisLine: {
        lineStyle: {
          color: '#dcdfe6'
        }
      }
    },
    yAxis: hasDualAxis ? [
      {
        type: 'value',
        name: seriesData[0]?.unit || '',
        axisLine: {
          lineStyle: {
            color: colors ? colors[0] : undefined
          }
        },
        splitLine: {
          lineStyle: {
            color: '#f0f2f5'
          }
        }
      },
      {
        type: 'value',
        name: seriesData.find(s => s.yAxisIndex === 1)?.unit || '',
        axisLine: {
          lineStyle: {
            color: colors ? colors[1] : undefined
          }
        },
        splitLine: {
          show: false
        }
      }
    ] : {
      type: 'value',
      name: seriesData[0]?.unit || '',
      axisLine: {
        lineStyle: {
          color: '#dcdfe6'
        }
      },
      splitLine: {
        lineStyle: {
          color: '#f0f2f5'
        }
      }
    },
    series
  }

  return option
}

export const createBarChartOption = (title, categories, seriesData, colors = null) => {
  return {
    title: {
      text: title,
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: seriesData.map(item => item.name),
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: {
        rotate: 30,
        fontSize: 10
      }
    },
    yAxis: {
      type: 'value',
      splitLine: {
        lineStyle: {
          color: '#f0f2f5'
        }
      }
    },
    series: seriesData.map((item, index) => ({
      name: item.name,
      type: 'bar',
      data: item.data,
      itemStyle: {
        color: colors ? colors[index] : undefined,
        borderRadius: [4, 4, 0, 0]
      },
      barMaxWidth: 40
    }))
  }
}

export const createScatterChartOption = (title, xData, yData, xName, yName) => {
  const data = xData.map((x, i) => [x, yData[i]])

  return {
    title: {
      text: title,
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: (params) => `${xName}: ${params.data[0].toFixed(2)}<br/>${yName}: ${params.data[1].toFixed(2)}`
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: xName,
      splitLine: {
        lineStyle: {
          color: '#f0f2f5'
        }
      }
    },
    yAxis: {
      type: 'value',
      name: yName,
      splitLine: {
        lineStyle: {
          color: '#f0f2f5'
        }
      }
    },
    series: [
      {
        type: 'scatter',
        data: data,
        itemStyle: {
          color: 'rgba(64, 158, 255, 0.6)',
          borderColor: '#409eff',
          borderWidth: 1
        },
        symbolSize: 8
      }
    ]
  }
}

export const createGaugeChartOption = (title, value, max = 100) => {
  const getColor = (val) => {
    if (val >= 90) return '#67c23a'
    if (val >= 75) return '#e6a23c'
    if (val >= 60) return '#f56c6c'
    return '#f56c6c'
  }

  return {
    title: {
      text: title,
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 'normal'
      }
    },
    series: [
      {
        type: 'gauge',
        startAngle: 200,
        endAngle: -20,
        min: 0,
        max: max,
        radius: '85%',
        center: ['50%', '60%'],
        axisLine: {
          lineStyle: {
            width: 15,
            color: [
              [0.6, '#f56c6c'],
              [0.75, '#e6a23c'],
              [0.9, '#409eff'],
              [1, '#67c23a']
            ]
          }
        },
        pointer: {
          itemStyle: {
            color: getColor(value)
          },
          width: 5,
          length: '65%'
        },
        axisTick: {
          distance: -15,
          splitNumber: 10,
          lineStyle: {
            color: '#fff',
            width: 1
          }
        },
        splitLine: {
          distance: -18,
          length: 10,
          lineStyle: {
            color: '#fff',
            width: 2
          }
        },
        axisLabel: {
          color: '#999',
          distance: 25,
          fontSize: 10
        },
        detail: {
          valueAnimation: true,
          formatter: '{value}',
          color: getColor(value),
          fontSize: 24,
          fontWeight: 'bold',
          offsetCenter: [0, '0%']
        },
        data: [
          {
            value: value
          }
        ]
      }
    ]
  }
}

export const createPieChartOption = (title, data) => {
  return {
    title: {
      text: title,
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'middle'
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['60%', '55%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: data
      }
    ]
  }
}

export const createRadarChartOption = (title, indicators, data) => {
  return {
    title: {
      text: title,
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'normal'
      }
    },
    tooltip: {},
    legend: {
      data: data.map(d => d.name),
      bottom: 0
    },
    radar: {
      indicator: indicators,
      radius: '65%',
      center: ['50%', '55%'],
      splitNumber: 5,
      axisName: {
        color: '#303133',
        fontSize: 11
      },
      splitArea: {
        areaStyle: {
          color: ['#f8f9fa', '#fff']
        }
      }
    },
    series: [
      {
        type: 'radar',
        data: data
      }
    ]
  }
}
