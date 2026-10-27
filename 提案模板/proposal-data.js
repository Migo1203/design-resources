// 复制整个“提案模板”文件夹作为一个新项目，再编辑本文件。
// 所有图片、字体使用相对于 index.html 的本地路径；不要在本文件填写秘密或凭据。
window.PROPOSAL_DATA = {
  schemaVersion: "1.0",
  projectId: "待填写项目编号",
  title: "商业 KV · 创意方向比较",
  version: "模板 v0.1",
  status: "结构演示 · 待填写真实 Brief 与参考",
  scopeNote: "本页演示提案结构。三个方向尚未对应真实产品，也没有用户认可的参考图；不代表已完成提案、已看图分析或已选定方向。",
  brief: {
    product: "待填写：产品 / 品牌及资料入口",
    problem: "待填写：这次需要解决的商业问题",
    audience: "待填写：受众与使用情境；推测请标注假设",
    message: "待填写：希望观众记住的一件事",
    channel: "待填写：使用渠道、画幅与交付范围",
    facts: "待填写：有来源的产品事实、数值及条件",
    assumptions: "待填写：创意假设、待核实参数与研究缺口",
    constraints: "待填写：产品保真、品牌规则、素材与制作条件"
  },
  directions: [
    {
      id: "A", name: "关系与尺度", tag: "演示机制 01",
      concept: "结构演示：用产品与人物、日常物件或环境的关系，让一个产品利益变得可见。",
      rationale: "待结合 Brief 说明：为什么这组关系能回答受众疑问；没有产品事实支持时，不推断轻便、耐用或性能优势。",
      mechanism: "关系叙事：观众通过动作、尺度或使用关系理解主题，而非只读产品标题。",
      photography: "待定：写明产品角度、机位、主辅光、接触阴影及环境关系。演示线框采用偏侧产品和场景留白。",
      material: "待定：列真实产品材质与需要的环境质感，并说明它们如何支持这次主张。",
      typography: { family: "system-ui, sans-serif", role: "系统无衬线示意；用于测试信息层级，不是已采用字体。", file: "", fileFamily: "" },
      sample: "让产品与日常，发生关系。", bodySample: "辅助信息应补充事实、条件和证据，不能补造产品能力。",
      colors: [{ hex: "#EFEAE0", role: "演示背景" }, { hex: "#687D64", role: "演示主色" }, { hex: "#252E2B", role: "演示文字" }],
      layout: "relationship",
      references: [{ id: "REF-待填-A", title: "待放入用户选定的参考图", image: "", source: "", selectionStatus: "待确认", viewStatus: "未查看", viewedAt: "", viewScope: "", observation: "待实际看图：摄影、字体、构图、材质分别是什么？", commercialRole: "待说明：这些手法让受众理解、相信或记住什么？", borrow: "待填写：借鉴机制、调整方式与不沿用的品牌资产。" }],
      series: "待定：主视觉负责建立关系；第二张验证不同利益或使用情境。说明哪些识别规则固定、哪些画面关系变化。",
      gaps: "待补：真实产品资料、用户参考选择、可靠视角或补拍素材；确认合成与字体使用条件。",
      tradeoff: "待填写：相对其他方向的优势、代价，以及什么条件下应放弃。"
    },
    {
      id: "B", name: "结构与证据", tag: "演示机制 02",
      concept: "结构演示：以一个明确的视觉组织规则，把已确认的信息或细节转成可理解的证据。",
      rationale: "待结合 Brief 说明：受众需要理解什么，现有素材能支持哪种证明；没有内部结构资料时，不画虚构爆炸图。",
      mechanism: "证据组织：中心产品与细节、信息轨道或对照关系协作，重点在解释而不是装饰光圈。",
      photography: "待定：写明中心产品角度、细节拍摄、轮廓光与背景分离方式；演示线框不代表真实产品结构。",
      material: "待定：用可验证细节展示真实材质，区分实际结构、信息图形与抽象隐喻。",
      typography: { family: "system-ui, sans-serif", role: "系统无衬线示意；可比较紧凑信息层级，具体字体待选。", file: "", fileFamily: "" },
      sample: "把主张，变成看得懂的依据。", bodySample: "数值、条件和出处属于同一信息组；图形不能冒充测量或实验结果。",
      colors: [{ hex: "#E5E9F2", role: "演示背景" }, { hex: "#4D62B2", role: "演示强调" }, { hex: "#20283D", role: "演示文字" }],
      layout: "evidence",
      references: [{ id: "REF-待填-B", title: "待放入与机制有关的真实参考", image: "", source: "", selectionStatus: "待确认", viewStatus: "未查看", viewedAt: "", viewScope: "", observation: "待实际看图：产品与细节怎样建立信息关系？", commercialRole: "待说明：它解释了什么购买疑问，证据是否成立？", borrow: "待填写：借鉴结构，不照搬他人产品结构或专属资产。" }],
      series: "待定：一张建立主张，一张解释细节，第三张处理另一购买疑问；避免换标题仍能通用的重复图。",
      gaps: "待补：可靠参数与条件、真实细节图、允许公开的证据；没有的内容明确记为缺口。",
      tradeoff: "待填写：信息密度、素材要求、产品辨识与实现难点如何取舍。"
    },
    {
      id: "C", name: "隐喻与识别", tag: "演示机制 03",
      concept: "结构演示：让一个与产品利益相关的视觉隐喻或字形关系成为记忆点。",
      rationale: "待结合 Brief 说明：隐喻与主张有什么必然联系、受众是否读得懂，以及是否会被误认成真实功能。",
      mechanism: "概念隐喻：放大图形或文字与产品发生关系；阅读结构以记忆点为先，而非只更换色彩与字体。",
      photography: "待定：写明产品的清晰识别角度、抠图边缘、光影与图形的前后关系。",
      material: "待定：明确真实产品材质和图形示意的边界；不把金属、透明或光效随意改造成产品事实。",
      typography: { family: "serif", role: "系统衬线示意；仅演示文字主导结构，最终字形与许可待核实。", file: "", fileFamily: "" },
      sample: "一个有理由的记忆点。", bodySample: "创意设定属于表达，不等于产品承诺。文字与图形需要共同支持同一概念。",
      colors: [{ hex: "#F3E4D3", role: "演示背景" }, { hex: "#C25F3A", role: "演示强调" }, { hex: "#3D2F2A", role: "演示文字" }],
      layout: "metaphor",
      references: [{ id: "REF-待填-C", title: "待放入用户认可或否决的案例", image: "", source: "", selectionStatus: "待确认", viewStatus: "未查看", viewedAt: "", viewScope: "", observation: "待实际看图：图形、字体、产品之间的动作与前后关系。", commercialRole: "待说明：隐喻如何帮助记忆，同时保留产品识别？", borrow: "待填写：可借鉴的关系与不可照搬的角色、Logo或品牌资产。" }],
      series: "待定：用同一概念规则发展不同职责画面；品牌或IP系统需独立说明角色、识别规则与使用边界。",
      gaps: "待补：有效隐喻依据、品牌/IP资产权限、图形与字体制作能力；先验证核心关系。",
      tradeoff: "待填写：概念辨识度与可理解性、产品清晰度和执行成本之间的取舍。"
    }
  ]
};
