/**
 * API通信工具类
 * 用于实现与后端服务的HTTP通信
 */
import eventBus from './eventBus.js';
import { callUniApi, uploadFile as platformUploadFile, safeGetStorage, safeSetStorage, normalizeError } from './platform-adapter.js';
import { API_BASE_URL } from './config.js';

// API基础URL
const BASE_URL = API_BASE_URL;

class ApiService {
  constructor() {
    this.baseUrl = BASE_URL;
  }

  /**
   * 设置API基础URL
   */
  setBaseUrl(url) {
    this.baseUrl = url;
  }

  /**
   * 获取完整URL
   */
  getFullUrl(path) {
    // 如果是完整URL，直接返回
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path;
    }
    // 如果路径以/开头，则不添加额外斜杠
    if (path.startsWith('/')) {
      return `${this.baseUrl}${path}`;
    }
    return `${this.baseUrl}/${path}`;
  }

  /**
   * 处理API响应
   */
  handleApiResponse(response) {
    // 检查响应中的错误码
    if (response && response.code) {
      // 处理成功状态码
      if (response.code === '0000' || response.code === 'SUCCESS') {
        return response;
      }
      
      // 处理错误状态码
      switch (response.code) {
        case 'UNAUTHORIZED':
          // 未授权，显示错误信息并跳转到登录页
          this.showError(response.message || '请先登录');
          // 清除本地存储的用户信息和token
          uni.removeStorageSync('userInfo');
          uni.removeStorageSync('token');
          uni.removeStorageSync('token_backup');
          // 更新全局状态
          getApp().globalData = getApp().globalData || {};
          getApp().globalData.userInfo = null;
          getApp().globalData.isLoggedIn = false;
          // 保存当前页面URL
          const pages = getCurrentPages();
          if (pages.length > 0) {
            const currentPage = pages[pages.length - 1];
            const path = `/${currentPage.route}`;
            safeSetStorage('redirectUrl', path);
          }
          // 发送登录状态变更事件
          eventBus.emit('authStatusChanged', { isLoggedIn: false });
          // 跳转到登录页
          setTimeout(() => {
            uni.reLaunch({
              url: '/pages/user/login/index'
            });
          }, 100);
          break;
        case 'PARAMETER_ERROR':
        case 'VALIDATION_ERROR':
        case 'RESOURCE_NOT_FOUND':
        case 'DATABASE_ERROR':
        case 'FILE_UPLOAD_ERROR':
        case 'SYSTEM_ERROR':
          // 显示错误信息
          this.showError(response.message || '操作失败');
          break;
      }
    }
    
    return response;
  }

  /**
   * 显示成功提示
   */
  showSuccess(message) {
    callUniApi('showToast', {
      title: message || '操作成功',
      icon: 'success',
      duration: 2000
    }).catch(() => {
      // 错误处理
    });
  }

  /**
   * 显示错误提示
   */
  showError(message) {
    callUniApi('showToast', {
      title: message || '操作失败',
      icon: 'none',
      duration: 2000
    }).catch(() => {
      // 错误处理
    });
  }

  /**
   * 统一处理401未授权响应
   */
  handleUnauthorized() {
    // 清除本地存储的用户信息和token
    uni.removeStorageSync('userInfo');
    uni.removeStorageSync('token');
    uni.removeStorageSync('token_backup');
    uni.removeStorageSync('isLoggingOut');
    
    // 更新全局状态
    const app = getApp();
    if (app) {
      app.globalData = app.globalData || {};
      app.globalData.userInfo = null;
      app.globalData.isLoggedIn = false;
    }
    
    // 保存当前页面URL
    const pages = getCurrentPages();
    if (pages.length > 0) {
      const currentPage = pages[pages.length - 1];
      const path = `/${currentPage.route}`;
      safeSetStorage('redirectUrl', path);
    }
    
    // 发送登录状态变更事件
    eventBus.emit('authStatusChanged', { isLoggedIn: false });
    
    // 显示提示
    this.showError('登录已过期，请重新登录');
    
    // 直接跳转到登录页
    setTimeout(() => {
      uni.reLaunch({
        url: '/pages/user/login/index'
      });
    }, 1000);
  }

  /**
   * 构建请求选项
   */
  buildRequestOptions(method, url, data = {}, requireAuth = true) {
    const fullUrl = this.getFullUrl(url);
    const header = {
      'Content-Type': 'application/json'
    };
    
    // 如果需要认证，添加token
    if (requireAuth) {
      const token = safeGetStorage('token');
      if (token) {
        header['Authorization'] = `Bearer ${token}`;
      } else {
        this.showError('请先登录');
        return null; // 返回null表示无法构建选项
      }
    }
    
    return {
      url: fullUrl,
      method: method,
      data: data,
      header: header
    };
  }

  /**
   * 执行请求
   */
  request(options) {
    if (!options) {
      return Promise.reject(new Error('请求选项无效'));
    }
    
    // 检查是否正在退出应用
    const isExitingApp = uni.getStorageSync('isExitingApp');
    if (isExitingApp === 'true') {
      return Promise.resolve({ code: 'IGNORE_REQUEST', message: '正在退出应用，忽略请求', data: null });
    }
    
    return callUniApi('request', options)
      .then(res => {
        // 处理401未授权状态码
        if (res.statusCode === 401) {
          this.handleUnauthorized();
          throw new Error('未授权，需要重新登录');
        }
        
        if (res.statusCode === 200) {
          return this.handleApiResponse(res.data);
        } else {
          // 处理其他HTTP错误状态码
          const errorMessage = `请求失败: ${res.statusCode}`;
          
          // 显示错误提示
          this.showError(errorMessage);
          
          throw new Error(errorMessage);
        }
      })
      .catch(err => {
        // 检查是否正在退出应用
        const isExitingApp = uni.getStorageSync('isExitingApp');
        if (isExitingApp === 'true') {
          return Promise.resolve({ code: 'IGNORE_REQUEST', message: '正在退出应用，忽略请求', data: null });
        }
        
        // 检查是否是网络错误
        const isNetworkError = err.errMsg && (
          err.errMsg.includes('request:fail') || 
          err.errMsg.includes('timeout') || 
          err.errMsg.includes('connection refused')
        );
        
        if (isNetworkError) {
          // 网络错误，显示友好提示
          this.showError('网络连接失败，请检查网络或服务器状态');
          
          // 返回标准化的错误对象
          return Promise.reject({
            code: 'NETWORK_ERROR',
            message: '网络连接失败，请检查网络或服务器状态',
            data: null,
            originalError: err
          });
        }
        
        // 其他错误
        this.showError(err.message || '请求失败');
        throw err;
      });
  }

  /**
   * GET请求
   */
  async get(url, params = {}, requireAuth = true) {
    const options = this.buildRequestOptions('GET', url, params, requireAuth);
    return this.request(options);
  }

  /**
   * POST请求
   */
  async post(url, data = {}, requireAuth = true) {
    const options = this.buildRequestOptions('POST', url, data, requireAuth);
    return this.request(options);
  }

  /**
   * PUT请求
   */
  async put(url, data = {}, requireAuth = true) {
    const options = this.buildRequestOptions('PUT', url, data, requireAuth);
    return this.request(options);
  }

  /**
   * DELETE请求
   */
  async delete(url, requireAuth = true) {
    const options = this.buildRequestOptions('DELETE', url, {}, requireAuth);
    return this.request(options);
  }

  /**
   * 流式POST请求 - 用于SSE/流式数据接收
   * @param {string} url - 请求地址
   * @param {Object} data - 请求数据
   * @param {Function} onChunk - 数据块回调函数
   * @param {boolean} requireAuth - 是否需要认证
   */
  streamPost(url, data = {}, onChunk, requireAuth = true) {
    const fullUrl = this.getFullUrl(url);
    const header = {
      'Content-Type': 'application/json'
    };
    
    if (requireAuth) {
      const token = safeGetStorage('token');
      if (token) {
        header['Authorization'] = `Bearer ${token}`;
      } else {
        this.showError('请先登录');
        return { abort: () => {} };
      }
    }
    
    let buffer = '';
    let abortController = null;
    
    const parseBuffer = () => {
      let newlineIndex;
      while ((newlineIndex = buffer.indexOf('\n\n')) !== -1) {
        const message = buffer.slice(0, newlineIndex);
        buffer = buffer.slice(newlineIndex + 2);
        
        if (message.startsWith('data: ')) {
          const dataStr = message.slice(6);
          if (dataStr === '[DONE]') return;
          try {
            const parsed = JSON.parse(dataStr);
            if (onChunk && typeof onChunk === 'function') {
              onChunk(parsed);
            }
          } catch (e) {
            console.warn('解析流式数据失败:', dataStr, e);
          }
        }
      }
    };
    
    try {
      // #ifdef H5
      if (typeof fetch !== 'undefined') {
        if (typeof AbortController !== 'undefined') {
          abortController = new AbortController();
        }
        
        fetch(fullUrl, {
          method: 'POST',
          headers: header,
          body: JSON.stringify(data),
          signal: abortController ? abortController.signal : undefined
        }).then(async (response) => {
          if (response.status === 401) {
            this.handleUnauthorized();
            return;
          }
          
          if (!response.ok) {
            console.error('流式请求失败:', response.status);
            return;
          }
          
          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value, { stream: true });
            buffer += chunk;
            parseBuffer();
          }
        }).catch((err) => {
          if (err.name !== 'AbortError') {
            console.error('流式请求错误:', err);
          }
        });
        
        return {
          abort: () => {
            if (abortController) abortController.abort();
          }
        };
      }
      // #endif
      
      // 小程序平台使用uni.request的onChunkReceived
      const options = {
        url: fullUrl,
        method: 'POST',
        data: data,
        header: header,
        enableChunked: true,
        responseType: 'arraybuffer'
      };
      
      const requestTask = uni.request(options);
      
      if (requestTask.onChunkReceived) {
        requestTask.onChunkReceived((res) => {
          const arrayBuffer = res.data;
          const chunk = String.fromCharCode.apply(null, new Uint8Array(arrayBuffer));
          buffer += chunk;
          parseBuffer();
        });
      }
      
      if (requestTask.onHeadersReceived) {
        requestTask.onHeadersReceived((res) => {
          if (res.statusCode === 401) {
            this.handleUnauthorized();
          }
        });
      }
      
      return {
        abort: () => {
          if (requestTask && requestTask.abort) {
            requestTask.abort();
          }
        }
      };
    } catch (e) {
      console.error('流式请求初始化失败:', e);
      return { abort: () => {} };
    }
  }

  /**
   * 文件上传
   */
  async upload(url, filePath, formData = {}, requireAuth = true) {
    const fullUrl = this.getFullUrl(url);
    const header = {};
    
    // 如果需要认证，添加token
    if (requireAuth) {
      const token = safeGetStorage('token');
      if (token) {
        header['Authorization'] = `Bearer ${token}`;
      } else {
        this.showError('请先登录');
        return Promise.reject(new Error('未登录'));
      }
    }
    
    try {
      // 使用跨平台上传适配器
      const result = await platformUploadFile(fullUrl, filePath, {
        name: 'file',
        formData: formData,
        header: header
      });
      
      // 处理响应
      if (result.statusCode === 401) {
        this.handleUnauthorized();
        throw new Error('未授权，需要重新登录');
      }
      
      if (result.statusCode === 200) {
        // platformUploadFile 已经解析好了 data，直接使用
        const data = result.data;
        
        // 确保data对象存在
        if (!data) {
          const error = { 
            code: 'ERROR', 
            message: '响应数据为空', 
            msg: '响应数据为空', 
            errMsg: '响应数据为空' 
          };
          this.showError(error.message);
          return error;
        }
        
        // 标准化错误属性
        if (data.message && !data.msg) {
          data.msg = data.message;
        } 
        if (data.msg && !data.message) {
          data.message = data.msg;
        }
        if (!data.errMsg) {
          data.errMsg = data.message || data.msg || '未知错误';
        }
        
        return this.handleApiResponse(data);
      } else {
        const error = { 
          code: 'ERROR',
          message: `上传失败: HTTP ${result.statusCode}`, 
          msg: `上传失败: HTTP ${result.statusCode}`,
          errMsg: `上传失败: HTTP ${result.statusCode}`,
          statusCode: result.statusCode
        };
        this.showError(error.message);
        throw error;
      }
    } catch (err) {
      console.error('[API上传] 上传出错:', err);
      
      // 标准化错误对象
      const normalizedError = normalizeError(err);
      
      // 显示错误提示
      this.showError(normalizedError.message || normalizedError.msg || normalizedError.errMsg || '上传失败');
      
      // 抛出标准化的错误
      throw normalizedError;
    }
  }
}

