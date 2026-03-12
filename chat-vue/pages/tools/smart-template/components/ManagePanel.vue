<template>
  <view class="manage-panel">
    <!-- 搜索和筛选 -->
    <view class="filter-bar">
      <view class="search-box">
        <text class="search-icon">🔍</text>
        <input 
          class="search-input" 
          type="text" 
          v-model="searchKeyword" 
          placeholder="搜索模板..."
          @confirm="loadTemplates"
        />
      </view>
    </view>
    
    <!-- 标签筛选 -->
    <scroll-view scroll-x class="tag-filter">
      <view class="tag-list">
        <view 
          class="filter-tag"
          :class="{ active: !selectedTag }"
          @tap="filterByTag(null)"
        >全部</view>
        <view 
          v-for="tag in tagOptions" 
          :key="tag"
          class="filter-tag"
          :class="{ active: selectedTag === tag }"
          @tap="filterByTag(tag)"
        >{{ tag }}</view>
      </view>
    </scroll-view>
    
    <!-- 模板列表 -->
    <view class="template-list">
      <view v-if="loading" class="loading">
        <text>加载中...</text>
      </view>
      
      <view v-else-if="templates.length === 0" class="empty">
        <text class="empty-icon">📁</text>
        <text class="empty-text">暂无模板</text>
        <text class="empty-hint">点击下方按钮上传模板</text>
      </view>
      
      <view v-else>
        <view 
          v-for="template in templates" 
          :key="template.id"
          class="template-item"
        >
          <view class="template-icon">
            {{ template.file_type === 'word' ? '📄' : '📕' }}
          </view>
          <view class="template-info">
            <text class="template-name">{{ template.name }}</text>
            <view class="template-meta">
              <text class="template-tags" v-if="template.tags">{{ template.tags }}</text>
              <text class="template-size">{{ formatSize(template.file_size) }}</text>
            </view>
          </view>
          <view class="template-actions">
            <text class="action-btn delete" @tap.stop="confirmDelete(template)">删除</text>
          </view>
        </view>
      </view>
    </view>
    
    <!-- 上传按钮 -->
    <view class="fab-btn" @tap="showUploadModal">
      <text class="fab-icon">+</text>
    </view>
    
    <!-- 隐藏的文件input，放在弹窗外面避免事件被阻止 -->
    <input 
      type="file" 
      ref="fileInput"
      class="global-file-input"
      accept=".doc,.docx,.pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/pdf"
      @change="onFileSelected"
    />
    
    <!-- 上传弹窗 -->
    <uni-popup ref="uploadPopup" type="center">
      <view class="upload-modal">
        <view class="modal-header">
          <text class="modal-title">上传模板</text>
          <text class="modal-close" @tap="closeUploadModal">×</text>
        </view>
        
        <view class="modal-body">
          <!-- 文件选择 -->
          <view class="form-item">
            <text class="form-label">选择文件</text>
            <view class="file-picker" @click="triggerFileInput">
              <text v-if="!selectedFile" class="file-placeholder">点击选择Word或PDF文件</text>
              <text v-else class="file-name">{{ selectedFile.name }}</text>
            </view>
          </view>
          
          <!-- 模板名称 -->
          <view class="form-item">
            <text class="form-label">模板名称</text>
            <input 
              class="form-input" 
              type="text" 
              v-model="uploadForm.name" 
              placeholder="输入模板名称"
            />
          </view>
          
          <!-- 标签选择 -->
          <view class="form-item">
            <text class="form-label">标签分类</text>
            <view class="tag-selector">
              <view 
                v-for="tag in tagOptions" 
                :key="tag"
                class="tag-option"
                :class="{ selected: uploadForm.tags.includes(tag) }"
                @tap="toggleTag(tag)"
              >
                {{ tag }}
              </view>
            </view>
          </view>
        </view>
        
        <view class="modal-footer">
          <view class="btn cancel" @tap="closeUploadModal">取消</view>
          <view class="btn confirm" :class="{ disabled: !canUpload }" @tap="uploadTemplate">上传</view>
        </view>
      </view>
    </uni-popup>
  </view>
</template>

<script>
import api from '../../../../utils/api';

