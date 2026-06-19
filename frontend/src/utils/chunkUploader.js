import SparkMD5 from 'spark-md5'
import { uploadChunk, completeUpload } from '@/api/upload'

const CHUNK_SIZE = 5 * 1024 * 1024

export class ChunkUploader {
  constructor(file, options = {}) {
    this.file = file
    this.chunkSize = options.chunkSize || CHUNK_SIZE
    this.onProgress = options.onProgress || (() => {})
    this.onStatusChange = options.onStatusChange || (() => {})
    this.fileId = null
    this.totalChunks = 0
    this.uploadedChunks = 0
    this.isCancelled = false
  }

  async generateFileId() {
    return new Promise((resolve, reject) => {
      const blobSlice = File.prototype.slice || File.prototype.mozSlice || File.prototype.webkitSlice
      const chunks = Math.ceil(this.file.size / this.chunkSize)
      let currentChunk = 0
      const spark = new SparkMD5.ArrayBuffer()
      const fileReader = new FileReader()

      fileReader.onload = (e) => {
        spark.append(e.target.result)
        currentChunk++

        if (currentChunk < chunks) {
          loadNext()
        } else {
          const hash = spark.end()
          resolve(`${hash}_${Date.now()}`)
        }
      }

      fileReader.onerror = () => {
        reject(new Error('Failed to read file for MD5 calculation'))
      }

      const loadNext = () => {
        const start = currentChunk * this.chunkSize
        const end = Math.min(start + this.chunkSize, this.file.size)
        fileReader.readAsArrayBuffer(blobSlice.call(this.file, start, end))
      }

      loadNext()
    })
  }

  async upload() {
    this.isCancelled = false
    this.onStatusChange('preparing')

    try {
      this.fileId = await this.generateFileId()
      this.totalChunks = Math.ceil(this.file.size / this.chunkSize)
      this.uploadedChunks = 0

      this.onStatusChange('uploading')

      const uploadPromises = []
      const concurrency = 3

      for (let i = 0; i < this.totalChunks; i += concurrency) {
        if (this.isCancelled) break

        const batch = []
        for (let j = 0; j < concurrency && i + j < this.totalChunks; j++) {
          batch.push(this.uploadSingleChunk(i + j))
        }

        await Promise.all(batch)
      }

      if (this.isCancelled) {
        this.onStatusChange('cancelled')
        return null
      }

      this.onStatusChange('merging')

      const result = await completeUpload({
        file_id: this.fileId,
        filename: this.file.name,
        total_chunks: this.totalChunks
      })

      this.onStatusChange('completed')
      return result
    } catch (error) {
      this.onStatusChange('error')
      throw error
    }
  }

  async uploadSingleChunk(chunkIndex) {
    if (this.isCancelled) return

    const start = chunkIndex * this.chunkSize
    const end = Math.min(start + this.chunkSize, this.file.size)
    const chunk = this.file.slice(start, end)

    const formData = new FormData()
    formData.append('file_id', this.fileId)
    formData.append('chunk_index', chunkIndex)
    formData.append('total_chunks', this.totalChunks)
    formData.append('filename', this.file.name)
    formData.append('file', chunk, `${this.file.name}.part${chunkIndex}`)

    await uploadChunk(formData)

    this.uploadedChunks++
    const progress = (this.uploadedChunks / this.totalChunks) * 100
    this.onProgress(progress)
  }

  cancel() {
    this.isCancelled = true
    this.onStatusChange('cancelled')
  }
}

export const calculateChunks = (fileSize, chunkSize = CHUNK_SIZE) => {
  return Math.ceil(fileSize / chunkSize)
}

export const formatFileSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
}
