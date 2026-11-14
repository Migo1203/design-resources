# Open Props缓动变量

2026-11-14入库。作者：Adam Argyle；来源版本：1.7.23。**候选／未采用**。

![桌面实际采样](桌面预览.png)

[手机预览](手机预览.png) · [实际运行演示](../管理资料/交互演示.html)

## 原件与用途

保存Open Props官方`src/props.easing.css`，外部名称为[缓动变量.css](原件/缓动变量.css)，6,415字节。版本1.7.23，作者Adam Argyle。

它是一组CSS自定义属性，包含cubic-bezier、steps与linear等缓动表达式；不是完整动效组件或整套Open Props样式。此文件无外部导入，未下载依赖其他预处理文件的完整动画预设或其他设计token。

本库演示将`--ease-out-3`用于240ms状态过渡；按钮、反馈卡片、状态文案、颜色和时长为本库编写。实际检查该变量被浏览器解析并应用到过渡，Enter切换后transform发生变化；未逐个认证全部曲线。

## 减少动效与采用限制

缓动变量本身不会自动启动或禁止动画。本库通过媒体查询与页面开关，在减少动效时取消过渡和位移，同时保留即时状态反馈；不要把适配逻辑归为源库自动完成。

可以学习“将缓动参数独立管理”的方法，不应为了使用变量给每个元素添加动画。高级linear曲线在目标浏览器的支持仍应另测；本批只在Chromium验证所选样例。

[官方源码](https://github.com/argyleink/open-props) · [官方站点](https://open-props.style/)

## 来源与完整性

[固定提交](https://github.com/argyleink/open-props/tree/f39ab7c377a0e047f930982e3611bbc95254a260)：`f39ab7c377a0e047f930982e3611bbc95254a260`。原件按官方Git blob和本地SHA256校验，原路径与下载URL见[统一清单](../../素材清单.json)。

[源码许可证完整原文](源码许可证.txt)来自[同一官方提交](https://github.com/argyleink/open-props/blob/f39ab7c377a0e047f930982e3611bbc95254a260/LICENSE)；使用／再分发时保留适用版权和许可，不用仓库根MIT替换它。原件仅外部中文命名，内容未改。

[集中检查记录](../管理资料/动效检查记录.json) · [返回交互与动效目录](../README.md)
