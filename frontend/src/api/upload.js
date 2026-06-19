import api from './index'

export const uploadChunk = (formData, config = {}) => {
  return api.post('/upload/chunk', formData, {
    ...config,
    headers: {
      'Content-Type': 'multipart/form-data',
      ...config.headers
    }
  })
}

export const completeUpload = (formData) => {
  return api.post('/upload/complete', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export const getUploadProgress = (fileId) => {
  return api.get(`/upload/progress/${fileId}`)
}

export const directUpload = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/upload/direct', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export const getUploadedFiles = () => {
  return api.get('/upload/files')
}
