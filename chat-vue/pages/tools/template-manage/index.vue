<template>
  <app-layout title="模板管理">
    <view class="template-manage-container">
      <!-- 搜索和筛选区域 -->
      <view class="filter-section">
        <view class="search-box">
          <input 
            class="search-input" 
            type="text" 
            v-model="searchKeyword" 
            placeholder="搜索模板名称"
            @confirm="handleSearch"
          />
          <view class="search-btn" @tap="handleSearch">
            <text class="icon">搜索</text>
          </view>
        </view>
        
        <!-- 标签筛选 -->
        <scroll-view class="tag-filter" scroll-x>
          <view 
            class="tag-item" 
            :class="{ active: selectedTag === '' }"
            @tap="selectTag('')"
          >
            全部
          </view>
          <view 
            v-for="tag in tagOptions" 
            :key="tag"
            class="tag-item" 
            :class="{ active: selectedTag === tag }"
            @tap="selectTag(tag)"
          >
            {{ tag }}
          </view>
        </scroll-view>
      </view>
      
      <!-- 模板列表 -->
      <scroll-view class="template-list" scroll-y @scrolltolower="loadMore">
        <view v-if="templates.length === 0 && !loading" class="empty-state">
          <text class="empty-icon">[文档]</text>
          <text class="empty-text">暂无模板</text>
          <text class="empty-subtext">点击右上角上传模板</text>
        </view>
        
        <view v-else class="template-grid">
          <view 
            v-for="template in templates" 
            :key="template.id"
            class="template-card"
          >
            <view class="template-header">
              <view class="file-icon" :class="template.file_type">
                <text v-if="template.file_type === 'word'">W</text>
                <text v-else-if="template.file_type === 'pdf'">P</text>
                <text v-else>文</text>
              </view>
              <view class="template-info">
                <text class="template-name">{{ template.name }}</text>
                <text class="template-meta">{{ formatFileSize(template.file_size) }} · {{ formatDate(template.created_at) }}</text>
              </view>
            </view>
            
            <view class="template-tags">
              <text v-for="(tag, index) in parseTags(template.tags)" :key="index" class="tag">{{ tag }}</text>
            </view>
            
            <view class="template-actions">
              <view class="action-btn use" @tap="useTemplate(template)">
                <text>使用</text>
              </view>
              <view class="action-btn delete" @tap="deleteTemplate(template)">
                <text>删除</text>
              </view>
            </view>
          </view>
        </view>
        
        <!-- 加载更多 -->
        <view v-if="loading" class="loading-more">
          <text>加载中...</text>
        </view>
      </scroll-view>
      
      <!-- 上传按钮 -->
      <view class="fab-btn" @tap="showUploadModal">
        <text class="fab-icon">+</text>
      </view>
      
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
              <view class="file-picker" @tap="chooseFile">
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
  </app-layout>
</template>

<script>
import AppLayout from '../../../components/layout/AppLayout.vue';
import api from '../../../utils/api.js';

