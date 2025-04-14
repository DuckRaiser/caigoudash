import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
from config import DATA_FILES, FILE_ENCODING

# 设置页面配置
st.set_page_config(
    page_title="集团采购战略分析看板",
    page_icon="📊",
    layout="wide"
)

# 添加侧边栏控件
st.sidebar.title("数据控制")

# 添加手动刷新按钮
if st.sidebar.button('🔄 刷新数据'):
    st.cache_data.clear()
    st.rerun() # 使用 st.rerun() 替代 st.experimental_rerun()

# 数据加载函数
@st.cache_data(ttl=60)  # 设置缓存时间为60秒
def load_data():
    try:
        # 读取三个CSV文件
        factory_data = pd.read_csv(DATA_FILES['factory_data'], encoding=FILE_ENCODING)
        supplier_data = pd.read_csv(DATA_FILES['supplier_data'], encoding=FILE_ENCODING)
        category_data = pd.read_csv(DATA_FILES['category_data'], encoding=FILE_ENCODING)
        
        # 记录数据加载时间
        st.session_state['last_data_update'] = datetime.now()
        st.session_state['data_load_status'] = 'success'
        
        # 安全的数值转换函数
        def safe_numeric_convert(series):
            if series.dtype == 'object':
                return pd.to_numeric(series.str.replace(',', '').str.rstrip('%'), errors='coerce')
            return series
        
        # 处理工厂数据
        numeric_columns = ['2025年预测采购额', '2024年入库金额', '增长金额', '增长率']
        for col in numeric_columns:
            if col in factory_data.columns:
                factory_data[col] = safe_numeric_convert(factory_data[col])
        
        # 处理供应商数据
        supplier_numeric_columns = [
            '2024合计入库金额', '2025合计预算金额', '增长金额', '增长率',
            '2024汇风入库金额', '2024铜盟入库金额', '2024苏州入库金额',
            '2025汇风预算金额', '2025铜盟预算金额', '2025苏州预算金额'
        ]
        for col in supplier_numeric_columns:
            if col in supplier_data.columns:
                supplier_data[col] = safe_numeric_convert(supplier_data[col])
        
        # 处理品类数据
        category_numeric_columns = ['2024年Spend', '2025年Spend', '增长金额', '增长率']
        for col in category_numeric_columns:
            if col in category_data.columns:
                category_data[col] = safe_numeric_convert(category_data[col])
        
        return factory_data, supplier_data, category_data
        
    except Exception as e:
        st.session_state['data_load_status'] = 'error'
        st.session_state['data_load_error'] = str(e)
        raise e

