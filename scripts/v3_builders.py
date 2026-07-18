from reportlab.platypus import Paragraph
def T(t, max_len=3000):
    """Safe text helper - returns clean, truncated text or empty string."""
    if t is None: return ""
    if isinstance(t, str): return t.strip()[:max_len]
    if isinstance(t, (int, float, bool)): return str(t)
    return str(t)[:max_len]
    return ""

def sec_km(da,S):
    km=da.get("knowledge_map",{});els=[]
    if not km:return els
    els+=[Paragraph("<b>一、知识地图：读懂本文需要什么基础</b>",S["subsection"])]
    for c in km.get("prerequisite_concepts",[]):
        if not isinstance(c,dict):continue
        cn,en=T(c.get("term_cn","")),T(c.get("term_en",""))
        expl,why=T(c.get("explanation","")),T(c.get("why_needed",""))
        t="<b>"+cn+"</b>"+(" ("+en+")" if en else "")
        els+=[Paragraph("- "+t,S["bullet_bold"])]
        if expl:els+=[Paragraph("  "+expl,S["small"])]
        if why:els+=[Paragraph("  <b>为何需要：</b> "+why,S["small"])]
    for c in km.get("new_concepts_introduced",[]):
        if not isinstance(c,dict):continue
        cn,en=T(c.get("term_cn","")),T(c.get("term_en",""))
        defin=T(c.get("definition",""));intu=T(c.get("intuition",""))
        els+=[Paragraph("- <b>"+cn+"</b>"+(" ("+en+")" if en else ""),S["bullet_bold"])]
        if defin:els+=[Paragraph("  <b>定义：</b> "+defin,S["small"])]
        if intu:els+=[Paragraph("  <b>直觉理解：</b> "+intu,S["small"])]
    return els

def sec_pa(da,S):
    pa=da.get("problem_analysis",{});els=[]
    if not pa:return els
    els+=[Paragraph("<b>二、问题剖析：为什么要做这个研究</b>",S["subsection"])]
    s=T(pa.get("real_world_scenario",""))
    if s:els+=[Paragraph(s,S["callout"])]
    for f in pa.get("why_existing_fails",[]):
        if isinstance(f,dict):
            for k in["method_name","core_idea","failure_mode","root_cause"]:
                v=T(f.get(k,""))
                if v:els+=[Paragraph("- <b>"+k+":</b> "+v,S["small"])]
    ch=T(pa.get("core_challenge",""))
    if ch:els+=[Paragraph("<b>核心挑战：</b> "+ch,S["body_ni"])]
    ins=T(pa.get("author_insight",""))
    if ins:els+=[Paragraph(ins,S["callout"])]
    return els

def sec_mo(da,S):
    mo=da.get("method_overview",{});els=[]
    if not mo:return els
    els+=[Paragraph("<b>三、方法全景：整体技术路线</b>",S["subsection"])]
    pl=T(mo.get("pipeline_diagram_text",""))
    if pl:els+=[Paragraph(pl,S["body"])]
    for c in mo.get("key_design_choices",[]):
        if isinstance(c,dict):
            for k in["decision","alternatives","reasoning","tradeoff"]:
                v=T(c.get(k,""))
                if v:els+=[Paragraph("- <b>"+k+":</b> "+v,S["bullet_bold"])]
    return els

def sec_mdd(da,S):
    mdd=da.get("method_deep_dive",[]);els=[]
    if not mdd:return els
    els+=[Paragraph("<b>四、方法深潜：逐组件拆解</b>",S["subsection"])]
    for i,c in enumerate(mdd):
        if not isinstance(c,dict):continue
        n=T(c.get("component_name","C"+str(i+1)))
        pos=T(c.get("position_in_pipeline",""))
        mi=T(c.get("mathematical_intuition",""))
        steps=c.get("step_by_step",[])
        ex=T(c.get("input_output_example",""))
        hp=T(c.get("key_hyperparameters",""))
        why=T(c.get("why_this_design",""))
        els+=[Paragraph("<b>C"+str(i+1)+": "+n+"</b>",S["subsubsection"])]
        if pos:els+=[Paragraph("<b>位置：</b> "+pos,S["body_ni"])]
        if mi:els+=[Paragraph("<b>数学直觉：</b> "+mi,S["body"])]
        for j,s in enumerate(steps):els+=[Paragraph("  "+str(j+1)+". "+T(s),S["small"])]
        if ex:els+=[Paragraph("<b>输入输出示例：</b> "+ex,S["body_ni"])]
        if hp:els+=[Paragraph("<b>关键超参数：</b> "+hp,S["body_ni"])]
        if why:els+=[Paragraph("<b>设计精髓：</b> "+why,S["body_ni"])]
    return els

