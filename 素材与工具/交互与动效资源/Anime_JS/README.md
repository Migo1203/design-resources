# Anime.js动画引擎

2026-11-14入库。作者：Julian Garnier；来源版本：4.5.0。**候选／未采用**。

![桌面实际采样](桌面预览.png)

[手机预览](手机预览.png) · [实际运行演示](../管理资料/交互演示.html)

## 原件与用途

保存Anime.js 4.5.0官方`dist/bundles/anime.umd.min.js`，外部名称为[动画引擎.umd.min.js](原件/动画引擎.umd.min.js)，118,043字节。它通过script标签提供全局`anime`，本例无需构建或npm依赖。

只下载此UMD版本及MIT声明，没有重复保存ESM／CJS、多种精简包、sourcemap、文档示例或第三方作品。原件内部版本、版权注释和内容未改，许可证与文件中的版权年份均原样保留。

## 本库时间线示例与实际检查

用官方`createTimeline()`与`add()`执行三项顺序入场，并检查`pause()`、`seek()`、`cancel()`。布局、文字、12px位移、320ms单项时长、110ms间隔及控制按钮均为本库验证参数，不是Migo正式动效规范。

初始全部内容静态可见；手动播放才初始化入场状态。已实际采样运动中的时间与透明度、暂停后时间不前进、单次完成后全部可读、重置恢复静态内容。PNG固定在200ms，只是中间状态，不是完整动画录像或最终页面。

减少动效判断由本库演示层负责：系统reduce或页面关闭开关生效时不创建新时间线；运行中变更会取消当前动画并显示全部内容。恢复普通模式后不自动播放。未验证该引擎的所有API、滚动动画、复杂SVG或真实网站性能。

可以研究顺序、取消与状态恢复，不必为简单hover或单个属性过渡引入完整引擎；实际网站采用时应按需求比较原生能力和按需导入。

[官方源码](https://github.com/juliangarnier/anime) · [官方安装文档](https://animejs.com/documentation/getting-started/installation/)

## 来源与完整性

[固定提交](https://github.com/juliangarnier/anime/tree/01b81be1df6843ccfe0a71c0699a746bf740dd77)：`01b81be1df6843ccfe0a71c0699a746bf740dd77`。原件按官方Git blob和本地SHA256校验，原路径与下载URL见[统一清单](../../素材清单.json)。

[源码许可证完整原文](源码许可证.txt)来自[同一官方提交](https://github.com/juliangarnier/anime/blob/01b81be1df6843ccfe0a71c0699a746bf740dd77/LICENSE.md)；使用／再分发时保留适用版权和许可，不用仓库根MIT替换它。原件仅外部中文命名，内容未改。

[集中检查记录](../管理资料/动效检查记录.json) · [返回交互与动效目录](../README.md)
