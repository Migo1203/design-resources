"use strict";
(() => {
  const data = window.PROPOSAL_DATA;
  if (!data || !Array.isArray(data.directions) || data.directions.length !== 3) {
    document.getElementById("scope-note").textContent = "数据无法读取：请检查 proposal-data.js，directions 应包含三个方向。";
    return;
  }
  const el = (tag, text, className) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = String(text);
    if (className) node.className = className;
    return node;
  };
  const str = value => value === undefined || value === null || value === "" ? "待填写" : String(value);
  const safeColor = value => /^#[0-9a-f]{6}$/i.test(String(value)) ? value : "#D8DBD4";
  const localPath = value => {
    const path = String(value || "").trim();
    return path && !/^(?:[a-z][a-z0-9+.-]*:|\/\/|\\|\/)/i.test(path) ? path : null;
  };
  const externalUrl = value => {
    try { const url = new URL(value); return /^(https?:)$/.test(url.protocol) ? url.href : null; }
    catch { return null; }
  };
  const field = (title, value) => { const box = el("div", undefined, "field"); box.append(el("span", title, "label"), el("p", str(value))); return box; };
  const svgNS = "http://www.w3.org/2000/svg";
  const svgNode = (name, attributes, text) => {
    const node = document.createElementNS(svgNS, name);
    for (const [key, value] of Object.entries(attributes || {})) node.setAttribute(key, String(value));
    if (text !== undefined) node.textContent = text;
    return node;
  };
  function wireframe(kind, colors) {
    const accent = safeColor(colors[1]?.hex), dark = safeColor(colors[2]?.hex);
    const svg = svgNode("svg", {viewBox:"0 0 480 360", class:"wireframe", role:"img", "aria-label":"构图线框示意：" + kind});
    svg.append(svgNode("rect", {x:0,y:0,width:480,height:360,fill:safeColor(colors[0]?.hex)}));
    const line = (x1,y1,x2,y2) => svg.append(svgNode("line", {x1,y1,x2,y2,stroke:dark,"stroke-width":1.5,opacity:.5}));
    const rect = (x,y,w,h,fill,stroke,rx=0) => svg.append(svgNode("rect",{x,y,width:w,height:h,fill,stroke:stroke||"none",rx}));
    const text = (x,y,t,size=14) => svg.append(svgNode("text",{x,y,fill:dark,"font-family":"system-ui, sans-serif","font-size":size},t));
    if (kind === "relationship") {
      line(28,270,452,270); rect(272,176,112,94,accent,undefined,8); rect(70,235,140,35,"none",dark,3);
      svg.append(svgNode("path",{d:"M211 230 Q226 174 273 199",fill:"none",stroke:dark,"stroke-width":2,"stroke-dasharray":"5 5"}));
      text(32,56,"主题标题 / 留白",23); text(32,86,"用动作、尺度或环境关系支持主张",13); text(294,221,"产品",18); text(85,256,"尺度 / 情境物",12); text(30,316,"场景关系主导 · 信息作为补充",12);
    } else if (kind === "evidence") {
      rect(184,122,112,144,accent,undefined,8); text(220,199,"产品",18); text(32,48,"一个主张 + 明确信息关系",22);
      rect(30,110,110,58,"none",dark,3); text(44,143,"证据 / 细节",13); line(140,139,184,161);
      rect(338,202,112,58,"none",dark,3); text(351,235,"事实 + 条件",13); line(296,223,338,231);
      line(32,303,448,303); text(32,328,"信息轨道与细节服务理解，不虚构结构",12);
    } else {
      text(28,91,"概念 / 记忆点",36); svg.append(svgNode("circle",{cx:205,cy:218,r:92,fill:"none",stroke:accent,"stroke-width":26}));
      rect(267,174,112,100,accent,dark,6); text(292,230,"产品",18); line(32,320,448,320);
      text(32,346,"图形与产品建立有理由的前后关系",12); text(80,222,"隐喻图形",15);
    }
    return svg;
  }
  function referenceCard(ref) {
    const card = el("article", undefined, "reference");
    const title = el("div", undefined, "ref-title"); title.append(el("strong", str(ref.title)), el("span", str(ref.id), "meta"));
    const visual = el("div", undefined, "reference-visual");
    const selectionStatus = el("span", "用户态度：" + str(ref.selectionStatus || "待确认"), "badge");
    const viewStatus = el("span", "看图状态：" + str(ref.viewStatus || "未查看"), "badge");
    const loadStatus = el("span", "本页尚未提供图片", "badge");
    const path = localPath(ref.image);
    if (path) {
      const img = el("img"); img.alt = str(ref.title); img.loading = "lazy";
      loadStatus.textContent = "本页图片加载中";
      img.addEventListener("error", () => { visual.replaceChildren(el("span", "图片无法读取：请核对相对路径；本页无法提供图片供复核。")); loadStatus.textContent = "本页缺图"; });
      img.addEventListener("load", () => { loadStatus.textContent = "本页图片已载入"; });
      img.src = path; visual.append(img);
    } else {
      visual.append(el("span", undefined, "missing-symbol"), el("span", "尚未放入参考图片"), el("span", "填入本地相对路径后显示；不能据此声称已看图。", "caption"));
      if (ref.image) loadStatus.textContent = "图片路径不受支持 · 请使用本地相对路径";
    }
    const metadata = el("div", undefined, "reference-meta"); metadata.append(selectionStatus, viewStatus, loadStatus);
    if (ref.viewedAt || ref.viewScope) metadata.append(el("span", "看图记录：" + str(ref.viewedAt) + " / " + str(ref.viewScope), "small"));
    const url = externalUrl(ref.source);
    if (url) { const link = el("a", "查看来源（外部网站）", "small"); link.href=url; link.target="_blank"; link.rel="noopener noreferrer"; metadata.append(link); }
    card.append(title,visual,metadata,field("看见了什么 / 可核对观察",ref.observation),field("商业作用 / 与目标的关系",ref.commercialRole),field("借鉴机制与不沿用内容",ref.borrow));
    return card;
  }
  const controls = [];
  document.title = str(data.title);
  document.getElementById("project-title").textContent = str(data.title);
  document.getElementById("project-status").textContent = str(data.status);
  document.getElementById("project-version").textContent = str(data.version) + " · " + str(data.projectId);
  document.getElementById("scope-note").textContent = str(data.scopeNote);
  const briefLabels = {product:"产品 / 品牌",problem:"商业问题",audience:"受众与情境",message:"核心信息",channel:"渠道与交付",facts:"已确认事实",assumptions:"假设与待确认",constraints:"限制与制作条件"};
  for (const [key,label] of Object.entries(briefLabels)) { const box=el("div",undefined,"brief-item");box.append(el("span",label,"label"),el("p",str(data.brief?.[key])));document.getElementById("brief-grid").append(box); }
  const table = document.getElementById("comparison-table"), head=el("thead"), heading=el("tr"); heading.append(el("th","比较项"));
  for (const direction of data.directions) heading.append(el("th",str(direction.id)+" / "+str(direction.name)));
  head.append(heading);table.append(head); const tbody=el("tbody");
  for (const [label,key] of [["核心概念","concept"],["创意机制","mechanism"],["适配理由","rationale"],["执行取舍","tradeoff"]]) { const row=el("tr");const th=el("th",label);th.scope="row";row.append(th);for(const d of data.directions)row.append(el("td",str(d[key])));tbody.append(row); }
  table.append(tbody);
  data.directions.forEach((d,index) => {
    const colors=Array.isArray(d.colors)&&d.colors.length ? d.colors : [{hex:"#EEEEEE"},{hex:"#687D64"},{hex:"#24282C"}];
    const card=el("article",undefined,"direction");card.id="direction-"+index;card.style.setProperty("--tone",safeColor(colors[0]?.hex));card.style.setProperty("--tone-ink",safeColor(colors[2]?.hex));
    const header=el("header",undefined,"direction-header"), title=el("div",undefined,"direction-title"), titleWords=el("div");titleWords.append(el("span",str(d.tag),"direction-tag"),el("h2",str(d.name)));title.append(el("span",str(d.id),"letter"),titleWords);const decisionBadge=el("span","方向待评审","badge");header.append(title,decisionBadge);
    const body=el("div",undefined,"direction-body");body.append(el("p",str(d.concept),"concept"));const strategy=el("div",undefined,"two-col");strategy.append(field("为什么适合这个 Brief",d.rationale),field("创意机制 / 实质差异",d.mechanism));body.append(strategy);
    const visuals=el("div",undefined,"visual-grid"), layout=el("div",undefined,"panel"), art=el("div",undefined,"panel");layout.append(el("h3","构图线框"),wireframe(d.layout,colors),el("p","结构演示，不是效果图；图形不代表真实产品结构。真实任务需重写构图。","caption"));
    art.append(el("h3","色彩与字体样张"));const swatches=el("div",undefined,"swatches");for(const color of colors){const swatch=el("div",undefined,"swatch"),patch=el("div",undefined,"swatch-color");patch.style.backgroundColor=safeColor(color.hex);swatch.append(patch,el("code",safeColor(color.hex)),el("span",str(color.role)));swatches.append(swatch);}art.append(swatches);
    const sample=el("div",str(d.sample),"font-sample"),sampleBody=el("div",str(d.bodySample),"font-body"),fontStatus=el("p","未指定独立字库：当前为系统字体示意，实际字形取决于此设备；不是已确定或已授权的最终字体。","font-status");
    const family=String(d.typography?.family||"system-ui, sans-serif");sample.style.fontFamily=family;sampleBody.style.fontFamily=family;art.append(sample,sampleBody,el("p",str(d.typography?.role),"small"),el("p","CSS 候选栈："+family,"caption"),fontStatus);
    const fontFile=localPath(d.typography?.file),fontName=String(d.typography?.fileFamily||"").trim();
    if (fontFile&&fontName&&window.FontFace) {
      try {
        const face=new FontFace(fontName,"url("+JSON.stringify(fontFile)+")");fontStatus.textContent="正在加载指定本地字库；未完成前使用系统回退。";
        face.load().then(loaded=>{document.fonts.add(loaded);sample.style.fontFamily=JSON.stringify(fontName)+", "+family;sampleBody.style.fontFamily=JSON.stringify(fontName)+", "+family;fontStatus.textContent="本地字库加载成功："+fontName+"（"+fontFile+"）。请另核对中文字符覆盖与许可；缺字仍可能回退。";}).catch(()=>{fontStatus.textContent="指定字库加载失败：继续显示系统回退示意，不能作为最终字体确认。";});
      } catch {fontStatus.textContent="指定字库配置无效：继续显示系统回退示意。";}
    } else if (d.typography?.file) fontStatus.textContent="字库配置未生效：需本地相对路径和 fileFamily；当前仍为系统回退示意。";
    visuals.append(layout,art);body.append(visuals);const artFields=el("div",undefined,"two-col");artFields.append(field("摄影 / 光线与产品视角",d.photography),field("材质 / 字体与商业作用",d.material));body.append(artFields);
    const refs=el("section",undefined,"references");refs.append(el("h3","参考图与实际拆解"),el("p","图片载入只表示浏览器显示成功，不表示 AI 已实际查看或用户已认可。先在审美参考包记录来源、用户态度和真实看图记录。","small"));
    const references=Array.isArray(d.references)&&d.references.length?d.references:[{title:"未提供参考",selectionStatus:"待确认",viewStatus:"未查看"}];references.forEach(ref=>refs.append(referenceCard(ref)));body.append(refs);
    const execution=el("div",undefined,"two-col");execution.append(field("系列延展 / 固定规则与变化",d.series),field("素材缺口 / 实现条件",d.gaps));body.append(execution,field("推荐与取舍依据",d.tradeoff));
    const review=el("section",undefined,"review");review.append(el("h3","这个方向，保留什么？改变什么？"),el("p","记录这次选择的具体理由；请区分审美偏好、事实错误、商业目标与制作限制。","small"));const reviewControls=el("div",undefined,"review-controls"),choiceBox=el("div"),reasonBox=el("div"),choiceLabel=el("label","评审选择"),select=el("select"),reasonLabel=el("label","选择理由与修改位置"),reason=el("textarea");select.id="choice-"+index;reason.id="reason-"+index;choiceLabel.htmlFor=select.id;reasonLabel.htmlFor=reason.id;
    select.addEventListener("change",()=>{decisionBadge.textContent=select.value==="待评审"?"方向待评审":"本轮评审："+select.value;});
    for(const choice of ["待评审","选中","修改后继续","否决","暂缓"]) {const option=el("option",choice);option.value=choice;select.append(option);}reason.placeholder="例如：保留哪种关系；哪处摄影、字形、材质或构图不合适；为什么；下一版怎样改。";choiceBox.append(choiceLabel,select);reasonBox.append(reasonLabel,reason);reviewControls.append(choiceBox,reasonBox);review.append(reviewControls);body.append(review);controls.push({id:str(d.id),name:str(d.name),choice:select,reason});card.append(header,body);document.getElementById("directions").append(card);
  });
  window.addEventListener("beforeprint",()=>{
    document.querySelectorAll(".printed-value").forEach(node=>node.remove());
    document.querySelectorAll("input,textarea,select").forEach(control=>{
      const value=el("div",control.value.trim()||"未填写","printed-value");
      control.insertAdjacentElement("afterend",value);
    });
  });
  window.addEventListener("afterprint",()=>document.querySelectorAll(".printed-value").forEach(node=>node.remove()));
  document.getElementById("print-button").addEventListener("click",()=>window.print());
  document.getElementById("export-button").addEventListener("click",()=>{
    const message=document.getElementById("export-message"), reviews=controls.map(c=>({directionId:c.id,directionName:c.name,decision:c.choice.value,reason:c.reason.value.trim()}));
    const missing=reviews.find(r=>r.decision!=="待评审"&&!r.reason);
    if(missing){message.textContent="请为方向 "+missing.directionId+" 补充选择理由，再导出。";controls.find(c=>c.id===missing.directionId).reason.focus();return;}
    const record={schemaVersion:"1.0",projectId:str(data.projectId),proposalVersion:str(data.version),proposalStatus:str(data.status),exportedAt:new Date().toISOString(),reviewer:document.getElementById("reviewer").value.trim()||"未填写",overallComment:document.getElementById("overall-comment").value.trim(),reviews,scope:"仅记录本轮选择；未自动更新参考认可状态或长期偏好，也未修改Skill。"};
    const blob=new Blob([JSON.stringify(record,null,2)+"\n"],{type:"application/json;charset=utf-8"}),url=URL.createObjectURL(blob),link=el("a");link.href=url;link.download="提案评审-"+new Date().toISOString().slice(0,10)+".json";document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);message.textContent="已发起 JSON 下载；请确认文件已保存并归档。页面不会自动写入仓库。";
  });
})();
