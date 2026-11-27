import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import datetime
import io
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# =============================================================================
# 1. 页面配置与商务风格 CSS
# =============================================================================
st.set_page_config(
    page_title="全链路销售转化与人效诊断中心（8模块脱敏Demo）",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
    .dashboard-title {
        background: linear-gradient(90deg, #1e3a8a, #0d9488);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2rem;
        margin-bottom: 0.25rem;
    }
    .dashboard-subtitle { color: #64748b; font-size: 0.95rem; margin-bottom: 1rem; }
    .demo-banner {
        background: #f0f9ff; border: 1px solid #bae6fd; border-left: 4px solid #0284c7;
        border-radius: 8px; padding: 10px 14px; font-size: 12.8px; color: #0c4a6e; margin-bottom: 14px;
    }
    .kpi-card {
        background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;
        padding: 15px 18px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); margin-bottom: 10px;
    }
    .kpi-label { font-size: 12px; color: #64748b; font-weight: 600; margin-bottom: 4px; }
    .kpi-value { font-size: 26px; font-weight: 800; color: #0f172a; line-height: 1.15; }
    .kpi-sub { font-size: 11.5px; color: #64748b; margin-top: 4px; }
    [data-testid="stElementToolbar"] button[title*="CSV"],
    [data-testid="stElementToolbar"] button[title*="csv"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 2. 100% 纯仿真模拟数据引擎（零真实姓名、零手机号、零企业密钥）
# =============================================================================
BUSINESS_LINES = {
    "业务线 A（高客单年度会员）": {"unit_price": 3980.0, "target_cr": 0.055, "seed": 202601},
    "业务线 B（核心增长训练营）": {"unit_price": 1980.0, "target_cr": 0.062, "seed": 202602},
    "业务线 C（新客体验转化线）": {"unit_price": 2980.0, "target_cr": 0.050, "seed": 202603},
}

CHANNELS = [
    ("短视频信息流 A", 0.36, 0.96),
    ("信息流竞价广告 B", 0.24, 0.90),
    ("平台小店直投 C", 0.18, 1.08),
    ("图文内容种草 D", 0.13, 1.24),
    ("搜索精准广告 E", 0.09, 1.38),
]

COHORTS = [
    ("第101期", "202X年09月", "202X-09-07"),
    ("第102期", "202X年09月", "202X-09-14"),
    ("第103期", "202X年09月", "202X-09-21"),
    ("第104期", "202X年10月", "202X-10-05"),
    ("第105期", "202X年10月", "202X-10-12"),
    ("第106期", "202X年10月", "202X-10-19"),
]

ADVISORS = [
    ("顾问 S01", "运营A组", 1.32), ("顾问 S02", "运营A组", 1.24), ("顾问 S03", "运营A组", 1.16),
    ("顾问 S04", "运营A组", 1.10), ("顾问 S05", "运营A组", 1.04), ("顾问 S06", "运营A组", 0.95),
    ("顾问 S07", "运营A组", 0.84), ("顾问 S08", "运营B组", 1.28), ("顾问 S09", "运营B组", 1.18),
    ("顾问 S10", "运营B组", 1.06), ("顾问 S11", "运营B组", 0.98), ("顾问 S12", "运营B组", 0.90),
    ("顾问 S13", "运营B组", 0.82), ("顾问 S14", "运营B组", 0.74),
]

@st.cache_data(ttl=600)
def generate_synthetic_sales_data(biz_name, refresh_tick=0):
    cfg = BUSINESS_LINES[biz_name]
    rng = np.random.default_rng(cfg["seed"])
    unit_price = cfg["unit_price"]
    base_cr = cfg["target_cr"]

    backfill_rows = []
    order_rows = []
    order_seq = 10001
    user_seq = 50001

    for p_idx, (period, month, start_date) in enumerate(COHORTS):
        period_trend = 0.92 + p_idx * 0.035  # 模拟期次爬坡趋势
        for adv_name, team_name, skill_factor in ADVISORS:
            # 每人每期分配线索 45~78 条（最新一期随 refresh_tick 模拟实时微增）
            extra_live = int((refresh_tick * 2) % 7) if p_idx == len(COHORTS) - 1 else 0
            leads = int(rng.integers(48, 76)) + extra_live
            # 目标转化率（按团队/个人能力与期次动态模拟）
            actual_cr = np.clip(base_cr * skill_factor * period_trend * rng.uniform(0.75, 1.25), 0.015, 0.14)
            target_orders = max(1.0, round(leads * base_cr, 1))
            total_orders = max(0, int(round(leads * actual_cr)))
            if p_idx == len(COHORTS) - 1 and refresh_tick > 0 and rng.random() < 0.35:
                total_orders += 1

            # 拆分为各渠道记录
            ch_weights = np.array([c[1] for c in CHANNELS])
            ch_leads_arr = rng.multinomial(leads, ch_weights)

            # 按渠道质量加权分配订单
            ch_order_probs = np.array([ch_leads_arr[i] * CHANNELS[i][2] for i in range(len(CHANNELS))], dtype=float)
            if ch_order_probs.sum() > 0:
                ch_order_probs /= ch_order_probs.sum()
            else:
                ch_order_probs = ch_weights
            ch_orders_arr = rng.multinomial(total_orders, ch_order_probs) if total_orders > 0 else np.zeros(len(CHANNELS), dtype=int)

            for ch_idx, (ch_name, _, _) in enumerate(CHANNELS):
                cl = int(ch_leads_arr[ch_idx])
                co = int(ch_orders_arr[ch_idx])
                if cl == 0 and co == 0:
                    continue
                backfill_rows.append({
                    "业务线": biz_name,
                    "月份": month,
                    "期次": period,
                    "开营日期": start_date,
                    "团队": team_name,
                    "顾问": adv_name,
                    "渠道": ch_name,
                    "分配线索量": cl,
                    "成交单数": co,
                    "目标单数": round(cl * base_cr, 2),
                    "成交流水": round(co * unit_price, 2),
                })

                # 生成逐笔脱敏订单流水（包含 D0-D5 营期内转化 与 D6-D14 结营后长尾开单！）
                for _ in range(co):
                    # 约 74% 发生在 D0-D5 营期内，26% 发生在 D6-D14 结营后长尾追单
                    if rng.random() < 0.74:
                        day_offset = int(rng.choice([0, 1, 2, 3, 4, 5], p=[0.12, 0.16, 0.22, 0.24, 0.16, 0.10]))
                        stage = "营期内转化 (D0-D5)"
                    else:
                        day_offset = int(rng.choice([6, 7, 8, 9, 10, 11, 12, 13, 14], p=[0.22, 0.18, 0.14, 0.12, 0.10, 0.08, 0.06, 0.05, 0.05]))
                        stage = "结营后长尾追单 (D6-D14)"

                    pay_type = rng.choice(["全款", "定金+尾款"], p=[0.84, 0.16])
                    order_rows.append({
                        "订单编号": f"ORD-202X-{order_seq}",
                        "学员编号": f"U{user_seq}",
                        "月份": month,
                        "期次": period,
                        "开营日期": start_date,
                        "成单距开营天数": f"D{day_offset}",
                        "成单天数_num": day_offset,
                        "成单阶段": stage,
                        "团队": team_name,
                        "顾问": adv_name,
                        "渠道": ch_name,
                        "付款类型": pay_type,
                        "实付流水": unit_price,
                    })
                    order_seq += 1
                    user_seq += 1

    return pd.DataFrame(backfill_rows), pd.DataFrame(order_rows)

def build_styled_excel(df_export, sheet_name="综合排名战报"):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df_export.to_excel(writer, index=False, sheet_name=sheet_name[:30])
        ws = writer.sheets[sheet_name[:30]]
        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        header_font = Font(name="微软雅黑", size=10, bold=True, color="FFFFFF")
        body_font = Font(name="微软雅黑", size=10, color="1E293B")
        thin = Side(border_style="thin", color="CBD5E1")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)

        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border

        for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
            for cell in row:
                cell.font = body_font
                cell.border = border
                cell.alignment = Alignment(horizontal="center", vertical="center")

        for col in ws.columns:
            max_len = max(len(str(c.value or "")) for c in col)
            ws.column_dimensions[col[0].column_letter].width = min(max(max_len * 1.5 + 4, 12), 28)
    return buf.getvalue()

# =============================================================================
# 3. 侧边栏全局筛选控制
# =============================================================================
if "sales_refresh_tick" not in st.session_state:
    st.session_state["sales_refresh_tick"] = 0
if "sales_sync_time" not in st.session_state:
    st.session_state["sales_sync_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with st.sidebar:
    st.markdown("## 🏆 销售人效诊断中心")
    st.caption("作者：吴幸晖 ｜ 8 模块全链路脱敏版")

    st.markdown("""
    <div style='background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:8px 12px;margin-bottom:10px;'>
        <div style='color:#166534;font-size:12px;font-weight:700;'>🟢 模拟 CRM/飞书双源已连接</div>
        <div style='color:#15803d;font-size:11px;margin-top:2px;'>100% 纯仿真数据 · 零隐私泄露</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 模拟实时拉取最新数据", use_container_width=True, type="primary"):
        st.session_state["sales_refresh_tick"] += 1
        st.session_state["sales_sync_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.cache_data.clear()
        st.rerun()
    st.caption(f"最近同步：{st.session_state['sales_sync_time']}")
    st.markdown("---")

    selected_biz = st.selectbox("🏢 切换业务线", options=list(BUSINESS_LINES.keys()), index=0)
    raw_bf, raw_orders = generate_synthetic_sales_data(selected_biz, st.session_state["sales_refresh_tick"])

    avail_months = sorted(raw_bf["月份"].unique().tolist())
    sel_months = st.multiselect("🗓️ 筛选月份", options=avail_months, default=avail_months)

    avail_periods = [c[0] for c in COHORTS if c[1] in sel_months]
    sel_periods = st.multiselect("🏫 筛选期次", options=avail_periods, default=avail_periods)

    avail_teams = sorted(raw_bf["团队"].unique().tolist())
    sel_teams = st.multiselect("👥 筛选运营团队", options=avail_teams, default=avail_teams)

    avail_channels = [c[0] for c in CHANNELS]
    sel_channels = st.multiselect("📢 筛选获客渠道", options=avail_channels, default=avail_channels)

    avail_advisors = sorted(raw_bf[raw_bf["团队"].isin(sel_teams)]["顾问"].unique().tolist())
    sel_advisors = st.multiselect("👤 筛选顾问（默认全选）", options=avail_advisors, default=avail_advisors)

# 过滤数据集
f_bf = raw_bf[
    raw_bf["月份"].isin(sel_months)
    & raw_bf["期次"].isin(sel_periods)
    & raw_bf["团队"].isin(sel_teams)
    & raw_bf["渠道"].isin(sel_channels)
    & raw_bf["顾问"].isin(sel_advisors)
].copy()

f_ord = raw_orders[
    raw_orders["月份"].isin(sel_months)
    & raw_orders["期次"].isin(sel_periods)
    & raw_orders["团队"].isin(sel_teams)
    & raw_orders["渠道"].isin(sel_channels)
    & raw_orders["顾问"].isin(sel_advisors)
].copy()

# =============================================================================
# 4. 页面头部与全局 KPI
# =============================================================================
st.markdown(f"<div class='dashboard-title'>🏆 {selected_biz} · 全链路销售转化与人效诊断中心</div>", unsafe_allow_html=True)
st.markdown("<div class='dashboard-subtitle'>覆盖渠道/期次转化、顾问人效排名、跨期转化热力矩阵、结营后 D6-D14 长尾滞后开单分析与格式化 Excel 战报导出</div>", unsafe_allow_html=True)

st.markdown("""
<div class='demo-banner'>
    🛡️ <strong>纯仿真作品集演示版</strong>：本系统原型曾以 PyInstaller 打包并直连飞书/CRM 赋能百人销售团队。公开 Demo 已彻底移除企业密钥与真实数据，全部记录均由算法独立仿真生成，完整还原 8 大分析模块的工程与业务设计。
</div>
""", unsafe_allow_html=True)

if f_bf.empty:
    st.warning("当前筛选条件下无匹配数据，请在左侧调整筛选条件。")
    st.stop()

tot_leads = int(f_bf["分配线索量"].sum())
tot_orders = int(f_bf["成交单数"].sum())
tot_gmv = float(f_bf["成交流水"].sum())
tot_target = float(f_bf["目标单数"].sum())
overall_cr = (tot_orders / tot_leads) if tot_leads > 0 else 0.0
overall_comp = (tot_orders / tot_target) if tot_target > 0 else 0.0
long_tail_cnt = int((f_ord["成单天数_num"] >= 6).sum()) if not f_ord.empty else 0
long_tail_share = (long_tail_cnt / len(f_ord)) if len(f_ord) > 0 else 0.0

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(f"<div class='kpi-card'><div class='kpi-label'>📥 分配有效线索</div><div class='kpi-value'>{tot_leads:,}</div><div class='kpi-sub'>覆盖 {len(sel_periods)} 个模拟期次</div></div>", unsafe_allow_html=True)
with k2:
    st.markdown(f"<div class='kpi-card'><div class='kpi-label'>🎯 累计成交单数</div><div class='kpi-value' style='color:#2563eb;'>{tot_orders:,}</div><div class='kpi-sub'>目标基准：{tot_target:.1f} 单</div></div>", unsafe_allow_html=True)
with k3:
    st.markdown(f"<div class='kpi-card'><div class='kpi-label'>🔥 综合转化率</div><div class='kpi-value' style='color:#059669;'>{overall_cr:.2%}</div><div class='kpi-sub'>综合完成度：{overall_comp:.1%}</div></div>", unsafe_allow_html=True)
with k4:
    st.markdown(f"<div class='kpi-card'><div class='kpi-label'>💰 累计成交流水</div><div class='kpi-value'>¥{tot_gmv:,.0f}</div><div class='kpi-sub'>客单价：¥{BUSINESS_LINES[selected_biz]['unit_price']:,.0f}</div></div>", unsafe_allow_html=True)
with k5:
    st.markdown(f"<div class='kpi-card'><div class='kpi-label'>⏳ D6-D14 长尾占比</div><div class='kpi-value' style='color:#d97706;'>{long_tail_share:.1%}</div><div class='kpi-sub'>结营后追回：{long_tail_cnt} 单</div></div>", unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# 5. 八大核心分析标签页
# =============================================================================
t1, t2, t3, t4, t5, t6, t7, t8 = st.tabs([
    "📢 渠道转化对比",
    "🏫 期次转化对比",
    "💼 销售业绩对比",
    "🏆 综合完成度排名",
    "📅 多期与月度完成度明细",
    "🎯 销售跨期转化热力矩阵",
    "⏳ 结营后长尾开单 (D6-D14)",
    "📑 详细排名表与Excel导出"
])

# --- Tab 1: 渠道转化对比 ---
with t1:
    st.markdown("#### 📢 各获客渠道线索量、成交单数与转化率对比")
    ch_agg = f_bf.groupby("渠道", as_index=False).agg(线索量=("分配线索量", "sum"), 成交单数=("成交单数", "sum"), 成交流水=("成交流水", "sum"))
    ch_agg["转化率"] = np.where(ch_agg["线索量"] > 0, ch_agg["成交单数"] / ch_agg["线索量"], 0.0)
    ch_agg = ch_agg.sort_values("转化率", ascending=False)

    c1, c2 = st.columns([1.2, 1])
    with c1:
        fig_ch = go.Figure()
        fig_ch.add_trace(go.Bar(name="分配线索量", x=ch_agg["渠道"], y=ch_agg["线索量"], marker_color="#cbd5e1", yaxis="y2"))
        fig_ch.add_trace(go.Scatter(name="转化率", x=ch_agg["渠道"], y=ch_agg["转化率"], mode="lines+markers+text", text=ch_agg["转化率"].apply(lambda x: f"{x:.2%}"), textposition="top center", line=dict(color="#2563eb", width=3), marker=dict(size=9), yaxis="y"))
        fig_ch.update_layout(title="渠道线索体量 vs 转化率表现", yaxis=dict(title="转化率", tickformat=".1%", rangemode="tozero"), yaxis2=dict(title="线索量", overlaying="y", side="right", showgrid=False), legend=dict(orientation="h", y=1.12), height=370, margin=dict(t=55, b=30))
        st.plotly_chart(fig_ch, use_container_width=True)
    with c2:
        disp_ch = ch_agg.copy()
        disp_ch["转化率"] = disp_ch["转化率"] * 100
        st.dataframe(disp_ch, hide_index=True, use_container_width=True, column_config={
            "转化率": st.column_config.NumberColumn("🔥 转化率", format="%.2f%%"),
            "成交流水": st.column_config.NumberColumn("成交流水", format="¥%.0f"),
        })

# --- Tab 2: 期次转化对比 ---
with t2:
    st.markdown("#### 🏫 跨期次转化率走势与线索规模变化")
    p_order = [c[0] for c in COHORTS if c[0] in sel_periods]
    p_agg = f_bf.groupby("期次", as_index=False).agg(线索量=("分配线索量", "sum"), 成交单数=("成交单数", "sum"), 成交流水=("成交流水", "sum"))
    p_agg["转化率"] = np.where(p_agg["线索量"] > 0, p_agg["成交单数"] / p_agg["线索量"], 0.0)
    p_agg["sort_idx"] = p_agg["期次"].apply(lambda x: p_order.index(x) if x in p_order else 99)
    p_agg = p_agg.sort_values("sort_idx").drop(columns=["sort_idx"])

    fig_p = go.Figure()
    fig_p.add_trace(go.Bar(name="期次线索量", x=p_agg["期次"], y=p_agg["线索量"], marker_color="#93c5fd", opacity=0.65, yaxis="y2"))
    fig_p.add_trace(go.Scatter(name="期次转化率", x=p_agg["期次"], y=p_agg["转化率"], mode="lines+markers+text", text=p_agg["转化率"].apply(lambda x: f"{x:.2%}"), textposition="top center", line=dict(color="#1e3a8a", width=3), marker=dict(size=10), yaxis="y"))
    fig_p.update_layout(title="各期次线索体量与转化率走势", yaxis=dict(title="转化率", tickformat=".1%", rangemode="tozero"), yaxis2=dict(title="线索量", overlaying="y", side="right", showgrid=False), legend=dict(orientation="h", y=1.12), height=380)
    st.plotly_chart(fig_p, use_container_width=True)

# --- Tab 3: 销售业绩对比 ---
with t3:
    st.markdown("#### 💼 销售顾问个人业绩对比")
    metric_choice = st.radio("选择对比指标", options=["按成交单数", "按成交流水", "按个人转化率"], horizontal=True)
    s_agg = f_bf.groupby(["顾问", "团队"], as_index=False).agg(线索量=("分配线索量", "sum"), 成交单数=("成交单数", "sum"), 成交流水=("成交流水", "sum"))
    s_agg["转化率"] = np.where(s_agg["线索量"] > 0, s_agg["成交单数"] / s_agg["线索量"], 0.0)

    if metric_choice == "按成交单数":
        s_agg = s_agg.sort_values("成交单数", ascending=False)
        fig_s = px.bar(s_agg, x="顾问", y="成交单数", color="团队", text="成交单数", title="各顾问累计成交单数对比", color_discrete_sequence=["#2563eb", "#0d9488"])
    elif metric_choice == "按成交流水":
        s_agg = s_agg.sort_values("成交流水", ascending=False)
        fig_s = px.bar(s_agg, x="顾问", y="成交流水", color="团队", text=s_agg["成交流水"].apply(lambda x: f"¥{x/10000:.1f}万"), title="各顾问累计成交流水对比", color_discrete_sequence=["#2563eb", "#0d9488"])
    else:
        s_agg = s_agg.sort_values("转化率", ascending=False)
        fig_s = px.bar(s_agg, x="顾问", y="转化率", color="团队", text=s_agg["转化率"].apply(lambda x: f"{x:.2%}"), title="各顾问个人综合转化率对比", color_discrete_sequence=["#2563eb", "#0d9488"])
        fig_s.update_yaxes(tickformat=".1%")
    fig_s.update_traces(textposition="outside")
    fig_s.update_layout(height=400, xaxis_tickangle=-25)
    st.plotly_chart(fig_s, use_container_width=True)

# --- Tab 4: 销售综合完成度排名 ---
with t4:
    st.markdown("#### 🏆 销售人员综合完成度排名（实际成交 / 线索目标单数）")
    comp_df = f_bf.groupby(["顾问", "团队"], as_index=False).agg(总线索=("分配线索量", "sum"), 实际成交=("成交单数", "sum"), 目标单数=("目标单数", "sum"))
    comp_df["综合完成度"] = np.where(comp_df["目标单数"] > 0, comp_df["实际成交"] / comp_df["目标单数"], 0.0)
    comp_df = comp_df.sort_values("综合完成度", ascending=False).reset_index(drop=True)
    comp_df["排名"] = comp_df.index + 1

    r1, r2 = st.columns([1, 1.15])
    with r1:
        show_comp = comp_df[["排名", "顾问", "团队", "总线索", "实际成交", "综合完成度"]].copy()
        show_comp["综合完成度"] = show_comp["综合完成度"] * 100
        st.dataframe(show_comp, hide_index=True, use_container_width=True, column_config={
            "综合完成度": st.column_config.NumberColumn("🎯 综合完成度", format="%.1f%%")
        })
    with r2:
        c_plot = comp_df.sort_values("综合完成度", ascending=True)
        fig_r = px.bar(c_plot, x="综合完成度", y="顾问", orientation="h", text=c_plot["综合完成度"].apply(lambda x: f"{x:.1%}"), color="综合完成度", color_continuous_scale="Viridis", title="顾问综合完成度梯队分布")
        fig_r.add_vline(x=1.0, line_dash="dash", line_color="#ef4444", annotation_text="100%达标线")
        fig_r.update_xaxes(tickformat=".0%")
        fig_r.update_traces(textposition="outside")
        fig_r.update_layout(height=420, coloraxis_showscale=False)
        st.plotly_chart(fig_r, use_container_width=True)

# --- Tab 5: 销售多期与月度完成度明细 ---
with t5:
    st.markdown("#### 📅 顾问分期次综合完成度追踪明细")
    p_comp = f_bf.groupby(["顾问", "期次"], as_index=False).agg(实际=("成交单数", "sum"), 目标=("目标单数", "sum"))
    p_comp["完成度"] = np.where(p_comp["目标"] > 0, p_comp["实际"] / p_comp["目标"] * 100, 0.0)
    piv_comp = p_comp.pivot(index="顾问", columns="期次", values="完成度").reindex(columns=p_order).round(1)
    piv_comp["全周期均值(%)"] = piv_comp.mean(axis=1).round(1)
    piv_comp = piv_comp.sort_values("全周期均值(%)", ascending=False)
    def _color_comp(val):
        if pd.isna(val):
            return ""
        if val >= 110:
            return "background-color: #dcfce7; color: #166534; font-weight: 600;"
        if val >= 95:
            return "background-color: #eff6ff; color: #1e40af;"
        return "background-color: #fef2f2; color: #991b1b;"
    st.dataframe(piv_comp.style.format("{:.1f}%", na_rep="-").map(_color_comp), use_container_width=True)

# --- Tab 6: 销售转化率跨期热力矩阵 ---
with t6:
    st.markdown("#### 🎯 销售转化率跨期矩阵热力图（快速诊断稳定标杆 vs 异常下滑个体）")
    st.caption("💡 颜色越深代表转化率越高，横向观察单顾问跨期稳定性，纵向对比单期次团队方差。")
    m_agg = f_bf.groupby(["顾问", "期次"], as_index=False).agg(线索=("分配线索量", "sum"), 成交=("成交单数", "sum"))
    m_agg["转化率"] = np.where(m_agg["线索"] > 0, m_agg["成交"] / m_agg["线索"] * 100, 0.0)
    heat_df = m_agg.pivot(index="顾问", columns="期次", values="转化率").reindex(columns=p_order).fillna(0.0)
    heat_df["avg"] = heat_df.mean(axis=1)
    heat_df = heat_df.sort_values("avg", ascending=False).drop(columns=["avg"])

    fig_heat = px.imshow(
        heat_df,
        text_auto=".2f",
        color_continuous_scale="Blues",
        aspect="auto",
        labels=dict(x="业务期次", y="销售顾问", color="转化率 (%)"),
        title="顾问 × 期次 转化率热力矩阵 (%)"
    )
    fig_heat.update_layout(height=460)
    st.plotly_chart(fig_heat, use_container_width=True)

# --- Tab 7: 结营后长尾开单分析 (D6-D14) ---
with t7:
    st.markdown("#### ⏳ Cohort 滞后转化：营期内 (D0-D5) vs 结营后长尾追单 (D6-D14) 分析")
    if f_ord.empty:
        st.info("暂无订单明细")
    else:
        day_dist = f_ord.groupby(["成单天数_num", "成单阶段"], as_index=False).agg(成交单数=("订单编号", "count"), 实付流水=("实付流水", "sum"))
        day_dist = day_dist.sort_values("成单天数_num")
        day_dist["天数标签"] = day_dist["成单天数_num"].apply(lambda x: f"D{x}")
        day_dist["累计占比"] = day_dist["成交单数"].cumsum() / day_dist["成交单数"].sum()

        lt1, lt2 = st.columns([1.4, 1])
        with lt1:
            fig_lt = go.Figure()
            for stg, col in [("营期内转化 (D0-D5)", "#2563eb"), ("结营后长尾追单 (D6-D14)", "#f59e0b")]:
                sub = day_dist[day_dist["成单阶段"] == stg]
                fig_lt.add_trace(go.Bar(name=stg, x=sub["天数标签"], y=sub["成交单数"], marker_color=col, text=sub["成交单数"], textposition="outside"))
            fig_lt.add_trace(go.Scatter(name="累计成单占比", x=day_dist["天数标签"], y=day_dist["累计占比"], mode="lines+markers", line=dict(color="#059669", width=2.5), yaxis="y2"))
            fig_lt.update_layout(title="D0 ～ D14 逐日成交分布与累计转化曲线", yaxis=dict(title="成单数"), yaxis2=dict(title="累计占比", overlaying="y", side="right", tickformat=".0%", range=[0, 1.12], showgrid=False), legend=dict(orientation="h", y=1.14), height=390)
            st.plotly_chart(fig_lt, use_container_width=True)
        with lt2:
            lt_adv = f_ord[f_ord["成单天数_num"] >= 6].groupby(["顾问", "团队"], as_index=False).agg(长尾追单数=("订单编号", "count"), 长尾流水=("实付流水", "sum")).sort_values("长尾追单数", ascending=False)
            st.markdown("##### 🌟 D6-D14 结营后长尾追单能力榜")
            st.dataframe(lt_adv, hide_index=True, use_container_width=True, column_config={
                "长尾流水": st.column_config.NumberColumn("长尾挽回流水", format="¥%.0f")
            })

# --- Tab 8: 详细排名表与格式化 Excel 导出 ---
with t8:
    st.markdown("#### 📑 顾问综合业绩与长尾转化详细排名总表")
    lt_map = f_ord[f_ord["成单天数_num"] >= 6].groupby("顾问")["订单编号"].count().to_dict() if not f_ord.empty else {}
    full_rank = f_bf.groupby(["顾问", "团队"], as_index=False).agg(分配线索=("分配线索量", "sum"), 成交单数=("成交单数", "sum"), 目标单数=("目标单数", "sum"), 成交流水=("成交流水", "sum"))
    full_rank["D6-D14长尾单"] = full_rank["顾问"].map(lt_map).fillna(0).astype(int)
    full_rank["长尾占比(%)"] = np.where(full_rank["成交单数"] > 0, (full_rank["D6-D14长尾单"] / full_rank["成交单数"] * 100).round(1), 0.0)
    full_rank["转化率(%)"] = np.where(full_rank["分配线索"] > 0, (full_rank["成交单数"] / full_rank["分配线索"] * 100).round(2), 0.0)
    full_rank["综合完成度(%)"] = np.where(full_rank["目标单数"] > 0, (full_rank["成交单数"] / full_rank["目标单数"] * 100).round(1), 0.0)
    full_rank = full_rank.sort_values("综合完成度(%)", ascending=False).reset_index(drop=True)
    full_rank.insert(0, "排名", full_rank.index + 1)

    st.dataframe(full_rank, hide_index=True, use_container_width=True, column_config={
        "成交流水": st.column_config.NumberColumn("成交流水", format="¥%.0f"),
        "转化率(%)": st.column_config.NumberColumn("转化率", format="%.2f%%"),
        "综合完成度(%)": st.column_config.NumberColumn("综合完成度", format="%.1f%%"),
        "长尾占比(%)": st.column_config.NumberColumn("长尾占比", format="%.1f%%"),
    })

    excel_bytes = build_styled_excel(full_rank, sheet_name="销售综合排名战报")
    st.download_button(
        label="📥 一键导出带样式 Excel 综合排名战报 (.xlsx)",
        data=excel_bytes,
        file_name=f"{selected_biz}_销售综合人效排名战报_脱敏Demo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )

# 底部脱敏订单明细预览
st.markdown("---")
with st.expander(f"🔍 展开脱敏订单明细流水（当前共 {len(f_ord):,} 笔仿真订单 · 0 真实手机号/姓名）", expanded=False):
    st.dataframe(f_ord.drop(columns=["成单天数_num"]).head(200), hide_index=True, use_container_width=True, column_config={
        "实付流水": st.column_config.NumberColumn("实付流水", format="¥%.0f")
    })
