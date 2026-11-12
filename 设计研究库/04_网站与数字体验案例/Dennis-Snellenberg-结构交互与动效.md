---
标题: Dennis Snellenberg｜结构、交互与动效
研究类型: 网站案例
研究状态: 待补充
创建日期: '2026-11-12'
更新日期: '2026-11-12'
标签:
- 领域/UI设计
- 领域/UX设计
- 方法/信息层级
- 项目/个人网站
- 领域/字体排版
关联项目:
- 个人网站
原研究日期: '2026-11-11'
来源仓库: Migo1203/migo-portfolio
来源提交: c1b787c4100443761ed63cb142f9df75f480970b
原始文档:
- https://github.com/Migo1203/migo-portfolio/blob/c1b787c4100443761ed63cb142f9df75f480970b/UI%E8%AE%BE%E8%AE%A1/%E6%A1%88%E4%BE%8B%E6%8B%86%E8%A7%A3/%E4%B8%B9%E5%B0%BC%E6%96%AF%E4%B8%AA%E4%BA%BA%E7%BD%91%E7%AB%99%E6%8B%86%E8%A7%A3.md
- https://github.com/Migo1203/migo-portfolio/blob/c1b787c4100443761ed63cb142f9df75f480970b/UI%E8%AE%BE%E8%AE%A1/%E6%A1%88%E4%BE%8B%E6%8B%86%E8%A7%A3/%E4%B8%B9%E5%B0%BC%E6%96%AF%E7%BD%91%E7%AB%99%E4%BA%A4%E4%BA%92%E4%B8%8E%E5%8A%A8%E6%95%88%E6%8B%86%E8%A7%A3.md
- https://github.com/Migo1203/migo-portfolio/blob/c1b787c4100443761ed63cb142f9df75f480970b/UI%E8%AE%BE%E8%AE%A1/%E4%B8%AA%E4%BA%BA%E7%BD%91%E7%AB%99%E6%A1%88%E4%BE%8B%E8%B5%84%E6%96%99%E5%BA%93.md
---

# Dennis Snellenberg｜结构、交互与动效

## 研究目的

把同一网站的静态结构与后续交互补查合成主档，保留不同采集阶段的限制。

这是对已有项目研究的归纳归档。原始讲解、完整截图与反馈历史保留在来源仓库，本库维护一份可检索主记录。以下事实／观察均注明继承范围；分析和建议不视为用户认可。

## 核心结论

1. 静态研究已检查首页、作品、The Damai案例的桌面／手机首屏，项目职责与合作者先于成果呈现。
2. 后续动作记录实际触发导航磁吸、作品跟随与切换、离开恢复、手机菜单、项目过渡及首页加载遮罩。
3. 实际触发、源码可确认和未验证三类证据必须分开；GSAP等实现线索不代表所有动画、性能或无障碍已测。
4. 最初“无加载遮罩”的判断已由后续观察更正；未完整记录多语言文字序列，不凭用户印象补造精确时序。

## 案例证据与历史查看范围

原静态记录1440×1000、390×844首屏；动作研究含12张截图与JSON状态、transform及原始异常。HTTPS经环境CA验证的响应渲染，部分请求屏蔽，因此不代表原生加载性能。本轮只读原研究，不重新操作网站。

## 案例图片与网站链接

