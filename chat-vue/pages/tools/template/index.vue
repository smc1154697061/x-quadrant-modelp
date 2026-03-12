<template>
  <view class="template-page">
    <view class="custom-navbar">
      <view class="navbar-left" @tap="goBack">
        <text class="back-icon">‹</text>
      </view>
      <view class="navbar-title">
        <text>模板管理</text>
      </view>
      <view class="navbar-right">
        <button class="add-btn" @tap="showUploadModal">+</button>
      </view>
    </view>
    
    <scroll-view class="content-scroll" scroll-y>
      <view class="template-container">
        <view class="info-card">
          <text class="info-icon">📑</text>
          <text class="info-text">上传Word/PDF文档模板，用于智能文档生成</text>
        </view>
        
        <view class="filter-bar">
          <view class="search-box">
            <text class="search-icon">🔍</text>
            <input 
              v-model="searchKeyword" 
              class="search-input" 
              placeholder="搜索模板名称"
              @input="handleSearch"
            />
          </view>
          <view class="tag-filter">
            <view 
              v-for="tag in tags" 
              :key="tag"
              class="tag-chip"
              :class="{ active: selectedTag === tag }"
              @tap="selectTag(tag)"
            >
              <text>{{ tag }}</text>
            </view>
          </view>
        </view>
        
        <view class="template-grid" :class="{ 'template-grid-pc': isPc }">
          <view 
            v-for="template in filteredTemplates" 
            :key="template.id"
            class="template-card"
            @tap="viewTemplate(template)"
          >
            <view class="template-icon">{{ getTemplateIcon(template.type) }}</view>
            <view class="template-info">
              <text class="template-name">{{ template.name }}</text>
              <text class="template-tag">{{ template.tag }}</text>
              <text class="template-date">{{ formatDate(template.createdAt) }}</text>
            </view>
            <text class="delete-icon" @tap.stop="deleteTemplate(template)">×</text>
          </view>
        </view>
        
        <view v-if="filteredTemplates.length === 0" class="empty-state">
          <text class="empty-icon">📭</text>
          <text class="empty-text">暂无模板</text>
        </view>
      </view>
    </scroll-view>
    
    <view v-if="showUpload" class="popup-mask" @tap="closeUploadModal">
      <view class="popup-content" @tap.stop>
        <view class="popup-header">
          <text class="popup-title">上传模板</text>
          <text class="popup-close" @tap="closeUploadModal">×</text>
        </view>
        <scroll-view class="popup-form" scroll-y>
          <view class="form-group">
            <text class="form-label">模板名称</text>
            <input v-model="uploadForm.name" class="form-input" placeholder="请输入模板名称" />
          </view>
          
          <view class="form-group">
            <text class="form-label">选择分类</text>
            <picker mode="selector" :range="['简历', '论文', '报告', '合同', '其他']" @change="onTagChange">
              <view class="form-picker">
                <text>{{ uploadForm.tag || '请选择分类' }}</text>
                <text class="picker-arrow">›</text>
              </view>
            </picker>
          </view>
          
          <view class="form-group">
            <text class="form-label">上传文件</text>
            <view class="upload-zone" @tap="selectFile">
              <view v-if="!selectedFile" class="upload-empty">
                <text class="upload-icon">📁</text>
                <text class="upload-hint">点击选择文件</text>
                <text class="upload-support">支持Word、PDF格式</text>
              </view>
              <view v-else class="file-selected">
                <text class="file-icon">{{ getTemplateIcon(selectedFile.name) }}</text>
                <view class="file-detail">
                  <text class="file-name">{{ selectedFile.name }}</text>
                  <text class="file-size">{{ formatFileSize(selectedFile.size) }}</text>
                </view>
                <text class="remove-icon" @tap.stop="removeFile">×</text>
              </view>
            </view>
          </view>
        </scroll-view>
        <view class="popup-footer">
          <button class="popup-btn cancel" @tap="closeUploadModal">取消</button>
          <button class="popup-btn confirm" :class="{ disabled: !canUpload }" :disabled="!canUpload" @tap="uploadTemplate">
            <text v-if="uploading">上传中...</text>
            <text v-else>上传</text>
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { templateApi } from '../../../utils/api.js';

