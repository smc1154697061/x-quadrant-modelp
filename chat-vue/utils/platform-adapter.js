/**
 * platform-adapter.js
 * 跨平台适配工具，提供统一的API接口，处理不同平台的差异
 */

/**
 * 平台适配工具
 */

// 平台类型枚举
export const PLATFORM_TYPE = {
  H5: 'h5',
  MP_WEIXIN: 'mp-weixin',
  APP: 'app',
  UNKNOWN: 'unknown'
};

/**
 * 获取当前平台类型
 * @returns {string} 平台类型
 */
export function getPlatformType() {
  // #ifdef H5
  return PLATFORM_TYPE.H5;
  // #endif
  
  // #ifdef MP-WEIXIN
  return PLATFORM_TYPE.MP_WEIXIN;
  // #endif
  
  // #ifdef APP-PLUS
  return PLATFORM_TYPE.APP;
  // #endif
  
  return PLATFORM_TYPE.UNKNOWN;
}

/**
 * 标准化错误对象，确保跨平台一致性
 * @param {Error|Object|String} error - 原始错误对象
 * @returns {Object} 标准化后的错误对象
 */
export function normalizeError(error) {
  // 创建一个标准错误对象，确保所有属性都存在
  let normalizedError = {
    message: '',
    msg: '',
    errMsg: '',
    code: '',
    stack: ''
  };
  
  // 处理不同类型的错误
  if (typeof error === 'string') {
    // 字符串类型错误
    normalizedError.message = error;
    normalizedError.msg = error;
    normalizedError.errMsg = error;
  } else if (error && typeof error === 'object') {
    // 对象类型错误
    
    // 复制所有原始属性
    Object.assign(normalizedError, error);
    
    // 检查是否为Python异常的JSON表示
    if (error.exc_type && error.exc_value) {
      // 这可能是Python异常的JSON表示
      normalizedError.name = error.exc_type;
      if (!normalizedError.message) normalizedError.message = error.exc_value;
      if (!normalizedError.msg) normalizedError.msg = error.exc_value;
      if (!normalizedError.errMsg) normalizedError.errMsg = error.exc_value;
    }
    
    // 处理常见错误属性，确保message和msg都存在
    if (error.message && !error.msg) {
      normalizedError.msg = error.message;
    } else if (error.msg && !error.message) {
      normalizedError.message = error.msg;
    } else if (error.errMsg && !error.message && !error.msg) {
      normalizedError.message = error.errMsg;
      normalizedError.msg = error.errMsg;
    } else if (!error.message && !error.msg && !error.errMsg) {
      // 如果没有任何错误消息属性，尝试从其他可能的属性中获取
      const possibleErrorMessages = [
        error.error,
        error.errorMessage,
        error.description,
        error.detail,
        error.reason
      ];
      
      // 找到第一个非空的错误消息
      const foundMessage = possibleErrorMessages.find(msg => msg && typeof msg === 'string');
      if (foundMessage) {
        normalizedError.message = foundMessage;
        normalizedError.msg = foundMessage;
        normalizedError.errMsg = foundMessage;
      }
    }
    
    // 特殊处理APIException
    if (error.constructor && error.constructor.name === 'APIException') {
      // 确保APIException对象有msg属性
      if (!normalizedError.msg && normalizedError.message) {
        normalizedError.msg = normalizedError.message;
      }
      // 反向确保也有message属性
      if (!normalizedError.message && normalizedError.msg) {
        normalizedError.message = normalizedError.msg;
      }
      // 确保有errMsg属性
      if (!normalizedError.errMsg) {
        normalizedError.errMsg = normalizedError.message || normalizedError.msg || '未知错误';
      }
      
      // 深度检查APIException对象的所有可能属性
      const possibleErrorFields = ['error', 'detail', 'description', 'reason', 'text', 'response'];
      for (const field of possibleErrorFields) {
        if (error[field]) {
          if (typeof error[field] === 'string') {
            // 如果是字符串，直接使用
            if (!normalizedError.message) normalizedError.message = error[field];
            if (!normalizedError.msg) normalizedError.msg = error[field];
            if (!normalizedError.errMsg) normalizedError.errMsg = error[field];
          } else if (typeof error[field] === 'object') {
            // 如果是对象，尝试提取message或msg
            if (error[field].message) {
              if (!normalizedError.message) normalizedError.message = error[field].message;
              if (!normalizedError.msg) normalizedError.msg = error[field].message;
            }
            if (error[field].msg) {
              if (!normalizedError.msg) normalizedError.msg = error[field].msg;
              if (!normalizedError.message) normalizedError.message = error[field].msg;
            }
            if (error[field].errMsg) {
              if (!normalizedError.errMsg) normalizedError.errMsg = error[field].errMsg;
              if (!normalizedError.message) normalizedError.message = error[field].errMsg;
              if (!normalizedError.msg) normalizedError.msg = error[field].errMsg;
            }
          }
        }
      }
      
      // 如果有data属性，从data中提取更多信息
      if (error.data && typeof error.data === 'object') {
        if (error.data.message && !normalizedError.message) {
          normalizedError.message = error.data.message;
          normalizedError.msg = error.data.message;
        }
        if (error.data.msg && !normalizedError.msg) {
          normalizedError.msg = error.data.msg;
          normalizedError.message = error.data.msg;
        }
      }
    }
    
    // 处理可能是Python API异常的情况
    if ((error.name === 'APIException' || error.type === 'APIException' || 
        (error.constructor && error.constructor.name === 'Object' && 
        (error.toString().includes('APIException') || JSON.stringify(error).includes('APIException')))) 
        && !normalizedError.msg) {
      // 这可能是一个Python APIException
      
      // 尝试从各种可能的属性中提取错误信息
      const possibleMsgSources = [
        error.args && error.args[0],
        error.detail,
        error.error,
        error.response && error.response.data,
        error.response && error.response.body,
        error.body,
        error.data
      ];
      
      // 查找第一个有效的消息源
      for (const source of possibleMsgSources) {
        if (source) {
          if (typeof source === 'string') {
            normalizedError.msg = source;
            normalizedError.message = source;
            normalizedError.errMsg = source;
            break;
          } else if (typeof source === 'object') {
            if (source.message) {
              normalizedError.message = source.message;
              normalizedError.msg = source.message;
              normalizedError.errMsg = source.message;
              break;
            } else if (source.msg) {
              normalizedError.msg = source.msg;
              normalizedError.message = source.msg;
              normalizedError.errMsg = source.msg;
              break;
            } else if (source.error) {
              normalizedError.message = source.error;
              normalizedError.msg = source.error;
              normalizedError.errMsg = source.error;
              break;
            }
          }
        }
      }
      
      // 如果仍然没有找到消息，使用一个默认值
      if (!normalizedError.msg && !normalizedError.message) {
        normalizedError.message = 'API错误';
        normalizedError.msg = 'API错误';
        normalizedError.errMsg = 'API错误';
      }
    }
    
    // 处理嵌套的错误数据
    if (error.data) {
      if (typeof error.data === 'string') {
        try {
          // 尝试解析JSON字符串
          const parsedData = JSON.parse(error.data);
          if (parsedData) {
            // 如果解析成功，提取错误消息
            if (parsedData.message && !normalizedError.message) {
              normalizedError.message = parsedData.message;
              normalizedError.msg = parsedData.message;
            } else if (parsedData.msg && !normalizedError.msg) {
              normalizedError.msg = parsedData.msg;
              normalizedError.message = parsedData.msg;
            } else if (parsedData.errMsg && !normalizedError.errMsg) {
              normalizedError.errMsg = parsedData.errMsg;
              if (!normalizedError.message) normalizedError.message = parsedData.errMsg;
              if (!normalizedError.msg) normalizedError.msg = parsedData.errMsg;
            }
            
            // 提取错误代码
            if (parsedData.code && !normalizedError.code) {
              normalizedError.code = parsedData.code;
            }
          }
        } catch (e) {
          // 解析失败，使用原始data作为消息
          if (!normalizedError.message) normalizedError.message = error.data;
          if (!normalizedError.msg) normalizedError.msg = error.data;
          if (!normalizedError.errMsg) normalizedError.errMsg = error.data;
        }
      } else if (typeof error.data === 'object') {
        // 处理对象类型的data
        if (error.data.message && !normalizedError.message) {
          normalizedError.message = error.data.message;
          if (!normalizedError.msg) normalizedError.msg = error.data.message;
        }
        if (error.data.msg && !normalizedError.msg) {
          normalizedError.msg = error.data.msg;
          if (!normalizedError.message) normalizedError.message = error.data.msg;
        }
        if (error.data.errMsg && !normalizedError.errMsg) {
          normalizedError.errMsg = error.data.errMsg;
          if (!normalizedError.message) normalizedError.message = error.data.errMsg;
          if (!normalizedError.msg) normalizedError.msg = error.data.errMsg;
        }
        if (error.data.code && !normalizedError.code) {
          normalizedError.code = error.data.code;
        }
      }
    }
    
    // 最后的兜底，如果仍然没有错误消息，使用JSON字符串
    if (!normalizedError.message && !normalizedError.msg && !normalizedError.errMsg) {
      try {
        const errorStr = JSON.stringify(error);
        normalizedError.message = errorStr;
        normalizedError.msg = errorStr;
        normalizedError.errMsg = errorStr;
      } catch (e) {
        normalizedError.message = '未知错误';
        normalizedError.msg = '未知错误';
        normalizedError.errMsg = '未知错误';
      }
    }
  } else {
    // 处理非对象非字符串的错误
    const errorStr = String(error);
    normalizedError.message = errorStr;
    normalizedError.msg = errorStr;
    normalizedError.errMsg = errorStr;
  }
  
  return normalizedError;
}