def sec_in(da,S):
    inns=da.get("innovation_analysis",[]);els=[]
    if not inns:return els
    els+=[Paragraph("<b>五、创新点深度分析</b>",S["subsection"])]
    for i in inns:
        if not isinstance(i,dict):continue
        p=T(i.get("innovation",""))
        if p:els+=[Paragraph("- <b>"+p+"</b>",S["bullet_bold"])]
        for k in["before_vs_after","why_nontrivial","generalizability"]:
            v=T(i.get(k,""))
            if v:els+=[Paragraph("  <b>"+k+":</b> "+v,S["small"])]
    return els

def sec_ex(da,S):
    exp=da.get("experiment_insights",{});els=[]
    if not exp:return els
    els+=[Paragraph("<b>六、实验深度解读</b>",S["subsection"])]
    for ds in exp.get("dataset_analysis",[]):
        if isinstance(ds,dict):
            for k in["dataset_name","scale","why_this_dataset","limitations_of_dataset"]:
                v=T(ds.get(k,""))
                if v:els+=[Paragraph("- <b>"+k+":</b> "+v,S["small"])]
    for r in exp.get("key_results",[]):
        if isinstance(r,dict):
            m=T(r.get("metric",""));v=T(r.get("value",""));w=T(r.get("what_it_means",""))
            if m:els+=[Paragraph("- <b>"+m+": "+v+"</b>",S["bullet_bold"])]
            if w:els+=[Paragraph("  "+w,S["small"])]
    for a in exp.get("ablation_insights",[]):
        if isinstance(a,dict):
            for k in["experiment","finding","takeaway"]:
                v=T(a.get(k,""))
                if v:els+=[Paragraph("- <b>"+k+":</b> "+v,S["small"])]
    sr=T(exp.get("surprising_results",""))
    if sr:els+=[Paragraph("<b>意外发现：</b> "+sr,S["body_ni"])]
    return els

def sec_rg(da,S):
    rg=da.get("reproducibility_guide",{});els=[]
    if not rg:return els
    els+=[Paragraph("<b>七、复现指南：从论文到代码</b>",S["subsection"])]
    for k,l in[("overall_architecture","Arch"),("data_flow","TrainFlow"),("inference_flow","InfFlow")]:
        v=T(rg.get(k,""))
        if v:els+=[Paragraph("<b>"+l+":</b> "+v,S["body_ni"])]
    pseudo=T(rg.get("pseudo_code",""))
    if pseudo:
        for line in pseudo.strip().split("\n"):
            if line.strip():els+=[Paragraph(line.strip(),S["code"])]
    for d in rg.get("critical_implementation_details",[]):
        els+=[Paragraph("! "+T(d),S["bullet"])]
    res=T(rg.get("estimated_resources",""))
    if res:els+=[Paragraph("<b>资源预估：</b> "+res,S["body_ni"])]
    gh=rg.get("github_analysis",{})
    if gh:
        repo=T(gh.get("repo_url",""))
        if repo:els+=[Paragraph("<b>代码仓库：</b> "+repo,S["body_ni"])]
        for k in["code_structure","entry_point"]:
            v=T(gh.get(k,""))
            if v:els+=[Paragraph("<b>"+k+":</b> "+v,S["body_ni"])]
        for f in gh.get("key_files",[]):els+=[Paragraph("  - "+T(f),S["bullet"])]
    return els

def sec_ct(da,S):
    ct=da.get("critical_thinking",{});els=[]
    if not ct:return els
    els+=[Paragraph("<b>八、批判性思考</b>",S["subsection"])]
    for s in ct.get("strengths",[]):els+=[Paragraph("+ "+T(s),S["bullet"])]
    for w in ct.get("weaknesses",[]):
        if isinstance(w,dict):
            for k in["weakness","impact","possible_fix"]:
                v=T(w.get(k,""))
                if v:els+=[Paragraph("- <b>"+k+":</b> "+v,S["small"])]
    for q in ct.get("unanswered_questions",[]):els+=[Paragraph("? "+T(q),S["bullet"])]
    sota=T(ct.get("comparison_to_sota_thinking",""))
    if sota:els+=[Paragraph("<b>SOTA对比：</b> "+sota,S["body_ni"])]
    return els

