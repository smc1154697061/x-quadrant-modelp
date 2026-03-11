<template>
  <view class="file-preview-container">
    <!-- 加载中 -->
    <view v-if="loading" class="preview-loading">
      <view class="loading-spinner"></view>
      <text class="loading-text">正在加载文档...</text>
    </view>
    
    <!-- 错误状态 -->
    <view v-else-if="error" class="preview-error">
      <text class="error-icon">⚠️</text>
      <text class="error-text">文件加载失败</text>
      <button class="action-btn primary" @tap="downloadFile">下载文件</button>
    </view>
    
    <!-- 图片预览 -->
    <image 
      v-else-if="isImage" 
      class="preview-image" 
      :src="fileUrl" 
      mode="aspectFit"
      @load="onImageLoad"
      @error="onError"
    />
    
    <!-- PDF预览 -->
    <view v-else-if="isPdf" class="pdf-preview">
      <!-- #ifdef H5 -->
      <iframe class="preview-iframe" :src="fileUrl"></iframe>
      <!-- #endif -->
      <!-- #ifndef H5 -->
      <view class="file-fallback">
        <text class="fallback-icon">📄</text>
        <text class="fallback-filename">{{ fileName }}</text>
        <text class="fallback-desc">PDF文件</text>
        <view class="fallback-actions">
          <button class="action-btn primary" @tap="downloadFile">下载文件</button>
          <button class="action-btn" @tap="openDocument">打开文件</button>
        </view>
      </view>
      <!-- #endif -->
    </view>
    
    <view v-else-if="isOffice" class="file-fallback">
      <text class="fallback-icon">📄</text>
      <text class="fallback-filename">{{ fileName }}</text>
      <text class="fallback-desc">{{ officeTypeText }}文件</text>
      <text class="fallback-tip">暂不支持在线预览，请下载后打开</text>
      <view class="fallback-actions">
        <button class="action-btn primary" @tap="downloadFile">下载文件</button>
        <!-- #ifndef H5 -->
        <button class="action-btn" @tap="openDocument">打开文件</button>
        <!-- #endif -->
      </view>
    </view>
    
    <!-- 文本文件预览 -->
    <scroll-view v-else-if="isText" class="preview-text" scroll-y>
      <text class="text-content">{{ textContent || '加载中...' }}</text>
    </scroll-view>
    
    <!-- 不支持的格式 -->
    <view v-else class="file-fallback">
      <text class="fallback-icon">📄</text>
      <text class="fallback-filename">{{ fileName }}</text>
      <text class="fallback-desc">不支持预览此文件格式</text>
      <view class="fallback-actions">
        <button class="action-btn primary" @tap="downloadFile">下载文件</button>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  name: 'FilePreview',
  props: {
    // 文件URL
    fileUrl: {
      type: String,
      required: true
    },
    // 文件名
    fileName: {
      type: String,
      default: ''
    },
    // 文件扩展名（可选，不传则从fileName或URL提取）
    fileExt: {
      type: String,
      default: ''
    }
  },
  data() {
    return {
      loading: false,
      error: false,
      textContent: ''
    }
  },
  computed: {
    // 获取文件扩展名
    ext() {
      if (this.fileExt) return this.fileExt.toLowerCase()
      if (this.fileName) {
        const parts = this.fileName.split('.')
        return parts.length > 1 ? parts.pop().toLowerCase() : ''
      }
      // 从URL提取
      try {
        const pathname = new URL(this.fileUrl).pathname
        const parts = pathname.split('.')
        return parts.length > 1 ? parts.pop().toLowerCase() : ''
      } catch (e) {
        return ''
      }
    },
    
    isImage() {
      return ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'].includes(this.ext)
    },
    
    isPdf() {
      return this.ext === 'pdf'
    },
    
    // 是否是 Office 文件（含 doc/docx/xls/xlsx/ppt/pptx）
    isOffice() {
      return ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'].includes(this.ext)
    },
    
    // 是否是 Word 文件（doc + docx，用于展示文案）
    isWord() {
      return ['doc', 'docx'].includes(this.ext)
    },
    
    isExcel() {
      return ['xls', 'xlsx'].includes(this.ext)
    },
    
    isPpt() {
      return ['ppt', 'pptx'].includes(this.ext)
    },
    
    isText() {
      return ['txt', 'md', 'markdown', 'log', 'csv', 'json', 'xml', 'html', 'css', 'js'].includes(this.ext)
    },
    
    officeTypeText() {
      if (this.isWord) return 'Word'
      if (this.isExcel) return 'Excel'
      if (this.isPpt) return 'PPT'
      return 'Office'
    },
    
  },
  watch: {
    fileUrl: {
      immediate: true,
      handler(newUrl) {
        if (newUrl) {
          this.error = false
          this.textContent = ''
          
          // 只有纯文本才用 loading，其它类型不再“转圈圈”
          if (this.isText) {
            this.loading = true
            this.loadTextContent()
          } else {
            this.loading = false
          }
        }
      }
    }
  },
  methods: {
    // 加载文本内容
    async loadTextContent() {
      try {
        // #ifdef H5
        const response = await fetch(this.fileUrl)
        this.textContent = await response.text()
        this.loading = false
        this.error = false
        // #endif
        
        // #ifndef H5
        uni.request({
          url: this.fileUrl,
          success: (res) => {
            this.textContent = typeof res.data === 'string' ? res.data : JSON.stringify(res.data, null, 2)
            this.loading = false
            this.error = false
          },
          fail: () => {
            this.textContent = '无法加载文件内容'
            this.loading = false
            this.error = true
          }
        })
        // #endif
      } catch (e) {
        console.error('加载文本失败:', e)
        this.textContent = '无法加载文件内容'
        this.loading = false
        this.error = true
      }
    },
    
    onImageLoad() {
      this.loading = false
      this.error = false
      this.$emit('rendered')
    },
    
    onError(e) {
      console.error('文件加载失败:', e)
      this.loading = false
      this.error = true
      this.$emit('error', e)
    },
    
    // 下载文件
    downloadFile() {
      // #ifdef H5
      const a = document.createElement('a')
      a.href = this.fileUrl
      a.download = this.fileName || 'download'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      // #endif
      
      // #ifndef H5
      uni.downloadFile({
        url: this.fileUrl,
        success: (res) => {
          uni.saveFile({
            tempFilePath: res.tempFilePath,
            success: () => {
              uni.showToast({ title: '文件已保存', icon: 'success' })
            }
          })
        },
        fail: () => {
          uni.showToast({ title: '下载失败', icon: 'none' })
        }
      })
      // #endif
      
      this.$emit('download')
    },
    
    // 在浏览器中打开（仅H5）
    openInBrowser() {
      // #ifdef H5
      window.open(this.fileUrl, '_blank')
      // #endif
    },
    
    // 使用本地应用打开文件（小程序/APP）
    openDocument() {
      // #ifndef H5
      uni.showLoading({ title: '下载中...' })
      uni.downloadFile({
        url: this.fileUrl,
        success: (res) => {
          uni.hideLoading()
          if (res.statusCode === 200) {
            uni.openDocument({
              filePath: res.tempFilePath,
              showMenu: true,
              success: () => {
                console.log('打开文档成功')
              },
              fail: (err) => {
                console.error('打开文档失败:', err)
                uni.showToast({ title: '无法打开文件', icon: 'none' })
              }
            })
          }
        },
        fail: () => {
          uni.hideLoading()
          uni.showToast({ title: '下载失败', icon: 'none' })
        }
      })
      // #endif
    }
  }
}
</script>