/**
 * 调用uni API并返回Promise
 * @param {string} apiName - API名称
 * @param {object} options - API参数
 * @returns {Promise} Promise对象
 */
export function callUniApi(apiName, options = {}) {
  return new Promise((resolve, reject) => {
    if (typeof uni[apiName] !== 'function') {
      reject(new Error(`API ${apiName} 不存在`));
      return;
    }
    
    uni[apiName]({
      ...options,
      success: (res) => {
        resolve(res);
      },
      fail: (err) => {
        reject(err);
      }
    });
  });
}

/**
 * 选择文件
 * @param {object} options - 选择文件参数
 * @returns {Promise} Promise对象
 */
export function chooseFile(options = {}) {
  const platform = getPlatformType();
  
  // 根据平台选择合适的API
  if (platform === PLATFORM_TYPE.H5) {
    // H5环境使用chooseFile
    return callUniApi('chooseFile', options);
  } else if (platform === PLATFORM_TYPE.MP_WEIXIN) {
    // 微信小程序使用chooseMessageFile
    return callUniApi('chooseMessageFile', options);
  } else if (platform === PLATFORM_TYPE.APP) {
    // App环境使用plus.io相关API
    return callUniApi('chooseImage', options);
  }
  
  // 其他平台返回错误
  return Promise.reject(new Error('当前平台不支持选择文件'));
}