export default {
  name: 'TemplateManagePanel',
  data() {
    return {
      templates: [],
      loading: false,
      searchKeyword: '',
      selectedTag: null,
      tagOptions: ['简历', '论文', '报告', '合同', '申请书', '其他'],
      selectedFile: null,
      uploadForm: {
        name: '',
        tags: []
      },
      uploading: false
    };
  },
  computed: {
    canUpload() {
      return this.selectedFile && this.uploadForm.name.trim();
    }
  },
  mounted() {
    this.loadTemplates();
  },
  methods: {
    async loadTemplates() {
      this.loading = true;
      try {
        const params = {};
        if (this.selectedTag) params.tag = this.selectedTag;
        if (this.searchKeyword) params.search = this.searchKeyword;
        
        const res = await api.get('/llm/templates', params);
        if (res.code === 'SUCCESS') {
          this.templates = res.data || [];
        }
      } catch (e) {
        console.error('加载模板失败:', e);
      } finally {
        this.loading = false;
      }
    },
    
    refresh() {
      this.loadTemplates();
    },
    
    filterByTag(tag) {
      this.selectedTag = tag;
      this.loadTemplates();
    },
    
    formatSize(bytes) {
      if (!bytes) return '';
      if (bytes < 1024) return bytes + 'B';
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + 'KB';
      return (bytes / (1024 * 1024)).toFixed(1) + 'MB';
    },
    
    showUploadModal() {
      this.selectedFile = null;
      this.uploadForm = { name: '', tags: [] };
      this.$refs.uploadPopup.open();
    },
    
    closeUploadModal() {
      this.$refs.uploadPopup.close();
    },
    
    triggerFileInput() {
      // 动态创建input元素选择文件（最可靠的H5方法）
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = '.doc,.docx,.pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/pdf';
      
      input.onchange = (e) => {
        const files = e.target.files;
        if (!files || files.length === 0) return;
        
        const file = files[0];
        const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
        
        if (!['.doc', '.docx', '.pdf'].includes(ext)) {
          uni.showToast({ title: '仅支持Word和PDF文件', icon: 'none' });
          return;
        }
        
        this.selectedFile = {
          name: file.name,
          size: file.size,
          path: URL.createObjectURL(file),
          fileObj: file
        };
        
        if (!this.uploadForm.name) {
          this.uploadForm.name = file.name.substring(0, file.name.lastIndexOf('.'));
        }
      };
      
      input.click();
    },
    
    onFileSelected(e) {
      // 保留此方法以防ref方式工作
      const files = e.target.files;
      if (!files || files.length === 0) return;
      
      const file = files[0];
      const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
      
      if (!['.doc', '.docx', '.pdf'].includes(ext)) {
        uni.showToast({ title: '仅支持Word和PDF文件', icon: 'none' });
        e.target.value = '';
        return;
      }
      
      this.selectedFile = {
        name: file.name,
        size: file.size,
        path: URL.createObjectURL(file),
        fileObj: file
      };
      
      if (!this.uploadForm.name) {
        this.uploadForm.name = file.name.substring(0, file.name.lastIndexOf('.'));
      }
      
      e.target.value = '';
    },
    
    toggleTag(tag) {
      const index = this.uploadForm.tags.indexOf(tag);
      if (index > -1) {
        this.uploadForm.tags.splice(index, 1);
      } else {
        this.uploadForm.tags.push(tag);
      }
    },
    
    async uploadTemplate() {
      if (!this.canUpload || this.uploading) return;
      
      this.uploading = true;
      uni.showLoading({ title: '上传中...' });
      
      try {
        // 传递整个selectedFile对象，让platform-adapter正确识别fileObj属性
        const filePath = this.selectedFile;
        const formData = {
          name: this.uploadForm.name,
          tags: this.uploadForm.tags.join(',')
        };
        
        const res = await api.upload('/llm/templates', filePath, formData);
        
        uni.hideLoading();
        
        if (res.code === 'SUCCESS') {
          uni.showToast({ title: '上传成功', icon: 'success' });
          this.closeUploadModal();
          this.loadTemplates();
          this.$emit('templateUploaded');
        } else {
          uni.showToast({ title: res.message || '上传失败', icon: 'none' });
        }
      } catch (e) {
        uni.hideLoading();
        console.error('上传失败:', e);
        uni.showToast({ title: '上传失败', icon: 'none' });
      } finally {
        this.uploading = false;
      }
    },
    
    confirmDelete(template) {
      uni.showModal({
        title: '确认删除',
        content: `确定要删除模板"${template.name}"吗？`,
        success: (res) => {
          if (res.confirm) {
            this.deleteTemplate(template.id);
          }
        }
      });
    },
    
    async deleteTemplate(templateId) {
      uni.showLoading({ title: '删除中...' });
      
      try {
        const res = await api.delete(`/llm/templates/${templateId}`);
        
        uni.hideLoading();
        
        if (res.code === 'SUCCESS') {
          uni.showToast({ title: '删除成功', icon: 'success' });
          this.loadTemplates();
        } else {
          uni.showToast({ title: res.message || '删除失败', icon: 'none' });
        }
      } catch (e) {
        uni.hideLoading();
        console.error('删除失败:', e);
        uni.showToast({ title: '删除失败', icon: 'none' });
      }
    }
  }
};
</script>

<style scoped>
.manage-panel {
  min-height: 100%;
  padding-bottom: 150rpx;
}