export default {
  data() {
    return {
      isPc: false,
      searchKeyword: '',
      selectedTag: '全部',
      tags: ['全部', '简历', '论文', '报告', '合同', '其他'],
      templates: [],
      showUpload: false,
      uploadForm: {
        name: '',
        tag: ''
      },
      selectedFile: null,
      uploading: false,
      mockTemplates: [
        {
          id: 1,
          name: '个人简历模板',
          tag: '简历',
          type: 'word',
          createdAt: '2026-03-01T10:00:00Z'
        },
        {
          id: 2,
          name: '技术报告模板',
          tag: '报告',
          type: 'pdf',
          createdAt: '2026-03-05T14:30:00Z'
        },
        {
          id: 3,
          name: '销售合同模板',
          tag: '合同',
          type: 'word',
          createdAt: '2026-03-10T09:15:00Z'
        }
      ]
    };
  },
  
  computed: {
    filteredTemplates() {
      let result = [...this.templates];
      
      if (this.selectedTag !== '全部') {
        result = result.filter(item => item.tag === this.selectedTag);
      }
      
      if (this.searchKeyword) {
        const keyword = this.searchKeyword.toLowerCase();
        result = result.filter(item => 
          item.name.toLowerCase().includes(keyword)
        );
      }
      
      return result;
    },
    
    canUpload() {
      return !this.uploading && this.uploadForm.name && this.uploadForm.tag && this.selectedFile;
    }
  },
  
  onLoad() {
    this.checkDeviceType();
    this.loadTemplates();
  },
  
  methods: {
    checkDeviceType() {
      uni.getSystemInfo({
        success: (res) => {
          this.isPc = res.windowWidth >= 768;
        }
      });
    },
    
    goBack() {
      uni.navigateBack();
    },
    
    handleSearch() {
    },
    
    selectTag(tag) {
      this.selectedTag = tag;
    },
    
    loadTemplates() {
      templateApi.getTemplates()
        .then(res => {
          if (res.code === 0 || res.code === '0000' || res.code === 'SUCCESS') {
            this.templates = res.data.map(item => ({
              id: item.id,
              name: item.name,
              tag: item.tag,
              type: item.file_type,
              createdAt: item.created_at
            }));
          } else {
            this.templates = [...this.mockTemplates];
          }
        })
        .catch(err => {
          console.error('加载模板失败:', err);
          this.templates = [...this.mockTemplates];
        });
    },
    
    showUploadModal() {
      this.showUpload = true;
      this.uploadForm = { name: '', tag: '' };
      this.selectedFile = null;
    },
    
    closeUploadModal() {
      this.showUpload = false;
    },
    
    onTagChange(e) {
      const tags = ['简历', '论文', '报告', '合同', '其他'];
      this.uploadForm.tag = tags[e.detail.value];
    },
    
    selectFile() {
      uni.chooseMessageFile({
        count: 1,
        type: 'file',
        extension: ['doc', 'docx', 'pdf'],
        success: (res) => {
          if (res.tempFiles && res.tempFiles.length > 0) {
            const file = res.tempFiles[0];
            this.selectedFile = {
              path: file.path,
              name: file.name,
              size: file.size
            };
          }
        },
        fail: (err) => {
          uni.chooseFile({
            count: 1,
            extension: ['.doc', '.docx', '.pdf'],
            success: (res) => {
              if (res.tempFilePaths && res.tempFilePaths.length > 0) {
                const path = res.tempFilePaths[0];
                const name = path.substring(path.lastIndexOf('/') + 1);
                this.selectedFile = {
                  path: path,
                  name: name,
                  size: 0
                };
              }
            },
            fail: (err2) => {
              if (!err2.errMsg?.includes('cancel')) {
                uni.showToast({
                  title: '选择文件失败',
                  icon: 'none'
                });
              }
            }
          });
        }
      });
    },
    
    removeFile() {
      this.selectedFile = null;
    },
    
    async uploadTemplate() {
      if (!this.canUpload) return;
      
      this.uploading = true;
      uni.showLoading({ title: '上传中...', mask: true });
      
      try {
        const formData = {
          name: this.uploadForm.name,
          tag: this.uploadForm.tag
        };
        
        const result = await templateApi.uploadTemplate(this.selectedFile.path, formData);
        
        uni.hideLoading();
        
        if (result && (result.code === 0 || result.code === '0000' || result.code === 'SUCCESS')) {
          uni.showToast({ title: '上传成功', icon: 'success' });
          this.closeUploadModal();
          this.loadTemplates();
        } else {
          const newTemplate = {
            id: Date.now(),
            name: this.uploadForm.name,
            tag: this.uploadForm.tag,
            type: this.selectedFile.name.toLowerCase().includes('.pdf') ? 'pdf' : 'word',
            createdAt: new Date().toISOString()
          };
          this.templates.unshift(newTemplate);
          this.mockTemplates.unshift(newTemplate);
          uni.showToast({ title: '上传成功', icon: 'success' });
          this.closeUploadModal();
        }
      } catch (error) {
        uni.hideLoading();
        console.error('上传失败:', error);
        uni.showToast({ title: '上传失败: ' + (error.message || '未知错误'), icon: 'none' });
      } finally {
        this.uploading = false;
      }
    },
    
    deleteTemplate(template) {
      uni.showModal({
        title: '确认删除',
        content: `确定要删除模板 "${template.name}" 吗？`,
        success: (res) => {
          if (res.confirm) {
            templateApi.deleteTemplate(template.id)
              .then(res => {
                if (res.code === 0 || res.code === '0000' || res.code === 'SUCCESS') {
                  this.templates = this.templates.filter(t => t.id !== template.id);
                  uni.showToast({ title: '删除成功', icon: 'success' });
                } else {
                  uni.showToast({ title: '删除失败', icon: 'none' });
                }
              })
              .catch(err => {
                console.error('删除失败:', err);
                uni.showToast({ title: '删除失败: ' + (err.message || '未知错误'), icon: 'none' });
              });
          }
        }
      });
    },
    
    viewTemplate(template) {
      uni.showToast({ title: '预览模板功能开发中', icon: 'none' });
    },
    
    getTemplateIcon(filename) {
      const lowerName = filename.toLowerCase();
      if (lowerName.includes('pdf')) return '📕';
      if (lowerName.includes('doc')) return '📘';
      return '📄';
    },
    
    formatFileSize(bytes) {
      if (!bytes || bytes === 0) return '0 B';
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    formatDate(timestamp) {
      const date = new Date(timestamp);
      return date.toLocaleDateString('zh-CN');
    }
  }
}
</script>

<style scoped>
.template-page {
  width: 100%;
  height: 100vh;
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
}

.custom-navbar {
  height: 44px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 15px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  position: sticky;
  top: 0;
  z-index: 100;
}

.navbar-left,
.navbar-right {
  width: 60px;
}

.navbar-left {
  display: flex;
  align-items: center;
}

.back-icon {
  font-size: 32px;
  color: #333;
  font-weight: 300;
}

.navbar-title {
  flex: 1;
  text-align: center;
  font-size: 17px;
  font-weight: 600;
  color: #333;
}

.add-btn {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
  border-radius: 50%;
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  margin-left: auto;
}

.content-scroll {
  flex: 1;
  height: 0;
}

.template-container {
  padding: 15px;
}

.info-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 15px;
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 15px;
}