/**
 * 文件上传适配器
 * @param {string} url - 上传URL
 * @param {string|object} file - 文件路径或文件对象
 * @param {object} options - 上传选项
 * @returns {Promise} Promise对象
 */
export function uploadFile(url, file, options = {}) {
  const platform = getPlatformType();
  
  // 合并选项
  const uploadOptions = {
    url: url,
    name: options.name || 'file',
    header: options.header || {},
    formData: options.formData || {}
  };
  
  // 根据平台差异处理文件
  switch (platform) {
    case PLATFORM_TYPE.H5:
      // H5环境可能传入的是File对象
      if (file && typeof file === 'object' && file.fileObj instanceof File) {
        // 创建FormData对象
        const formData = new FormData();
        
        // 添加文件
        formData.append(uploadOptions.name, file.fileObj);
        
        // 添加其他表单数据
        Object.keys(uploadOptions.formData).forEach(key => {
          formData.append(key, uploadOptions.formData[key]);
        });
        
        // 使用fetch API上传
        return new Promise((resolve, reject) => {
          fetch(uploadOptions.url, {
            method: 'POST',
            headers: uploadOptions.header,
            body: formData
          })
          .then(async response => {
            const data = await response.json();
            resolve({ 
              statusCode: response.status,
              data: data  // 直接返回对象，不需要JSON.stringify
            });
          })
          .catch(error => {
            reject({ errMsg: error.message });
          });
        });
      }
      // 如果不是File对象，降级为uni.uploadFile
      uploadOptions.filePath = file.path || file;
      break;
      
    case PLATFORM_TYPE.MP_WEIXIN:
    case PLATFORM_TYPE.APP:
    default:
      // 微信小程序和App使用filePath
      uploadOptions.filePath = file.path || file;
  }
  
  // 使用通用的上传方式，返回标准化的Promise
  return new Promise((resolve, reject) => {
    const uploadTask = uni.uploadFile({
      ...uploadOptions,
      success: (res) => {
        if (res.statusCode === 200) {
          try {
            // 解析返回的JSON字符串
            const data = typeof res.data === 'string' ? JSON.parse(res.data) : res.data;
            resolve({
              statusCode: res.statusCode,
              data: data  // 直接返回对象
            });
          } catch (e) {
            console.error('[文件上传] 解析响应失败:', e);
            reject({ errMsg: '解析响应失败' });
          }
        } else {
          resolve({
            statusCode: res.statusCode,
            data: res.data
          });
        }
      },
      fail: (err) => {
        console.error('[文件上传] 上传失败:', err);
        reject(err);
      }
    });
    
    // 返回uploadTask，允许取消上传
    if (options.onProgressUpdate && uploadTask.onProgressUpdate) {
      uploadTask.onProgressUpdate(options.onProgressUpdate);
    }
  });
}

