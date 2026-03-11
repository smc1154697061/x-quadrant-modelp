/**
 * 微信小程序文件选择器
 * 直接使用原生wx API，绕过uni-app的兼容层
 */

// 处理wx.chooseMessageFile可能不存在的情况
function safeWxChooseMessageFile(options = {}) {
  return new Promise((resolve, reject) => {
    if (typeof wx === 'undefined') {
      console.warn('wx对象未定义，无法调用wx.chooseMessageFile');
      reject({errMsg: 'chooseMessageFile:fail wx is undefined'});
      return;
    }
    
    // 安全检查wx.chooseMessageFile是否存在
    if (typeof wx.chooseMessageFile !== 'function') {
      console.warn('wx.chooseMessageFile不存在，降级为wx.chooseImage');
      // 降级为chooseImage
      safeWxChooseImage(options).then(resolve).catch(reject);
      return;
    }
    
    // 默认参数
    const safeOptions = {
      count: options.count || 1,
      type: options.type || 'file',
      extension: options.extension || options.extensions || [],
      ...options
    };
    
    // 直接调用微信API
    try {
      wx.chooseMessageFile({
        ...safeOptions,
        success: (res) => {
          // 格式化返回结果与uni API一致
          if (res.tempFiles && res.tempFiles.length > 0) {
            const result = {
              errMsg: res.errMsg || 'chooseMessageFile:ok',
              tempFilePaths: res.tempFiles.map(file => file.path),
              tempFiles: res.tempFiles
            };
            resolve(result);
          } else {
            reject({errMsg: 'chooseMessageFile:fail no file selected'});
          }
        },
        fail: (err) => {
          console.error('wx.chooseMessageFile调用失败:', err);
          reject(err);
        }
      });
    } catch (err) {
      console.error('wx.chooseMessageFile执行出错:', err);
      safeWxChooseImage(options).then(resolve).catch(reject);
    }
  });
}

// 安全的图片选择API
function safeWxChooseImage(options = {}) {
  return new Promise((resolve, reject) => {
    if (typeof wx === 'undefined' || typeof wx.chooseImage !== 'function') {
      console.warn('wx.chooseImage不可用');
      reject({errMsg: 'chooseImage:fail API unavailable'});
      return;
    }
    
    try {
      wx.chooseImage({
        count: options.count || 1,
        sizeType: ['original', 'compressed'],
        sourceType: ['album', 'camera'],
        success: (res) => {
          if (res.tempFilePaths && res.tempFilePaths.length > 0) {
            // 构造与chooseMessageFile一致的返回结果
            const tempFiles = res.tempFiles || res.tempFilePaths.map((path, index) => {
              return {
                path: path,
                name: getFileNameFromPath(path) || `image_${index}.png`,
                size: (res.tempFiles && res.tempFiles[index]) ? res.tempFiles[index].size : 0,
                type: 'image'
              };
            });
            
            const result = {
              errMsg: res.errMsg || 'chooseImage:ok',
              tempFilePaths: res.tempFilePaths,
              tempFiles: tempFiles
            };
            
            resolve(result);
          } else {
            reject({errMsg: 'chooseImage:fail no image selected'});
          }
        },
        fail: (err) => {
          reject(err);
        }
      });
    } catch(err) {
      console.error('wx.chooseImage执行出错:', err);
      reject(err);
    }
  });
}

// 从路径中获取文件名
function getFileNameFromPath(path) {
  if (!path) return '';
  const parts = path.split(/[\/\\]/);
  return parts[parts.length - 1] || '';
}

// 格式化文件大小
function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(Math.max(bytes, 1)) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 导出工具函数
export default {
  chooseFile: safeWxChooseMessageFile,
  chooseImage: safeWxChooseImage,
  formatFileSize,
  getFileNameFromPath
}; 