// 创建API服务实例
const api = new ApiService();

// 导出API服务实例
export default api;
export { BASE_URL };

// 导出callUniApi函数，方便其他模块使用
export { callUniApi };

/**
 * 安全调用uni API
 * @param {String} apiName - API名称，如'chooseFile'
 * @param {Object} options - API选项
 * @returns {Promise} - Promise对象
 */
export function safeUniApiCall(apiName, options = {}) {
  return new Promise((resolve, reject) => {
    // 检查API是否存在
    if (typeof uni[apiName] !== 'function') {
      if (options.fail) {
        options.fail({ errMsg: `${apiName}:fail 不支持的API` });
      }
      reject(new Error(`API ${apiName} 不存在`));
      return;
    }
    
    // 创建新的选项对象，添加成功和失败回调
    const newOptions = {
      ...options,
      success: (res) => {
        if (options.success) {
          options.success(res);
        }
        resolve(res);
      },
      fail: (err) => {
        if (options.fail) {
          options.fail(err);
        }
        reject(err);
      }
    };
    
    // 尝试调用API
    try {
      const result = uni[apiName](newOptions);
      
      // 如果API返回false，表示平台不支持该API
      if (result === false) {
        const error = { errMsg: `${apiName}:fail 当前环境不支持该API` };
        if (options.fail) {
          options.fail(error);
        }
        reject(error);
        return;
      }
    } catch (e) {
      if (options.fail) {
        options.fail({ errMsg: `${apiName}:fail ${e.message}` });
      }
      reject(e);
    }
  });
}

