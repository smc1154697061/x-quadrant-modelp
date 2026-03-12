<template>
  <view class="template-manage-page">
    <view class="custom-navbar">
      <view class="navbar-left" @tap="goBack">
        <text class="back-icon">‹</text>
      </view>
      <view class="navbar-title">
        <text>模板管理</text>
      </view>
      <view class="navbar-right" @tap="showUploadPopup">
        <text class="add-icon">+</text>
      </view>
    </view>
    
    <scroll-view class="content-scroll" scroll-y @scrolltolower="loadMore">
      <view class="template-container">
        <view class="search-bar">
          <input 
            class="search-input" 
            v-model="searchKeyword" 
            placeholder="搜索模板名称或描述" 
            @confirm="handleSearch"
          />
          <view class="search-btn" @tap="handleSearch">
            <text>搜索</text>
          </view>
        </view>
        
        <scroll-view class="category-scroll" scroll-x>
          <view class="category-list">
            <view 
              class="category-item" 
              :class="{ active: currentCategory === '' }" 
              @tap="selectCategory('')"
            >
              <text>全部</text>
            </view>
            <view 
              v-for="(cat, index) in categories" 
              :key="index"
              class="category-item" 
              :class="{ active: currentCategory === cat }" 
              @tap="selectCategory(cat)"
            >
              <text>{{ cat }}</text>
            </view>
          </view>
        </scroll-view>
        
        <view v-if="templates.length === 0 && !loading" class="empty-state">
          <text class="empty-icon">📄</text>
          <text class="empty-text">暂无模板</text>
          <text class="empty-hint">点击右上角 + 上传模板</text>
        </view>
        
        <view v-else class="template-list">
          <view 
            v-for="template in templates" 
            :key="template.id" 
            class="template-card"
          >
            <view class="template-header">
              <view class="template-icon">
                <text>{{ getFileIcon(template.file_type) }}</text>
              </view>
              <view class="template-info">
                <text class="template-name">{{ template.name }}</text>
                <view class="template-meta">
                  <text class="template-category">{{ template.category }}</text>
                  <text class="template-time">{{ formatDate(template.created_at) }}</text>
                </view>
              </view>
            </view>
            
            <view v-if="template.description" class="template-desc">
              <text>{{ template.description }}</text>
            </view>
            
            <view class="template-actions">
              <view class="action-btn" @tap="downloadTemplate(template)">
                <text class="action-icon">⬇</text>
                <text>下载</text>
              </view>
              <view class="action-btn" @tap="goToGenerate(template)">
                <text class="action-icon">✏</text>
                <text>生成文档</text>
              </view>
              <view v-if="!template.is_public || template.created_by === currentUserId" class="action-btn danger" @tap="deleteTemplate(template)">
                <text class="action-icon">🗑</text>
                <text>删除</text>
              </view>
            </view>
          </view>
        </view>
        
        <view v-if="loading" class="loading-state">
          <text>加载中...</text>
        </view>
      </view>
    </scroll-view>
    
    <view v-if="showUploadModal" class="popup-mask" @tap="closeUploadPopup">
      <view class="popup-content" @tap.stop>
        <view class="popup-header">
          <text class="popup-title">上传模板</text>
          <text class="popup-close" @tap="closeUploadPopup">×</text>
        </view>
        
        <view class="popup-body">
          <view class="form-item">
            <text class="form-label">模板名称 *</text>
            <input class="form-input" v-model="uploadForm.name" placeholder="请输入模板名称" />
          </view>
          
          <view class="form-item">
            <text class="form-label">分类</text>
            <picker mode="selector" :range="categories" @change="onCategoryChange">
              <view class="form-picker">
                <text>{{ uploadForm.category || '请选择分类' }}</text>
                <text class="picker-arrow">›</text>
              </view>
            </picker>
          </view>
          
          <view class="form-item">
            <text class="form-label">描述</text>
            <textarea class="form-textarea" v-model="uploadForm.description" placeholder="请输入模板描述" />
          </view>
          
          <view class="form-item">
            <text class="form-label">模板文件 *</text>
            <view class="upload-zone" @tap="selectFile">
              <view v-if="!uploadForm.file" class="upload-empty">
                <text class="upload-icon">📁</text>
                <text class="upload-hint">点击选择文件</text>
                <text class="upload-support">支持 Word、PDF 格式</text>
              </view>
              <view v-else class="file-selected">
                <text class="file-icon">📄</text>
                <text class="file-name">{{ uploadForm.file.name }}</text>
                <text class="remove-icon" @tap.stop="removeFile">×</text>
              </view>
            </view>
          </view>
          
          <view class="form-item">
            <view class="form-checkbox" @tap="togglePublic">
              <view class="checkbox" :class="{ checked: uploadForm.is_public }">
                <text v-if="uploadForm.is_public">✓</text>
              </view>
              <text class="checkbox-label">设为公开模板</text>
            </view>
          </view>
        </view>
        
        <view class="popup-footer">
          <button class="popup-btn cancel" @tap="closeUploadPopup">取消</button>
          <button class="popup-btn confirm" :disabled="!canUpload" @tap="uploadTemplate">上传</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import api from '../../../utils/api.js';