.info-icon {
  font-size: 24px;
}

.info-text {
  flex: 1;
  font-size: 13px;
  color: #fff;
  line-height: 1.5;
}

.filter-bar {
  margin-bottom: 15px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.search-box {
  display: flex;
  align-items: center;
  background: #fff;
  border-radius: 8px;
  padding: 8px 12px;
  gap: 8px;
}

.search-icon {
  font-size: 14px;
  color: #999;
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 14px;
}

.tag-filter {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tag-chip {
  padding: 6px 14px;
  background: #fff;
  border-radius: 20px;
  font-size: 12px;
  color: #666;
  transition: all 0.3s;
}

.tag-chip.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(1, 1fr);
  gap: 10px;
}

.template-grid-pc {
  grid-template-columns: repeat(2, 1fr);
}

.template-card {
  background: #fff;
  border-radius: 12px;
  padding: 15px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.template-icon {
  font-size: 40px;
  width: 50px;
  text-align: center;
}

.template-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.template-name {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.template-tag {
  font-size: 12px;
  color: #667eea;
  background: #f0f2ff;
  padding: 2px 8px;
  border-radius: 10px;
  align-self: flex-start;
}

.template-date {
  font-size: 12px;
  color: #999;
}

.delete-icon {
  font-size: 20px;
  color: #ff4444;
  font-weight: 300;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-state {
  padding: 60px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.empty-icon {
  font-size: 48px;
  opacity: 0.5;
}

.empty-text {
  font-size: 14px;
  color: #999;
}

.popup-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

.popup-content {
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  background: #fff;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
}

.popup-header {
  padding: 15px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #f0f0f0;
}

.popup-title {
  font-size: 17px;
  font-weight: 600;
  color: #333;
}

.popup-close {
  font-size: 24px;
  color: #999;
  font-weight: 300;
}

.popup-form {
  flex: 1;
  padding: 15px 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-picker {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 14px;
  color: #333;
}

.picker-arrow {
  color: #999;
  transform: rotate(90deg);
}

.upload-zone {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  transition: all 0.3s;
}

.upload-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.upload-icon {
  font-size: 40px;
  opacity: 0.6;
}

.upload-hint {
  font-size: 15px;
  color: #666;
  font-weight: 500;
}

.upload-support {
  font-size: 12px;
  color: #999;
}

.file-selected {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-icon {
  font-size: 32px;
}

.file-detail {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: left;
}

.file-name {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.file-size {
  font-size: 12px;
  color: #999;
}

.popup-footer {
  padding: 15px 20px;
  display: flex;
  gap: 10px;
  border-top: 1px solid #f0f0f0;
}

.popup-btn {
  flex: 1;
  height: 40px;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
}

.popup-btn.cancel {
  background: #f0f2f5;
  color: #666;
}

.popup-btn.confirm {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.popup-btn.confirm.disabled {
  background: #ddd;
  color: #999;
}

@media screen and (min-width: 768px) {
  .template-container {
    max-width: 1000px;
    margin: 0 auto;
  }
  
  .filter-bar {
    flex-direction: row;
    align-items: center;
  }
  
  .search-box {
    flex: 1;
  }
}
</style>