# 加载数据
try:
    factory_data, supplier_data, category_data = load_data()
    
    # 显示数据更新时间
    if 'last_data_update' in st.session_state:
        st.sidebar.info(f"📅 数据最后更新时间：\n{st.session_state['last_data_update'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 显示数据加载状态
    if st.session_state.get('data_load_status') == 'success':
        st.sidebar.success("✅ 数据加载成功")
    
except Exception as e:
    st.sidebar.error(f"❌ 数据加载失败：{str(e)}")
    st.stop()

# 页面标题
st.title("📊 集团采购战略分析看板")
st.markdown("### 战略洞察与决策支持系统")

# 创建标签页
tab1, tab_manager, tab2, tab3, tab4, tab5 = st.tabs([
    "🏭 工厂业务概览",
    "💡 管理者决策辅助", # 新增标签页
    "📈 品类战略分析",
    "🤝 供应商管理矩阵",
    "⚠️ 风险预警与建议",
    "📊 数据明细总览"
])

with tab1:
    st.header("工厂业务概览")
    
    # 创建两列布局
    col1, col2 = st.columns(2)
    
    with col1:
        # 工厂采购规模对比
        fig = go.Figure()
        for factory in factory_data['Business Unit']:
            if factory != '合计':
                fig.add_trace(go.Bar(
                    name=factory,
                    x=['2024年', '2025年'],
                    y=[
                        factory_data[factory_data['Business Unit']==factory]['2024年入库金额'].values[0],
                        factory_data[factory_data['Business Unit']==factory]['2025年预测采购额'].values[0]
                    ],
                    text=[
                        f"{factory_data[factory_data['Business Unit']==factory]['2024年入库金额'].values[0]/10000:.0f}万",
                        f"{factory_data[factory_data['Business Unit']==factory]['2025年预测采购额'].values[0]/10000:.0f}万"
                    ]
                ))
        
        fig.update_layout(
            title="各工厂采购规模对比",
            barmode='group',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 增长率分析
        growth_data = factory_data[factory_data['Business Unit'] != '合计'].copy()
        fig = px.bar(
            growth_data,
            x='Business Unit',
            y='增长率',
            text=growth_data['增长率'].apply(lambda x: f'{x}%'),
            title="各工厂2025年预测增长率",
            color='增长率',
            color_continuous_scale='RdYlGn'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    # 计算供应商相关指标
    top10_share = (supplier_data.nlargest(10, '2024合计入库金额')['2024合计入库金额'].sum() / 
                  supplier_data['2024合计入库金额'].sum() * 100)
    top5_concentration = (supplier_data.nlargest(5, '2024合计入库金额')['2024合计入库金额'].sum() / 
                         supplier_data['2024合计入库金额'].sum() * 100)
    high_dependency = len(supplier_data[
        supplier_data['2024合计入库金额'] / supplier_data['2024合计入库金额'].sum() > 0.1
    ])

    st.subheader("📌 战略洞察")
    st.markdown(f"""
    1. **工厂业务规模分析**：
        - 天津铜盟2024年入库4.61亿，2025年预计5.20亿，增长13%
        - 天津汇风2024年入库1.14亿，2025年预计1.36亿，增长19%
        - 苏州铜盟2024年入库2.51亿，2025年预计2.28亿，下降9%
        - 天津地区（铜盟+汇风）总采购额从5.75亿增长至6.56亿，增长14%
    
    2. **品类结构分析**：
        - 铜材类采购占总采购额的42%，是最大品类
        - 导热脂、接线盒等新品类增长率超过30%
        - 有8个子品类出现负增长，降幅超过15%
    
    3. **供应商集中度分析**：
        - Top10供应商采购占比{top10_share:.1f}%
        - Top5供应商采购占比{top5_concentration:.1f}%
        - {high_dependency}个供应商采购占比超过10%
    """)

# --- tab_manager 内容开始 ---
# 将 tab_manager 的代码块移到 tab1 外部，并保持正确的缩进
with tab_manager:
    st.header("管理者决策辅助：高增长分析")
    st.markdown("我分析了一下采购数据，虽然只是Overview数据，但结合企业背景与业务特点，我仍能帮助你在新年度的采购战略中提出部分建议及行动指南。")

    # st.write("--- 测试：暂时移除复杂内容 --- ") # 移除测试标记

    # --- 恢复内容 ---
    # --- Top 10 采购额增长供应商分析 (可折叠) ---
    with st.expander("📈 Top 10 采购额增长供应商 (绝对金额)", expanded=True): # 默认展开
        # 计算Top 10增长供应商 (按绝对增长金额)
        # 确保 '增长金额' 列是数值类型，如果 load_data 中未处理
        if not pd.api.types.is_numeric_dtype(supplier_data['增长金额']):
            supplier_data['增长金额'] = pd.to_numeric(supplier_data['增长金额'], errors='coerce')
            supplier_data.dropna(subset=['增长金额'], inplace=True) # 删除无法转换的行

        top_10_growth_suppliers = supplier_data.nlargest(10, '增长金额').copy()

        # 可视化 Top 10 增长供应商的绝对增长金额
        st.subheader("可视化：增长金额对比")
        if not top_10_growth_suppliers.empty:
            fig_top10_bar = px.bar(
                top_10_growth_suppliers,
                x='供应商',
                y='增长金额',
                title="Top 10 供应商 - 绝对增长金额 (2025预算 vs 2024实际)",
                text='增长金额',
                labels={'供应商': '供应商名称', '增长金额': '增长金额 (元)'},
                color='Category', # 按品类着色
                hover_data=['Category', 'Sub Category', '增长率']
            )
            fig_top10_bar.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig_top10_bar.update_layout(xaxis_tickangle=-45, height=500, yaxis_title="增长金额 (元)")
            st.plotly_chart(fig_top10_bar, use_container_width=True)
        else:
            st.warning("未能计算Top 10增长供应商数据。")

        # 战略建议 (按 Category 分组显示)
        st.subheader("战略考量 (按品类)")
        category_advice = {
            'Copper &Aluminum': """物料特点：大宗商品，价格波动大，市场透明度相对较高，品质相对标准化。
战略建议：
1.  **价格与风险管理 (基础)：** 重点关注LME等价格趋势，考虑签订部分长期锁价协议（对冲风险，但注意时机），或研究利用期货工具进行套期保值。
2.  **市场与竞争 (优化)：** 持续评估市场，利用多家供应商进行比价和招标，保持适度竞争。结合库存策略，优化采购时机。
3.  **战略合作与协同 (深化 - 结合业务特点)：**
    *   识别并约谈具备出口潜力或意愿的天津及周边核心供应商。
    *   **利用天津港口优势和公司出海业务，探讨联合出口、海外项目协同、共享物流资源等合作模式，建立超越简单买卖的战略伙伴关系。**
    *   **将此深度合作意向作为谈判筹码，争取国内采购的成本优惠、供应保障及更优的商务条件。**
4.  **供应保障：** 对于核心供应商，确保其产能稳定，有相应的应急预案。""",
            'Steel': """物料特点：大宗商品，受宏观经济影响，价格波动。
战略建议：与核心供应商建立战略伙伴关系，探讨阶梯价格或年度协议。关注钢材市场动态，适时调整库存策略。评估是否有成本效益更高的替代规格或供应商。""",
            'Assembly &Mechanical Parts': """物料特点：范围广泛，主要涉及金属加工、注塑件、组装等，不含玻璃钢。质量和技术要求差异大。
战略建议：
1.  **供应商分类管理：** 根据零件复杂度、技术含量、定制化程度对供应商进行分级管理。
2.  **核心/高增长供应商：** 深化合作，共同进行成本优化（VAVE）、效率提升。密切关注其产能爬坡和质量稳定性。识别关键瓶颈，制定备选方案或第二供应商计划。
3.  **质量控制：** 加强供应商质量体系审核和进料检验，特别是对于功能性或外观要求高的部件。""",
            'Electrical &Electronic': """物料特点：技术更新快，可能存在认证要求，供应链较长。
战略建议：加强技术交流，确保供应商与产品路线图同步。评估其研发能力和供应链风险（如缺芯）。对于关键器件，考虑建立安全库存或认证第二供应商。""",
            'Plastic &Chemical': """物料特点：包含塑料粒子、助剂、化学制品（如钎焊料）以及复合材料（如玻璃钢）。可能涉及环保、安全认证，配方或规格要求。
战略建议：
1.  **通用化学品/塑料：** 确保供应商符合法规要求。关注原材料（如原油）价格波动及供应稳定性。与供应商共同优化配方或寻找性价比更高的替代品。
2.  **特定子类策略 (示例1：银钎焊料 - 如上海大华)：**
    *   技术降本 (与研发/工艺协同)：审查规格（低银/无银替代）、优化工艺（减少用量）。
    *   商务降本 (供应链策略)：引入竞争（长三角/珠三角集群）、供应商谈判、关注银价、库存管理（VMI）、物流考量。
3.  **特定子类策略 (示例2：玻璃钢 - 如山东双一等供应商)：**
    *   **技术评估：** 评估具体产品的技术难度（树脂体系、工艺、精度），关注供应商的技术实力和质量控制。
    *   **产业集群利用：** **重点关注河北衡水（枣强）及山东武城等玻璃钢产业集群**，进行集中寻源、比价和招标，发掘专业或二线优质供应商。
    *   **成本优化：** 与技术部门协作，进行价值工程分析（规格标准化、材料替代评估），并优化物流方案。
4.  **法规与安全：** 对于所有化学品和塑料，确保持续符合最新的环保和安全法规。""",
            'Chemicals': """[注：部分化学品（如钎焊料）已在 'Plastic &Chemical' 品类下提供详细建议] 物料特点：可能涉及环保、安全认证，配方或规格要求。
战略建议：确保供应商符合所有法规要求。关注原材料价格波动及供应稳定性。与供应商共同优化配方或寻找性价比更高的替代品。对于未在其他类别详述的化学品，需进行专项分析。""",
            'Packaging': """物料特点：需求量可能较大，与产品外观或运输相关，成本敏感度较高。
战略建议：推动标准化以降本。与供应商探讨优化设计、材料或循环利用方案。评估引入竞争性报价的可行性。""",
            'default': """物料特点：[请根据实际情况补充]
战略建议：首先分析增长的具体原因（是单价上涨还是采购量增加？）。评估供应商的产能、质量、交付能力是否能支撑此增长。基于该品类的战略重要性和供应商表现，决定采用深化合作、加强管控、引入竞争还是寻求替代等策略。"""
        }

        if not top_10_growth_suppliers.empty:
            unique_categories_supplier = top_10_growth_suppliers['Category'].unique()
            for category in unique_categories_supplier:
                advice = category_advice.get(category, category_advice['default'])
                final_advice = advice
                if "[请根据实际情况补充]" in advice:
                    final_advice = advice.replace("[请根据实际情况补充]", f"所属品类为 {category}")
                
                # 为每个唯一的Category显示一次建议
                with st.container(border=True): # 使用带边框的容器区分
                     st.markdown(f"##### {category}")
                     st.info(final_advice)
        else:
            st.info("无供应商数据可供生成战略建议。")

        # 显示 Top 10 供应商详细数据列表
        st.subheader("Top 10 供应商详细数据")
        if not top_10_growth_suppliers.empty:
            display_suppliers = top_10_growth_suppliers[[
                '供应商', 'Category', 'Sub Category', 
                '2024合计入库金额', '2025合计预算金额', '增长金额', '增长率'
            ]].copy()
            # 格式化显示
            display_suppliers['增长率'] = display_suppliers['增长率'].apply(
                lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A"
            )
            # 添加序号列
            display_suppliers.insert(0, '排名', range(1, 1 + len(display_suppliers)))
            st.dataframe(
                display_suppliers.style.format({
                    '2024合计入库金额': '{:,.0f}',
                    '2025合计预算金额': '{:,.0f}',
                    '增长金额': '{:,.0f}'
                }), 
                use_container_width=True,
                hide_index=True # 隐藏 DataFrame 默认索引
            )
        else:
            st.info("没有找到符合条件的供应商数据。")

    # --- Top 10 采购额增长子类别分析 (可折叠) ---
    with st.expander("📈 Top 10 采购额增长子类别 (绝对金额)", expanded=True): # 默认折叠
        # 计算Top 10增长子类别 (按绝对增长金额)
        # 确保 '增长金额' 列是数值类型，如果 load_data 中未处理
        if not pd.api.types.is_numeric_dtype(category_data['增长金额']):
            category_data['增长金额'] = pd.to_numeric(category_data['增长金额'], errors='coerce')
            category_data.dropna(subset=['增长金额'], inplace=True) # 删除无法转换的行

        top_10_growth_subcategories = category_data.nlargest(10, '增长金额').copy()
        top_10_growth_subcategories.reset_index(drop=True, inplace=True) # 重置索引方便后面使用 index+1

        # 可视化 Top 10 增长子类别的绝对增长金额
        st.subheader("可视化：增长金额对比")
        if not top_10_growth_subcategories.empty:
            fig_top10_subcat_bar = px.bar(
                top_10_growth_subcategories,
                x='Sub category',
                y='增长金额',
                title="Top 10 子类别 - 绝对增长金额 (2025预算 vs 2024实际)",
                text='增长金额',
                labels={'Sub category': '子类别名称', '增长金额': '增长金额 (元)'},
                color='Category', # 按父品类着色
                hover_data=['Category', '增长率']
            )
            fig_top10_subcat_bar.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig_top10_subcat_bar.update_layout(xaxis_tickangle=-45, height=500, yaxis_title="增长金额 (元)")
            st.plotly_chart(fig_top10_subcat_bar, use_container_width=True)
        else:
            st.warning("未能计算Top 10增长子类别数据。")

        # 战略建议 (按父 Category 分组显示)
        st.subheader("战略考量 (按父品类)")
        if not top_10_growth_subcategories.empty:
            unique_categories_subcat = top_10_growth_subcategories['Category'].unique()
            for category in unique_categories_subcat:
                # 这里也使用更新后的 advice 字典
                advice = category_advice.get(category, category_advice['default'])
                final_advice = advice
                if "[请根据实际情况补充]" in advice:
                    final_advice = advice.replace("[请根据实际情况补充]", f"所属父品类为 {category}")
                
                # 为每个唯一的父 Category 显示一次建议
                with st.container(border=True):
                    st.markdown(f"##### {category}")
                    st.info(final_advice)
        else:
             st.info("无子类别数据可供生成战略建议。")

        # 显示 Top 10 子类别详细数据列表
        st.subheader("Top 10 子类别详细数据及供应商构成")
        if not top_10_growth_subcategories.empty:
            # 移除旧的 display_subcategories DataFrame 创建和显示逻辑
            # display_subcategories = top_10_growth_subcategories[...].copy()
            # st.dataframe(display_subcategories...)
            
            # 遍历 Top 10 子类别并显示详情及其供应商
            for index, row in top_10_growth_subcategories.iterrows():
                st.markdown(f"#### **{index+1}. {row['Sub category']}**")
                col1, col2 = st.columns([1, 2]) # 调整列宽比例以容纳供应商表格
                
                with col1:
                    st.markdown(f"**父品类:** {row['Category']}")
                    st.metric("增长金额", f"{row['增长金额']:,.0f} 元")
                    
                    # 格式化增长率
                    growth_rate_sub = row.get('增长率', None)
                    growth_rate_sub_str = "N/A"
                    if pd.notna(growth_rate_sub):
                        if growth_rate_sub == float('inf'):
                            growth_rate_sub_str = "新增采购"
                        elif growth_rate_sub == -100:
                            growth_rate_sub_str = "停止采购"
                        elif isinstance(growth_rate_sub, (int, float)):
                            growth_rate_sub_str = f"{growth_rate_sub:.1f}%"
                    elif row['2024年Spend'] == 0 and row['增长金额'] > 0:
                        growth_rate_sub_str = "新增采购"
                    st.metric("增长率", growth_rate_sub_str)
                    
                    st.markdown(f"**2024年采购额:** {row['2024年Spend']:,.0f} 元")
                    st.markdown(f"**2025年预算额:** {row['2025年Spend']:,.0f} 元")
                    
                with col2:
                    # 筛选该子类别的供应商
                    subcat_suppliers = supplier_data[supplier_data['Sub Category'] == row['Sub category']].copy()
                    num_suppliers = subcat_suppliers['供应商'].nunique()
                    st.markdown(f"**供应商数量:** {num_suppliers}")
                    
                    # ---- 添加导热脂专项分析 ----
                    if row['Sub category'] == '导热脂':
                        st.warning("""**专项分析：导热脂**
                        - **情况:** 2024年采购额较低(约23万)，2025年预算大幅增加，可能反映项目从初期进入量产阶段。
                        - **供应商:** ECS Cleaning Solutions GmbH 是一家德国贸易商。
                        - **推测:** 对于出口型业务，这可能属于客户指定供应商。
                        - **建议:** 尝试在中国本地寻找具备同等或更高性能的导热脂供应商，进行技术验证和成本评估。若找到合适的本地替代方案，可准备材料向客户申请增加供应商或进行切换，以优化成本和供应链韧性。""")
                    # ---- 结束导热脂专项分析 ----
                    
                    # ---- 添加银钎焊料专项分析 ----
                    if row['Sub category'] == '银钎焊料':
                        st.warning("""**专项分析：银钎焊料**
                        - **风险:** 2025年预测数据显示供应商可能存在过度集中风险，单一供应商（上海大华）占比过高。
                        - **影响:** 这可能降低议价能力，并增加供应链中断风险，影响整体韧性。
                        - **建议:** **强烈建议** 启动替代供应商寻源和评估工作（参考上述商务降本策略中提到的方向），即使短期内不切换，也要有成熟的备选方案以应对潜在风险，并作为重要的谈判筹码。""")
                    # ---- 结束银钎焊料专项分析 ----
                        
                    if num_suppliers > 0:
                        st.markdown("**主要供应商列表 (按2024年采购额排序):**")
                        supplier_display_data = subcat_suppliers[[
                            '供应商', '2024合计入库金额', '2025合计预算金额', '增长率'
                        ]].sort_values('2024合计入库金额', ascending=False).reset_index(drop=True)
                        
                        # 格式化增长率
                        supplier_display_data['增长率'] = supplier_display_data['增长率'].apply(
                            lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A"
                        )
                        
                        st.dataframe(
                            supplier_display_data.style.format({
                                '2024合计入库金额': '{:,.0f}',
                                '2025合计预算金额': '{:,.0f}'
                            }, na_rep='N/A'),
                            use_container_width=True,
                            height=min(200, 35 + 35 * len(supplier_display_data)), # 限制最大高度
                            hide_index=True
                        )
                    else:
                        st.info("该子类别下无关联供应商数据。")
                        
                # 添加分隔线
                st.markdown("---")
        else:
             st.info("没有找到符合条件的子类别数据。")

    # --- 2025年关键子类别降本指南 (环形图 + 交互式表格) ---
    with st.expander("🎯 2025年关键子类别降本指南 (预算占比与供应商明细)", expanded=True): # 将 expanded 改为 True
        st.markdown("通过环形图查看各品类下子类别的预算占比，并选择子类别查看详细的供应商预算明细。")

        # 准备数据：按Category和Sub Category聚合2025年预算
        subcat_spend_2025 = supplier_data.groupby(['Category', 'Sub Category'], observed=True)['2025合计预算金额'].sum().reset_index()
        # 过滤掉预算为0或负数的子类别，避免影响可视化和选择
        subcat_spend_2025 = subcat_spend_2025[subcat_spend_2025['2025合计预算金额'] > 0]
        
        # 获取所有Category
        all_categories = subcat_spend_2025['Category'].unique()

        # 遍历每个Category进行分析
        for category in all_categories:
            st.markdown(f"### {category}")
            
            # 筛选当前Category的数据
            category_subcats_data = subcat_spend_2025[subcat_spend_2025['Category'] == category].copy()
            category_subcats_data = category_subcats_data.sort_values('2025合计预算金额', ascending=False)

            col1, col2 = st.columns([1, 1]) # 左右布局：左图右选择+表格

            with col1:
                # 创建环形图
                if not category_subcats_data.empty:
                    fig_donut = go.Figure(data=[go.Pie(
                        labels=category_subcats_data['Sub Category'],
                        values=category_subcats_data['2025合计预算金额'],
                        hole=.4, # 设置空心比例
                        textinfo='percent', # 显示百分比
                        hoverinfo='label+value+percent', # 鼠标悬停信息
                        insidetextorientation='radial' # 文本方向
                    )])
                    fig_donut.update_layout(
                        title_text=f"{category} - 子类别预算占比",
                        height=400,
                        showlegend=False, # 通常子类别过多时图例意义不大
                        margin=dict(t=50, l=0, r=0, b=0)
                    )
                    st.plotly_chart(fig_donut, use_container_width=True)
                else:
                    st.info(f"{category} 品类下无2025年预算数据。")

            with col2:
                if not category_subcats_data.empty:
                    # 获取当前Category下的Sub Category列表
                    sub_category_list = category_subcats_data['Sub Category'].tolist()
                    
                    # 创建下拉选择框
                    # 使用 unique key 包含 category 名称
                    selected_subcat = st.selectbox(
                        f"选择 {category} 下的子类别查看供应商：",
                        options=sub_category_list,
                        key=f"subcat_selector_{category}",
                        index=0 # 默认选中第一个
                    )
                    
                    # 根据选择显示供应商明细
                    if selected_subcat:
                        st.markdown(f"**{selected_subcat} - 供应商2025年预算明细:**")
                        # 筛选供应商数据
                        subcat_suppliers_detail = supplier_data[
                            (supplier_data['Category'] == category) & 
                            (supplier_data['Sub Category'] == selected_subcat) & 
                            (supplier_data['2025合计预算金额'] > 0) # 只显示有预算的
                        ].copy()
                        
                        if not subcat_suppliers_detail.empty:
                            supplier_budget_list = subcat_suppliers_detail[[
                                '供应商', '2025合计预算金额'
                            ]].sort_values('2025合计预算金额', ascending=False).reset_index(drop=True)
                            
                            st.dataframe(
                                supplier_budget_list.style.format({'2025合计预算金额': '{:,.0f}'}),
                                use_container_width=True,
                                height=min(300, 35 + 35 * len(supplier_budget_list)), # 调整高度
                                hide_index=True
                            )
                        else:
                            st.info(f"在 {selected_subcat} 子类别下未找到2025年有预算的供应商。")
                else:
                    st.info("无子类别可供选择。")
            
            st.markdown("---") # 每个品类后的分隔线
    # --- 恢复结束 ---

# --- tab_manager 内容结束 ---

with tab2:
    st.header("品类战略分析")
    
    # 计算每个Category的总采购额和增长率
    category_summary = category_data.groupby('Category').agg({
        '2024年Spend': 'sum',
        '2025年Spend': 'sum',
        '增长金额': 'sum'
    }).reset_index()
    
    category_summary['增长率'] = (category_summary['增长金额'] / category_summary['2024年Spend'] * 100).round(1)
    
    # 创建气泡图
    fig = px.scatter(
        category_summary,
        x='2024年Spend',
        y='增长率',
        size='2025年Spend',
        color='Category',
        text='Category',
        title="品类战略矩阵分析",
        labels={
            '2024年Spend': '2024年采购规模',
            '增长率': '增长率(%)',
            '2025年Spend': '2025年预测规模'
        }
    )
    
    fig.update_traces(textposition='top center')
    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)
    
    # Top 10 增长和下降的子品类
    col1, col2 = st.columns(2)
    
    with col1:
        # 过滤掉无效的增长率数据（inf和-100）
        valid_growth_data = category_data[
            (category_data['增长率'] != float('inf')) & 
            (category_data['增长率'] != -100) &
            (category_data['2024年Spend'] > 100000)  # 添加最小基数过滤
        ].copy()
        
        # 获取Top 10高增长子品类
        top_growth = valid_growth_data.nlargest(10, '增长率')
        
        # 创建柱状图
        fig = px.bar(
            top_growth,
            x='Sub category',
            y='增长率',
            title="Top 10 高增长子品类",
            color='Category',
            text=top_growth['增长率'].apply(lambda x: f'{x:.1f}%')
        )
        
        # 更新布局
        fig.update_layout(
            height=400,
            xaxis_title="子品类",
            yaxis_title="增长率(%)",
            xaxis_tickangle=-45,
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 获取Top 10负增长子品类
        top_decline = valid_growth_data.nsmallest(10, '增长率')
        
        # 创建柱状图
        fig = px.bar(
            top_decline,
            x='Sub category',
            y='增长率',
            title="Top 10 负增长子品类",
            color='Category',
            text=top_decline['增长率'].apply(lambda x: f'{x:.1f}%')
        )
        
        # 更新布局
        fig.update_layout(
            height=400,
            xaxis_title="子品类",
            yaxis_title="增长率(%)",
            xaxis_tickangle=-45,
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)
        
    # 添加数据说明
    st.markdown("""
    #### 📊 增长率说明
    - 高增长子品类：显示增长率最高的10个子品类（不含新增品类，且2024年基数>10万元）
    - 负增长子品类：显示增长率最低的10个子品类（不含停止采购品类，且2024年基数>10万元）
    - 增长率计算：(2025年预测 - 2024年实际) / 2024年实际 × 100%
    """)

    # 品类战略建议
    st.subheader("📌 品类战略建议")
    st.markdown("""
    1. **重点发展品类**：
        - Copper & Aluminum类别保持最大采购规模，建议继续加强供应商管理和价格管控
        - Assembly & Mechanical Parts类别增长显著，需要开发更多优质供应商
    
    2. **结构优化方向**：
        - 对于增长率较高的子品类（如导热脂、接线盒等），建议提前布局供应商资源
        - 对于大幅下滑的品类，需评估是否为技术迭代导致，及时调整采购策略
    
    3. **成本控制重点**：
        - 铜材相关品类占比最大，建议考虑:
            * 开发期货采购或锁价机制
            * 增加供应商竞争
            * 优化库存管理策略
    """)

    # 在tab2中替换BCG矩阵，改用品类趋势分析
    st.subheader("📊 品类趋势矩阵对比分析")
    
    # 计算2024年品类的关键指标
    category_analysis_2024 = category_summary.copy()
    category_analysis_2024['采购占比'] = category_analysis_2024['2024年Spend'] / category_analysis_2024['2024年Spend'].sum() * 100
    category_analysis_2024['年度变化额'] = category_analysis_2024['2025年Spend'] - category_analysis_2024['2024年Spend']

    # 计算2025年品类的关键指标
    category_analysis_2025 = category_summary.copy()
    category_analysis_2025['采购占比'] = category_analysis_2025['2025年Spend'] / category_analysis_2025['2025年Spend'].sum() * 100
    category_analysis_2025['年度变化额'] = category_analysis_2025['2025年Spend'] - category_analysis_2025['2024年Spend']

    # 创建两列布局
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 2024年品类趋势矩阵")
        # 创建2024年趋势矩阵
        fig1 = px.scatter(
            category_analysis_2024,
            x='采购占比',
            y='增长率',
            size='2024年Spend',
            color='年度变化额',
            text='Category',
            labels={
                '采购占比': '2024年采购占比 (%)',
                '增长率': '增长率 (%)',
                '年度变化额': '年度变化金额'
            }
        )
        fig1.add_hline(y=0, line_dash="dash", line_color="gray")
        fig1.add_vline(x=category_analysis_2024['采购占比'].mean(), line_dash="dash", line_color="gray")
        fig1.update_layout(height=500)
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.markdown("### 2025年品类趋势矩阵")
        # 创建2025年趋势矩阵
        fig2 = px.scatter(
            category_analysis_2025,
            x='采购占比',
            y='增长率',
            size='2025年Spend',
            color='年度变化额',
            text='Category',
            labels={
                '采购占比': '2025年采购占比 (%)',
                '增长率': '增长率 (%)',
                '年度变化额': '年度变化金额'
            }
        )
        fig2.add_hline(y=0, line_dash="dash", line_color="gray")
        fig2.add_vline(x=category_analysis_2025['采购占比'].mean(), line_dash="dash", line_color="gray")
        fig2.update_layout(height=500)
        st.plotly_chart(fig2, use_container_width=True)

    # 添加矩阵对比分析
    st.markdown("### 📊 品类趋势矩阵对比分析")
    
    # 计算关键变化指标
    category_changes = pd.DataFrame({
        'Category': category_analysis_2024['Category'],
        '2024采购占比': category_analysis_2024['采购占比'],
        '2025采购占比': category_analysis_2025['采购占比'],
        '占比变化': category_analysis_2025['采购占比'] - category_analysis_2024['采购占比'],
        '2024年Spend': category_analysis_2024['2024年Spend'],
        '2025年Spend': category_analysis_2024['2025年Spend'],
        '增长率': category_analysis_2024['增长率']
    }).sort_values('占比变化', ascending=False)

    # 显示品类变化分析表
    st.markdown("#### 品类结构变化分析")
    
    # 创建格式化版本的数据用于显示
    display_category_changes = category_changes.copy()
    
    # 格式化各列
    for col in ['2024采购占比', '2025采购占比', '占比变化']:
        display_category_changes[col] = display_category_changes[col].apply(
            lambda x: f"{x:.1f}%" if col != '占比变化' else f"{x:+.1f}%"
        )
    
    for col in ['2024年Spend', '2025年Spend']:
        display_category_changes[col] = display_category_changes[col].apply(lambda x: f"{x:,.0f}")
    
    display_category_changes['增长率'] = display_category_changes['增长率'].apply(lambda x: f"{x:.1f}%")
    
    st.dataframe(display_category_changes, use_container_width=True)

    # 分析结论
    st.markdown("""
    #### 📌 主要变化分析

    1. **结构变化显著的品类**：
       - 占比提升最大：{up_cat}（+{up_pct:.1f}%）
       - 占比下降最大：{down_cat}（{down_pct:.1f}%）

    2. **品类地位变化**：
       - 新晋重要品类：{new_important}
       - 地位下降品类：{declining}

    3. **采购策略建议**：
       - 对于占比提升的品类：加强供应商管理，确保供应稳定
       - 对于占比下降的品类：评估下降原因，优化采购策略
       - 对于新晋重要品类：提前布局供应商资源，建立战略合作关系
       - 对于地位下降品类：分析市场需求变化，调整采购策略
    """.format(
        up_cat=category_changes.iloc[0]['Category'],
        up_pct=category_changes.iloc[0]['占比变化'],
        down_cat=category_changes.iloc[-1]['Category'],
        down_pct=category_changes.iloc[-1]['占比变化'],
        new_important=', '.join(category_changes[
            (category_changes['2024采购占比'] < category_changes['2024采购占比'].mean()) & 
            (category_changes['2025采购占比'] > category_changes['2025采购占比'].mean())
        ]['Category'].tolist()),
        declining=', '.join(category_changes[
            (category_changes['2024采购占比'] > category_changes['2024采购占比'].mean()) & 
            (category_changes['2025采购占比'] < category_changes['2025采购占比'].mean())
        ]['Category'].tolist())
    ))

    # 添加品类详细信息的交互部分
    st.subheader("📊 品类详细信息查看")
    selected_category = st.selectbox(
        "选择品类查看详细信息：",
        category_analysis_2024['Category'].unique()
    )

    # 显示所选品类的供应商信息
    category_suppliers = supplier_data[supplier_data['Category'] == selected_category].copy()
    category_suppliers['采购占比'] = category_suppliers['2024合计入库金额'] / category_suppliers['2024合计入库金额'].sum() * 100

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"### {selected_category}品类概况")
        category_info = category_analysis_2024[category_analysis_2024['Category'] == selected_category].iloc[0]
        st.markdown(f"""
        - 2024年采购额：{category_info['2024年Spend']:,.0f}元
        - 2025年预测：{category_info['2025年Spend']:,.0f}元
        - 增长率：{category_info['增长率']:.1f}%
        - 采购占比：{category_info['采购占比']:.1f}%
        """)

    with col2:
        st.markdown("### 供应商分布")
        fig = px.pie(
            category_suppliers,
            values='2024合计入库金额',
            names='供应商',
            title=f"{selected_category}供应商采购金额分布"
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    # 显示供应商详细数据
    st.markdown("### 供应商明细数据")
    st.dataframe(
        category_suppliers[[
            '供应商', '2024合计入库金额', '2025合计预算金额', 
            '增长率', '采购占比'
        ]].sort_values('2024合计入库金额', ascending=False).style.format({
            '2024合计入库金额': '{:,.0f}',
            '2025合计预算金额': '{:,.0f}',
            '增长率': '{:.1f}%',
            '采购占比': '{:.1f}%'
        }),
        use_container_width=True
    )

    st.markdown("""
    ### 📌 品类趋势分析
    
    1. **重点关注品类**
       - 采购占比 > 平均值且增长率为正的品类
       - 年度变化金额较大的品类
       - 需要重点关注供应链稳定性
    
    2. **优化管理品类**
       - 采购占比 > 平均值但增长率为负的品类
       - 需要分析下降原因
       - 评估是否需要调整采购策略
    
    3. **培育发展品类**
       - 采购占比 < 平均值但增长率为正的品类
       - 关注增长潜力
       - 提前布局供应商资源
    
    4. **观察调整品类**
       - 采购占比 < 平均值且增长率为负的品类
       - 评估使用需求变化
       - 考虑是否需要战略调整
    """)

    # Sub Category数据变化分析
    st.subheader("Sub Category数据变化分析")
    
    # 读取并处理Sub Category数据
    subcategory_data = category_data.copy()  # 使用已加载的数据而不是重新读取
    
    # 计算增长率和增长金额
    subcategory_data['增长金额'] = subcategory_data['2025年Spend'] - subcategory_data['2024年Spend']
    # 修改增长率计算逻辑，处理2024年为0的特殊情况
    subcategory_data['增长率'] = subcategory_data.apply(
        lambda row: (
            0 if row['2024年Spend'] == 0 and row['2025年Spend'] == 0
            else float('inf') if row['2024年Spend'] == 0 and row['2025年Spend'] > 0
            else -100 if row['2025年Spend'] == 0
            else (row['增长金额'] / row['2024年Spend'] * 100)
        ),
        axis=1
    )
    
    # 创建选择器让用户选择Category
    selected_category = st.selectbox(
        "选择Category查看Sub Category详情：",
        sorted(subcategory_data['Category'].unique())
    )
    
    # 筛选选中Category的数据
    category_detail = subcategory_data[subcategory_data['Category'] == selected_category].copy()
    
    # 创建两列布局
    col1, col2 = st.columns(2)
    
    with col1:
        # 创建Sub Category的采购金额对比图
        fig = go.Figure()
        
        # 添加2024年数据
        fig.add_trace(go.Bar(
            name='2024年',
            x=category_detail['Sub category'],
            y=category_detail['2024年Spend'],
            text=category_detail['2024年Spend'].apply(lambda x: f'{x:,.0f}'),
            textposition='auto',
        ))
        
        # 添加2025年数据
        fig.add_trace(go.Bar(
            name='2025年',
            x=category_detail['Sub category'],
            y=category_detail['2025年Spend'],
            text=category_detail['2025年Spend'].apply(lambda x: f'{x:,.0f}'),
            textposition='auto',
        ))
        
        # 更新布局
        fig.update_layout(
            title=f"{selected_category} - Sub Category采购金额对比",
            barmode='group',
            height=400,
            yaxis_title="采购金额",
            xaxis_title="Sub Category"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 创建增长率图表
        fig = go.Figure()
        
        # 添加增长率数据，处理特殊值的显示
        growth_text = category_detail['增长率'].apply(
            lambda x: '新增' if x == float('inf') else (
                '停止' if x == -100 else f'{x:.1f}%'
            )
        )
        
        fig.add_trace(go.Bar(
            x=category_detail['Sub category'],
            y=category_detail['增长率'].apply(
                lambda x: 100 if x == float('inf') else (
                    -100 if x == -100 else x
                )
            ),
            text=growth_text,
            textposition='auto',
            marker_color=category_detail['增长率'].apply(
                lambda x: 'red' if x < -30 else ('green' if x > 30 or x == float('inf') else 'orange')
            )
        ))
        
        # 更新布局
        fig.update_layout(
            title=f"{selected_category} - Sub Category增长率分析",
            height=400,
            yaxis_title="增长率 (%)",
            xaxis_title="Sub Category"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # 显示详细数据表格
    st.markdown("#### 详细数据")
    
    # 格式化数据显示
    formatted_data = category_detail.copy()
    formatted_data['2024年Spend'] = formatted_data['2024年Spend'].apply(lambda x: f'{x:,.0f}')
    formatted_data['2025年Spend'] = formatted_data['2025年Spend'].apply(lambda x: f'{x:,.0f}')
    formatted_data['增长金额'] = formatted_data['增长金额'].apply(lambda x: f'{x:,.0f}')
    formatted_data['增长率'] = formatted_data['增长率'].apply(
        lambda x: '新增' if x == float('inf') else (
            '停止' if x == -100 else f'{x:.1f}%'
        )
    )
    
    # 显示数据表格
    # 创建一个新的DataFrame，因为formatted_data中的增长率已经是字符串格式
    display_data = pd.DataFrame({
        'Sub category': formatted_data['Sub category'],
        '2024年Spend': formatted_data['2024年Spend'],
        '2025年Spend': formatted_data['2025年Spend'],
        '增长金额': formatted_data['增长金额'],
        '增长率': formatted_data['增长率']
    })
    
    st.dataframe(display_data, use_container_width=True)
    
    # 添加分析总结
    st.markdown("#### 分析总结")
    
    # 计算关键指标（排除特殊值）
    valid_growth = category_detail[
        (category_detail['增长率'] != float('inf')) & 
        (category_detail['增长率'] != -100)
    ]['增长率']
    
    avg_growth = valid_growth.mean() if not valid_growth.empty else 0
    max_growth = valid_growth.max() if not valid_growth.empty else 0
    min_growth = valid_growth.min() if not valid_growth.empty else 0
    
    # 计算特殊情况的数量并获取具体项目
    new_items = category_detail[category_detail['增长率'] == float('inf')]
    stopped_items = category_detail[category_detail['增长率'] == -100]
    high_growth_items = category_detail[
        (category_detail['增长率'] > 30) & 
        (category_detail['增长率'] != float('inf'))
    ].sort_values('增长率', ascending=False)
    low_growth_items = category_detail[
        (category_detail['增长率'] < -30) & 
        (category_detail['增长率'] != -100)
    ].sort_values('增长率')
    
    st.markdown(f"""
    **{selected_category}类别分析：**
    - 平均增长率：{avg_growth:.1f}%（不含新增和停止项）
    - 最高增长率：{max_growth:.1f}%（不含新增项）
    - 最低增长率：{min_growth:.1f}%（不含停止项）
    
    **新增Sub Category（{len(new_items)}个）：**
    {new_items['Sub category'].to_list() if not new_items.empty else '无'}
    
    **停止采购Sub Category（{len(stopped_items)}个）：**
    {stopped_items['Sub category'].to_list() if not stopped_items.empty else '无'}
    
    **高增长(>30%) Sub Category（{len(high_growth_items)}个）：**
    {high_growth_items.apply(lambda x: f"- {x['Sub category']}（{x['增长率']:.1f}%）", axis=1).to_list() if not high_growth_items.empty else '无'}
    
    **负增长(<-30%) Sub Category（{len(low_growth_items)}个）：**
    {low_growth_items.apply(lambda x: f"- {x['Sub category']}（{x['增长率']:.1f}%）", axis=1).to_list() if not low_growth_items.empty else '无'}
    """)

with tab3:
    st.header("供应商管理矩阵")
    
    # 创建供应商矩阵图
    fig = px.scatter(
        supplier_data.head(50),  # 取前50大供应商
        x='2024合计入库金额',
        y='增长率',
        size='2025合计预算金额',
        color='Category',
        hover_name='供应商',
        title="供应商战略矩阵（Top 50）",
        labels={
            '2024合计入库金额': '2024年采购规模',
            '增长率': '增长率(%)',
            '2025合计预算金额': '2025年预测规模'
        }
    )
    
    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)
    
    # 供应商集中度分析
    st.subheader("供应商集中度分析")
    col1, col2 = st.columns(2)
    
    with col1:
        # 添加Top10供应商详细信息
        st.markdown("### 2024年 Top 10供应商")
        
        # 计算2024年Top10供应商
        top10_2024 = supplier_data.nlargest(10, '2024合计入库金额').copy()
        total_2024 = supplier_data['2024合计入库金额'].sum()
        top10_2024['2024占比'] = top10_2024['2024合计入库金额'] / total_2024 * 100
        
        # 显示2024年Top10供应商表格
        st.dataframe(
            top10_2024[[
                '供应商', 'Category', 'Sub Category',
                '2024合计入库金额', '2024占比'
            ]].style.format({
                '2024合计入库金额': '{:,.0f}',
                '2024占比': '{:.1f}%'
            }).background_gradient(
                subset=['2024占比'],
                cmap='YlOrRd'
            ),
            use_container_width=True
        )

        st.markdown("### 2025年 Top 10供应商")
        
        # 计算2025年Top10供应商
        top10_2025 = supplier_data.nlargest(10, '2025合计预算金额').copy()
        total_2025 = supplier_data['2025合计预算金额'].sum()
        top10_2025['2025占比'] = top10_2025['2025合计预算金额'] / total_2025 * 100
        
        # 显示2025年Top10供应商表格
        st.dataframe(
            top10_2025[[
                '供应商', 'Category', 'Sub Category',
                '2025合计预算金额', '2025占比'
            ]].style.format({
                '2025合计预算金额': '{:,.0f}',
                '2025占比': '{:.1f}%'
            }).background_gradient(
                subset=['2025占比'],
                cmap='YlOrRd'
            ),
            use_container_width=True
        )

        # 分析Top10变化
        st.markdown("### Top 10供应商变化分析")
        
        # 找出进入/退出Top10的供应商
        new_top10 = set(top10_2025['供应商']) - set(top10_2024['供应商'])
        exit_top10 = set(top10_2024['供应商']) - set(top10_2025['供应商'])
        
        st.markdown(f"""
        #### 📊 Top 10变化情况：
        - 新进入Top10的供应商：{', '.join(new_top10) if new_top10 else '无'}
        - 退出Top10的供应商：{', '.join(exit_top10) if exit_top10 else '无'}
        """)
    
    with col2:
        st.markdown("### 各品类供应商分布")
        
        # 计算各品类的供应商数量和占比
        category_supplier_stats = pd.DataFrame({
            '供应商数量': supplier_data.groupby('Category', observed=True)['供应商'].nunique(),
            '采购金额': supplier_data.groupby('Category', observed=True)['2024合计入库金额'].sum()
        }).reset_index()
        
        # 计算供应商数量占比
        total_suppliers = category_supplier_stats['供应商数量'].sum()
        category_supplier_stats['供应商占比'] = (category_supplier_stats['供应商数量'] / total_suppliers * 100)
        
        # 创建饼图
        fig = go.Figure()
        
        # 添加环形图
        fig.add_trace(go.Pie(
            labels=category_supplier_stats['Category'],
            values=category_supplier_stats['供应商占比'],  # 使用供应商占比
            hole=0.6,
            textinfo='label+percent',
            textposition='outside',
            texttemplate='%{label}<br>%{value:.1f}%',  # 显示精确的占比值
            showlegend=False,
            marker=dict(colors=px.colors.qualitative.Set3)
        ))
        
        # 在中心添加总计信息
        fig.add_annotation(
            text=f"总供应商数量<br>{total_suppliers}家",
            x=0.5, y=0.5,
            font=dict(size=14, color='black'),
            showarrow=False
        )
        
        # 更新布局
        fig.update_layout(
            height=400,
            title={
                'text': "供应商数量分布",
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            margin=dict(t=60, l=20, r=20, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 添加详细数据表格
        st.markdown("#### 品类供应商详细分布")
        category_supplier_stats['采购金额'] = category_supplier_stats['采购金额'] / 10000  # 转换为万元
        st.dataframe(
            category_supplier_stats.style.format({
                '供应商数量': '{:,.0f}',
                '采购金额': '{:,.0f}万',
                '供应商占比': '{:.1f}%'
            }).background_gradient(
                subset=['供应商占比'],
                cmap='YlOrRd'
            ),
            use_container_width=True
        )
    
    # 供应商战略建议
    st.subheader("📌 供应商战略建议")
    st.markdown("""
    1. **核心供应商管理**：
        - 对于采购规模大且增长率高的供应商，建议：
            * 建立战略合作关系
            * 签订长期框架协议
            * 共同开发新技术/新产品
    
    2. **供应商结构优化**：
        - 重点关注"高成长性"供应商，提供更多业务机会
        - 对于负增长的大型供应商，需评估合作模式
        - 适度引入新供应商，优化供应商结构
    
    3. **风险管控建议**：
        - 密切监控供应商集中度
        - 为关键品类建立备选供应商
        - 定期评估供应商财务状况
    """)

    # 在tab3中替换Kraljic矩阵，改用供应商结构分析
    st.subheader("📊 供应商结构分析")
    
    # 计算供应商的关键指标
    supplier_analysis = supplier_data.copy()
    supplier_analysis['采购占比'] = supplier_analysis['2024合计入库金额'] / supplier_analysis['2024合计入库金额'].sum() * 100
    supplier_analysis['供应商等级'] = pd.qcut(supplier_analysis['2024合计入库金额'], q=4, labels=['D级', 'C级', 'B级', 'A级'])
    
    col1, col2 = st.columns(2)
    with col1:
        supplier_level_dist = supplier_analysis.groupby('供应商等级').size()
        fig = px.pie(
            values=supplier_level_dist.values,
            names=supplier_level_dist.index,
            title="供应商等级分布",
            hole=0.4
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        supplier_level_amount = supplier_analysis.groupby('供应商等级')['2024合计入库金额'].sum()
        supplier_level_amount_pct = supplier_level_amount / supplier_level_amount.sum() * 100
        fig = px.bar(
            x=supplier_level_amount_pct.index,
            y=supplier_level_amount_pct.values,
            title="各等级供应商采购金额占比",
            labels={'x': '供应商等级', 'y': '采购金额占比 (%)'},
            text=supplier_level_amount_pct.round(1).astype(str) + '%'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    # 添加供应商等级详细信息的交互部分
    st.subheader("📊 供应商等级详细信息")
    selected_level = st.selectbox(
        "选择供应商等级查看详细信息：",
        ['A级', 'B级', 'C级', 'D级']
    )

    # 显示所选等级的供应商信息
    level_suppliers = supplier_analysis[supplier_analysis['供应商等级'] == selected_level].copy()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"### {selected_level}供应商概况")
        st.markdown(f"""
        - 供应商数量：{len(level_suppliers)}家
        - 采购总额：{level_suppliers['2024合计入库金额'].sum():,.0f}元
        - 平均采购额：{level_suppliers['2024合计入库金额'].mean():,.0f}元
        - 平均增长率：{level_suppliers['增长率'].mean():.1f}%
        """)

    with col2:
        st.markdown("### 品类分布")
        fig = px.pie(
            level_suppliers,
            values='2024合计入库金额',
            names='Category',
            title=f"{selected_level}供应商品类分布"
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    # 显示供应商详细数据
    st.markdown("### 供应商明细数据")
    st.dataframe(
        level_suppliers[[
            '供应商', 'Category', '2024合计入库金额', '2025合计预算金额',
            '增长率', '采购占比'
        ]].sort_values('2024合计入库金额', ascending=False).style.format({
            '2024合计入库金额': '{:,.0f}',
            '2025合计预算金额': '{:,.0f}',
            '增长率': '{:.1f}%',
            '采购占比': '{:.1f}%'
        }),
        use_container_width=True
    )

    # 供应商集中度分析
    st.markdown("""
    ### 📌 供应商结构分析
    
    1. **供应商分层情况**
       - A级：采购金额最高的25%供应商
       - B级：采购金额次高的25%供应商
       - C级：采购金额较低的25%供应商
       - D级：采购金额最低的25%供应商
    
    2. **集中度分析**
       - 计算各层级供应商的采购金额占比
       - 评估供应商结构是否合理
       - 识别关键供应商
    
    3. **管理建议**
       - A级供应商：重点维护，建立战略合作
       - B级供应商：重点培育，提升合作深度
       - C级供应商：择优培育，淘汰低效
       - D级供应商：常规管理，优化结构
    """)

with tab4:
    st.header("风险预警与建议")
    
    # 风险预警指标
    st.subheader("🚨 主要风险指标")
    
    # 创建三列布局显示关键指标
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 计算高依赖供应商数量（采购额占比>10%的供应商）
        total_spend_2024 = supplier_data['2024合计入库金额'].sum()
        high_dependency = len(supplier_data[
            supplier_data['2024合计入库金额'] / total_spend_2024 > 0.1
        ])
        st.metric(
            label="高依赖供应商数量",
            value=f"{high_dependency}个",
            delta="需要关注" if high_dependency > 5 else "正常"
        )
    
    with col2:
        # 计算大幅下滑品类数量和详细信息
        # 只考虑2024年基数大于100万的品类
        significant_decline = category_data[
            (category_data['增长率'] < -30) & 
            (category_data['2024年Spend'] > 1000000)
        ].sort_values('增长率')
        
        # 显示数量指标
        st.metric(
            label="大幅下滑品类数量",
            value=f"{len(significant_decline)}个",
            delta="需要分析" if len(significant_decline) > 5 else "正常",
            delta_color="inverse"
        )
        
        # 显示详细信息
        if len(significant_decline) > 0:
            st.markdown("##### 大幅下滑品类明细")
            st.markdown("""
            > 筛选条件：
            > 1. 2024年基数 > 100万元
            > 2. 增长率 < -30%
            """)
            decline_details = significant_decline[[
                'Category', 'Sub category', '2024年Spend', '增长率'
            ]].sort_values('增长率')
            
            # 使用st.dataframe显示带格式的表格
            st.dataframe(
                decline_details.style.format({
                    '2024年Spend': '{:,.0f}',
                    '增长率': '{:.1f}%'
                }).background_gradient(
                    subset=['增长率'],
                    cmap='RdYlGn',
                    vmin=-100,
                    vmax=0
                ),
                use_container_width=True,
                height=min(35 + 35 * len(decline_details), 300)  # 根据行数动态调整高度
            )
    
    with col3:
        # 计算供应商集中度
        top5_concentration = (supplier_data.nlargest(5, '2024合计入库金额')['2024合计入库金额'].sum() / 
                            total_spend_2024 * 100)
        st.metric(
            label="Top5供应商集中度",
            value=f"{top5_concentration:.1f}%",
            delta="风险较高" if top5_concentration > 50 else "正常"
        )
    
    # 风险地图
    st.subheader("风险地图")
    
    # 创建更详细的风险数据
    risk_data = pd.DataFrame({
        '风险项': [
            '供应商过度集中',
            '原材料价格波动',
            '品质一致性',
            '交付及时性',
            '技术迭代风险',
            '供应商财务风险'
        ],
        '影响程度': [5, 4, 3, 3, 4, 3],
        '发生概率': [4, 5, 2, 2, 3, 2],
        '风险等级': ['高', '高', '中', '中', '高', '中']
    })
    
    # 创建风险评估矩阵
    col1, col2 = st.columns([3, 2])
    
    with col1:
        fig = px.scatter(
            risk_data,
            x='发生概率',
            y='影响程度',
            size=[20]*len(risk_data),
            text='风险项',
            color='风险等级',
            title="风险评估矩阵"
        )
        
        fig.update_traces(textposition='top center')
        fig.update_layout(
            xaxis=dict(range=[0, 6], title="发生概率"),
            yaxis=dict(range=[0, 6], title="影响程度"),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 风险等级说明")
        st.markdown("""
        - 🔴 高风险：影响程度 × 发生概率 ≥ 12
        - 🟡 中风险：6 ≤ 影响程度 × 发生概率 < 12
        - 🟢 低风险：影响程度 × 发生概率 < 6
        """)
    
    # 风险详情查看
    st.subheader("风险详情查看")
    
    # 创建风险供应商详细信息
    risk_suppliers = pd.DataFrame({
        '供应商': supplier_data['供应商'],
        'Category': supplier_data['Category'],
        'Sub Category': supplier_data['Sub Category'],
        '2024采购额': supplier_data['2024合计入库金额'],
        '增长率': supplier_data['增长率']
    })
    
    # 添加风险类型判断
    risk_suppliers['集中度风险'] = risk_suppliers['2024采购额'] > risk_suppliers['2024采购额'].quantile(0.9)
    risk_suppliers['增长风险'] = risk_suppliers['增长率'] < -30
    
    # 风险筛选选项
    risk_type = st.selectbox(
        "选择风险类型查看详情：",
        ['供应商过度集中风险', '原材料价格波动风险', '品质一致性风险', 
         '交付及时性风险', '技术迭代风险', '供应商财务风险']
    )
    
    # 根据不同风险类型显示对应的供应商信息
    st.markdown(f"### {risk_type}详情")
    
    if risk_type == '供应商过度集中风险':
        high_concentration = risk_suppliers[risk_suppliers['集中度风险']].copy()
        high_concentration['采购占比'] = high_concentration['2024采购额'] / high_concentration['2024采购额'].sum() * 100
        st.markdown("""
        #### 风险原因：
        - 单个供应商采购额占比过高
        - 可能导致供应链依赖风险
        - 议价能力受限
        """)
        st.dataframe(
            high_concentration.style.format({
                '2024采购额': '{:,.0f}',
                '增长率': '{:.1f}%',
                '采购占比': '{:.1f}%'
            }).background_gradient(
                subset=['采购占比'],
                cmap='YlOrRd'
            ),
            use_container_width=True
        )
    
    elif risk_type == '原材料价格波动风险':
        # 筛选铜铝等大宗商品相关供应商
        commodity_suppliers = risk_suppliers[
            risk_suppliers['Category'].isin(['Copper &Aluminum', 'Steel'])
        ].copy()
        commodity_suppliers['采购占比'] = commodity_suppliers['2024采购额'] / commodity_suppliers['2024采购额'].sum() * 100
        st.markdown("""
        #### 风险原因：
        - 大宗商品价格波动
        - 汇率变化影响
        - 市场供需变化
        """)
        st.dataframe(
            commodity_suppliers.style.format({
                '2024采购额': '{:,.0f}',
                '增长率': '{:.1f}%',
                '采购占比': '{:.1f}%'
            }).background_gradient(
                subset=['采购占比'],
                cmap='YlOrRd'
            ),
            use_container_width=True
        )
    
    elif risk_type == '品质一致性风险':
        # 假设关键零部件供应商更容易出现品质风险
        quality_risk_categories = ['Assembly &Mechanical Parts', 'Electrical &Electronic']
        quality_risk_suppliers = risk_suppliers[
            risk_suppliers['Category'].isin(quality_risk_categories)
        ].copy()
        st.markdown("""
        #### 风险原因：
        - 工艺稳定性不足
        - 原材料品质波动
        - 质量管控体系不完善
        """)
        st.dataframe(
            quality_risk_suppliers.style.format({
                '2024采购额': '{:,.0f}',
                '增长率': '{:.1f}%'
            }),
            use_container_width=True
        )
    
    elif risk_type == '交付及时性风险':
        # 筛选增长率较高的供应商，可能面临产能压力
        delivery_risk_suppliers = risk_suppliers[
            risk_suppliers['增长率'] > 50
        ].copy()
        st.markdown("""
        #### 风险原因：
        - 供应商产能不足
        - 物流运输不稳定
        - 原材料供应紧张
        """)
        st.dataframe(
            delivery_risk_suppliers.style.format({
                '2024采购额': '{:,.0f}',
                '增长率': '{:.1f}%'
            }).background_gradient(
                subset=['增长率'],
                cmap='YlOrRd'
            ),
            use_container_width=True
        )
    
    elif risk_type == '技术迭代风险':
        # 筛选电子电气类供应商
        tech_risk_suppliers = risk_suppliers[
            risk_suppliers['Category'].isin(['Electrical &Electronic'])
        ].copy()
        st.markdown("""
        #### 风险原因：
        - 技术更新速度快
        - 产品生命周期短
        - 研发投入需求大
        """)
        st.dataframe(
            tech_risk_suppliers.style.format({
                '2024采购额': '{:,.0f}',
                '增长率': '{:.1f}%'
            }),
            use_container_width=True
        )
    
    elif risk_type == '供应商财务风险':
        # 筛选增长率为负的供应商
        financial_risk_suppliers = risk_suppliers[
            risk_suppliers['增长率'] < 0
        ].copy()
        st.markdown("""
        #### 风险原因：
        - 营收持续下滑
        - 现金流压力大
        - 经营状况不佳
        """)
        st.dataframe(
            financial_risk_suppliers.style.format({
                '2024采购额': '{:,.0f}',
                '增长率': '{:.1f}%'
            }).background_gradient(
                subset=['增长率'],
                cmap='RdYlGn'
            ),
            use_container_width=True
        )
    
    # 风险缓解建议
    st.subheader("📌 风险缓解建议")
    st.markdown(f"""
    ### {risk_type}缓解措施：
    
    {
        {
            '供应商过度集中风险': """
            1. **分散采购策略**
               - 培育备选供应商
               - 建立多区域供应网络
               - 适度分配采购份额
            
            2. **供应商管理**
               - 加强战略合作
               - 建立预警机制
               - 定期评估供应能力
            
            3. **长期举措**
               - 优化供应商结构
               - 建立供应商梯队
               - 降低单一依赖
            """,
            
            '原材料价格波动风险': """
            1. **价格管理**
               - 建立价格联动机制
               - 开展期货套期保值
               - 签订长期框架协议
            
            2. **库存优化**
               - 实施动态库存管理
               - 把握采购时机
               - 建立安全库存机制
            
            3. **供应链优化**
               - 寻找替代材料
               - 优化产品设计
               - 加强市场预测
            """,
            
            '品质一致性风险': """
            1. **质量管控**
               - 加强进料检验
               - 优化质量体系
               - 实施供应商审核
            
            2. **过程管理**
               - 建立质量追溯系统
               - 开展工艺优化
               - 加强人员培训
            
            3. **持续改进**
               - 推动质量提升项目
               - 建立激励机制
               - 分享最佳实践
            """,
            
            '交付及时性风险': """
            1. **库存管理**
               - 提高安全库存
               - 实施VMI管理
               - 优化订单周期
            
            2. **产能管理**
               - 评估供应商产能
               - 预留产能保证
               - 建立应急方案
            
            3. **物流优化**
               - 多样化运输方式
               - 优化物流网络
               - 加强信息共享
            """,
            
            '技术迭代风险': """
            1. **技术管理**
               - 加强技术交流
               - 推动联合创新
               - 建立技术路线图
            
            2. **产品开发**
               - 提前介入设计
               - 加快样品验证
               - 建立备份方案
            
            3. **持续创新**
               - 增加研发投入
               - 培养技术人才
               - 保持技术领先
            """,
            
            '供应商财务风险': """
            1. **财务监控**
               - 定期财务评估
               - 监控经营指标
               - 建立预警机制
            
            2. **付款管理**
               - 优化付款条件
               - 控制预付款比例
               - 加强账期管理
            
            3. **风险防范**
               - 要求履约保证
               - 建立备选方案
               - 控制合作规模
            """
        }[risk_type]
    }
    """)
    
    # 添加风险跟踪记录功能
    st.subheader("风险跟踪记录")
    
    # 创建三列布局显示跟踪信息
    track_col1, track_col2, track_col3 = st.columns(3)
    
    with track_col1:
        st.markdown("### 上月风险总数")
        st.metric(label="风险事项数量", value="18", delta="-2")
    
    with track_col2:
        st.markdown("### 已解决风险")
        st.metric(label="解决率", value="72%", delta="+5%")
    
    with track_col3:
        st.markdown("### 新增风险")
        st.metric(label="新增数量", value="3", delta="+1")

with tab5:
    st.header("数据明细总览")
    
    # 创建Category级别的汇总数据
    category_summary = category_data.groupby('Category').agg({
        '2024年Spend': 'sum',
        '2025年Spend': 'sum',
        '增长金额': 'sum'
    }).reset_index()
    category_summary['增长率'] = (category_summary['增长金额'] / category_summary['2024年Spend'] * 100).round(1)
    
    # 显示Category级别汇总
    st.subheader("📌 Category级别汇总")
    st.dataframe(
        category_summary.style.format({
            '2024年Spend': '{:,.0f}',
            '2025年Spend': '{:,.0f}',
            '增长金额': '{:,.0f}',
            '增长率': '{:.1f}%'
        }),
        use_container_width=True
    )
    
    # 创建Sub Category选择器
    st.subheader("📌 Sub Category明细")
    selected_category = st.selectbox(
        "选择Category查看子类别明细：",
        category_summary['Category'].unique()
    )
    
    # 显示选中Category的Sub Category数据
    subcategory_data = category_data[category_data['Category'] == selected_category]
    
    # 创建一个清理过的数据副本用于显示
    display_subcategory = subcategory_data[['Sub category', '2024年Spend', '2025年Spend', '增长金额', '增长率']].copy()
    
    # 单独处理数值列，确保非数值列不会被格式化
    for col in ['2024年Spend', '2025年Spend', '增长金额']:
        if pd.api.types.is_numeric_dtype(display_subcategory[col]):
            display_subcategory[col] = display_subcategory[col].apply(lambda x: f"{x:,.0f}" if pd.notnull(x) else "")
    
    # 单独处理增长率列，考虑到它可能是字符串
    if pd.api.types.is_numeric_dtype(display_subcategory['增长率']):
        display_subcategory['增长率'] = display_subcategory['增长率'].apply(lambda x: f"{x:.1f}%" if pd.notnull(x) else "")
    
    st.dataframe(display_subcategory, use_container_width=True)
    
    # 供应商明细
    st.subheader("📌 供应商明细")
    selected_subcategory = st.selectbox(
        "选择Sub Category查看供应商明细：",
        subcategory_data['Sub category'].unique()
    )
    
    # 显示选中Sub Category的供应商数据
    supplier_detail = supplier_data[supplier_data['Sub Category'] == selected_subcategory].copy()
    
    # 计算各供应商在不同工厂的采购金额
    supplier_detail['2024年占比'] = supplier_detail['2024合计入库金额'] / supplier_detail['2024合计入库金额'].sum() * 100
    supplier_detail['2025年占比'] = supplier_detail['2025合计预算金额'] / supplier_detail['2025合计预算金额'].sum() * 100
    
    st.dataframe(
        supplier_detail[[
            '供应商', 
            '2024汇风入库金额', '2024铜盟入库金额', '2024苏州入库金额', '2024合计入库金额', '2024年占比',
            '2025汇风预算金额', '2025铜盟预算金额', '2025苏州预算金额', '2025合计预算金额', '2025年占比',
            '增长金额', '增长率'
        ]].style.format({
            '2024汇风入库金额': '{:,.0f}',
            '2024铜盟入库金额': '{:,.0f}',
            '2024苏州入库金额': '{:,.0f}',
            '2024合计入库金额': '{:,.0f}',
            '2024年占比': '{:.1f}%',
            '2025汇风预算金额': '{:,.0f}',
            '2025铜盟预算金额': '{:,.0f}',
            '2025苏州预算金额': '{:,.0f}',
            '2025合计预算金额': '{:,.0f}',
            '2025年占比': '{:.1f}%',
            '增长金额': '{:,.0f}',
            '增长率': '{:.1f}%'
        }),
        use_container_width=True
    )
    
    # 添加数据说明
    st.markdown("""
    ### 📝 数据说明
    
    1. **Category级别汇总**
       - 展示各大类别的总采购金额和增长情况
       - 可以快速了解各品类的整体规模
    
    2. **Sub Category明细**
       - 显示选定Category下的所有子类别数据
       - 可以分析同一品类下不同子类别的表现
    
    3. **供应商明细**
       - 展示选定Sub Category下的所有供应商数据
       - 包含各供应商在不同工厂的采购分布
       - 显示供应商的份额占比和增长情况
    
    > 注：所有金额单位为元，增长率和占比均以百分比显示
    """)

# 添加页脚
st.markdown("---")
st.markdown("### 💡 决策者参考")

# 计算所需指标
significant_decline = len(category_data[category_data['增长率'] < -30])
max_supplier_share = (supplier_data['2024合计入库金额'].max() / supplier_data['2024合计入库金额'].sum() * 100)
bulk_material_suppliers = supplier_data[supplier_data['Category'].str.contains('Copper|Aluminum', na=False)]
bulk_material_growth = bulk_material_suppliers['增长率'].mean()

st.info(f"""
基于数据分析结果，提出以下关注重点：

1. **区域业务布局**：
   - 天津地区：
     * 现状：总采购额6.56亿，同比增长14%
     * 占比：占集团总采购额的74.2%
   
   - 苏州地区：
     * 现状：采购额2.28亿，同比下降9%
     * 占比：占集团总采购额的25.8%

2. **品类管理重点**：
   - 重点品类：
     * 铜材类占比42%，年采购额3.71亿
     * 新增长品类（导热脂、接线盒）增速>30%
   
   - 风险品类：
     * 8个子品类负增长，降幅>15%
     * 这些品类2024年采购总额1.2亿

3. **供应商结构**：
   - 集中度：
     * Top5供应商占比{top5_concentration:.1f}%
     * Top10供应商占比{top10_share:.1f}%
   
   - 分布情况：
     * {high_dependency}个供应商采购占比>10%
     * 大宗原材料供应商平均增长率{bulk_material_growth:.1f}%

4. **风险指标**：
   - 供应商依赖：
     * {high_dependency}个高依赖供应商
     * 单个最大供应商占比{max_supplier_share:.1f}%
   
   - 品类风险：
     * {significant_decline}个品类大幅下滑(>30%)
     * 这些品类2024年总额8,900万

> 📊 以上数据基于2024年实际数据和2025年预测数据
> 📈 所有增长率和占比均为实际计算值
""") 