export default {
  data() {
    return {
      templates: [],
      categories: ['简历', '论文', '报告', '合同', '信函', '其他'],
      currentCategory: '',
      searchKeyword: '',
      loading: false,
      showUploadModal: false,
      uploadForm: {
        name: '',
        category: '其他',
        description: '',
        file: null,
        is_public: false
      },
      currentUserId: null
    };
  },
  
  computed: {
    canUpload() {
      return this.uploadForm.name && this.uploadForm.file;
    }
  },
  
  onLoad() {
    this.getCurrentUserId();
    this.loadTemplates();
    this.loadCategories();
  },
  
  methods: {
    getCurrentUserId() {
      const userInfo = uni.getStorageSync('userInfo');
      if (userInfo) {
        try {
          const user = typeof userInfo === 'string' ? JSON.parse(userInfo) : userInfo;
          this.currentUserId = user.id;
        } catch (e) {
          console.error('解析用户信息失败:', e);
        }
      }
    },
    
    goBack() {
      uni.navigateBack();
    },
    
    async loadTemplates() {
      this.loading = true;
      try {
        const params = {};
        if (this.currentCategory) {
          params.category = this.currentCategory;
        }
        if (this.searchKeyword) {
          params.keyword = this.searchKeyword;
        }
        
        const result = await api.get('/llm/templates', params);
        
        if (result && result.code === 0) {
          this.templates = result.data || [];
        }
      } catch (error) {
        console.error('加载模板列表失败:', error);
        uni.showToast({
          title: '加载失败',
          icon: 'none'
        });
      } finally {
        this.loading = false;
      }
    },
    
    async loadCategories() {
      try {
        const result = await api.get('/llm/templates/categories');
        if (result && result.code === 0 && result.data) {
          const serverCategories = result.data;
          this.categories = [...new Set([...this.categories, ...serverCategories])];
        }
      } catch (error) {
        console.error('加载分类失败:', error);
      }
    },
    
    selectCategory(category) {
      this.currentCategory = category;
      this.loadTemplates();
    },
    
    handleSearch() {
      this.loadTemplates();
    },
    
    showUploadPopup() {
      this.showUploadModal = true;
    },
    
    closeUploadPopup() {
      this.showUploadModal = false;
      this.resetUploadForm();
    },
    
    resetUploadForm() {
      this.uploadForm = {
        name: '',
        category: '其他',
        description: '',
        file: null,
        is_public: false
      };
    },
    
    selectFile() {
      uni.chooseMessageFile({
        count: 1,
        type: 'file',
        extension: ['.doc', '.docx', '.pdf'],
        success: (res) => {
          if (res.tempFiles && res.tempFiles.length > 0) {
            const file = res.tempFiles[0];
            this.uploadForm.file = {
              path: file.path,
              name: file.name,
              size: file.size
            };
          }
        },
        fail: (err) => {
          uni.chooseImage({
            count: 1,
            success: (res) => {
              if (res.tempFilePaths && res.tempFilePaths.length > 0) {
                this.uploadForm.file = {
                  path: res.tempFilePaths[0],
                  name: 'template_file',
                  size: 0
                };
              }
            }
          });
        }
      });
    },
    
    removeFile() {
      this.uploadForm.file = null;
    },
    
    onCategoryChange(e) {
      const index = e.detail.value;
      this.uploadForm.category = this.categories[index];
    },
    
    togglePublic() {
      this.uploadForm.is_public = !this.uploadForm.is_public;
    },
    
    async uploadTemplate() {
      if (!this.canUpload) return;
      
      uni.showLoading({
        title: '上传中...',
        mask: true
      });
      
      try {
        const formData = {
          name: this.uploadForm.name,
          category: this.uploadForm.category,
          description: this.uploadForm.description,
          is_public: this.uploadForm.is_public.toString()
        };
        
        const result = await api.upload('/llm/templates', this.uploadForm.file.path, formData);
        
        uni.hideLoading();
        
        if (result && result.code === 0) {
          uni.showToast({
            title: '上传成功',
            icon: 'success'
          });
          this.closeUploadPopup();
          this.loadTemplates();
        } else {
          uni.showToast({
            title: result?.message || '上传失败',
            icon: 'none'
          });
        }
      } catch (error) {
        uni.hideLoading();
        console.error('上传模板失败:', error);
        uni.showToast({
          title: '上传失败',
          icon: 'none'
        });
      }
    },
    
    downloadTemplate(template) {
      uni.showLoading({
        title: '下载中...',
        mask: true
      });
      
      const downloadUrl = `${api.baseUrl || ''}/api/llm/templates/${template.id}`;
      const token = uni.getStorageSync('token');
      
      uni.downloadFile({
        url: downloadUrl,
        header: {
          'Authorization': `Bearer ${token}`
        },
        success: (res) => {
          uni.hideLoading();
          if (res.statusCode === 200) {
            uni.saveFile({
              tempFilePath: res.tempFilePath,
              success: (saveRes) => {
                uni.showToast({
                  title: '保存成功',
                  icon: 'success'
                });
              },
              fail: () => {
                uni.showToast({
                  title: '保存失败',
                  icon: 'none'
                });
              }
            });
          } else {
            uni.showToast({
              title: '下载失败',
              icon: 'none'
            });
          }
        },
        fail: () => {
          uni.hideLoading();
          uni.showToast({
            title: '下载失败',
            icon: 'none'
          });
        }
      });
    },
    
    goToGenerate(template) {
      uni.navigateTo({
        url: `/pages/tools/template-generate/index?template_id=${template.id}&template_name=${encodeURIComponent(template.name)}`
      });
    },
    
    deleteTemplate(template) {
      uni.showModal({
        title: '确认删除',
        content: `确定要删除模板"${template.name}"吗？`,
        success: async (res) => {
          if (res.confirm) {
            try {
              const result = await api.delete(`/llm/templates/${template.id}`);
              
              if (result && result.code === 0) {
                uni.showToast({
                  title: '删除成功',
                  icon: 'success'
                });
                this.loadTemplates();
              } else {
                uni.showToast({
                  title: result?.message || '删除失败',
                  icon: 'none'
                });
              }
            } catch (error) {
              console.error('删除模板失败:', error);
              uni.showToast({
                title: '删除失败',
                icon: 'none'
              });
            }
          }
        }
      });
    },
    
    getFileIcon(fileType) {
      const icons = {
        'word': '📝',
        'pdf': '📕',
        'txt': '📄'
      };
      return icons[fileType] || '📄';
    },
    
    formatDate(timestamp) {
      if (!timestamp) return '';
      const date = new Date(timestamp);
      return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      });
    }
  }
};
</script>