def sec_pr(da,S):
    pr=da.get("personal_relevance",{});els=[]
    if not pr:return els
    els+=[Paragraph("<b>九、对个人研究的启发</b>",S["subsection"])]
    for k,l in[("direct_relevance","Direct"),("skill_building","Skill"),("career_relevance","Career")]:
        v=T(pr.get(k,""))
        if v:els+=[Paragraph("<b>"+l+":</b> "+v,S["body_ni"])]
    for idea in pr.get("transferable_ideas",[]):els+=[Paragraph("> "+T(idea),S["bullet"])]
    for a in pr.get("action_items",[]):els+=[Paragraph("[ ] "+T(a),S["bullet"])]
    return els

def sec_lr(da,S):
    lr=da.get("learning_roadmap",{});els=[]
    if not lr:return els
    els+=[Paragraph("<b>十、学习路线图</b>",S["subsection"])]
    for key,title in[("phase1_prerequisites","阶段一：前置准备"),("phase2_first_read","阶段二：第一遍通读"),("phase3_deep_read","阶段三：第二遍精读"),("phase4_implementation","阶段四：动手复现"),("phase5_beyond","阶段五：延伸拓展")]:
        ph=lr.get(key,{})
        if not ph:continue
        d=T(ph.get("description",""));et=T(ph.get("estimated_time",""))
        els+=[Paragraph("<b>"+title+"</b>",S["subsubsection"])]
        if d:els+=[Paragraph(d,S["body"])]
        if et:els+=[Paragraph("  Time: "+et,S["small"])]
        for it in ph.get("items",[]):
            if isinstance(it,dict):
                t=T(it.get("topic",""));te=T(it.get("estimated_time",""));r=T(it.get("resource",""))
                ln="  - "+t+(" ("+te+")" if te else "")+("=> "+r if r else "")
                els+=[Paragraph(ln,S["small"])]
        for f in ph.get("focus_on",[]):els+=[Paragraph("  - Focus: "+T(f),S["small"])]
        for ex in ph.get("exercises",[]):els+=[Paragraph("  - Ex: "+T(ex),S["small"])]
        for j,s in enumerate(ph.get("steps",[])):els+=[Paragraph("  "+str(j+1)+". "+T(s),S["small"])]
        sc=T(ph.get("self_check",""))
        if sc:els+=[Paragraph("  <b>自测：</b> "+sc,S["small"])]
        for cq in ph.get("comprehension_check",[]):els+=[Paragraph("  - Q: "+T(cq),S["small"])]
        eo=T(ph.get("expected_outcome",""))
        if eo:els+=[Paragraph("  <b>预期成果：</b> "+eo,S["small"])]
        for np in ph.get("next_papers",[]):els+=[Paragraph("  - Next: "+T(np),S["small"])]
        op=T(ph.get("open_problems",""))
        if op:els+=[Paragraph("  <b>开放问题：</b> "+op,S["small"])]
    return els

def sec_gl(da,S):
        els=[]
        terms=da.get("key_terms_glossary",[])
        if terms:
            els+=[Paragraph("<b>附录A：术语表</b>",S["subsection"])]
            for t_ in terms:
                if isinstance(t_,dict):
                    en=T(t_.get("en",""));cn=T(t_.get("cn",""));ex=T(t_.get("explanation",""))
                    els+=[Paragraph("  <b>"+en+"</b> - "+cn+(": "+ex if ex else ""),S["small"])]
        formulas=da.get("formula_explanations",[])
        if formulas:
            els+=[Paragraph("<b>附录B：公式解读</b>",S["subsection"])]
            for f in formulas:
                if isinstance(f,dict):
                    for k in["formula_context","symbols","intuition"]:
                        v=T(f.get(k,""))
                        if v:els+=[Paragraph("  <b>"+k+":</b> "+v,S["small"])]
        return els



def safe_build(builder, da, S):
    """Wrap builder call with full exception safety."""
    try:
        if da is None or not isinstance(da, dict):
            return []
        if S is None or not isinstance(S, dict):
            return []
        result = builder(da, S)
        return result if isinstance(result, list) else []
    except Exception:
        return []
V3_BUILDERS = [sec_km,sec_pa,sec_mo,sec_mdd,sec_in,sec_ex,sec_rg,sec_ct,sec_pr,sec_lr,sec_gl]
