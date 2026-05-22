/**
 * 备份相关API
 */

import apiClient from './client.js'

/**
 * 创建系统备份
 * @param {Object} options - 备份选项
 * @param {boolean} options.include_database - 是否包含数据库
 * @param {boolean} options.include_images - 是否包含图片文件
 * @returns {Promise} 备份结果
 */
export const createBackup = async (options = { include_database: true, include_images: true }) => {
  const response = await apiClient.post('/api/v1/backup/create', options)
  return response.data
}

/**
 * 获取备份列表
 * @returns {Promise} 备份文件列表
 */
export const getBackupList = async () => {
  const response = await apiClient.get('/api/v1/backup/list')
  return response.data
}

/**
 * 下载备份文件
 * @param {string} filename - 备份文件名
 * @returns {Promise} 文件下载
 */
export const downloadBackup = async (filename) => {
  const response = await apiClient.get(`/api/v1/backup/download/${filename}`, {
    responseType: 'blob'
  })

  // 创建下载链接
  const blob = new Blob([response.data])
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  window.URL.revokeObjectURL(url)
  document.body.removeChild(a)
}

/**
 * 恢复系统备份
 * @param {File} backupFile - 备份文件
 * @param {Object} options - 恢复选项
 * @param {boolean} options.restore_database - 是否恢复数据库
 * @param {boolean} options.restore_images - 是否恢复图片文件
 * @returns {Promise} 恢复结果
 */
export const restoreBackup = async (backupFile, options = { restore_database: true, restore_images: true }) => {
  const formData = new FormData()
  formData.append('backup_file', backupFile)
  formData.append('restore_database', options.restore_database)
  formData.append('restore_images', options.restore_images)

  const response = await apiClient.post('/api/v1/backup/restore', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })

  return response.data
}

/**
 * 删除备份文件
 * @param {string} filename - 备份文件名
 * @returns {Promise} 删除结果
 */
export const deleteBackup = async (filename) => {
  const response = await apiClient.delete(`/api/v1/backup/delete/${filename}`)
  return response.data
}

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @returns {string} 格式化后的大小
 */
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 格式化日期时间
 * @param {string} dateString - ISO日期字符串
 * @returns {string} 格式化后的日期时间
 */
export const formatDateTime = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}