/**
 * 微信小程序环境下的图片选择降级方案
 */
// #ifdef MP-WEIXIN
function wxChooseImageFallback(options) {
  return new Promise((resolve, reject) => {
    try {
      // 直接使用wx API，不经过uni
      wx.chooseImage({
        count: options.count || 1,
        sizeType: ['original', 'compressed'],
        sourceType: ['album', 'camera'],
        success: (res) => {
          if (res.tempFilePaths && res.tempFilePaths.length > 0) {
            // 构造文件列表
            const files = res.tempFiles || res.tempFilePaths.map((path, index) => {
              return {
                path: path,
                name: platformUtils.getFileNameFromPath(path) || `image_${index}.png`,
                size: (res.tempFiles && res.tempFiles[index]) ? res.tempFiles[index].size : 0
              };
            });
            
            // 返回标准格式
            resolve({
              tempFiles: files,
              tempFilePaths: res.tempFilePaths
            });
          } else {
            reject(new Error('未选择任何图片'));
          }
        },
        fail: (err) => {
          console.error('[文件选择] wx.chooseImage调用失败:', err);
          reject(err);
        }
      });
    } catch (err) {
      console.error('[文件选择] wx.chooseImage调用出错:', err);
      reject(err);
    }
  });
}
// #endif

// 辅助函数：调用图片选择作为降级方案
function callImageFallback(options) {
  return new Promise((resolve, reject) => {
    try {
      // 优先使用通过我们的安全包装后的uni.chooseImage
      const wrappedChooseImage = function(opts) {
        // 创建一个安全的options对象
        const safeOpts = { ...opts };
        
        // 手动添加success和fail回调
        const originalSuccess = safeOpts.success;
        safeOpts.success = function(res) {
          if (originalSuccess) {
            try {
              originalSuccess(res);
            } catch (err) {
              console.error('[文件选择] 原始success回调执行出错:', err);
            }
          }
        };
        
        const originalFail = safeOpts.fail;
        safeOpts.fail = function(err) {
          if (originalFail) {
            try {
              originalFail(err);
            } catch (innerErr) {
              console.error('[文件选择] 原始fail回调执行出错:', innerErr);
            }
          }
        };
        
        // 尝试调用uni.chooseImage
        try {
          // 如果uni.chooseImage返回false，我们返回一个空对象
          const result = uni.chooseImage(safeOpts);
          return result === false ? {} : result;
        } catch (err) {
          console.error('[文件选择] uni.chooseImage调用失败:', err);
          if (safeOpts.fail) {
            safeOpts.fail(err);
          }
          return {};
        }
      };
      
      // 使用包装后的函数
      wrappedChooseImage({
        count: options.count || 1,
        success: (res) => {
          if (res && res.tempFilePaths && res.tempFilePaths.length > 0) {
            // 构造与chooseFile返回格式一致的结果
            const files = res.tempFiles || res.tempFilePaths.map((path, index) => {
              return {
                path: path,
                name: platformUtils.getFileNameFromPath(path) || `image_${index}.png`,
                size: (res.tempFiles && res.tempFiles[index]) ? res.tempFiles[index].size : 0
              };
            });
            
            // 返回标准格式
            resolve({
              tempFiles: files,
              tempFilePaths: res.tempFilePaths
            });
          } else {
            reject(new Error('未选择任何图片'));
          }
        },
        fail: (err) => {
          console.error('[文件选择] 图片选择失败:', err);
          reject(err);
        }
      });
    } catch (err) {
      console.error('[文件选择] 调用图片选择器出错:', err);
      reject(err);
    }
  });
}