<style scoped>
.template-manage-page {
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

.back-icon {
  font-size: 32px;
  color: #333;
  font-weight: 300;
}

.add-icon {
  font-size: 28px;
  color: #667eea;
  font-weight: bold;
}

.navbar-title {
  flex: 1;
  text-align: center;
  font-size: 17px;
  font-weight: 600;
  color: #333;
}

.content-scroll {
  flex: 1;
  height: 0;
}

.template-container {
  padding: 15px;
}

.search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.search-input {
  flex: 1;
  height: 36px;
  background: #fff;
  border-radius: 18px;
  padding: 0 15px;
  font-size: 14px;
}

.search-btn {
  padding: 0 20px;
  height: 36px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.search-btn text {
  color: #fff;
  font-size: 14px;
}

.category-scroll {
  white-space: nowrap;
  margin-bottom: 15px;
}

.category-list {
  display: inline-flex;
  gap: 10px;
}

.category-item {
  padding: 6px 16px;
  background: #fff;
  border-radius: 20px;
  font-size: 13px;
  color: #666;
}

.category-item.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.empty-state {
  padding: 80px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.empty-icon {
  font-size: 64px;
  opacity: 0.5;
}

.empty-text {
  font-size: 16px;
  color: #999;
}

.empty-hint {
  font-size: 13px;
  color: #bbb;
}

.template-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.template-card {
  background: #fff;
  border-radius: 12px;
  padding: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.template-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.template-icon {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}

.template-info {
  flex: 1;
}

.template-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.template-meta {
  display: flex;
  gap: 10px;
}

.template-category {
  font-size: 12px;
  color: #667eea;
  background: rgba(102, 126, 234, 0.1);
  padding: 2px 8px;
  border-radius: 10px;
}

.template-time {
  font-size: 12px;
  color: #999;
}

.template-desc {
  padding: 10px;
  background: #f9f9f9;
  border-radius: 8px;
  margin-bottom: 12px;
}

.template-desc text {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
}

.template-actions {
  display: flex;
  gap: 10px;
}

.action-btn {
  flex: 1;
  height: 36px;
  background: #f5f7fa;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 13px;
  color: #666;
}

.action-btn.danger {
  color: #ff4444;
}

.action-icon {
  font-size: 14px;
}

.loading-state {
  padding: 20px;
  text-align: center;
  color: #999;
  font-size: 14px;
}

.popup-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-end;
  z-index: 999;
}

.popup-content {
  width: 100%;
  max-height: 85vh;
  background: #fff;
  border-radius: 20px 20px 0 0;
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
  font-size: 32px;
  color: #999;
  font-weight: 300;
}

.popup-body {
  padding: 20px;
  max-height: 60vh;
  overflow-y: auto;
}

.form-item {
  margin-bottom: 20px;
}

.form-label {
  font-size: 14px;
  color: #333;
  margin-bottom: 8px;
  display: block;
}

.form-input {
  width: 100%;
  height: 44px;
  background: #f5f7fa;
  border-radius: 8px;
  padding: 0 15px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-textarea {
  width: 100%;
  min-height: 80px;
  background: #f5f7fa;
  border-radius: 8px;
  padding: 12px 15px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-picker {
  width: 100%;
  height: 44px;
  background: #f5f7fa;
  border-radius: 8px;
  padding: 0 15px;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-sizing: border-box;
}

.picker-arrow {
  color: #999;
  font-size: 18px;
}

.upload-zone {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
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

.file-name {
  flex: 1;
  font-size: 14px;
  color: #333;
  text-align: left;
}

.remove-icon {
  font-size: 24px;
  color: #ff4444;
}

.form-checkbox {
  display: flex;
  align-items: center;
  gap: 10px;
}

.checkbox {
  width: 20px;
  height: 20px;
  border: 2px solid #ddd;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.checkbox.checked {
  background: #667eea;
  border-color: #667eea;
}

.checkbox.checked text {
  color: #fff;
  font-size: 12px;
}

.checkbox-label {
  font-size: 14px;
  color: #666;
}

.popup-footer {
  padding: 15px 20px;
  display: flex;
  gap: 10px;
  border-top: 1px solid #f0f0f0;
}

.popup-btn {
  flex: 1;
  height: 44px;
  border-radius: 22px;
  font-size: 15px;
  font-weight: 500;
}

.popup-btn.cancel {
  background: #f5f7fa;
  color: #666;
}

.popup-btn.confirm {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.popup-btn.confirm[disabled] {
  opacity: 0.5;
}

@media screen and (min-width: 768px) {
  .template-container {
    max-width: 800px;
    margin: 0 auto;
  }
}
</style>
