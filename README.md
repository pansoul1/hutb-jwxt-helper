# 🎓 湖南工商大学教务系统辅助工具

<div align="center">

![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)

</div>

<p align="center">为湖南工商大学（HUTB）学生开发的现代化教务系统辅助工具，提供更便捷的成绩查询与课表查询服务</p>

<div align="center">
  
<h2>🚀 立即体验 🚀</h2>

<a href="http://hutb.pansoul.xyz" target="_blank">
  <img src="https://img.shields.io/badge/点击访问-hutb.pansoul.xyz-blue?style=for-the-badge&logo=firefox&logoColor=white" alt="访问网站" width="300" />
</a>

<p>⭐ 自动验证码识别 | 📊 成绩可视化 | 📅 课表查询 ⭐</p>
  
</div>

---

## 📋 目录

- [主要功能](#-主要功能)
- [技术实现](#-技术实现)
- [数据模型](#-数据模型)
- [未来计划](#-未来计划)

---

## ✨ 主要功能

### 👨‍🎓 用户功能

| 功能 | 描述 |
| --- | --- |
| 🔐 **统一认证登录** | 支持教务系统的统一认证登录 |
| 📊 **成绩查询** | 查询各学期课程成绩，并计算平均绩点（GPA） |
| 📅 **课表查询** | 可视化课程表查询，支持表格视图和卡片视图 |
| 📱 **自适应界面** | 同时支持PC和移动端访问 |

### 👨‍💼 管理员功能

| 功能 | 描述 |
| --- | --- |
| 👥 **用户管理** | 查看和管理系统用户 |
| 📈 **数据统计** | 系统使用数据统计和分析 |
| 📉 **仪表盘** | 系统运行状态可视化展示 |

---

## 🛠 技术实现

### 🏗 后端架构

- 🌐 **Web框架**: 基于Flask构建的Web应用
- 💾 **数据库**: 使用MySQL存储用户数据和系统日志
- 🔄 **会话管理**: 支持Redis和文件系统两种会话存储方式
- 🔒 **权限控制**: 基于装饰器实现的管理员权限控制

### 🕷 爬虫模块

- 🔑 **登录模块**: 通过模拟浏览器行为实现教务系统统一认证
- 🧩 **验证码识别**: 使用Qwen-VL-Plus模型识别算术验证码
- 📝 **成绩爬取**: 针对学生成绩页面的数据爬取和解析
- 📋 **课表爬取**: 针对课程表页面的数据爬取和解析
- 🍪 **Cookie管理**: 保存用户会话状态，减少重复登录

### 🎨 前端实现

<div align="center">
<table>
  <tr>
    <td align="center">📱 <b>响应式设计</b></td>
    <td align="center">✨ <b>交互体验</b></td>
  </tr>
  <tr>
    <td>适配不同设备的界面布局</td>
    <td>现代化的界面设计和交互体验</td>
  </tr>
  <tr>
    <td align="center">📊 <b>数据可视化</b></td>
    <td align="center">🔄 <b>多视图支持</b></td>
  </tr>
  <tr>
    <td>成绩和课表的可视化展示</td>
    <td>课表支持表格和卡片两种查看模式</td>
  </tr>
</table>
</div>

### 🔐 安全机制

> 🛡️ **系统采用多层次安全保障措施**

- 🔒 **会话保护**: 基于设备ID和用户名的会话验证机制
- 🔑 **密码安全**: 不存储明文密码，使用加密方式存储
- 🚫 **权限控制**: 严格的用户权限控制，防止未授权访问

---

## 📊 数据模型

<div align="center">

### 核心数据表

| 表名 | 用途 |
|-----|------|
| **users** | 存储用户信息、凭证和Cookies |
| **admin_users** | 存储管理员账户信息 |
| **user_login_logs** | 记录用户登录活动 |
| **system_usage_logs** | 记录系统使用情况 |
| **system_stats** | 存储系统统计数据 |

</div>

---

## 🚀 未来计划

<div align="center">

### 即将推出的功能

| 计划功能 | 状态 |
|---------|------|
| 🔔 **消息通知系统** | 开发中 |
| 📋 **一键教评** | 构思中 |

</div>

> 💡 **敬请期待更多功能的开发与上线！**
> 
> 我们正在不断优化和扩展系统功能，为湖南工商大学的师生提供更加智能、便捷的教务系统体验。

---

<div align="center">
<p>🏫 湖南工商大学教务系统助手</p>
<p>
  <a href="http://hutb.pansoul.xyz" target="_blank">📍 立即体验: hutb.pansoul.xyz</a>
</p>
</div> 