<style scoped>
.file-preview-container {
  width: 100%;
  height: 100%;
  min-height: 400px;
  display: flex;
  flex-direction: column;
  background: #fff;
  position: relative;
}

/* 加载状态 */
.preview-loading {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: rgba(255, 255, 255, 0.9);
  z-index: 10;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #007AFF;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  font-size: 14px;
  color: #666;
}

/* 图片预览 */
.preview-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

/* iframe预览 */
.preview-iframe {
  width: 100%;
  height: 100%;
  border: none;
  flex: 1;
}

/* PDF预览 */
.pdf-preview {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 文件下载提示 */
.file-fallback {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 40px 20px;
  text-align: center;
}

.fallback-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.fallback-filename {
  font-size: 16px;
  font-weight: bold;
  color: #333;
  margin-bottom: 8px;
  word-break: break-all;
  max-width: 80%;
}

.fallback-desc {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.fallback-tip {
  font-size: 12px;
  color: #999;
  margin-bottom: 20px;
}

.fallback-actions {
  display: flex;
  flex-direction: column;       /* 按钮上下排列 */
  gap: 12px;
  flex-wrap: nowrap;
  justify-content: center;
  align-items: center;          /* 水平居中 */
  width: 100%;
}

/* 文本预览 */
.preview-text {
  width: 100%;
  height: 100%;
  padding: 16px;
  box-sizing: border-box;
  background: #fafafa;
}

.text-content {
  font-family: 'Courier New', Consolas, monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #333;
  white-space: pre-wrap;
  word-break: break-all;
}

/* 错误状态 */
.preview-error {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: #fff;
  gap: 12px;
}

.error-icon {
  font-size: 48px;
}

.error-text {
  font-size: 14px;
  color: #f56c6c;
}

/* 按钮样式 */
.action-btn {
  padding: 10px 24px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #fff;
  color: #606266;
  font-size: 14px;
  cursor: pointer;
  display: inline-flex;          /* 让按钮内容用flex布局 */
  align-items: center;           /* 垂直居中文字 */
  justify-content: center;       /* 水平居中文字 */
  line-height: 1;                /* 避免文字偏下 */
}

.action-btn.primary {
  background: #007AFF;
  border-color: #007AFF;
  color: #fff;
}

.action-btn:active {
  opacity: 0.8;
}
</style>