export default {
  components: {
    AppLayout
  },
  data() {
    return {
      templates: [],
      loading: false,
      searchKeyword: '',
      selectedTag: '',
      tagOptions: ['简历', '论文', '报告', '合同', '申请书', '信函', '其他'],
      selectedFile: null,
      uploadForm: {
        name: '',
        tags: []
      }
    };
  },
  computed: {
    canUpload() {
      return this.selectedFile && this.uploadForm.name.trim();
    }
  },
  onLoad() {
    this.loadTemplates();
  },
  onShow() {
    this.loadTemplates();
  },
  methods: {
    // 加载模板列表
    async loadTemplates() {
      if (this.loading) return;
      this.loading = true;
      
      try {
        const params = {};
        if (this.selectedTag) {
          params.tag = this.selectedTag;
        }
        if (this.searchKeyword) {
          params.search = this.searchKeyword;
        }
        
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
    
    // 搜索
    handleSearch() {
      this.loadTemplates();
    },
    
    // 选择标签
    selectTag(tag) {
      this.selectedTag = tag;
      this.loadTemplates();
    },
    
    // 解析标签
    parseTags(tagsStr) {
      if (!tagsStr) return [];
      return tagsStr.split(',').filter(t => t.trim());
    },
    
    // 格式化文件大小
    formatFileSize(size) {
      if (!size) return '0 B';
      const units = ['B', 'KB', 'MB', 'GB'];
      let index = 0;
      while (size >= 1024 && index < units.length - 1) {
        size /= 1024;
        index++;
      }
      return size.toFixed(2) + ' ' + units[index];
    },
    
    // 格式化日期
    formatDate(dateStr) {
      if (!dateStr) return '';
      const date = new Date(dateStr);
      return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
    },
    
    // 使用模板
    useTemplate(template) {
      uni.navigateTo({
        url: `/pages/tools/template-generate/index?templateId=${template.id}&templateName=${encodeURIComponent(template.name)}`
      });
    },
    
    // 删除模板
    deleteTemplate(template) {
      uni.showModal({
        title: '确认删除',
        content: `确定要删除模板"${template.name}"吗？`,
        confirmColor: '#ff4d4f',
        success: async (res) => {
          if (res.confirm) {
            try {
              const result = await api.delete(`/llm/templates/${template.id}`);
              if (result.code === 'SUCCESS') {
                uni.showToast({ title: '删除成功', icon: 'success' });
                this.loadTemplates();
              }
            } catch (e) {
              console.error('删除模板失败:', e);
            }
          }
        }
      });
    },
    
    // 显示上传弹窗
    showUploadModal() {
      this.selectedFile = null;
      this.uploadForm = { name: '', tags: [] };
      this.$refs.uploadPopup.open();
    },
    
    // 关闭上传弹窗
    closeUploadModal() {
      this.$refs.uploadPopup.close();
    },
    
    // 选择文件
    chooseFile() {
      uni.chooseFile({
        count: 1,
        type: 'all',
        extension: ['.doc', '.docx', '.pdf'],
        success: (res) => {
          const file = res.tempFiles[0];
          const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
          if (!['.doc', '.docx', '.pdf'].includes(ext)) {
            uni.showToast({ title: '仅支持Word和PDF文件', icon: 'none' });
            return;
          }
          this.selectedFile = file;
          // 自动填充名称
          if (!this.uploadForm.name) {
            this.uploadForm.name = file.name.substring(0, file.name.lastIndexOf('.'));
          }
        }
      });
    },
    
    // 切换标签
    toggleTag(tag) {
      const index = this.uploadForm.tags.indexOf(tag);
      if (index > -1) {
        this.uploadForm.tags.splice(index, 1);
      } else {
        this.uploadForm.tags.push(tag);
      }
    },
    
    // 上传模板
    async uploadTemplate() {
      if (!this.canUpload) return;
      
      uni.showLoading({ title: '上传中...' });
      
      try {
        const formData = {
          name: this.uploadForm.name,
          tags: this.uploadForm.tags.join(',')
        };
        
        const res = await api.upload('/llm/templates', this.selectedFile.path, formData);
        
        if (res.code === 'SUCCESS') {
          uni.showToast({ title: '上传成功', icon: 'success' });
          this.closeUploadModal();
          this.loadTemplates();
        } else {
          uni.showToast({ title: res.message || '上传失败', icon: 'none' });
        }
      } catch (e) {
        console.error('上传模板失败:', e);
        uni.showToast({ title: '上传失败', icon: 'none' });
      } finally {
        uni.hideLoading();
      }
    },
    
    // 加载更多
    loadMore() {
      // 如果需要分页，在这里实现
    }
  }
};
</script>

<style scoped>
.template-manage-container {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding: 20rpx;
  padding-bottom: 120rpx;
}

/* 筛选区域 */
.filter-section {
  background: #fff;
  border-radius: 16rpx;
  padding: 20rpx;
  margin-bottom: 20rpx;
}

.search-box {
  display: flex;
  align-items: center;
  background: #f5f7fa;
  border-radius: 12rpx;
  padding: 16rpx 20rpx;
  margin-bottom: 20rpx;
}

.search-input {
  flex: 1;
  font-size: 28rpx;
  color: #333;
}

.search-btn {
  padding: 0 10rpx;
}

.search-btn .icon {
  font-size: 32rpx;
}

.tag-filter {
  white-space: nowrap;
}

.tag-item {
  display: inline-block;
  padding: 12rpx 24rpx;
  margin-right: 16rpx;
  background: #f5f7fa;
  border-radius: 8rpx;
  font-size: 26rpx;
  color: #666;
  transition: all 0.3s;
}

.tag-item.active {
  background: #007bff;
  color: #fff;
}

/* 模板列表 */
.template-list {
  height: calc(100vh - 280rpx);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100rpx 40rpx;
}

.empty-icon {
  font-size: 120rpx;
  margin-bottom: 20rpx;
}

.empty-text {
  font-size: 32rpx;
  color: #333;
  margin-bottom: 10rpx;
}

.empty-subtext {
  font-size: 26rpx;
  color: #999;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(1, 1fr);
  gap: 20rpx;
}

@media screen and (min-width: 768px) {
  .template-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.template-card {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.08);
}

.template-header {
  display: flex;
  align-items: flex-start;
  gap: 20rpx;
  margin-bottom: 16rpx;
}

.file-icon {
  font-size: 60rpx;
  width: 80rpx;
  height: 80rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12rpx;
  flex-shrink: 0;
}

.template-info {
  flex: 1;
  min-width: 0;
}

.template-name {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
  display: block;
  margin-bottom: 8rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.template-meta {
  font-size: 24rpx;
  color: #999;
}

.template-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-bottom: 20rpx;
}

.template-tags .tag {
  padding: 6rpx 16rpx;
  background: #e6f7ff;
  color: #007bff;
  font-size: 22rpx;
  border-radius: 6rpx;
}

.template-actions {
  display: flex;
  gap: 16rpx;
}

.action-btn {
  flex: 1;
  padding: 16rpx 0;
  border-radius: 8rpx;
  text-align: center;
  font-size: 26rpx;
}

.action-btn.use {
  background: #007bff;
  color: #fff;
}

.action-btn.delete {
  background: #fff;
  color: #ff4d4f;
  border: 2rpx solid #ff4d4f;
}

/* 悬浮按钮 */
.fab-btn {
  position: fixed;
  right: 40rpx;
  bottom: 140rpx;
  width: 100rpx;
  height: 100rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(102, 126, 234, 0.4);
  z-index: 100;
}

.fab-icon {
  font-size: 48rpx;
  color: #fff;
  font-weight: 300;
}

/* 上传弹窗 */
.upload-modal {
  background: #fff;
  border-radius: 20rpx;
  width: 640rpx;
  max-width: 90vw;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30rpx;
  border-bottom: 2rpx solid #f0f0f0;
}

.modal-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}

.modal-close {
  font-size: 40rpx;
  color: #999;
  padding: 0 10rpx;
}

.modal-body {
  padding: 30rpx;
}

.form-item {
  margin-bottom: 30rpx;
}

.form-label {
  display: block;
  font-size: 28rpx;
  color: #333;
  margin-bottom: 16rpx;
  font-weight: 500;
}

.file-picker {
  padding: 40rpx;
  border: 2rpx dashed #d9d9d9;
  border-radius: 12rpx;
  text-align: center;
}

.file-placeholder {
  font-size: 28rpx;
  color: #999;
}

.file-name {
  font-size: 28rpx;
  color: #007bff;
}

.form-input {
  width: 100%;
  padding: 20rpx;
  border: 2rpx solid #e8e8e8;
  border-radius: 12rpx;
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
  border-radius: 8rpx;
  font-size: 26rpx;
  color: #666;
  transition: all 0.3s;
}

.tag-option.selected {
  background: #007bff;
  color: #fff;
}

.modal-footer {
  display: flex;
  padding: 20rpx 30rpx 30rpx;
  gap: 20rpx;
}

.btn {
  flex: 1;
  padding: 24rpx 0;
  border-radius: 12rpx;
  text-align: center;
  font-size: 30rpx;
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
  background: #d9d9d9;
  color: #999;
}

.loading-more {
  text-align: center;
  padding: 30rpx;
  color: #999;
  font-size: 26rpx;
}
</style>