/* 搜索和筛选 */
.filter-bar {
  padding: 20rpx;
  background: #fff;
}

.search-box {
  display: flex;
  align-items: center;
  background: #f5f7fa;
  border-radius: 40rpx;
  padding: 16rpx 24rpx;
}

.search-icon {
  margin-right: 16rpx;
  font-size: 28rpx;
}

.search-input {
  flex: 1;
  font-size: 28rpx;
}

/* 标签筛选 */
.tag-filter {
  white-space: nowrap;
  background: #fff;
  padding: 0 20rpx 20rpx;
}

.tag-list {
  display: inline-flex;
  gap: 16rpx;
}

.filter-tag {
  padding: 12rpx 24rpx;
  background: #f5f7fa;
  border-radius: 30rpx;
  font-size: 26rpx;
  color: #666;
  flex-shrink: 0;
}

.filter-tag.active {
  background: #007bff;
  color: #fff;
}

/* 模板列表 */
.template-list {
  padding: 20rpx;
}

.loading, .empty {
  padding: 100rpx 0;
  text-align: center;
}

.empty-icon {
  font-size: 80rpx;
  display: block;
  margin-bottom: 20rpx;
}

.empty-text {
  font-size: 32rpx;
  color: #333;
  display: block;
  margin-bottom: 10rpx;
}

.empty-hint {
  font-size: 26rpx;
  color: #999;
}

.template-item {
  display: flex;
  align-items: center;
  background: #fff;
  padding: 24rpx;
  border-radius: 16rpx;
  margin-bottom: 16rpx;
}

.template-icon {
  font-size: 48rpx;
  margin-right: 20rpx;
}

.template-info {
  flex: 1;
  overflow: hidden;
}

.template-name {
  font-size: 30rpx;
  font-weight: 500;
  color: #333;
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.template-meta {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-top: 8rpx;
}

.template-tags {
  font-size: 24rpx;
  color: #007bff;
  background: rgba(0, 123, 255, 0.1);
  padding: 4rpx 12rpx;
  border-radius: 20rpx;
}

.template-size {
  font-size: 24rpx;
  color: #999;
}

.template-actions {
  margin-left: 20rpx;
}

.action-btn {
  font-size: 26rpx;
  padding: 8rpx 20rpx;
  border-radius: 20rpx;
}

.action-btn.delete {
  color: #ff4d4f;
  background: rgba(255, 77, 79, 0.1);
}

/* 悬浮按钮 */
.fab-btn {
  position: fixed;
  right: 40rpx;
  bottom: calc(120rpx + env(safe-area-inset-bottom));
  width: 100rpx;
  height: 100rpx;
  background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(0, 123, 255, 0.4);
  z-index: 100;
}

.fab-icon {
  font-size: 48rpx;
  color: #fff;
}

/* 上传弹窗 */
.upload-modal {
  width: 90vw;
  max-width: 600px;
  background: #fff;
  border-radius: 20rpx;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30rpx;
  border-bottom: 1rpx solid #eee;
}

.modal-title {
  font-size: 34rpx;
  font-weight: 600;
  color: #333;
}

.modal-close {
  font-size: 48rpx;
  color: #999;
  line-height: 1;
}

.modal-body {
  padding: 30rpx;
}

.form-item {
  margin-bottom: 30rpx;
  position: relative;
}

.form-label {
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
  display: block;
  margin-bottom: 16rpx;
}

.file-picker {
  background: #f5f7fa;
  border-radius: 12rpx;
  padding: 24rpx;
  text-align: center;
  border: 2rpx dashed #ddd;
}

.file-placeholder {
  font-size: 28rpx;
  color: #999;
}

.file-name {
  font-size: 28rpx;
  color: #007bff;
}

/* 全局文件input隐藏 */
.global-file-input {
  position: fixed;
  top: -9999px;
  left: -9999px;
  opacity: 0;
  pointer-events: none;
}

.form-input {
  width: 100%;
  height: 80rpx;
  background: #f5f7fa;
  border-radius: 12rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
  box-sizing: border-box;
}

.tag-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.tag-option {
  padding: 12rpx 24rpx;
  background: #f5f7fa;
  border-radius: 30rpx;
  font-size: 26rpx;
  color: #666;
  border: 2rpx solid transparent;
}

.tag-option.selected {
  background: #e6f2ff;
  color: #007bff;
  border-color: #007bff;
}

.modal-footer {
  display: flex;
  padding: 20rpx 30rpx 30rpx;
  gap: 20rpx;
}

.btn {
  flex: 1;
  height: 80rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12rpx;
  font-size: 28rpx;
  font-weight: 500;
}

.btn.cancel {
  background: #f5f7fa;
  color: #666;
}

.btn.confirm {
  background: #007bff;
  color: #fff;
}

.btn.confirm.disabled {
  background: #ccc;
}
</style>
