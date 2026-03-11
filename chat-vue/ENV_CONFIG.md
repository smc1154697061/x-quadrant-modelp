# 环境配置说明

## 自动环境检测

uniapp 会根据编译环境自动选择配置：

### 1. H5 环境
- **开发环境**: `npm run dev:h5` → 使用 `http://127.0.0.1:5000/api`
- **生产环境**: `npm run build:h5` → 使用 `http://115.190.130.68:5000/api`

### 2. 微信小程序环境
- **开发环境**: `npm run dev:mp-weixin` → 使用 `http://127.0.0.1:5000/api`
- **生产环境**: `npm run build:mp-weixin` → 使用 `http://115.190.130.68:5000/api`

### 3. App 环境
- **开发环境**: `npm run dev:app-plus` → 使用 `http://127.0.0.1:5000/api`
- **生产环境**: `npm run build:app-plus` → 使用 `http://115.190.130.68:5000/api`

## 手动环境切换

如果需要手动切换环境，修改 `utils/config.js` 中的环境判断逻辑：

```javascript
function getCurrentEnv() {
  // 手动指定环境
  return 'development'; // 或 'production' 或 'test'
}
```

## 环境配置

### development (开发环境)
- API地址: `http://127.0.0.1:5000/api`
- 调试模式: 开启
- 超时时间: 10秒

### production (生产环境)
- API地址: `http://115.190.130.68:5000/api`
- 调试模式: 关闭
- 超时时间: 30秒

### test (测试环境)
- API地址: `https://wx-dudubot.vip.cpolar.cn/api`
- 调试模式: 开启
- 超时时间: 15秒

## 平台特定配置

不同平台有不同的超时设置：

- **H5**: 上传超时 60秒，请求超时 10秒
- **微信小程序**: 上传超时 120秒，请求超时 30秒
- **App**: 上传超时 180秒，请求超时 30秒

## 调试信息

在开发环境下，控制台会显示：
- 当前环境
- 当前平台
- API地址

## 使用示例

```javascript
import { API_BASE_URL, isDevelopment, isH5 } from './utils/config.js';

// 环境判断
if (isDevelopment()) {
  console.log('开发环境');
}

if (isH5()) {
  console.log('H5平台');
}
```
