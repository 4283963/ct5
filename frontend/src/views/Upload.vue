<template>
  <div class="upload-page">
    <el-row :gutter="20">
      <el-col :span="14">
        <el-card class="upload-card">
          <template #header>
            <div class="card-header">
              <el-icon><Upload /></el-icon>
              <span>海量轨迹数据分片上传</span>
            </div>
          </template>

          <el-upload
            drag
            :auto-upload="false"
            :on-change="handleFileChange"
            :file-list="fileList"
            :limit="1"
            accept=".csv,.xlsx,.xls,.parquet"
          >
            <el-icon class="upload-icon"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 CSV、Excel、Parquet 格式，建议大文件使用分片上传
              </div>
            </template>
          </el-upload>

          <div v-if="selectedFile" class="file-info">
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="文件名">
                {{ selectedFile.name }}
              </el-descriptions-item>
              <el-descriptions-item label="文件大小">
                {{ formatFileSize(selectedFile.size) }}
              </el-descriptions-item>
              <el-descriptions-item label="分片大小">
                {{ formatFileSize(CHUNK_SIZE) }}
              </el-descriptions-item>
              <el-descriptions-item label="总分片数">
                {{ totalChunks }}
              </el-descriptions-item>
            </el-descriptions>
          </div>

          <div v-if="uploadStatus !== 'idle'" class="upload-progress">
            <el-progress
              :percentage="Math.round(uploadProgress)"
              :status="uploadStatus === 'error' ? 'exception' : uploadStatus === 'completed' ? 'success' : undefined"
            />
            <div class="status-text">
              <el-tag :type="statusTagType">{{ statusText }}</el-tag>
            </div>
          </div>

          <div class="upload-actions">
            <el-button
              type="primary"
              :disabled="!selectedFile || uploadStatus === 'uploading' || uploadStatus === 'merging'"
              @click="startUpload"
              :loading="uploadStatus === 'uploading'"
            >
              <el-icon><VideoPlay /></el-icon>
              开始上传
            </el-button>
            <el-button
              v-if="uploadStatus === 'uploading'"
              type="danger"
              @click="cancelUpload"
            >
              <el-icon><Close /></el-icon>
              取消上传
            </el-button>
            <el-button
              v-if="selectedFile && uploadStatus !== 'uploading'"
              @click="resetUpload"
            >
              <el-icon><Refresh /></el-icon>
              重新选择
            </el-button>
          </div>
        </el-card>

        <el-card class="format-card">
          <template #header>
            <div class="card-header">
              <el-icon><Document /></el-icon>
              <span>数据格式要求</span>
            </div>
          </template>
          <div class="format-info">
            <el-alert
              title="必填字段"
              type="info"
              :closable="false"
              style="margin-bottom: 12px"
            >
              <ul>
                <li>timestamp - 时间戳</li>
                <li>longitude - 经度 (-180 ~ 180)</li>
                <li>latitude - 纬度 (-90 ~ 90)</li>
                <li>speed - 航速 (节)</li>
                <li>fuel_consumption - 油耗 (吨/小时)</li>
                <li>wind_speed - 风速 (m/s)</li>
                <li>wind_direction - 风向 (0~360度)</li>
                <li>course - 航向 (0~360度)</li>
              </ul>
            </el-alert>
            <el-alert
              title="可选字段"
              type="success"
              :closable="false"
            >
              <ul>
                <li>vessel_name - 船名</li>
                <li>voyage_id - 航次ID</li>
                <li>departure_port - 出发港</li>
                <li>arrival_port - 到达港</li>
                <li>engine_power - 主机功率</li>
                <li>draft - 吃水深度</li>
              </ul>
            </el-alert>
          </div>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card class="history-card">
          <template #header>
            <div class="card-header">
              <el-icon><List /></el-icon>
              <span>上传历史</span>
              <el-button
                type="primary"
                link
                @click="refreshHistory"
                :loading="historyLoading"
              >
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </template>

          <el-table
            :data="uploadHistory"
            v-loading="historyLoading"
            stripe
            size="small"
            style="width: 100%"
          >
            <el-table-column prop="filename" label="文件名" show-overflow-tooltip />
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag size="small" :type="row.status === 'processed' ? 'success' : 'info'">
                  {{ row.status === 'processed' ? '已处理' : '处理中' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="航次数" width="70" align="center">
              <template #default="{ row }">
                {{ row.voyage_count }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button
                  type="primary"
                  link
                  size="small"
                  @click="viewVoyages(row)"
                >
                  查看
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card class="sample-card">
          <template #header>
            <div class="card-header">
              <el-icon><Download /></el-icon>
              <span>示例数据</span>
            </div>
          </template>
          <div class="sample-content">
            <p style="margin-bottom: 12px; color: #606266;">
              点击下方按钮下载示例数据文件，了解正确的数据格式：
            </p>
            <el-button type="primary" @click="generateSampleData">
              <el-icon><Download /></el-icon>
              生成示例数据 (CSV)
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ChunkUploader, calculateChunks, formatFileSize } from '@/utils/chunkUploader'
import { getUploadedFiles } from '@/api/upload'

const CHUNK_SIZE = 5 * 1024 * 1024

const fileList = ref([])
const selectedFile = ref(null)
const uploadProgress = ref(0)
const uploadStatus = ref('idle')
const uploader = ref(null)

const uploadHistory = ref([])
const historyLoading = ref(false)

const totalChunks = computed(() => {
  if (!selectedFile.value) return 0
  return calculateChunks(selectedFile.value.size, CHUNK_SIZE)
})

const statusText = computed(() => {
  const statusMap = {
    idle: '等待上传',
    preparing: '准备中...',
    uploading: '上传中...',
    merging: '合并分片...',
    completed: '上传完成',
    error: '上传失败',
    cancelled: '已取消'
  }
  return statusMap[uploadStatus.value] || '等待上传'
})

const statusTagType = computed(() => {
  const typeMap = {
    idle: 'info',
    preparing: 'warning',
    uploading: 'primary',
    merging: 'primary',
    completed: 'success',
    error: 'danger',
    cancelled: 'info'
  }
  return typeMap[uploadStatus.value] || 'info'
})

const handleFileChange = (file) => {
  selectedFile.value = file.raw
  uploadProgress.value = 0
  uploadStatus.value = 'idle'
}

const startUpload = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  try {
    uploader.value = new ChunkUploader(selectedFile.value, {
      chunkSize: CHUNK_SIZE,
      onProgress: (progress) => {
        uploadProgress.value = progress
      },
      onStatusChange: (status) => {
        uploadStatus.value = status
      }
    })

    const result = await uploader.value.upload()

    if (result) {
      ElMessage.success(
        `上传成功！共 ${result.total_records} 条记录，识别到 ${result.voyage_ids.length} 个航次`
      )
      refreshHistory()
    }
  } catch (error) {
    console.error('Upload failed:', error)
    ElMessage.error(`上传失败: ${error.message || '未知错误'}`)
  }
}

const cancelUpload = () => {
  if (uploader.value) {
    uploader.value.cancel()
    uploadStatus.value = 'cancelled'
    ElMessage.info('上传已取消')
  }
}

const resetUpload = () => {
  fileList.value = []
  selectedFile.value = null
  uploadProgress.value = 0
  uploadStatus.value = 'idle'
  uploader.value = null
}

const refreshHistory = async () => {
  historyLoading.value = true
  try {
    const files = await getUploadedFiles()
    uploadHistory.value = files
  } catch (error) {
    console.error('Failed to fetch history:', error)
  } finally {
    historyLoading.value = false
  }
}

const viewVoyages = (row) => {
  ElMessage.info(`查看文件 ${row.filename} 的航次数据`)
}

const generateSampleData = () => {
  const headers = [
    'timestamp', 'longitude', 'latitude', 'speed', 'fuel_consumption',
    'wind_speed', 'wind_direction', 'course', 'vessel_name', 'voyage_id',
    'departure_port', 'arrival_port'
  ]

  const startDate = new Date('2024-01-01')
  const rows = []

  for (let i = 0; i < 1000; i++) {
    const timestamp = new Date(startDate.getTime() + i * 10 * 60 * 1000)
    const longitude = 120 + Math.sin(i * 0.01) * 10
    const latitude = 30 + Math.cos(i * 0.01) * 5
    const speed = 14 + Math.random() * 4
    const fuel_consumption = 25 + (speed - 14) * 2 + Math.random() * 3
    const wind_speed = 5 + Math.random() * 15
    const wind_direction = Math.random() * 360
    const course = 90 + Math.sin(i * 0.005) * 20

    rows.push([
      timestamp.toISOString(),
      longitude.toFixed(6),
      latitude.toFixed(6),
      speed.toFixed(2),
      fuel_consumption.toFixed(2),
      wind_speed.toFixed(2),
      wind_direction.toFixed(2),
      course.toFixed(2),
      '远洋一号',
      'VOYAGE_SAMPLE_001',
      '上海',
      '新加坡'
    ])
  }

  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.join(','))
  ].join('\n')

  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'vessel_sample_data.csv'
  link.click()
  URL.revokeObjectURL(url)

  ElMessage.success('示例数据已生成并下载')
}

onMounted(() => {
  refreshHistory()
})
</script>

<style scoped>
.upload-page {
  min-height: 100%;
}

.upload-card,
.format-card,
.history-card,
.sample-card {
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

.upload-icon {
  font-size: 64px;
  color: #409eff;
  margin-bottom: 16px;
}

.file-info {
  margin-top: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.upload-progress {
  margin-top: 20px;
}

.status-text {
  margin-top: 12px;
  text-align: center;
}

.upload-actions {
  margin-top: 20px;
  display: flex;
  gap: 12px;
  justify-content: center;
}

.format-info ul {
  margin: 0;
  padding-left: 20px;
}

.format-info li {
  line-height: 1.8;
}

.sample-content {
  text-align: center;
  padding: 20px 0;
}
</style>