/**
 * 模板管理API
 */
export const templateApi = {
  /**
   * 获取模板列表
   * @param {Object} params - 查询参数 (tag, keyword)
   */
  getTemplates(params = {}) {
    return api.get('/llm/templates', params);
  },

  /**
   * 上传模板文件
   * @param {String} filePath - 文件路径
   * @param {Object} formData - 表单数据 (name, tags)
   */
  uploadTemplate(filePath, formData = {}) {
    return api.upload('/llm/templates', filePath, formData);
  },

  /**
   * 删除模板
   * @param {String|Number} templateId - 模板ID
   */
  deleteTemplate(templateId) {
    return api.delete(`/llm/templates/${templateId}`);
  },

  /**
   * 获取模板详情
   * @param {String|Number} templateId - 模板ID
   */
  getTemplateDetail(templateId) {
    return api.get(`/llm/templates/${templateId}`);
  }
};

/**
 * 文档生成API
 */
export const docGenerateApi = {
  /**
   * 生成文档
   * @param {Object} data - 请求数据 (templateId, userInput)
   */
  generateDocument(data) {
    return api.post('/llm/doc/generate', data);
  },

  /**
   * 获取生成历史
   */
  getHistory() {
    return api.get('/llm/doc/history');
  },

  /**
   * 获取生成结果详情
   * @param {String|Number} resultId - 结果ID
   */
  getResultDetail(resultId) {
    return api.get(`/llm/doc/result/${resultId}`);
  },

  /**
   * 下载生成的文档
   * @param {String|Number} resultId - 结果ID
   * @param {String} format - 格式 (word, pdf)
   */
  downloadDocument(resultId, format = 'word') {
    return api.get(`/llm/doc/download/${resultId}/${format}`);
  }
};