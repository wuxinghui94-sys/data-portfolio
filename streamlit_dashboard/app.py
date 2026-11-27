import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import datetime
import io
import re

# 1. 页面基本配置
st.set_page_config(
    page_title="渠道ROI与转化分析实时看板（脱敏Demo）",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 现代轻奢商务风格 CSS
st.markdown("""
<style>
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
    }
    .metric-hero-card {
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 50%, #3b82f6 100%);
        border-radius: 12px;
        padding: 20px 24px;
        color: #ffffff;
        box-shadow: 0 4px 14px 0 rgba(37, 99, 235, 0.25);
        margin-bottom: 14px;
    }
    .metric-hero-title {
        font-size: 13px;
        font-weight: 500;
        opacity: 0.9;
        margin-bottom: 4px;
    }
    .metric-hero-value {
        font-size: 34px;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    .metric-hero-sub {
        font-size: 12.5px;
        opacity: 0.85;
        margin-top: 4px;
    }
    .metric-sub-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 14px 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 14px;
    }
    .metric-sub-title {
        font-size: 12.5px;
        color: #64748b;
        font-weight: 500;
        margin-bottom: 2px;
    }
    .metric-sub-value {
        font-size: 22px;
        font-weight: 700;
        color: #0f172a;
    }
    .metric-sub-badge {
        font-size: 11.5px;
        display: inline-block;
        padding: 2px 7px;
        border-radius: 4px;
        margin-top: 3px;
        font-weight: 500;
    }
    .project-pill {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        background-color: #e0f2fe;
        color: #0369a1;
        font-weight: 600;
        font-size: 13.5px;
        margin-bottom: 8px;
    }
    .demo-banner {
        background: #f0f9ff;
        border: 1px solid #bae6fd;
        border-left: 4px solid #0284c7;
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 12.8px;
        color: #0c4a6e;
        margin-bottom: 12px;
    }
    [data-testid="stElementToolbar"] button[title*="CSV"],
    [data-testid="stElementToolbar"] button[title*="csv"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. 脱敏业务线与核心渠道配置
PROJECT_LIST = [
    "业务线 A（高客单年度会员）",
    "业务线 B（核心增长训练营）",
    "业务线 C（新客体验转化线）"
]

CORE_CHANNELS_MAP = {
    "业务线 A（高客单年度会员）": [
        "短视频信息流 A",
        "信息流竞价广告 B",
        "平台小店直投 C",
        "图文内容种草 D",
        "搜索精准广告 E"
    ],
    "业务线 B（核心增长训练营）": [
        "短视频信息流 A",
        "平台小店直投 C",
        "达人直播引流 C",
        "低门槛体验引流 D"
    ],
    "业务线 C（新客体验转化线）": [
        "短视频信息流 A",
        "官方直播间引流 B",
        "5低门槛体验引流 D"
    ]
}

ALL_CHANNELS_MAP = {
    "业务线 A（高客单年度会员）": [
        ("短视频信息流 A", 420, 0.048, 128, 0.62, 0.088),
        ("信息流竞价广告 B", 260, 0.041, 138, 0.58, 0.075),
        ("平台小店直投 C", 195, 0.053, 122, 0.65, 0.068),
        ("图文内容种草 D", 150, 0.064, 152, 0.45, 0.052),
        ("搜索精准广告 E", 95, 0.072, 165, 0.40, 0.035),
        ("泛信息流测投 F", 110, 0.029, 135, 0.55, 0.105),
        ("私域裂变转介绍", 65, 0.095, 42, 0.35, 0.025),
    ],
    "业务线 B（核心增长训练营）": [
        ("短视频信息流 A", 380, 0.052, 78, 0.60, 0.062),
        ("平台小店直投 C", 240, 0.058, 74, 0.64, 0.055),
        ("达人直播引流 C", 190, 0.044, 68, 0.72, 0.070),
        ("低门槛体验引流 D", 310, 0.036, 56, 0.55, 0.082),
        ("图文内容种草 E", 120, 0.066, 92, 0.42, 0.045),
    ],
    "业务线 C（新客体验转化线）": [
        ("短视频信息流 A", 290, 0.046, 118, 0.58, 0.072),
        ("官方直播间引流 B", 210, 0.054, 125, 0.68, 0.060),
        ("5低门槛体验引流 D", 130, 0.078, 168, 0.48, 0.042),
        ("社交信息流测投 D", 140, 0.033, 132, 0.52, 0.095),
    ]
}

UNIT_PRICE_MAP = {
    "业务线 A（高客单年度会员）": 3980.0,
    "业务线 B（核心增长训练营）": 1980.0,
    "业务线 C（新客体验转化线）": 3680.0,
}

def sort_channels_core_first(channels, proj_name):
    core_list = CORE_CHANNELS_MAP.get(proj_name, [])
    in_core = [c for c in core_list if c in channels]
    others = sorted([c for c in channels if c not in core_list])
    return in_core + others

def format_period_axis_label(p_str):
    if not p_str or pd.isna(p_str):
        return ""
    s = str(p_str).strip()
    clean = re.sub(r'[\(（].*?[\)）]', '', s).strip()
    return clean if clean else s

# 同一期次内相同渠道的智能加权聚合函数（解决新老课分段导致的单期双点怪异曲线）
def aggregate_channel_by_period(df_part):
    if df_part.empty: return pd.DataFrame()
    period_order = []
    for p in df_part['当前期次']:
        if p not in period_order:
            period_order.append(p)
    records = []
    for (p, ch), group in df_part.groupby(['当前期次', '渠道名称'], sort=False, as_index=False):
        leads = group['线索量'].sum()
        total_conv = group['总转化量'].sum()
        conv_rate = (total_conv / leads) if leads > 0 else 0.0
        live_conv = group['直播转化'].sum()
        chat_conv = group['私聊转化'].sum()
        live_share = (live_conv / total_conv) if total_conv > 0 else 0.0
        chat_share = (chat_conv / total_conv) if total_conv > 0 else 0.0
        cost = group['总成本'].sum()
        cac = (cost / leads) if leads > 0 else 0.0
        revenue = group['总销售额'].sum()
        roi = (revenue / cost) if cost > 0 else 0.0
        profit = group['总盈亏'].sum()
        refund = group['正式课退单'].sum()
        refund_denom = refund + total_conv
        refund_rate = (refund / refund_denom) if refund_denom > 0 else 0.0
        d_val = group['开课时间'].iloc[0] if '开课时间' in group.columns else ''
        records.append({
            '当前期次': p, '开课时间': d_val, '渠道名称': ch,
            '线索量': leads, '总转化率': conv_rate, '总转化量': total_conv,
            '直播转化': live_conv, '直播占比': live_share,
            '私聊转化': chat_conv, '私聊占比': chat_share,
            '单粉成本': cac, '总成本': cost, '总销售额': revenue,
            'roi': roi, '总盈亏': profit, '正式课退单': refund, '正式课总退单率': refund_rate
        })
    res = pd.DataFrame(records)
    res['sort_key'] = res['当前期次'].apply(lambda x: period_order.index(x) if x in period_order else 999)
    res.sort_values(by=['sort_key'], inplace=True)
    res.drop(columns=['sort_key'], inplace=True)
    return res

def aggregate_by_period_overall(df_part):
    if df_part.empty: return pd.DataFrame()
    period_order = []
    for p in df_part['当前期次']:
        if p not in period_order:
            period_order.append(p)
    records = []
    for p, group in df_part.groupby('当前期次', sort=False):
        leads = group['线索量'].sum()
        total_conv = group['总转化量'].sum()
        conv_rate = (total_conv / leads) if leads > 0 else 0.0
        live_conv = group['直播转化'].sum()
        chat_conv = group['私聊转化'].sum()
        live_share = (live_conv / total_conv) if total_conv > 0 else 0.0
        chat_share = (chat_conv / total_conv) if total_conv > 0 else 0.0
        cost = group['总成本'].sum()
        cac = (cost / leads) if leads > 0 else 0.0
        revenue = group['总销售额'].sum()
        roi = (revenue / cost) if cost > 0 else 0.0
        profit = group['总盈亏'].sum()
        refund = group['正式课退单'].sum()
        refund_denom = refund + total_conv
        refund_rate = (refund / refund_denom) if refund_denom > 0 else 0.0
        d_val = group['开课时间'].iloc[0] if '开课时间' in group.columns else ''
        records.append({
            '当前期次': p, '开课时间': d_val, '渠道名称': '全渠道大盘汇总',
            '线索量': leads, '总转化率': conv_rate, '总转化量': total_conv,
            '直播转化': live_conv, '直播占比': live_share,
            '私聊转化': chat_conv, '私聊占比': chat_share,
            '单粉成本': cac, '总成本': cost, '总销售额': revenue,
            'roi': roi, '总盈亏': profit, '正式课退单': refund, '正式课总退单率': refund_rate
        })
    res = pd.DataFrame(records)
    res['sort_key'] = res['当前期次'].apply(lambda x: period_order.index(x) if x in period_order else 999)
    res.sort_values(by=['sort_key'], inplace=True)
    res.drop(columns=['sort_key'], inplace=True)
    return res

def build_clean_column_config(has_period_col=False):
    cfg = {}
    if has_period_col:
        cfg["当前期次"] = st.column_config.TextColumn("期次", width="medium")
    cfg.update({
        "渠道名称": st.column_config.TextColumn("渠道", width="medium"),
        "线索量": st.column_config.NumberColumn("线索量 (人)", format="%d"),
        "总转化率": st.column_config.NumberColumn("🔥 总转化率", format="%.2f%%", help="总单数 / 线索量"),
        "总转化量": st.column_config.NumberColumn("总单数", format="%.1f"),
        "roi": st.column_config.NumberColumn("ROI", format="%.2f"),
        "总销售额": st.column_config.NumberColumn("总销售额", format="¥%.2f"),
        "总成本": st.column_config.NumberColumn("总成本", format="¥%.2f"),
        "总盈亏": st.column_config.NumberColumn("总盈亏", format="¥%.2f"),
        "单粉成本": st.column_config.NumberColumn("单粉成本", format="¥%.2f"),
        "正式课退单": st.column_config.NumberColumn("正式课退单", format="%d"),
        "正式课总退单率": st.column_config.NumberColumn("正式课退单率", format="%.2f%%", help="公式：正式课退单 / (正式课退单 + 总单数)"),
        "直播转化": st.column_config.NumberColumn("🎙️ 直播转化", format="%.1f", help="直播间现场成交单数"),
        "直播占比": st.column_config.NumberColumn("直播占比", format="%.1f%%", help="直播转化单数 / 总成交单数"),
        "私聊转化": st.column_config.NumberColumn("💬 私聊转化", format="%.1f", help="私域1v1私聊/社群跟进成交单数"),
        "私聊占比": st.column_config.NumberColumn("私聊占比", format="%.1f%%", help="私聊转化单数 / 总成交单数"),
    })
    return cfg

def prepare_display_dataframe(df_input, is_cross_period=False):
    df_out = df_input.copy()
    rate_cols = ['总转化率', '正式课总退单率', '直播占比', '私聊占比']
    for c in rate_cols:
        if c in df_out.columns:
            df_out[c] = df_out[c] * 100.0
    cols_order = []
    if is_cross_period and '当前期次' in df_out.columns:
        cols_order.append('当前期次')
    cols_order.extend([
        '渠道名称', '线索量', '总转化率', '总转化量',
        'roi', '总销售额', '总成本', '总盈亏', '单粉成本',
        '正式课退单', '正式课总退单率',
        '直播转化', '直播占比', '私聊转化', '私聊占比'
    ])
    valid_cols = [c for c in cols_order if c in df_out.columns]
    return df_out[valid_cols]

# =============================================================================
# 高仿真脱敏模拟 API 数据引擎（零密钥、零泄密、支持实时增量刷新）
# =============================================================================
def _make_record(proj_name, key_col, key_val, ch_name, leads, conv_rate, cac, live_ratio, refund_rate, unit_price, rng, date_val="", live_delta=0):
    leads = max(15, int(round(leads * rng.uniform(0.86, 1.16))) + live_delta)
    cr = max(0.015, conv_rate * rng.uniform(0.84, 1.18))
    total_conv = max(1, int(round(leads * cr)))
    actual_cr = total_conv / leads
    live_conv = int(round(total_conv * np.clip(live_ratio * rng.uniform(0.9, 1.1), 0.25, 0.85)))
    chat_conv = max(0, total_conv - live_conv)
    actual_cac = round(cac * rng.uniform(0.90, 1.12), 2)
    cost = round(leads * actual_cac, 2)
    revenue = round(total_conv * unit_price, 2)
    roi = (revenue / cost) if cost > 0 else 0.0
    profit = round(revenue - cost, 2)
    refund = int(round(total_conv * refund_rate * rng.uniform(0.6, 1.4)))
    refund_denom = refund + total_conv
    actual_ref_rate = (refund / refund_denom) if refund_denom > 0 else 0.0
    rec = {
        key_col: key_val,
        '渠道名称': ch_name,
        '线索量': leads,
        '总转化率': actual_cr,
        '总转化量': float(total_conv),
        '直播转化': float(live_conv),
        '直播占比': (live_conv / total_conv) if total_conv > 0 else 0.0,
        '私聊转化': float(chat_conv),
        '私聊占比': (chat_conv / total_conv) if total_conv > 0 else 0.0,
        '单粉成本': actual_cac,
        '总成本': cost,
        '总销售额': revenue,
        'roi': roi,
        '总盈亏': profit,
        '正式课退单': refund,
        '正式课总退单率': actual_ref_rate,
        'is_summary': False,
        '项目': proj_name,
    }
    if key_col == '当前期次':
        rec['开课时间'] = date_val
    return rec

@st.cache_data(ttl=600)
def load_all_dashboard_data(refresh_tick=0):
    all_data = {}
    period_templates = {
        "业务线 A（高客单年度会员）": [("第106期 (10.26)", "202X-10-26"), ("第105期 (10.19)", "202X-10-19"), ("第104期 (10.12)", "202X-10-12"), ("第103期 (10.05)", "202X-10-05"), ("第102期 (09.28)", "202X-09-28"), ("第101期 (09.21)", "202X-09-21")],
        "业务线 B（核心增长训练营）": [("第36期 (10.26)", "202X-10-26"), ("第35期 (10.19)", "202X-10-19"), ("第34期 (10.12)", "202X-10-12"), ("第33期 (10.06)", "202X-10-06"), ("第32期 (09.29)", "202X-09-29"), ("第31期 (09.22)", "202X-09-22")],
        "业务线 C（新客体验转化线）": [("第15期 (10.25)", "202X-10-25"), ("第14期 (10.18)", "202X-10-18"), ("第13期 (10.11)", "202X-10-11"), ("第12期 (10.04)", "202X-10-04"), ("第11期 (09.27)", "202X-09-27")],
    }
    months = ["202X年10月", "202X年09月", "202X年08月"]

    for p_idx, proj_name in enumerate(PROJECT_LIST):
        rng = np.random.default_rng(202601 + p_idx * 97)
        unit_price = UNIT_PRICE_MAP[proj_name]
        channels = ALL_CHANNELS_MAP[proj_name]

        # 1. 期次数据（最新一期随 refresh_tick 模拟实时微增线索）
        p_rows = []
        for idx, (p_label, p_date) in enumerate(period_templates[proj_name]):
            trend_boost = 1.0 + (len(period_templates[proj_name]) - idx) * 0.025
            for ch_name, base_leads, base_cr, base_cac, live_r, ref_r in channels:
                live_delta = int((refresh_tick * 3) % 15) if idx == 0 else 0
                p_rows.append(_make_record(
                    proj_name, '当前期次', p_label, ch_name,
                    base_leads, base_cr * trend_boost, base_cac, live_r, ref_r,
                    unit_price, rng, date_val=p_date, live_delta=live_delta
                ))
        period_df = pd.DataFrame(p_rows)

        # 2. 月度数据
        m_rows = []
        for m_idx, m_label in enumerate(months):
            m_boost = 1.0 + (2 - m_idx) * 0.03
            for ch_name, base_leads, base_cr, base_cac, live_r, ref_r in channels:
                live_delta = int((refresh_tick * 4) % 20) if m_idx == 0 else 0
                m_rows.append(_make_record(
                    proj_name, '月份标签', m_label, ch_name,
                    base_leads * 4, base_cr * m_boost, base_cac, live_r, ref_r,
                    unit_price, rng, live_delta=live_delta
                ))
        monthly_df = pd.DataFrame(m_rows)

        # 3. 项目 A 分团队月度对比数据（A组/B组/C组）
        team_monthly_df = pd.DataFrame()
        if proj_name == "业务线 A（高客单年度会员）":
            tm_rows = []
            teams_cfg = [
                ("10月运营A组", 1.15, 1.08, 0.96),
                ("10月运营B组", 0.95, 0.98, 1.02),
                ("10月运营C组", 0.82, 1.12, 0.92),
            ]
            for t_name, vol_f, cr_f, cac_f in teams_cfg:
                for ch_name, base_leads, base_cr, base_cac, live_r, ref_r in channels:
                    tm_rows.append(_make_record(
                        proj_name, '月份标签', t_name, ch_name,
                        base_leads * 1.4 * vol_f, base_cr * cr_f, base_cac * cac_f,
                        live_r, ref_r, unit_price, rng
                    ))
            team_monthly_df = pd.DataFrame(tm_rows)

        all_data[proj_name] = {
            "period_df": period_df,
            "monthly_df": monthly_df,
            "team_monthly_df": team_monthly_df,
        }
    return all_data

if "refresh_tick" not in st.session_state:
    st.session_state["refresh_tick"] = 0
if "last_sync_time" not in st.session_state:
    st.session_state["last_sync_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 侧边栏：项目选择与实时刷新模拟
with st.sidebar:
    st.markdown("## 📊 渠道 ROI 实时看板")
    st.caption("作者：吴幸晖 ｜ 脱敏公开演示版")

    st.markdown("""
    <div style='background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 8px 12px; margin-bottom: 10px;'>
        <div style='color: #166534; font-size: 12px; font-weight: 700;'>🟢 模拟 API 实时引擎已连接</div>
        <div style='color: #15803d; font-size: 11px; margin-top: 2px;'>已脱敏处理 · 免密公开演示模式</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 模拟实时拉取 API 数据", use_container_width=True, type="primary"):
        st.session_state["refresh_tick"] += 1
        st.session_state["last_sync_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.cache_data.clear()
        st.rerun()

    st.caption(f"最近同步时间：{st.session_state['last_sync_time']}")
    st.markdown("---")
    st.markdown("### 🏢 切换分析业务线")
    selected_project = st.radio(
        "切换分析业务线",
        options=PROJECT_LIST,
        index=0,
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.markdown("""
    <div style='font-size:11.5px; color:#64748b; line-height:1.6;'>
        <b>核心工程设计说明：</b><br>
        • 生产环境直连 CRM 与飞书开放平台 API<br>
        • 同期次分段同名渠道自动加权聚合<br>
        • 退单率严格按 <code>退单/(退单+总单数)</code> 计算<br>
        • MySQL 独立反向校验 + 人工卡点验收
    </div>
    """, unsafe_allow_html=True)

# 加载脱敏模拟数据
data_bundle = load_all_dashboard_data(st.session_state["refresh_tick"])
current_proj_data = data_bundle.get(selected_project, {})
period_df = current_proj_data.get("period_df", pd.DataFrame())
monthly_df = current_proj_data.get("monthly_df", pd.DataFrame())
team_monthly_df = current_proj_data.get("team_monthly_df", pd.DataFrame())

# 页面头部
st.markdown(f"<div class='project-pill'>当前业务线：{selected_project}</div>", unsafe_allow_html=True)
st.title(f"📈 {selected_project} - 渠道投放与转化分析中心")

st.markdown("""
<div class='demo-banner'>
    🛡️ <strong>作品集脱敏演示说明</strong>：本看板完整还原生产环境架构与交互功能；为保护商业机密，已移除真实 CRM/飞书密钥及企业敏感数据，当前展示为高仿真模拟接口数据。点击左侧 <b>「🔄 模拟实时拉取 API 数据」</b> 可体验动态增量刷新效果。
</div>
""", unsafe_allow_html=True)

with st.expander("📐 查看核心指标统计口径与数据校验规范（Analytics Engineering 亮点）", expanded=False):
    st.markdown("""
    - **总转化率**：`总转化量 / 线索量`（跨期与大盘汇总采用加权聚合，杜绝均值再平均的统计偏差）
    - **正式课退单率**：`正式课退单 / (正式课退单 + 总转化量)`（统一销售、CRM、财务三方退费冲销口径）
    - **渠道分段智能合并**：针对同一期次内新老课分段导致的同名渠道重复记录，通过 `aggregate_channel_by_period` 自动完成加权合并，确保趋势图单期单点无歧义
    - **数据准确性核验**：生产环境中每日同步 20+ 张核心报表，坚持 **MySQL 独立聚合对账 + 抽样回源比对 + 边界异常测试**，日均耗时由 3 小时压缩至 0.5 小时
    """)

# 三个一级导航标签
tab_period, tab_cross_period, tab_month = st.tabs(["🎯 期次明细复盘", "📈 渠道跨期对比", "🗓️ 月度数据看板"])

# =========================================================================
# 标签 1：期次明细复盘 (单期横切面)
# =========================================================================
with tab_period:
    if period_df.empty:
        st.warning("暂无期次数据")
    else:
        all_periods = [p for p in period_df['当前期次'].dropna().unique() if not any(x in str(p) for x in ['合计', '总计', 'nan', 'None'])]
        
        filter_col1, filter_col2, filter_col3 = st.columns([1.8, 2.5, 1.7])
        with filter_col1:
            selected_period = st.selectbox("📌 选择复盘期次", options=all_periods, index=0 if all_periods else None)
        
        p_filtered = period_df[(period_df['当前期次'] == selected_period) & (~period_df['is_summary'])].copy()
        
        # 期次内同名渠道合并
        p_filtered = aggregate_channel_by_period(p_filtered)
        
        # 渠道排序：核心主要渠道排在最前
        raw_channels = list(p_filtered['渠道名称'].dropna().unique())
        sorted_channels = sort_channels_core_first(raw_channels, selected_project)
        core_channels = CORE_CHANNELS_MAP.get(selected_project, [])
        in_core_selected = [c for c in core_channels if c in sorted_channels]
        
        with filter_col2:
            scope_mode = st.radio("渠道聚焦模式", options=["⭐ 仅看核心主要渠道", "全部渠道"], horizontal=True, label_visibility="collapsed", key="p_scope_radio")
            default_channels = in_core_selected if (scope_mode.startswith("⭐") and in_core_selected) else sorted_channels
            selected_channels = st.multiselect("🔍 筛选具体渠道", options=sorted_channels, default=default_channels, key=f"p_channels_select_{scope_mode}")
            
        with filter_col3:
            sort_by = st.selectbox("🔃 排序依据", options=["总转化率（从高到低）", "线索量（从多到少）", "ROI（从高到低）", "总单数（从多到少）"])

        if selected_channels:
            p_display = p_filtered[p_filtered['渠道名称'].isin(selected_channels)].copy()
        else:
            p_display = p_filtered.copy()

        if sort_by == "总转化率（从高到低）":
            p_display.sort_values(by="总转化率", ascending=False, inplace=True)
        elif sort_by == "线索量（从多到少）":
            p_display.sort_values(by="线索量", ascending=False, inplace=True)
        elif sort_by == "ROI（从高到低）":
            p_display.sort_values(by="roi", ascending=False, inplace=True)
        elif sort_by == "总单数（从多到少）":
            p_display.sort_values(by="总转化量", ascending=False, inplace=True)

        total_leads = p_display['线索量'].sum()
        total_conv = p_display['总转化量'].sum()
        overall_conv_rate = (total_conv / total_leads) if total_leads > 0 else 0.0
        
        total_live = p_display['直播转化'].sum()
        total_chat = p_display['私聊转化'].sum()
        live_ratio = (total_live / total_conv) if total_conv > 0 else 0.0
        chat_ratio = (total_chat / total_conv) if total_conv > 0 else 0.0

        total_cost = p_display['总成本'].sum()
        total_revenue = p_display['总销售额'].sum()
        period_roi = (total_revenue / total_cost) if total_cost > 0 else 0.0
        total_profit = p_display['总盈亏'].sum()
        avg_cac = (total_cost / total_leads) if total_leads > 0 else 0.0
        
        total_refund_orders = p_display['正式课退单'].sum()
        # 【核心修正】：退单率严格按照 = 退单 / (退单 + 总单数)
        total_refund_denom = total_refund_orders + total_conv
        total_refund_rate = (total_refund_orders / total_refund_denom) if total_refund_denom > 0 else 0.0

        # --- 核心指标大卡片 ---
        st.markdown("### 🎯 核心经营指标（本期大盘）")
        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns([1.3, 1, 1.1, 1])
        
        with kpi_col1:
            st.markdown(f"""
            <div class='metric-hero-card'>
                <div class='metric-hero-title'>总转化率</div>
                <div class='metric-hero-value'>{overall_conv_rate:.2%}</div>
                <div class='metric-hero-sub'>总成交: <b>{total_conv:g} 单</b> / 消耗线索: <b>{int(total_leads):,} 人</b></div>
            </div>
            """, unsafe_allow_html=True)
            
        with kpi_col2:
            st.markdown(f"""
            <div class='metric-sub-card'>
                <div class='metric-sub-title'>总单数</div>
                <div class='metric-sub-value' style='color:#1d4ed8;'>{total_conv:g} <span style='font-size:14px;font-weight:normal;'>单</span></div>
                <div class='metric-sub-badge' style='background:#eff6ff;color:#1e40af;'>单粉成本 (CAC): ¥{avg_cac:.2f}</div>
            </div>
            """, unsafe_allow_html=True)

        with kpi_col3:
            roi_color = "#16a34a" if period_roi >= 1 else "#dc2626"
            roi_badge_bg = "#f0fdf4" if period_roi >= 1 else "#fef2f2"
            roi_badge_color = "#166534" if period_roi >= 1 else "#991b1b"
            st.markdown(f"""
            <div class='metric-sub-card'>
                <div class='metric-sub-title'>ROI</div>
                <div class='metric-sub-value' style='color:{roi_color};'>{period_roi:.2f}</div>
                <div class='metric-sub-badge' style='background:{roi_badge_bg};color:{roi_badge_color};'>销售额 ¥{total_revenue:,.0f} | 成本 ¥{total_cost:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)

        with kpi_col4:
            refund_badge_bg = "#fef2f2" if total_refund_rate > 0.05 else "#f0fdf4"
            refund_badge_color = "#991b1b" if total_refund_rate > 0.05 else "#166534"
            st.markdown(f"""
            <div class='metric-sub-card'>
                <div class='metric-sub-title'>正式课退单</div>
                <div class='metric-sub-value' style='color:#dc2626;'>{int(total_refund_orders)} <span style='font-size:14px;font-weight:normal;'>单</span></div>
                <div class='metric-sub-badge' style='background:{refund_badge_bg};color:{refund_badge_color};'>正式课退单率: {total_refund_rate:.2%}</div>
            </div>
            """, unsafe_allow_html=True)

        fin_col1, fin_col2, fin_col3, fin_col4 = st.columns(4)
        with fin_col1:
            st.metric("总销售额", f"¥{total_revenue:,.2f}")
        with fin_col2:
            st.metric("投放总成本", f"¥{total_cost:,.2f}")
        with fin_col3:
            st.metric("本期总盈亏", f"¥{total_profit:,.2f}", delta="盈利" if total_profit >= 0 else "亏损", delta_color="normal" if total_profit >= 0 else "inverse")
        with fin_col4:
            st.metric("单粉平均成本 (CAC)", f"¥{avg_cac:.2f}")

        st.markdown("---")
        
        # 图表展示（总转化率与 ROI 并列呈现，剔除多余子模块）
        st.markdown("### 📊 渠道转化率与 ROI 表现")
        chart_col1, chart_col2 = st.columns([1, 1])
        with chart_col1:
            top_conv_df = p_display.sort_values(by="总转化率", ascending=False)
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                x=top_conv_df["渠道名称"],
                y=top_conv_df["总转化率"],
                text=top_conv_df["总转化率"].apply(lambda x: f"{x:.2%}"),
                textposition='outside',
                marker_color='#2563eb',
                cliponaxis=False,
                customdata=np.stack((
                    top_conv_df['线索量'].astype(int),
                    top_conv_df['总转化量']
                ), axis=-1),
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    + "🔥 总转化率: <b>%{text}</b><br>"
                    + "👥 消耗线索: <b>%{customdata[0]:,} 人</b><br>"
                    + "🎯 成交单数: <b>%{customdata[1]:g} 单</b>"
                    + "<extra></extra>"
                )
            ))
            max_c = top_conv_df["总转化率"].max() if not top_conv_df.empty else 0.05
            fig_bar.update_layout(
                title="总转化率",
                xaxis_title="",
                yaxis_title="总转化率",
                yaxis_tickformat='.1%',
                yaxis_range=[0, max(max_c * 1.25, 0.05)],
                xaxis=dict(
                    tickangle=-15 if len(top_conv_df) > 3 else 0,
                    tickfont=dict(size=12, color="#334155"),
                    showgrid=True,
                    gridcolor="#f1f5f9"
                ),
                yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
                height=380,
                margin=dict(l=10, r=20, t=50, b=50)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with chart_col2:
            top_roi_df = p_display.sort_values(by="roi", ascending=False)
            bar_colors = ['#10b981' if r >= 1.0 else '#3b82f6' for r in top_roi_df['roi']]
            fig_roi = go.Figure()
            fig_roi.add_trace(go.Bar(
                x=top_roi_df["渠道名称"],
                y=top_roi_df["roi"],
                text=top_roi_df["roi"].apply(lambda x: f"{x:.2f}"),
                textposition='outside',
                marker_color=bar_colors,
                cliponaxis=False,
                customdata=np.stack((
                    top_roi_df['总销售额'],
                    top_roi_df['总成本'],
                    top_roi_df['总盈亏']
                ), axis=-1),
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    + "💹 ROI: <b>%{text}</b><br>"
                    + "💰 销售额: <b>¥%{customdata[0]:,.2f}</b><br>"
                    + "💸 成本: <b>¥%{customdata[1]:,.2f}</b><br>"
                    + "⚖️ 盈亏: <b>¥%{customdata[2]:,.2f}</b>"
                    + "<extra></extra>"
                )
            ))
            fig_roi.add_hline(
                y=1.0,
                line_dash="dash",
                line_color="#ef4444",
                line_width=1.5,
                annotation_text="保本 1.0",
                annotation_position="top left",
                annotation_font_color="#ef4444"
            )
            max_r = top_roi_df["roi"].max() if not top_roi_df.empty else 1.2
            fig_roi.update_layout(
                title="ROI",
                xaxis_title="",
                yaxis_title="ROI",
                yaxis_range=[0, max(max_r * 1.25, 1.2)],
                xaxis=dict(
                    tickangle=-15 if len(top_roi_df) > 3 else 0,
                    tickfont=dict(size=12, color="#334155"),
                    showgrid=True,
                    gridcolor="#f1f5f9"
                ),
                yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
                height=380,
                margin=dict(l=10, r=20, t=50, b=50)
            )
            st.plotly_chart(fig_roi, use_container_width=True)

        st.markdown("---")
        
        # 详细数据表格（纯数值呈现，无进度条，精简高价值商业核心列）
        st.markdown(f"### 📋 【{selected_period}】渠道详细数据透视 (共 {len(p_display)} 个渠道)")
        
        p_table_df = prepare_display_dataframe(p_display, is_cross_period=False)
        p_col_cfg = build_clean_column_config(has_period_col=False)
        
        st.dataframe(
            p_table_df,
            column_config=p_col_cfg,
            use_container_width=True,
            hide_index=True
        )
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            export_cols = [
                '渠道名称', '线索量', '总转化率', '总转化量',
                'roi', '总销售额', '总成本', '总盈亏', '单粉成本',
                '正式课退单', '正式课总退单率',
                '直播转化', '直播占比', '私聊转化', '私聊占比'
            ]
            valid_export_cols = [c for c in export_cols if c in p_display.columns]
            p_display[valid_export_cols].to_excel(writer, index=False, sheet_name=selected_period[:30])
        st.download_button(
            label=f"📥 导出【{selected_period}】渠道数据 Excel",
            data=buffer.getvalue(),
            file_name=f"{selected_project}_{selected_period}_渠道数据.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# =========================================================================
# 标签 2：渠道跨期对比 (解决核心痛点：多期纵向无歧义对比)
# =========================================================================
with tab_cross_period:
    st.markdown("### 📈 同一渠道跨期走势与多期纵向对比")
    st.caption("💡 针对同一期次内存在的多段同名渠道（如新课与老课），系统已自动完成真实加权合并，确保各期次折线点唯一、数据精准。")
    
    if period_df.empty:
        st.warning("暂无期次数据")
    else:
        all_detail_df = period_df[~period_df['is_summary']].copy()
        
        avail_channels = list(all_detail_df['渠道名称'].dropna().unique())
        sorted_cross_channels = sort_channels_core_first(avail_channels, selected_project)
        core_channels = CORE_CHANNELS_MAP.get(selected_project, [])
        default_target_ch = [c for c in core_channels if c in sorted_cross_channels]
        if not default_target_ch and sorted_cross_channels:
            default_target_ch = [sorted_cross_channels[0]]
            
        # 跨期分析视角选择
        cp_view_mode = st.radio(
            "📊 跨期分析视角",
            options=["🌐 全期次大盘汇总（按期汇总·看整期表现）", "🔍 细分渠道跨期对比（选具体渠道）"],
            horizontal=True,
            help="全期次大盘汇总模式下，系统自动将所有渠道合并为整期宏观表现；细分渠道对比模式下可对比特定渠道。"
        )
        
        c_filter1, c_filter2 = st.columns([3, 3])
        
        if cp_view_mode.startswith("🌐"):
            with c_filter1:
                st.info("💡 **当前为【全期次大盘汇总】模式**：已自动将所有渠道合并为整期宏观表现，无多渠道线条干扰。")
            selected_comp_channels = sorted_cross_channels
            is_period_overall = True
        else:
            with c_filter1:
                selected_comp_channels = st.multiselect(
                    "📌 选择需要追踪对比的渠道（支持多选并在下方同图对比）",
                    options=sorted_cross_channels,
                    default=default_target_ch[:1]
                )
            # 用户在细分模式下如果 select all，也自动智能切换为大盘汇总，满足“全选时就不看渠道搞得乱七八糟”的需求
            is_period_overall = (len(selected_comp_channels) == len(sorted_cross_channels))
            if is_period_overall and selected_comp_channels:
                st.caption("✨ 已全选所有渠道，系统自动为您折叠为【全期次大盘汇总】单条曲线，防止多线条杂乱。")
            
        if not selected_comp_channels:
            st.info("👈 请在上方选择至少一个渠道以查看跨期对比数据。")
        else:
            raw_comp_df = all_detail_df[all_detail_df['渠道名称'].isin(selected_comp_channels)].copy()
            
            # 根据是否汇总为期次总计，选择不同的聚合函数
            if is_period_overall:
                comp_df = aggregate_by_period_overall(raw_comp_df)
            else:
                comp_df = aggregate_channel_by_period(raw_comp_df)
            
            all_comp_periods = list(comp_df['当前期次'].unique())
            with c_filter2:
                selected_comp_periods = st.multiselect(
                    "📅 选择对比的业务期次（默认全选）",
                    options=all_comp_periods,
                    default=all_comp_periods,
                    format_func=format_period_axis_label
                )
                
            comp_df = comp_df[comp_df['当前期次'].isin(selected_comp_periods)].copy()
            
            if comp_df.empty:
                st.warning("选定范围无数据")
            else:
                # 生成双行优化的期次展示标签（消除重叠倾斜拥挤，横向清晰易读）
                comp_df['当前期次_展示'] = comp_df['当前期次'].apply(format_period_axis_label)

                cp_leads = comp_df['线索量'].sum()
                cp_conv = comp_df['总转化量'].sum()
                cp_conv_rate = (cp_conv / cp_leads) if cp_leads > 0 else 0.0
                
                cp_live = comp_df['直播转化'].sum()
                cp_chat = comp_df['私聊转化'].sum()
                cp_live_ratio = (cp_live / cp_conv) if cp_conv > 0 else 0.0
                cp_chat_ratio = (cp_chat / cp_conv) if cp_conv > 0 else 0.0

                cp_cost = comp_df['总成本'].sum()
                cp_rev = comp_df['总销售额'].sum()
                cp_roi = (cp_rev / cp_cost) if cp_cost > 0 else 0.0
                cp_profit = comp_df['总盈亏'].sum()
                
                cp_refund = comp_df['正式课退单'].sum()
                # 【核心修正】：正式课退单率 = 退单 / (退单 + 总单数)
                cp_refund_denom = cp_refund + cp_conv
                cp_refund_rate = (cp_refund / cp_refund_denom) if cp_refund_denom > 0 else 0.0
                
                # 顶部加权跨期汇总卡片
                st.markdown(f"#### 📊 所选渠道在所选 {len(selected_comp_periods)} 个期次中的【累计加权大盘】")
                cp_kpi1, cp_kpi2, cp_kpi3, cp_kpi4 = st.columns([1.3, 1, 1.1, 1])
                with cp_kpi1:
                    st.markdown(f"""
                    <div class='metric-hero-card' style='background: linear-gradient(135deg, #1e3a8a 0%, #312e81 100%);'>
                        <div class='metric-hero-title'>总转化率</div>
                        <div class='metric-hero-value'>{cp_conv_rate:.2%}</div>
                        <div class='metric-hero-sub'>跨期累计成交: <b>{cp_conv:g} 单</b> / 累计线索: <b>{int(cp_leads):,} 人</b></div>
                    </div>
                    """, unsafe_allow_html=True)
                with cp_kpi2:
                    st.markdown(f"""
                    <div class='metric-sub-card'>
                        <div class='metric-sub-title'>总单数</div>
                        <div class='metric-sub-value' style='color:#1d4ed8;'>{cp_conv:g} <span style='font-size:14px;font-weight:normal;'>单</span></div>
                        <div class='metric-sub-badge' style='background:#eff6ff;color:#1e40af;'>累计线索: {int(cp_leads):,} 人</div>
                    </div>
                    """, unsafe_allow_html=True)
                with cp_kpi3:
                    cp_roi_color = "#16a34a" if cp_roi >= 1 else "#dc2626"
                    cp_roi_badge_bg = "#f0fdf4" if cp_roi >= 1 else "#fef2f2"
                    cp_roi_badge_color = "#166534" if cp_roi >= 1 else "#991b1b"
                    st.markdown(f"""
                    <div class='metric-sub-card'>
                        <div class='metric-sub-title'>ROI</div>
                        <div class='metric-sub-value' style='color:{cp_roi_color};'>{cp_roi:.2f}</div>
                        <div class='metric-sub-badge' style='background:{cp_roi_badge_bg};color:{cp_roi_badge_color};'>销售额 ¥{cp_rev:,.0f} | 成本 ¥{cp_cost:,.0f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with cp_kpi4:
                    cp_ref_bg = "#fef2f2" if cp_refund_rate > 0.05 else "#f0fdf4"
                    cp_ref_color = "#991b1b" if cp_refund_rate > 0.05 else "#166534"
                    st.markdown(f"""
                    <div class='metric-sub-card'>
                        <div class='metric-sub-title'>正式课退单</div>
                        <div class='metric-sub-value' style='color:#dc2626;'>{int(cp_refund)} <span style='font-size:14px;font-weight:normal;'>单</span></div>
                        <div class='metric-sub-badge' style='background:{cp_ref_bg};color:{cp_ref_color};'>正式课退单率: {cp_refund_rate:.2%}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                cp_fin1, cp_fin2, cp_fin3, cp_fin4 = st.columns(4)
                with cp_fin1:
                    st.metric("跨期总销售额", f"¥{cp_rev:,.2f}")
                with cp_fin2:
                    st.metric("跨期总成本", f"¥{cp_cost:,.2f}")
                with cp_fin3:
                    st.metric("跨期总盈亏", f"¥{cp_profit:,.2f}", delta="盈利" if cp_profit >= 0 else "亏损", delta_color="normal" if cp_profit >= 0 else "inverse")
                with cp_fin4:
                    cp_cac = (cp_cost / cp_leads) if cp_leads > 0 else 0.0
                    st.metric("跨期单粉成本", f"¥{cp_cac:.2f}")

                st.markdown("---")
                
                # --- 图表区：纯单点无歧义折线图 与 ROI对比图（直接并列，去除多余子标签） ---
                st.markdown("#### 📉 跨期走势与 ROI 对比")
                cp_chart1, cp_chart2 = st.columns([1.3, 1])
                with cp_chart1:
                    # 转化率条形柱状图（根据要求改为条形柱状图，与ROI图保持一致清晰直观）
                    if is_period_overall:
                        customdata_trend = np.stack((
                            comp_df['当前期次_展示'],
                            comp_df['总转化率'].apply(lambda x: f"{x:.2%}"),
                            comp_df['线索量'].astype(int)
                        ), axis=-1)
                        
                        fig_trend = go.Figure()
                        fig_trend.add_trace(go.Bar(
                            x=comp_df['当前期次_展示'],
                            y=comp_df['总转化率'],
                            text=comp_df['总转化率'].apply(lambda x: f"{x:.2%}"),
                            textposition='outside',
                            marker_color='#2563eb',
                            cliponaxis=False,
                            customdata=customdata_trend,
                            hovertemplate=(
                                "<b>%{customdata[0]}</b><br>"
                                + "🔥 总转化率: <b>%{customdata[1]}</b><br>"
                                + "👥 消耗线索: <b>%{customdata[2]:,} 人</b>"
                                + "<extra></extra>"
                            )
                        ))
                        max_c = comp_df['总转化率'].max() if not comp_df.empty else 0.05
                        fig_trend.update_layout(
                            title="总转化率",
                            xaxis=dict(
                                tickangle=0,
                                tickfont=dict(size=11, color="#334155"),
                                showgrid=True,
                                gridcolor="#f1f5f9",
                                gridwidth=1
                            ),
                            yaxis=dict(
                                title="总转化率",
                                tickformat='.1%',
                                range=[0, max(max_c * 1.25, 0.05)],
                                showgrid=True,
                                gridcolor="#f1f5f9"
                            ),
                            height=400,
                            margin=dict(l=10, r=20, t=50, b=50)
                        )
                    else:
                        fig_trend = px.bar(
                            comp_df,
                            x="当前期次_展示",
                            y="总转化率",
                            color="渠道名称",
                            barmode="group",
                            text=comp_df["总转化率"].apply(lambda x: f"{x:.2%}"),
                            title="总转化率"
                        )
                        for trace in fig_trend.data:
                            ch_name = trace.name
                            sub_df = comp_df[comp_df['渠道名称'] == ch_name]
                            c_data = np.stack((
                                sub_df['当前期次_展示'],
                                sub_df['总转化率'].apply(lambda x: f"{x:.2%}"),
                                sub_df['线索量'].astype(int),
                                sub_df['渠道名称']
                            ), axis=-1)
                            trace.customdata = c_data
                            trace.hovertemplate = (
                                "<b>%{customdata[0]}</b><br>"
                                + "渠道: %{customdata[3]}<br>"
                                + "🔥 总转化率: <b>%{customdata[1]}</b><br>"
                                + "👥 消耗线索: <b>%{customdata[2]:,} 人</b>"
                                + "<extra></extra>"
                            )
                            trace.textposition = "outside"
                            trace.cliponaxis = False
                        max_c = comp_df['总转化率'].max() if not comp_df.empty else 0.05
                        fig_trend.update_layout(
                            yaxis_tickformat='.1%',
                            yaxis_range=[0, max(max_c * 1.25, 0.05)],
                            xaxis=dict(
                                tickangle=0,
                                tickfont=dict(size=11, color="#334155"),
                                showgrid=True,
                                gridcolor="#f1f5f9",
                                gridwidth=1
                            ),
                            yaxis_title="总转化率",
                            height=400,
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                            margin=dict(l=10, r=20, t=50, b=50)
                        )
                    st.plotly_chart(fig_trend, use_container_width=True)
                    
                with cp_chart2:
                    # ROI 投入产出对比图
                    if is_period_overall:
                        bar_colors = ['#10b981' if r >= 1.0 else '#3b82f6' for r in comp_df['roi']]
                        customdata_roi = np.stack((
                            comp_df['当前期次_展示'],
                            comp_df['roi'],
                            comp_df['总销售额'],
                            comp_df['总成本'],
                            comp_df['总盈亏']
                        ), axis=-1)

                        fig_roi = go.Figure()
                        fig_roi.add_trace(go.Bar(
                            x=comp_df['当前期次_展示'],
                            y=comp_df['roi'],
                            text=comp_df['roi'].apply(lambda x: f"{x:.2f}"),
                            textposition='outside',
                            marker_color=bar_colors,
                            cliponaxis=False,
                            customdata=customdata_roi,
                            hovertemplate=(
                                "<b>%{customdata[0]}</b><br>"
                                + "💹 ROI: <b>%{customdata[1]:.2f}</b><br>"
                                + "💰 总销售额: <b>¥%{customdata[2]:,.2f}</b><br>"
                                + "💸 投放成本: <b>¥%{customdata[3]:,.2f}</b><br>"
                                + "⚖️ 本期盈亏: <b>¥%{customdata[4]:,.2f}</b>"
                                + "<extra></extra>"
                            )
                        ))
                        fig_roi.add_hline(
                            y=1.0,
                            line_dash="dash",
                            line_color="#ef4444",
                            line_width=1.5,
                            annotation_text="保本 1.0",
                            annotation_position="top left",
                            annotation_font_color="#ef4444"
                        )
                        max_roi_p = comp_df['roi'].max() if not comp_df.empty else 1.2
                        fig_roi.update_layout(
                            title="ROI",
                            xaxis=dict(
                                tickangle=0,
                                tickfont=dict(size=11, color="#334155"),
                                showgrid=True,
                                gridcolor="#f1f5f9",
                                gridwidth=1
                            ),
                            yaxis=dict(
                                title="ROI",
                                rangemode='tozero',
                                range=[0, max(max_roi_p * 1.25, 1.2)],
                                showgrid=True,
                                gridcolor="#f1f5f9"
                            ),
                            height=400,
                            margin=dict(l=10, r=20, t=50, b=50)
                        )
                    else:
                        fig_roi = px.bar(
                            comp_df,
                            x="当前期次_展示",
                            y="roi",
                            color="渠道名称",
                            barmode="group",
                            text=comp_df["roi"].apply(lambda x: f"{x:.2f}"),
                            title="ROI"
                        )
                        for trace in fig_roi.data:
                            ch_name = trace.name
                            sub_df = comp_df[comp_df['渠道名称'] == ch_name]
                            c_data = np.stack((
                                sub_df['当前期次_展示'],
                                sub_df['roi'],
                                sub_df['总销售额'],
                                sub_df['总成本'],
                                sub_df['总盈亏'],
                                sub_df['渠道名称']
                            ), axis=-1)
                            trace.customdata = c_data
                            trace.hovertemplate = (
                                "<b>%{customdata[0]}</b><br>"
                                + "渠道: %{customdata[5]}<br>"
                                + "💹 ROI: <b>%{customdata[1]:.2f}</b><br>"
                                + "💰 销售额: <b>¥%{customdata[2]:,.2f}</b><br>"
                                + "💸 成本: <b>¥%{customdata[3]:,.2f}</b>"
                                + "<extra></extra>"
                            )
                            trace.textposition = "outside"
                            trace.cliponaxis = False
                        fig_roi.add_hline(
                            y=1.0,
                            line_dash="dash",
                            line_color="#ef4444",
                            line_width=1.5,
                            annotation_text="保本 1.0",
                            annotation_position="top left",
                            annotation_font_color="#ef4444"
                        )
                        max_roi_p = comp_df['roi'].max() if not comp_df.empty else 1.2
                        fig_roi.update_layout(
                            xaxis=dict(
                                tickangle=0,
                                tickfont=dict(size=11, color="#334155"),
                                showgrid=True,
                                gridcolor="#f1f5f9",
                                gridwidth=1
                            ),
                            yaxis_title="ROI",
                            yaxis_range=[0, max(max_roi_p * 1.25, 1.2)],
                            height=400,
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                            margin=dict(l=10, r=20, t=50, b=50)
                        )
                    st.plotly_chart(fig_roi, use_container_width=True)

                st.markdown("---")
                
                # --- 跨期详细数据表格（纯数值呈现，无进度条，精简高价值商业核心列） ---
                table_title = f"#### 📋 全期次大盘汇总对照明细表 (共 {len(comp_df)} 期)" if is_period_overall else f"#### 📋 渠道跨期详细对照明细表 (共 {len(comp_df)} 条期次记录)"
                st.markdown(table_title)
                
                cp_table_df = prepare_display_dataframe(comp_df, is_cross_period=True)
                cp_col_cfg = build_clean_column_config(has_period_col=True)
                
                st.dataframe(
                    cp_table_df,
                    column_config=cp_col_cfg,
                    use_container_width=True,
                    hide_index=True
                )
                
                cp_buffer = io.BytesIO()
                with pd.ExcelWriter(cp_buffer, engine='openpyxl') as writer:
                    export_cols = [
                        '当前期次', '渠道名称', '线索量', '总转化率', '总转化量',
                        '直播转化', '直播占比', '私聊转化', '私聊占比',
                        '单粉成本', '总成本', '总销售额', 'roi', '总盈亏',
                        '正式课退单', '正式课总退单率'
                    ]
                    valid_export_cols = [c for c in export_cols if c in comp_df.columns]
                    comp_df[valid_export_cols].to_excel(writer, index=False, sheet_name="跨期对比")
                st.download_button(
                    label="📥 导出渠道跨期对比 Excel",
                    data=cp_buffer.getvalue(),
                    file_name=f"{selected_project}_渠道跨期对比.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

# =========================================================================
# 标签 3：月度数据看板 (全量渠道正常展现，核心经营指标)
# =========================================================================
with tab_month:
    if monthly_df.empty:
        st.warning("暂无月度数据")
    else:
        m_view_type = "全项目月度汇总"
        if selected_project == "业务线 A（高客单年度会员）" and not team_monthly_df.empty:
            m_view_type = st.radio("视角切换", options=["全项目月度汇总", "分团队月度数据 (运营A组/运营B组/运营C组)"], horizontal=True)

        is_team_comparison = m_view_type.startswith("分团队")
        
        if not is_team_comparison:
            # -------------------------------------------------------------
            # 模式 A：全项目月度汇总
            # -------------------------------------------------------------
            target_monthly_df = monthly_df
            avail_months = target_monthly_df['月份标签'].dropna().unique().tolist()
            avail_months = [m for m in avail_months if not any(x in str(m) for x in ['合计', '总计', 'nan', 'None'])]
            
            m_filter_col1, m_filter_col2 = st.columns([2, 4])
            with m_filter_col1:
                selected_month_period = st.selectbox("📅 选择月份", options=avail_months, index=0 if avail_months else None)
                
            m_filtered = target_monthly_df[(target_monthly_df['月份标签'] == selected_month_period) & (~target_monthly_df['is_summary'])].copy()
            
            raw_m_channels = list(m_filtered['渠道名称'].dropna().unique())
            sorted_m_channels = sort_channels_core_first(raw_m_channels, selected_project)
            core_channels = CORE_CHANNELS_MAP.get(selected_project, [])
            in_core_m = [c for c in core_channels if c in sorted_m_channels]
            
            with m_filter_col2:
                m_scope = st.radio("月度渠道聚焦", options=["⭐ 仅看核心主要渠道", "全部渠道"], horizontal=True, label_visibility="collapsed", key="m_scope_radio")
                default_m = in_core_m if (m_scope.startswith("⭐") and in_core_m) else sorted_m_channels
                selected_m_channels = st.multiselect("🔍 筛选渠道", options=sorted_m_channels, default=default_m, key=f"m_channels_select_{m_scope}")
                
            if selected_m_channels:
                m_display = m_filtered[m_filtered['渠道名称'].isin(selected_m_channels)].copy()
            else:
                m_display = m_filtered.copy()

            m_leads = m_display['线索量'].sum()
            m_conv = m_display['总转化量'].sum()
            m_conv_rate = (m_conv / m_leads) if m_leads > 0 else 0.0
            
            m_cost = m_display['总成本'].sum()
            m_rev = m_display['总销售额'].sum()
            m_roi = (m_rev / m_cost) if m_cost > 0 else 0.0
            m_profit = m_display['总盈亏'].sum()
            m_cac = (m_cost / m_leads) if m_leads > 0 else 0.0
            
            m_refund = m_display['正式课退单'].sum()
            m_refund_denom = m_refund + m_conv
            m_refund_rate = (m_refund / m_refund_denom) if m_refund_denom > 0 else 0.0

            st.markdown(f"### 🗓️ 【{selected_month_period}】大盘经营成果")
            mkpi_col1, mkpi_col2, mkpi_col3, mkpi_col4 = st.columns([1.3, 1, 1.1, 1])
            with mkpi_col1:
                st.markdown(f"""
                <div class='metric-hero-card' style='background: linear-gradient(135deg, #0f766e 0%, #0d9488 50%, #14b8a6 100%);'>
                    <div class='metric-hero-title'>总转化率</div>
                    <div class='metric-hero-value'>{m_conv_rate:.2%}</div>
                    <div class='metric-hero-sub'>总成交: <b>{m_conv:g} 单</b> / 消耗线索: <b>{int(m_leads):,} 人</b></div>
                </div>
                """, unsafe_allow_html=True)
            with mkpi_col2:
                st.markdown(f"""
                <div class='metric-sub-card'>
                    <div class='metric-sub-title'>总单数</div>
                    <div class='metric-sub-value' style='color:#1d4ed8;'>{m_conv:g} <span style='font-size:14px;font-weight:normal;'>单</span></div>
                    <div class='metric-sub-badge' style='background:#eff6ff;color:#1e40af;'>单粉成本: ¥{m_cac:.2f}</div>
                </div>
                """, unsafe_allow_html=True)
            with mkpi_col3:
                m_roi_color = "#16a34a" if m_roi >= 1 else "#dc2626"
                m_roi_badge_bg = "#f0fdf4" if m_roi >= 1 else "#fef2f2"
                m_roi_badge_color = "#166534" if m_roi >= 1 else "#991b1b"
                st.markdown(f"""
                <div class='metric-sub-card'>
                    <div class='metric-sub-title'>ROI</div>
                    <div class='metric-sub-value' style='color:{m_roi_color};'>{m_roi:.2f}</div>
                    <div class='metric-sub-badge' style='background:{m_roi_badge_bg};color:{m_roi_badge_color};'>销售额 ¥{m_rev:,.0f} | 成本 ¥{m_cost:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
            with mkpi_col4:
                m_refund_bg = "#fef2f2" if m_refund_rate > 0.05 else "#f0fdf4"
                m_refund_color = "#991b1b" if m_refund_rate > 0.05 else "#166534"
                st.markdown(f"""
                <div class='metric-sub-card'>
                    <div class='metric-sub-title'>正式课退单</div>
                    <div class='metric-sub-value' style='color:#dc2626;'>{int(m_refund)} <span style='font-size:14px;font-weight:normal;'>单</span></div>
                    <div class='metric-sub-badge' style='background:{m_refund_bg};color:{m_refund_color};'>正式课退单率: {m_refund_rate:.2%}</div>
                </div>
                """, unsafe_allow_html=True)

            mfin_col1, mfin_col2, mfin_col3, mfin_col4 = st.columns(4)
            with mfin_col1:
                st.metric("月度总销售额", f"¥{m_rev:,.2f}")
            with mfin_col2:
                st.metric("月度总成本", f"¥{m_cost:,.2f}")
            with mfin_col3:
                st.metric("月度总盈亏", f"¥{m_profit:,.2f}", delta="盈利" if m_profit >= 0 else "亏损", delta_color="normal" if m_profit >= 0 else "inverse")
            with mfin_col4:
                st.metric("单粉综合成本 (CAC)", f"¥{m_cac:.2f}")

            st.markdown("---")
            
            # 单月各渠道图表
            st.markdown(f"### 📊 【{selected_month_period}】各渠道表现")
            m_col1, m_col2 = st.columns([1, 1])
            with m_col1:
                top_m_conv = m_display.sort_values(by="总转化率", ascending=False)
                fig_m_bar = go.Figure()
                fig_m_bar.add_trace(go.Bar(
                    x=top_m_conv["渠道名称"],
                    y=top_m_conv["总转化率"],
                    text=top_m_conv["总转化率"].apply(lambda x: f"{x:.2%}"),
                    textposition='outside',
                    marker_color='#2563eb',
                    cliponaxis=False,
                    customdata=np.stack((
                        top_m_conv['线索量'].astype(int),
                        top_m_conv['总转化量']
                    ), axis=-1),
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        + "🔥 总转化率: <b>%{text}</b><br>"
                        + "👥 消耗线索: <b>%{customdata[0]:,} 人</b><br>"
                        + "🎯 成交单数: <b>%{customdata[1]:g} 单</b>"
                        + "<extra></extra>"
                    )
                ))
                max_mc = top_m_conv["总转化率"].max() if not top_m_conv.empty else 0.05
                fig_m_bar.update_layout(
                    title="总转化率",
                    xaxis_title="",
                    yaxis_title="总转化率",
                    yaxis_tickformat='.1%',
                    yaxis_range=[0, max(max_mc * 1.25, 0.05)],
                    xaxis=dict(
                        tickangle=-15 if len(top_m_conv) > 3 else 0,
                        tickfont=dict(size=12, color="#334155"),
                        showgrid=True,
                        gridcolor="#f1f5f9"
                    ),
                    yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
                    height=380,
                    margin=dict(l=10, r=20, t=50, b=50)
                )
                st.plotly_chart(fig_m_bar, use_container_width=True)

            with m_col2:
                top_m_roi = m_display.sort_values(by="roi", ascending=False)
                m_bar_colors = ['#10b981' if r >= 1.0 else '#3b82f6' for r in top_m_roi['roi']]
                fig_m_roi = go.Figure()
                fig_m_roi.add_trace(go.Bar(
                    x=top_m_roi["渠道名称"],
                    y=top_m_roi["roi"],
                    text=top_m_roi["roi"].apply(lambda x: f"{x:.2f}"),
                    textposition='outside',
                    marker_color=m_bar_colors,
                    cliponaxis=False,
                    customdata=np.stack((
                        top_m_roi['总销售额'],
                        top_m_roi['总成本'],
                        top_m_roi['总盈亏']
                    ), axis=-1),
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        + "💹 ROI: <b>%{text}</b><br>"
                        + "💰 销售额: <b>¥%{customdata[0]:,.2f}</b><br>"
                        + "💸 成本: <b>¥%{customdata[1]:,.2f}</b><br>"
                        + "⚖️ 盈亏: <b>¥%{customdata[2]:,.2f}</b>"
                        + "<extra></extra>"
                    )
                ))
                fig_m_roi.add_hline(
                    y=1.0,
                    line_dash="dash",
                    line_color="#ef4444",
                    line_width=1.5,
                    annotation_text="保本 1.0",
                    annotation_position="top left",
                    annotation_font_color="#ef4444"
                )
                max_mr = top_m_roi["roi"].max() if not top_m_roi.empty else 1.2
                fig_m_roi.update_layout(
                    title="ROI",
                    xaxis_title="",
                    yaxis_title="ROI",
                    yaxis_range=[0, max(max_mr * 1.25, 1.2)],
                    xaxis=dict(
                        tickangle=-15 if len(top_m_roi) > 3 else 0,
                        tickfont=dict(size=12, color="#334155"),
                        showgrid=True,
                        gridcolor="#f1f5f9"
                    ),
                    yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
                    height=380,
                    margin=dict(l=10, r=20, t=50, b=50)
                )
                st.plotly_chart(fig_m_roi, use_container_width=True)

            st.markdown("---")
            
            # 月度表格（ROI等核心商业数据前置，直播/私聊后置）
            st.markdown(f"### 📋 【{selected_month_period}】月度详细数据透视 (共 {len(m_display)} 个渠道)")
            m_sorted = m_display.sort_values(by='总转化率', ascending=False)
            m_table_df = prepare_display_dataframe(m_sorted, is_cross_period=False)
            m_col_cfg = build_clean_column_config(has_period_col=False)
            
            st.dataframe(m_table_df, column_config=m_col_cfg, use_container_width=True, hide_index=True)
            
            m_buffer = io.BytesIO()
            with pd.ExcelWriter(m_buffer, engine='openpyxl') as writer:
                export_cols = [
                    '渠道名称', '线索量', '总转化率', '总转化量',
                    'roi', '总销售额', '总成本', '总盈亏', '单粉成本',
                    '正式课退单', '正式课总退单率',
                    '直播转化', '直播占比', '私聊转化', '私聊占比'
                ]
                valid_export_cols = [c for c in export_cols if c in m_sorted.columns]
                m_sorted[valid_export_cols].to_excel(writer, index=False, sheet_name=selected_month_period[:30])
            st.download_button(
                label=f"📥 导出【{selected_month_period}】月度数据 Excel",
                data=m_buffer.getvalue(),
                file_name=f"{selected_project}_{selected_month_period}_月度数据.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        else:
            # -------------------------------------------------------------
            # 模式 B：分团队月度数据对比（各个团队主要渠道横向 PK）
            # -------------------------------------------------------------
            pref_teams = ['10月运营A组', '10月运营B组', '10月运营C组', '运营A组', '运营B组', '运营C组']
            avail_teams = [m for m in team_monthly_df['月份标签'].dropna().unique().tolist() if not any(x in str(m) for x in ['合计', '总计', 'nan', 'None'])]
            avail_teams = sorted(avail_teams, key=lambda x: pref_teams.index(x) if x in pref_teams else 99)
            
            m_filter_col1, m_filter_col2 = st.columns([2.5, 3.5])
            with m_filter_col1:
                selected_teams = st.multiselect("👥 选择对比团队（支持多团队同图PK）", options=avail_teams, default=avail_teams, key="m_team_select_top")
                
            raw_team_channels = list(team_monthly_df[team_monthly_df['月份标签'].isin(selected_teams)]['渠道名称'].dropna().unique())
            sorted_team_channels = sort_channels_core_first(raw_team_channels, selected_project)
            core_channels = CORE_CHANNELS_MAP.get(selected_project, [])
            in_core_team = [c for c in core_channels if c in sorted_team_channels]
            
            with m_filter_col2:
                m_team_scope = st.radio("对比渠道范围", options=["⭐ 仅看核心主要渠道", "全部渠道"], horizontal=True, label_visibility="collapsed", key="m_team_scope_radio_top")
                default_team_ch = in_core_team if (m_team_scope.startswith("⭐") and in_core_team) else sorted_team_channels
                selected_team_channels = st.multiselect("🔍 筛选对比渠道（控制上方汇总战报与对比图表）", options=sorted_team_channels, default=default_team_ch, key=f"m_team_channels_select_{m_team_scope}")

            if not selected_teams:
                st.info("👈 请在上方选择至少一个团队以进行对比")
            elif not selected_team_channels:
                st.info("👈 请在上方选择至少一个对比渠道")
            else:
                team_display = team_monthly_df[
                    (team_monthly_df['月份标签'].isin(selected_teams))
                    & (team_monthly_df['渠道名称'].isin(selected_team_channels))
                    & (~team_monthly_df['is_summary'])
                ].copy()

                # 按核心渠道及团队顺序排序
                team_display['ch_sort'] = team_display['渠道名称'].apply(lambda x: selected_team_channels.index(x) if x in selected_team_channels else 99)
                team_display['team_sort'] = team_display['月份标签'].apply(lambda x: selected_teams.index(x) if x in selected_teams else 99)
                team_display.sort_values(by=['ch_sort', 'team_sort'], inplace=True)

                # 顶部所选团队在已选渠道的总体汇总战报卡片
                tm_leads = team_display['线索量'].sum()
                tm_conv = team_display['总转化量'].sum()
                tm_conv_rate = (tm_conv / tm_leads) if tm_leads > 0 else 0.0
                tm_cost = team_display['总成本'].sum()
                tm_rev = team_display['总销售额'].sum()
                tm_roi = (tm_rev / tm_cost) if tm_cost > 0 else 0.0
                tm_profit = team_display['总盈亏'].sum()
                tm_refund = team_display['正式课退单'].sum()
                tm_refund_denom = tm_refund + tm_conv
                tm_refund_rate = (tm_refund / tm_refund_denom) if tm_refund_denom > 0 else 0.0
                tm_cac = (tm_cost / tm_leads) if tm_leads > 0 else 0.0

                st.markdown(f"### 👥 所选 {len(selected_teams)} 个团队在主要渠道的【汇总战报】")
                tkpi1, tkpi2, tkpi3, tkpi4 = st.columns([1.3, 1, 1.1, 1])
                with tkpi1:
                    st.markdown(f"""
                    <div class='metric-hero-card' style='background: linear-gradient(135deg, #0f766e 0%, #0d9488 50%, #14b8a6 100%);'>
                        <div class='metric-hero-title'>总转化率</div>
                        <div class='metric-hero-value'>{tm_conv_rate:.2%}</div>
                        <div class='metric-hero-sub'>总成交: <b>{tm_conv:g} 单</b> / 消耗线索: <b>{int(tm_leads):,} 人</b></div>
                    </div>
                    """, unsafe_allow_html=True)
                with tkpi2:
                    st.markdown(f"""
                    <div class='metric-sub-card'>
                        <div class='metric-sub-title'>总单数</div>
                        <div class='metric-sub-value' style='color:#1d4ed8;'>{tm_conv:g} <span style='font-size:14px;font-weight:normal;'>单</span></div>
                        <div class='metric-sub-badge' style='background:#eff6ff;color:#1e40af;'>平均单粉成本: ¥{tm_cac:.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with tkpi3:
                    tm_roi_color = "#16a34a" if tm_roi >= 1 else "#dc2626"
                    tm_roi_badge_bg = "#f0fdf4" if tm_roi >= 1 else "#fef2f2"
                    tm_roi_badge_color = "#166534" if tm_roi >= 1 else "#991b1b"
                    st.markdown(f"""
                    <div class='metric-sub-card'>
                        <div class='metric-sub-title'>ROI</div>
                        <div class='metric-sub-value' style='color:{tm_roi_color};'>{tm_roi:.2f}</div>
                        <div class='metric-sub-badge' style='background:{tm_roi_badge_bg};color:{tm_roi_badge_color};'>销售额 ¥{tm_rev:,.0f} | 成本 ¥{tm_cost:,.0f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with tkpi4:
                    tm_ref_bg = "#fef2f2" if tm_refund_rate > 0.05 else "#f0fdf4"
                    tm_ref_color = "#991b1b" if tm_refund_rate > 0.05 else "#166534"
                    st.markdown(f"""
                    <div class='metric-sub-card'>
                        <div class='metric-sub-title'>正式课退单</div>
                        <div class='metric-sub-value' style='color:#dc2626;'>{int(tm_refund)} <span style='font-size:14px;font-weight:normal;'>单</span></div>
                        <div class='metric-sub-badge' style='background:{tm_ref_bg};color:{tm_ref_color};'>正式课退单率: {tm_refund_rate:.2%}</div>
                    </div>
                    """, unsafe_allow_html=True)

                # 各团队总体经营指标对比小卡
                st.markdown("##### 🏢 各团队大盘数据快速对齐")
                t_cols = st.columns(len(selected_teams))
                for i, t_name in enumerate(selected_teams):
                    t_sub = team_display[team_display['月份标签'] == t_name]
                    tl = t_sub['线索量'].sum()
                    tc = t_sub['总转化量'].sum()
                    tr = (tc / tl) if tl > 0 else 0.0
                    t_rev = t_sub['总销售额'].sum()
                    t_cost = t_sub['总成本'].sum()
                    t_r = (t_rev / t_cost) if t_cost > 0 else 0.0
                    with t_cols[i]:
                        st.markdown(f"""
                        <div style='background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px 12px; margin-bottom: 12px;'>
                            <div style='font-weight: 700; color: #1e293b; font-size: 14px;'>📌 {t_name}</div>
                            <div style='margin-top: 4px; font-size: 13px; color: #334155;'>
                                转化率: <b style='color:#2563eb;'>{tr:.2%}</b> ｜ ROI: <b style='color:{"#16a34a" if t_r>=1 else "#dc2626"};'>{t_r:.2f}</b>
                            </div>
                            <div style='font-size: 12px; color: #64748b; margin-top: 2px;'>
                                成交: <b>{tc:g}</b> 单 / 线索: <b>{int(tl):,}</b> 人 / 销售: <b>¥{t_rev:,.0f}</b>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("---")

                # =========================================================
                # 核心对比图表（各团队主要渠道横向对比图）
                # =========================================================
                st.markdown("### 📊 各团队主要渠道横向对比图")
                team_col1, team_col2 = st.columns([1, 1])

                team_colors = ['#2563eb', '#0ea5e9', '#f59e0b', '#8b5cf6', '#10b981']

                with team_col1:
                    # 分团队主要渠道【总转化率】分组柱状图
                    fig_team_conv = px.bar(
                        team_display,
                        x="渠道名称",
                        y="总转化率",
                        color="月份标签",
                        barmode="group",
                        text=team_display["总转化率"].apply(lambda x: f"{x:.2%}"),
                        title="总转化率",
                        color_discrete_sequence=team_colors
                    )
                    for trace in fig_team_conv.data:
                        t_name = trace.name
                        sub_t = team_display[team_display['月份标签'] == t_name]
                        c_data = np.stack((
                            sub_t['渠道名称'],
                            sub_t['总转化率'].apply(lambda x: f"{x:.2%}"),
                            sub_t['线索量'].astype(int),
                            sub_t['总转化量'],
                            sub_t['月份标签']
                        ), axis=-1)
                        trace.customdata = c_data
                        trace.hovertemplate = (
                            "<b>%{customdata[0]}</b><br>"
                            + "团队: <b>%{customdata[4]}</b><br>"
                            + "🔥 总转化率: <b>%{customdata[1]}</b><br>"
                            + "👥 消耗线索: <b>%{customdata[2]:,} 人</b><br>"
                            + "🎯 成交单数: <b>%{customdata[3]:g} 单</b>"
                            + "<extra></extra>"
                        )
                        trace.textposition = "outside"
                        trace.cliponaxis = False
                    max_tc = team_display['总转化率'].max() if not team_display.empty else 0.05
                    fig_team_conv.update_layout(
                        yaxis_tickformat='.1%',
                        yaxis_range=[0, max(max_tc * 1.25, 0.05)],
                        xaxis=dict(
                            tickangle=-15 if len(selected_team_channels) > 3 else 0,
                            tickfont=dict(size=12, color="#334155"),
                            showgrid=True,
                            gridcolor="#f1f5f9"
                        ),
                        yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
                        yaxis_title="总转化率",
                        height=400,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=""),
                        margin=dict(l=10, r=20, t=50, b=50)
                    )
                    st.plotly_chart(fig_team_conv, use_container_width=True)

                with team_col2:
                    # 分团队主要渠道【ROI】分组柱状图
                    fig_team_roi = px.bar(
                        team_display,
                        x="渠道名称",
                        y="roi",
                        color="月份标签",
                        barmode="group",
                        text=team_display["roi"].apply(lambda x: f"{x:.2f}"),
                        title="ROI",
                        color_discrete_sequence=team_colors
                    )
                    for trace in fig_team_roi.data:
                        t_name = trace.name
                        sub_t = team_display[team_display['月份标签'] == t_name]
                        c_data = np.stack((
                            sub_t['渠道名称'],
                            sub_t['roi'].apply(lambda x: f"{x:.2f}"),
                            sub_t['总销售额'],
                            sub_t['总成本'],
                            sub_t['总盈亏'],
                            sub_t['月份标签']
                        ), axis=-1)
                        trace.customdata = c_data
                        trace.hovertemplate = (
                            "<b>%{customdata[0]}</b><br>"
                            + "团队: <b>%{customdata[5]}</b><br>"
                            + "💹 ROI: <b>%{customdata[1]}</b><br>"
                            + "💰 销售额: <b>¥%{customdata[2]:,.2f}</b><br>"
                            + "💸 成本: <b>¥%{customdata[3]:,.2f}</b><br>"
                            + "⚖️ 盈亏: <b>¥%{customdata[4]:,.2f}</b>"
                            + "<extra></extra>"
                        )
                        trace.textposition = "outside"
                        trace.cliponaxis = False
                    fig_team_roi.add_hline(
                        y=1.0,
                        line_dash="dash",
                        line_color="#ef4444",
                        line_width=1.5,
                        annotation_text="保本 1.0",
                        annotation_position="top left",
                        annotation_font_color="#ef4444"
                    )
                    max_tr = team_display['roi'].max() if not team_display.empty else 1.2
                    fig_team_roi.update_layout(
                        xaxis=dict(
                            tickangle=-15 if len(selected_team_channels) > 3 else 0,
                            tickfont=dict(size=12, color="#334155"),
                            showgrid=True,
                            gridcolor="#f1f5f9"
                        ),
                        yaxis=dict(
                            title="ROI",
                            range=[0, max(max_tr * 1.25, 1.2)],
                            showgrid=True,
                            gridcolor="#f1f5f9"
                        ),
                        yaxis_title="ROI",
                        height=400,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=""),
                        margin=dict(l=10, r=20, t=50, b=50)
                    )
                    st.plotly_chart(fig_team_roi, use_container_width=True)

                st.markdown("---")

                # =========================================================
                # 表格独立区域：在表格正上方直接筛选渠道（无需页面上下滚动）
                # =========================================================
                st.markdown("### 📋 分团队渠道详细数据对比表")
                st.caption("💡 此处自带就近专属渠道筛选：无需反复上滑页面，可直接在此处单选切换某个渠道深入透视三大团队PK，或多选渠道拉通对比。")

                tbl_filter_col1, tbl_filter_col2 = st.columns([2.2, 4.8])
                with tbl_filter_col1:
                    tbl_view_type = st.radio(
                        "表格对比视角",
                        options=["🎯 单渠道横向透视（行：团队 ｜ 列：指标）", "📊 多渠道拉通对比大表"],
                        horizontal=True,
                        key="tbl_view_type_radio"
                    )

                if tbl_view_type.startswith("🎯"):
                    with tbl_filter_col2:
                        tbl_single_channel = st.selectbox(
                            "🎯 选择单渠道进行团队横向透视（一键切换任一渠道，查看三大团队对比）",
                            options=sorted_team_channels,
                            index=0 if sorted_team_channels else None,
                            key="tbl_single_ch_select"
                        )

                    if not tbl_single_channel:
                        st.info("👈 请选择一个渠道以查看团队对比")
                    else:
                        # 获取该渠道在各团队的数据
                        ch_team_df = team_monthly_df[
                            (team_monthly_df['渠道名称'] == tbl_single_channel)
                            & (team_monthly_df['月份标签'].isin(selected_teams))
                            & (~team_monthly_df['is_summary'])
                        ].copy()

                        # 构建每个团队的完整对比记录（行：团队）
                        table_rows = []
                        for t in selected_teams:
                            t_match = ch_team_df[ch_team_df['月份标签'] == t]
                            if not t_match.empty:
                                row = t_match.iloc[0].to_dict()
                                table_rows.append(row)
                            else:
                                table_rows.append({
                                    '月份标签': t,
                                    '渠道名称': tbl_single_channel,
                                    '线索量': 0,
                                    '总转化率': 0.0,
                                    '总转化量': 0.0,
                                    'roi': 0.0,
                                    '总销售额': 0.0,
                                    '总成本': 0.0,
                                    '总盈亏': 0.0,
                                    '单粉成本': 0.0,
                                    '正式课退单': 0,
                                    '正式课总退单率': 0.0,
                                    '直播转化': 0.0,
                                    '直播占比': 0.0,
                                    '私聊转化': 0.0,
                                    '私聊占比': 0.0
                                })
                        team_comp_df = pd.DataFrame(table_rows)

                        # 计算全团队合计指标
                        tot_leads = team_comp_df['线索量'].sum()
                        tot_conv = team_comp_df['总转化量'].sum()
                        tot_conv_rate = (tot_conv / tot_leads) if tot_leads > 0 else 0.0
                        tot_cost = team_comp_df['总成本'].sum()
                        tot_rev = team_comp_df['总销售额'].sum()
                        tot_roi = (tot_rev / tot_cost) if tot_cost > 0 else 0.0
                        tot_profit = team_comp_df['总盈亏'].sum()
                        tot_cac = (tot_cost / tot_leads) if tot_leads > 0 else 0.0
                        tot_refund = team_comp_df['正式课退单'].sum()
                        tot_refund_denom = tot_refund + tot_conv
                        tot_refund_rate = (tot_refund / tot_refund_denom) if tot_refund_denom > 0 else 0.0
                        tot_live = team_comp_df['直播转化'].sum()
                        tot_chat = team_comp_df['私聊转化'].sum()
                        tot_live_ratio = (tot_live / tot_conv) if tot_conv > 0 else 0.0
                        tot_chat_ratio = (tot_chat / tot_conv) if tot_conv > 0 else 0.0

                        total_row = {
                            '月份标签': '全团队合计',
                            '渠道名称': tbl_single_channel,
                            '线索量': tot_leads,
                            '总转化率': tot_conv_rate,
                            '总转化量': tot_conv,
                            'roi': tot_roi,
                            '总销售额': tot_rev,
                            '总成本': tot_cost,
                            '总盈亏': tot_profit,
                            '单粉成本': tot_cac,
                            '正式课退单': tot_refund,
                            '正式课总退单率': tot_refund_rate,
                            '直播转化': tot_live,
                            '直播占比': tot_live_ratio,
                            '私聊转化': tot_chat,
                            '私聊占比': tot_chat_ratio
                        }
                        team_comp_with_total = pd.concat([team_comp_df, pd.DataFrame([total_row])], ignore_index=True)

                        st.markdown(f"#### 📋 【{tbl_single_channel}】各团队详细数据对比（行：团队 ｜ 列：具体指标）")
                        
                        display_table = team_comp_with_total.copy()
                        rate_cols = ['总转化率', '正式课总退单率', '直播占比', '私聊占比']
                        for c in rate_cols:
                            if c in display_table.columns:
                                display_table[c] = display_table[c] * 100.0

                        cols_order = [
                            '月份标签', '线索量', '总转化率', '总转化量',
                            'roi', '总销售额', '总成本', '总盈亏', '单粉成本',
                            '正式课退单', '正式课总退单率',
                            '直播转化', '直播占比', '私聊转化', '私聊占比'
                        ]
                        display_table = display_table[[c for c in cols_order if c in display_table]]
                        
                        team_col_cfg = {
                            "月份标签": st.column_config.TextColumn("团队", width="medium"),
                            "线索量": st.column_config.NumberColumn("线索量 (人)", format="%d"),
                            "总转化率": st.column_config.NumberColumn("🔥 总转化率", format="%.2f%%"),
                            "总转化量": st.column_config.NumberColumn("总单数", format="%.1f"),
                            "roi": st.column_config.NumberColumn("ROI", format="%.2f"),
                            "总销售额": st.column_config.NumberColumn("总销售额", format="¥%.2f"),
                            "总成本": st.column_config.NumberColumn("总成本", format="¥%.2f"),
                            "总盈亏": st.column_config.NumberColumn("总盈亏", format="¥%.2f"),
                            "单粉成本": st.column_config.NumberColumn("单粉成本", format="¥%.2f"),
                            "正式课退单": st.column_config.NumberColumn("正式课退单", format="%d"),
                            "正式课总退单率": st.column_config.NumberColumn("正式课退单率", format="%.2f%%"),
                            "直播转化": st.column_config.NumberColumn("🎙️ 直播转化", format="%.1f"),
                            "直播占比": st.column_config.NumberColumn("直播占比", format="%.1f%%"),
                            "私聊转化": st.column_config.NumberColumn("💬 私聊转化", format="%.1f"),
                            "私聊占比": st.column_config.NumberColumn("私聊占比", format="%.1f%%"),
                        }
                        
                        st.dataframe(display_table, column_config=team_col_cfg, use_container_width=True, hide_index=True)

                        # 导出 Excel
                        t_buffer = io.BytesIO()
                        with pd.ExcelWriter(t_buffer, engine='openpyxl') as writer:
                            export_cols = [
                                '月份标签', '渠道名称', '线索量', '总转化率', '总转化量',
                                'roi', '总销售额', '总成本', '总盈亏', '单粉成本',
                                '正式课退单', '正式课总退单率',
                                '直播转化', '直播占比', '私聊转化', '私聊占比'
                            ]
                            valid_export_cols = [c for c in export_cols if c in team_comp_with_total.columns]
                            team_comp_with_total[valid_export_cols].to_excel(writer, index=False, sheet_name=tbl_single_channel[:30])
                        st.download_button(
                            label=f"📥 导出【{tbl_single_channel}】各团队对比 Excel",
                            data=t_buffer.getvalue(),
                            file_name=f"{selected_project}_{tbl_single_channel}_各团队对比.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"dl_single_{tbl_single_channel}"
                        )

                else:
                    # ---------------------------------------------------------
                    # 多渠道拉通大表模式（支持就地多选渠道，看全量数据）
                    # ---------------------------------------------------------
                    with tbl_filter_col2:
                        tbl_multi_channels = st.multiselect(
                            "🔍 筛选表格渠道（支持多选，就近直接筛选无需上滑）",
                            options=sorted_team_channels,
                            default=in_core_team if in_core_team else sorted_team_channels[:5],
                            key="tbl_multi_ch_select"
                        )

                    if not tbl_multi_channels:
                        st.info("👈 请在上方选择至少一个渠道以展示对比明细表")
                    else:
                        all_tbl_rows = []
                        for ch in tbl_multi_channels:
                            ch_sub = team_monthly_df[
                                (team_monthly_df['渠道名称'] == ch)
                                & (team_monthly_df['月份标签'].isin(selected_teams))
                                & (~team_monthly_df['is_summary'])
                            ].copy()
                            
                            ch_leads = 0
                            ch_conv = 0.0
                            ch_cost = 0.0
                            ch_rev = 0.0
                            ch_profit = 0.0
                            ch_refund = 0
                            ch_live = 0.0
                            ch_chat = 0.0

                            for t in selected_teams:
                                t_match = ch_sub[ch_sub['月份标签'] == t]
                                if not t_match.empty:
                                    r = t_match.iloc[0].to_dict()
                                else:
                                    r = {
                                        '渠道名称': ch,
                                        '月份标签': t,
                                        '线索量': 0,
                                        '总转化率': 0.0,
                                        '总转化量': 0.0,
                                        'roi': 0.0,
                                        '总销售额': 0.0,
                                        '总成本': 0.0,
                                        '总盈亏': 0.0,
                                        '单粉成本': 0.0,
                                        '正式课退单': 0,
                                        '正式课总退单率': 0.0,
                                        '直播转化': 0.0,
                                        '直播占比': 0.0,
                                        '私聊转化': 0.0,
                                        '私聊占比': 0.0
                                    }
                                all_tbl_rows.append(r)
                                ch_leads += r['线索量']
                                ch_conv += r['总转化量']
                                ch_cost += r['总成本']
                                ch_rev += r['总销售额']
                                ch_profit += r['总盈亏']
                                ch_refund += r['正式课退单']
                                ch_live += r['直播转化']
                                ch_chat += r['私聊转化']

                            # 渠道小计行
                            sub_rate = (ch_conv / ch_leads) if ch_leads > 0 else 0.0
                            sub_roi = (ch_rev / ch_cost) if ch_cost > 0 else 0.0
                            sub_cac = (ch_cost / ch_leads) if ch_leads > 0 else 0.0
                            sub_ref_rate = (ch_refund / (ch_refund + ch_conv)) if (ch_refund + ch_conv) > 0 else 0.0
                            sub_live_ratio = (ch_live / ch_conv) if ch_conv > 0 else 0.0
                            sub_chat_ratio = (ch_chat / ch_conv) if ch_conv > 0 else 0.0
                            all_tbl_rows.append({
                                '渠道名称': ch,
                                '月份标签': f'【{ch} 合计】',
                                '线索量': ch_leads,
                                '总转化率': sub_rate,
                                '总转化量': ch_conv,
                                'roi': sub_roi,
                                '总销售额': ch_rev,
                                '总成本': ch_cost,
                                '总盈亏': ch_profit,
                                '单粉成本': sub_cac,
                                '正式课退单': ch_refund,
                                '正式课总退单率': sub_ref_rate,
                                '直播转化': ch_live,
                                '直播占比': sub_live_ratio,
                                '私聊转化': ch_chat,
                                '私聊占比': sub_chat_ratio
                            })

                        multi_comp_df = pd.DataFrame(all_tbl_rows)

                        # 追加全渠道大盘总计行
                        g_leads = multi_comp_df[~multi_comp_df['月份标签'].str.contains('合计')]['线索量'].sum()
                        g_conv = multi_comp_df[~multi_comp_df['月份标签'].str.contains('合计')]['总转化量'].sum()
                        g_rate = (g_conv / g_leads) if g_leads > 0 else 0.0
                        g_cost = multi_comp_df[~multi_comp_df['月份标签'].str.contains('合计')]['总成本'].sum()
                        g_rev = multi_comp_df[~multi_comp_df['月份标签'].str.contains('合计')]['总销售额'].sum()
                        g_roi = (g_rev / g_cost) if g_cost > 0 else 0.0
                        g_profit = multi_comp_df[~multi_comp_df['月份标签'].str.contains('合计')]['总盈亏'].sum()
                        g_cac = (g_cost / g_leads) if g_leads > 0 else 0.0
                        g_refund = multi_comp_df[~multi_comp_df['月份标签'].str.contains('合计')]['正式课退单'].sum()
                        g_ref_rate = (g_refund / (g_refund + g_conv)) if (g_refund + g_conv) > 0 else 0.0
                        g_live = multi_comp_df[~multi_comp_df['月份标签'].str.contains('合计')]['直播转化'].sum()
                        g_chat = multi_comp_df[~multi_comp_df['月份标签'].str.contains('合计')]['私聊转化'].sum()
                        g_live_ratio = (g_live / g_conv) if g_conv > 0 else 0.0
                        g_chat_ratio = (g_chat / g_conv) if g_conv > 0 else 0.0

                        grand_total_row = {
                            '渠道名称': '⭐ 全部已选渠道',
                            '月份标签': '【全渠道总计】',
                            '线索量': g_leads,
                            '总转化率': g_rate,
                            '总转化量': g_conv,
                            'roi': g_roi,
                            '总销售额': g_rev,
                            '总成本': g_cost,
                            '总盈亏': g_profit,
                            '单粉成本': g_cac,
                            '正式课退单': g_refund,
                            '正式课总退单率': g_ref_rate,
                            '直播转化': g_live,
                            '直播占比': g_live_ratio,
                            '私聊转化': g_chat,
                            '私聊占比': g_chat_ratio
                        }
                        multi_comp_with_total = pd.concat([multi_comp_df, pd.DataFrame([grand_total_row])], ignore_index=True)

                        st.markdown(f"#### 📋 所选 {len(tbl_multi_channels)} 个渠道各团队对比明细大表")

                        display_multi_table = multi_comp_with_total.copy()
                        rate_cols = ['总转化率', '正式课总退单率', '直播占比', '私聊占比']
                        for c in rate_cols:
                            if c in display_multi_table.columns:
                                display_multi_table[c] = display_multi_table[c] * 100.0

                        multi_cols_order = [
                            '渠道名称', '月份标签', '线索量', '总转化率', '总转化量',
                            'roi', '总销售额', '总成本', '总盈亏', '单粉成本',
                            '正式课退单', '正式课总退单率',
                            '直播转化', '直播占比', '私聊转化', '私聊占比'
                        ]
                        display_multi_table = display_multi_table[[c for c in multi_cols_order if c in display_multi_table]]

                        multi_col_cfg = {
                            "渠道名称": st.column_config.TextColumn("渠道名称", width="medium"),
                            "月份标签": st.column_config.TextColumn("团队", width="medium"),
                            "线索量": st.column_config.NumberColumn("线索量 (人)", format="%d"),
                            "总转化率": st.column_config.NumberColumn("🔥 总转化率", format="%.2f%%"),
                            "总转化量": st.column_config.NumberColumn("总单数", format="%.1f"),
                            "roi": st.column_config.NumberColumn("ROI", format="%.2f"),
                            "总销售额": st.column_config.NumberColumn("总销售额", format="¥%.2f"),
                            "总成本": st.column_config.NumberColumn("总成本", format="¥%.2f"),
                            "总盈亏": st.column_config.NumberColumn("总盈亏", format="¥%.2f"),
                            "单粉成本": st.column_config.NumberColumn("单粉成本", format="¥%.2f"),
                            "正式课退单": st.column_config.NumberColumn("正式课退单", format="%d"),
                            "正式课总退单率": st.column_config.NumberColumn("正式课退单率", format="%.2f%%"),
                            "直播转化": st.column_config.NumberColumn("🎙️ 直播转化", format="%.1f"),
                            "直播占比": st.column_config.NumberColumn("直播占比", format="%.1f%%"),
                            "私聊转化": st.column_config.NumberColumn("💬 私聊转化", format="%.1f"),
                            "私聊占比": st.column_config.NumberColumn("私聊占比", format="%.1f%%"),
                        }

                        st.dataframe(display_multi_table, column_config=multi_col_cfg, use_container_width=True, hide_index=True)

                        # 导出 Excel
                        m_buffer = io.BytesIO()
                        with pd.ExcelWriter(m_buffer, engine='openpyxl') as writer:
                            valid_export_cols = [c for c in multi_cols_order if c in multi_comp_with_total.columns]
                            multi_comp_with_total[valid_export_cols].to_excel(writer, index=False, sheet_name="多渠道团队对比")
                        st.download_button(
                            label="📥 导出多渠道团队对比 Excel",
                            data=m_buffer.getvalue(),
                            file_name=f"{selected_project}_多渠道各团队对比.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="dl_multi_teams"
                        )