[![原研究：首页桌面首屏](https://raw.githubusercontent.com/Migo1203/migo-portfolio/c1b787c4100443761ed63cb142f9df75f480970b/UI%E8%AE%BE%E8%AE%A1/%E7%A0%94%E7%A9%B6%E8%AE%B0%E5%BD%95/%E5%8F%82%E8%80%83%E6%88%AA%E5%9B%BE/%E4%B8%B9%E5%B0%BC%E6%96%AF_%E9%A6%96%E9%A1%B5_%E6%A1%8C%E9%9D%A2.png)](https://github.com/Migo1203/migo-portfolio/blob/c1b787c4100443761ed63cb142f9df75f480970b/UI%E8%AE%BE%E8%AE%A1/%E7%A0%94%E7%A9%B6%E8%AE%B0%E5%BD%95/%E5%8F%82%E8%80%83%E6%88%AA%E5%9B%BE/%E4%B8%B9%E5%B0%BC%E6%96%AF_%E9%A6%96%E9%A1%B5_%E6%A1%8C%E9%9D%A2.png)

原研究：首页桌面首屏。[图片来源／原图](https://github.com/Migo1203/migo-portfolio/blob/c1b787c4100443761ed63cb142f9df75f480970b/UI%E8%AE%BE%E8%AE%A1/%E7%A0%94%E7%A9%B6%E8%AE%B0%E5%BD%95/%E5%8F%82%E8%80%83%E6%88%AA%E5%9B%BE/%E4%B8%B9%E5%B0%BC%E6%96%AF_%E9%A6%96%E9%A1%B5_%E6%A1%8C%E9%9D%A2.png)。固定提交中的历史截图，不代表网站当前状态。

[![原研究：案例手机首屏](https://raw.githubusercontent.com/Migo1203/migo-portfolio/c1b787c4100443761ed63cb142f9df75f480970b/UI%E8%AE%BE%E8%AE%A1/%E7%A0%94%E7%A9%B6%E8%AE%B0%E5%BD%95/%E5%8F%82%E8%80%83%E6%88%AA%E5%9B%BE/%E4%B8%B9%E5%B0%BC%E6%96%AF_%E6%A1%88%E4%BE%8B_%E6%89%8B%E6%9C%BA.png)](https://github.com/Migo1203/migo-portfolio/blob/c1b787c4100443761ed63cb142f9df75f480970b/UI%E8%AE%BE%E8%AE%A1/%E7%A0%94%E7%A9%B6%E8%AE%B0%E5%BD%95/%E5%8F%82%E8%80%83%E6%88%AA%E5%9B%BE/%E4%B8%B9%E5%B0%BC%E6%96%AF_%E6%A1%88%E4%BE%8B_%E6%89%8B%E6%9C%BA.png)

原研究：案例手机首屏。[图片来源／原图](https://github.com/Migo1203/migo-portfolio/blob/c1b787c4100443761ed63cb142f9df75f480970b/UI%E8%AE%BE%E8%AE%A1/%E7%A0%94%E7%A9%B6%E8%AE%B0%E5%BD%95/%E5%8F%82%E8%80%83%E6%88%AA%E5%9B%BE/%E4%B8%B9%E5%B0%BC%E6%96%AF_%E6%A1%88%E4%BE%8B_%E6%89%8B%E6%9C%BA.png)。固定提交中的历史截图，不代表网站当前状态。

[![原研究：手机菜单展开状态](https://raw.githubusercontent.com/Migo1203/migo-portfolio/c1b787c4100443761ed63cb142f9df75f480970b/UI%E8%AE%BE%E8%AE%A1/%E7%A0%94%E7%A9%B6%E8%AE%B0%E5%BD%95/%E4%B8%B9%E5%B0%BC%E6%96%AF%E4%BA%A4%E4%BA%92%E6%88%AA%E5%9B%BE/09_%E6%89%8B%E6%9C%BA%E8%8F%9C%E5%8D%95%E5%B1%95%E5%BC%80.png)](https://github.com/Migo1203/migo-portfolio/blob/c1b787c4100443761ed63cb142f9df75f480970b/UI%E8%AE%BE%E8%AE%A1/%E7%A0%94%E7%A9%B6%E8%AE%B0%E5%BD%95/%E4%B8%B9%E5%B0%BC%E6%96%AF%E4%BA%A4%E4%BA%92%E6%88%AA%E5%9B%BE/09_%E6%89%8B%E6%9C%BA%E8%8F%9C%E5%8D%95%E5%B1%95%E5%BC%80.png)

原研究：手机菜单展开状态。[图片来源／原图](https://github.com/Migo1203/migo-portfolio/blob/c1b787c4100443761ed63cb142f9df75f480970b/UI%E8%AE%BE%E8%AE%A1/%E7%A0%94%E7%A9%B6%E8%AE%B0%E5%BD%95/%E4%B8%B9%E5%B0%BC%E6%96%AF%E4%BA%A4%E4%BA%92%E6%88%AA%E5%9B%BE/09_%E6%89%8B%E6%9C%BA%E8%8F%9C%E5%8D%95%E5%B1%95%E5%BC%80.png)。固定提交中的历史截图，不代表网站当前状态。

相关网站：[首页](https://www.dennissnellenberg.com/) · [作品](https://www.dennissnellenberg.com/work) · [The Damai](https://www.dennissnellenberg.com/work/the-damai) · [公开脚本](https://www.dennissnellenberg.com/assets/js/index-new.js)。

图片属于原作者／相应权利人；仅作有出处的学习引用，不登记为Migo可复用品牌资产。归档保留访问日期，图片可用性不等于素材授权或当前页面未变化。

## 设计分析

下表是对原记录的归纳；未取得的资料保持待补充，不用常识补造作者意图或完整系统。

| 维度 | 证据、分析与边界 |
| --- | --- |
| 信息架构 | 首页认识作者→作品选择→详情职责和成果→关于／联系；是分析路径，没有转化实测。 |
| 页面布局 | 原截图记录大幅人像与姓名、作品列表、详情服务与署名；Migo可提前露出作品，不照搬人像首屏。 |
| 字体色彩 | 原记录以尺度、分隔、留白和蓝色入口建立层级；未核完整字库许可和标准色，不猜具体参数。 |
| 交互 | 进入项目行→显示→跟随→换图→离开收起→点击详情；手机菜单有展开和关闭实测。 |
| 动效证据 | 磁吸与页面遮罩实测为局部；姓名循环、滚动联动部分来自源码，不能统称实测通过。 |
| 响应式 | 桌面与手机模拟视口分开看；未做真实设备与全部触控路径。 |
| 用户体验 | 作品名称与实际贡献应可直接找到；磁吸、浮动预览和等待不能成为唯一入口；键盘／读屏／减少动效整体验证缺失。 |

## 学习价值与不照搬部分

先设计可逆的状态与普通浏览路径，再增加轻量反馈；作品图与关键信息不能只在hover出现。保留内容结构与职责方法，不复制源码、曲面遮罩、人像、蓝色按钮或精确动效参数。

## 关联项目与采用记录

关联项目：个人网站。

网站已有第三版审阅稿与动效清单，但本轮未逐项核对其对应实现，不自动把所有Dennis方法标成采用或已应用验证。

## 资料来源

访问日期须结合范围阅读：C编号是本轮实际读取的内部历史记录，不是权威第三方；A编号沿用原研究的外站访问日期，本轮未重做外站核验。原网站正文不可访问、未看图和来源不完整的限制不因归档消失。

| 编号 | 来源名称与原始链接 | 访问日期 | 可信度 | 核验范围与限制 |
| --- | --- | --- | --- | --- |
| C1 | [原研究：丹尼斯个人网站拆解](https://github.com/Migo1203/migo-portfolio/blob/c1b787c4100443761ed63cb142f9df75f480970b/UI%E8%AE%BE%E8%AE%A1/%E6%A1%88%E4%BE%8B%E6%8B%86%E8%A7%A3/%E4%B8%B9%E5%B0%BC%E6%96%AF%E4%B8%AA%E4%BA%BA%E7%BD%91%E7%AB%99%E6%8B%86%E8%A7%A3.md) | 2026-11-12 | C类·项目内部历史研究 | 本轮已读固定提交中的文档；原研究日期2026-11-11，不是独立外部事实证明 |
| C2 | [原研究：丹尼斯网站交互与动效拆解](https://github.com/Migo1203/migo-portfolio/blob/c1b787c4100443761ed63cb142f9df75f480970b/UI%E8%AE%BE%E8%AE%A1/%E6%A1%88%E4%BE%8B%E6%8B%86%E8%A7%A3/%E4%B8%B9%E5%B0%BC%E6%96%AF%E7%BD%91%E7%AB%99%E4%BA%A4%E4%BA%92%E4%B8%8E%E5%8A%A8%E6%95%88%E6%8B%86%E8%A7%A3.md) | 2026-11-12 | C类·项目内部历史研究 | 本轮已读固定提交中的文档；原研究日期2026-11-11，不是独立外部事实证明 |
| C3 | [原研究：个人网站案例资料库](https://github.com/Migo1203/migo-portfolio/blob/c1b787c4100443761ed63cb142f9df75f480970b/UI%E8%AE%BE%E8%AE%A1/%E4%B8%AA%E4%BA%BA%E7%BD%91%E7%AB%99%E6%A1%88%E4%BE%8B%E8%B5%84%E6%96%99%E5%BA%93.md) | 2026-11-12 | C类·项目内部历史研究 | 本轮已读固定提交中的文档；原研究日期2026-11-11，不是独立外部事实证明 |
| A1 | [首页](https://www.dennissnellenberg.com/) | 2026-11-11 | A类·原始机构／作者入口 | 原研究桌面／手机与局部进入状态；日期继承原研究，不是本轮重新访问 |
| A2 | [作品](https://www.dennissnellenberg.com/work) | 2026-11-11 | A类·原始机构／作者入口 | 原研究悬停、预览切换与点击；日期继承原研究，不是本轮重新访问 |
| A3 | [The Damai](https://www.dennissnellenberg.com/work/the-damai) | 2026-11-11 | A类·原始机构／作者入口 | 原研究详情与页面切换；日期继承原研究，不是本轮重新访问 |
| A4 | [公开脚本](https://www.dennissnellenberg.com/assets/js/index-new.js) | 2026-11-11 | A类·原始机构／作者入口 | 原研究源码核对；仅链接，不复制代码；日期继承原研究，不是本轮重新访问 |

## 研究记录与待补充

首页全部作品悬停、桌面菜单、所有滚动联动、真机、性能、键盘和减少动效尚未完整测量。Migo的开场文案和实现决策仍在网站项目维护。

- 2026-11-12：按GitHub `migo-portfolio` 的 `c1b787c` 归档，保留原研究日期和前后范围更正；研究状态为“待补充”。
- 本轮完成归档不等于研究已完成；未新增用户认可，不改品牌定义、设计源文件或网站实现。未来新研究优先更新本库主档，项目保留实际采用、版本与反馈。

[研究总索引](../研究模板与索引/研究总索引.md) · [跨仓库归档记录](../研究模板与索引/跨仓库案例归档记录.md)
