# 搜索互赞机器人 (Search Like Bot)

一个基于Kivy框架的Android自动化工具，用于搜索用户并自动点赞其最新作品。

## 功能特点

- 🔍 自动搜索指定用户
- ❤️ 自动点赞用户最新作品
- 🔄 支持多轮循环操作
- 📱 支持多个平台（抖音、小红书、快手）
- 🎯 智能坐标转换，适配不同分辨率
- 🛑 音量键紧急停止功能
- 💾 配置自动保存
- 🧪 完整的测试功能

## 系统要求

- Android 5.0+ (API 21+)
- Root权限（用于自动化操作）
- 目标应用已安装（抖音/小红书/快手）

## 使用GitHub Actions自动构建APK

### 步骤1：Fork或创建仓库

1. 在GitHub上创建新仓库或Fork本项目
2. 将所有代码文件上传到仓库

### 步骤2：配置仓库

确保仓库包含以下文件结构：
```
├── main.py                    # 主程序文件
├── buildozer.spec            # Buildozer配置
├── requirements.txt          # Python依赖
├── README.md                 # 项目说明
└── .github/
    └── workflows/
        └── build.yml         # GitHub Actions工作流
```

### 步骤3：触发构建

有以下方式触发APK构建：

1. **推送代码**：向`main`或`master`分支推送代码
2. **手动触发**：
   - 进入仓库的`Actions`标签页
   - 选择`Build APK`工作流
   - 点击`Run workflow`按钮

### 步骤4：下载APK

构建完成后（约15-30分钟）：

1. **从Actions下载**：
   - 进入`Actions`标签页
   - 点击最新的构建记录
   - 在`Artifacts`部分下载`SearchLikeBot-APK`

2. **从Releases下载**：
   - 进入`Releases`页面
   - 下载最新版本的APK文件

## 本地构建（可选）

### 环境准备

```bash
# 安装系统依赖（Ubuntu/Debian）
sudo apt update
sudo apt install -y python3-pip build-essential git ffmpeg \
    libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
    libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev \
    zlib1g-dev openjdk-17-jdk

# 安装Python依赖
pip install -r requirements.txt
```

### 构建APK

```bash
# 清理之前的构建（如果有）
buildozer android clean

# 构建debug版本
buildozer android debug

# APK文件将生成在 bin/ 目录下
```

## 使用说明

### 首次使用

1. 安装APK文件
2. 授予Root权限
3. 打开应用，配置以下内容：
   - 添加100个用户ID（每行一个）
   - 选择目标APP
   - 设置循环次数
   - 调整延迟时间

### 开始自动化

1. 确保目标APP已安装并登录
2. 点击"保存配置"
3. 点击"开始100用户循环点赞"
4. 应用将自动执行搜索和点赞操作

### 紧急停止

- 按音量减键（-）可随时停止任务
- 或点击界面上的"停止"按钮

## 坐标配置

默认坐标基于1260x2800分辨率，如需适配其他分辨率：

1. 点击"应用目标分辨率"按钮
2. 或手动修改`config['coordinates']`中的坐标值

## 常见问题

### Q: 构建失败怎么办？
A: 检查GitHub Actions日志，常见原因：
- 依赖安装失败：重新触发构建
- 缓存问题：在Actions中清除缓存后重试

### Q: APK安装失败？
A: 
- 确保允许安装未知来源应用
- 卸载旧版本后重新安装
- 检查Android版本是否满足要求

### Q: 自动化操作失败？
A: 
- 确保已授予Root权限
- 检查目标APP是否已登录
- 使用测试功能验证各步骤

### Q: 如何修改为其他功能？
A: 
- 修改`main.py`中的相关方法
- 更新坐标配置
- 重新构建APK

## 注意事项

1. **合法使用**：请遵守相关平台的使用条款
2. **隐私保护**：不要分享包含个人信息的配置文件
3. **适度使用**：避免频繁操作导致账号异常
4. **测试优先**：使用测试功能验证配置正确性

## 更新日志

### v1.0.0
- 初始版本发布
- 支持搜索用户和点赞功能
- 支持多平台切换
- 音量键停止功能

## 许可证

本项目仅供学习和研究使用，请勿用于商业用途。

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

如有问题或建议，请通过GitHub Issues联系。