// 工具函数
export const platformUtils = {
  // 格式化文件大小
  formatFileSize(bytes) {
    if (!bytes || bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(Math.max(bytes, 1)) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },
  
  // 从路径中获取文件名
  getFileNameFromPath(path) {
    if (!path) return '未知文件';
    const parts = path.split(/[\/\\]/);
    return parts[parts.length - 1] || '未知文件';
  },
  
  // 获取文件扩展名
  getFileExtension(fileName) {
    if (!fileName) return '';
    const parts = fileName.split('.');
    return parts.length > 1 ? parts[parts.length - 1].toLowerCase() : '';
  }
};

/**
 * 平台适配器初始化
 * 在应用启动时调用，预先处理一些已知的平台兼容性问题
 */
export function initPlatformAdapter() {
  try {
    const platform = getPlatformType();

    // 处理uni API调用可能返回false的问题
    // 仅防止页面崩溃，不尝试修改原生API
    if (typeof uni !== 'undefined') {
      // 记录本该被包装的API列表，但不实际修改
      const apisToWatch = [
        'chooseFile', 'chooseMessageFile', 'chooseImage', 
        'chooseVideo', 'scanCode', 'chooseLocation'
      ];
    }

    return platform;
  } catch(err) {
    console.error('[平台适配] 初始化出错:', err);
    return 'unknown';
  }
}

/**
 * 安全存储数据到本地
 * @param {string} key - 存储键名
 * @param {any} data - 要存储的数据
 * @returns {boolean} 是否存储成功
 */
export function safeSetStorage(key, data) {
  try {
    // 针对不同平台进行特殊处理
    const platform = getPlatformType();
    
    if (platform === PLATFORM_TYPE.MP_WEIXIN) {
      // 微信小程序环境下的特殊处理
      if (key === 'token') {
        // 确保token是字符串
        const tokenStr = String(data);
        
        // 先尝试同步方法
        try {
          wx.setStorageSync(key, tokenStr);
        } catch (err) {
          console.error('[存储] token同步保存失败，尝试异步方法:', err);
          // 同步方法失败，尝试异步方法
          wx.setStorage({
            key: key,
            data: tokenStr,
            success: () => console.log('[存储] token异步保存成功'),
            fail: (err) => console.error('[存储] token异步保存失败:', err)
          });
        }
        
        // 额外保存一份备份，以防主存储出问题
        try {
          wx.setStorageSync('token_backup', tokenStr);
        } catch (e) {}
        
        return true;
      }
    }
    
    // 默认使用uni API
    uni.setStorageSync(key, data);
    return true;
  } catch (err) {
    console.error(`[存储] 保存${key}失败:`, err);
    return false;
  }
}

/**
 * 安全从本地获取数据
 * @param {string} key - 存储键名
 * @returns {any} 存储的数据，获取失败返回null
 */
export function safeGetStorage(key) {
  try {
    // 针对不同平台进行特殊处理
    const platform = getPlatformType();
    
    if (platform === PLATFORM_TYPE.MP_WEIXIN) {
      // 微信小程序环境下的特殊处理
      if (key === 'token') {
        try {
          // 先尝试获取主token
          const token = wx.getStorageSync(key);
          if (token) {
            return token;
          }
          
          // 如果主token获取失败，尝试获取备份token
          const backupToken = wx.getStorageSync('token_backup');
          if (backupToken) {
            // 恢复主token
            wx.setStorageSync(key, backupToken);
            return backupToken;
          }
          
          return null;
        } catch (err) {
          console.error('[存储] 获取token失败:', err);
          return null;
        }
      }
    }
    
    // 默认使用uni API
    return uni.getStorageSync(key);
  } catch (err) {
    console.error(`[存储] 获取${key}失败:`, err);
    return null;
  }
}

export default {
  initPlatformAdapter,
  getPlatformType,
  callUniApi,
  uploadFile,
  chooseFile,
  platformUtils,
  PLATFORM_TYPE
}; 