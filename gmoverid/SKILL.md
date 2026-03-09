---
name: gmoverid
description: "gm/ID 晶体管表征与设计方法学，基于 ngspice + Python。包含两个独立工作流：(1) 表征工作流 — 对任意 MOSFET 模型生成三套标准曲线：栅电容 Cgg/Cgs/Cgd/Cgb vs Vgs、gm/ID 四象限特性（gm/Id vs Vov、Id/W vs gm/Id、fT vs gm/Id、gm·ro vs gm/Id）、IV 特性（线性/对数 Id vs Vov、输出特性）；支持 180nm 单节点及 45/22nm HP 多节点流程，内置 PTM 模型文件（180/45/22nm），无需额外下载。(2) 设计工作流 — GmIdTable 类将仿真数据构建为查找表（缓存至 logs/cache/），提供 lookup()、size()、size_from_ft()、size_from_gmro() API，按 gm/ID 方法论对 NMOS/PMOS 定尺寸。仅依赖 ngspice skill。当需要搭建或扩展 gm/ID 表征项目、生成特性曲线、解读设计曲线、或按 gm/ID 方法对晶体管定尺寸时，使用本 skill。"
---

# gm/ID 表征与设计 Skill

**依赖**：`ngspice` skill（网表执行、wrdata 解析）。模型文件已内置，无需 `transistor-models` skill。

## 资产文件

```
assets/
├── simulate_gmoverid.py   — ngspice 仿真引擎、数据提取、解析电容、MODEL_INFO 注册表
├── plot_gmoverid.py       — 所有 matplotlib 绘图函数
├── run_gmoverid.py        — 180nm 单节点编排（NMOS/PMOS + 沟道长度扫描）
├── run_multinode.py       — 多节点编排（45/22nm HP）
├── design_gmoverid.py     — GmIdTable 查表/定尺寸 API + print_op()
├── models/                — 内置 PTM 模型文件（开箱即用）
│   ├── nmos180.lib        — 180nm BSIM3v3（VDD=1.8V）
│   ├── pmos180.lib
│   ├── nmos45hp.lib       — 45nm HP BSIM4（VDD=1.0V）
│   ├── pmos45hp.lib
│   ├── nmos22hp.lib       — 22nm HP BSIM4（VDD=0.8V）
│   └── pmos22hp.lib
└── netlist/
    ├── gmoverid_vgs.cir.tmpl       — NMOS Vgs 扫描（固定 Vds）
    ├── gmoverid_vds.cir.tmpl       — NMOS Vds 扫描（固定 Vgs）
    ├── gmoverid_pmos_vsg.cir.tmpl  — PMOS |Vsg| 扫描（固定 |Vsd|）
    └── gmoverid_pmos_vsd.cir.tmpl  — PMOS |Vsd| 扫描（固定 |Vsg|）
```

内置模型来自 [PTM — Arizona State University (ptm.asu.edu)](https://ptm.asu.edu)，免费用于学术研究。如需引用，请使用：W. Zhao and Y. Cao, "New Generation of Predictive Technology Model for Sub-45 nm Early Design Exploration," *IEEE Trans. Electron Devices*, vol. 53, no. 11, pp. 2816–2823, Nov. 2006. doi: 10.1109/TED.2006.884077。如需内置三节点之外的其他工艺，可安装 `transistor-models` skill（完整 PTM 模型库，需自行配置 MODEL_INFO）或从 [mec.umn.edu/ptm](https://mec.umn.edu/ptm) 下载，复制到项目 `models/` 目录。

---

## 工作流一：表征（仿真 + 绘图）

### 部署

1. 将所有 assets（含 `models/` 子目录）复制到 `<project>/`
2. 创建空目录 `plots/` 和 `logs/`
3. 运行 `python run_gmoverid.py`（180nm）或 `python run_multinode.py`（HP 多节点）

如需其他节点，将额外 `.lib` 文件复制到 `<project>/models/` 即可。

路径无需配置 — 全部通过 `Path(__file__).resolve().parent` 自动解析。

### 三套标准图（每个模型）

| 套数 | 函数 | 输出文件 |
|------|------|----------|
| 栅电容 | `plot_caps()` | `gmoverid_caps_{model}_L{node}nm.png` |
| gm/ID 四象限 | `plot_main()` | `gmoverid_{model}_L{node}nm.png` |
| IV 特性 | `plot_iv()` | `gmoverid_iv_{model}_L{node}nm.png` |

**gm/ID 四象限布局（`plot_main`，2×2）：**
```
(0,0) gm/Id [V⁻¹] vs Vov      | (0,1) Id/W [µA/µm] vs gm/Id  (对数 Y)
(1,0) fT [GHz]    vs gm/Id    | (1,1) gm·ro         vs gm/Id
```
- 全部四格以 Vds 为参数族（VDS_LIST）
- gm/Id X 轴：xlim=[4,24]，每 2 V⁻¹ 一格

### 新增工艺节点

1. 将模型 `.lib` 复制到 `models/`（可从 [mec.umn.edu/ptm](https://mec.umn.edu/ptm) 下载或安装 `transistor-models` skill）
2. 在 `simulate_gmoverid.py` 的 `MODEL_INFO` 新增条目（见 conventions.md §3）
3. 在 `run_multinode.py` 的 `NODE_CFG` 新增条目

---

## 绘图规范（新建图时须遵守）

> 为新项目生成图件或在设计报告中绘图时，须与本 skill 已有图件风格一致。

**格式要求：**
- 不得调用 `plt.show()`，统一使用 `fig.savefig(path, dpi=150, bbox_inches='tight')`；图件保存至 `plots/`
- 颜色与线型按 `plot_gmoverid.py` 中的 `COLORS`/`LSTYLE` 列表依次取用（蓝实线、橙虚线、绿点划线、紫点线）
- X 轴若为 gm/ID，统一 `xlim=[4, 24]`，每 2 V⁻¹ 一刻度；Y 轴 `ylim(bottom=0)`
- 图题与轴标签用 **ASCII + LaTeX**（如 `$g_m/I_D$`），**不要在 matplotlib 标签中直接写中文字符**
- **`µ`（U+00B5）在部分终端和字体下显示失败**，轴标签中一律用 `u` 替代（如 `uA/um`、`W=10um`），或用 LaTeX `$\\mu$`；除非用户明确要求才使用 Unicode µ

**中文字体警告：**
matplotlib 默认不含中文字体，直接写中文会显示方框（□□）。如确需中文，在脚本顶部添加：
```python
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
```
Windows 优先用 `Microsoft YaHei`；Linux/macOS 需确认系统已安装对应字体，否则仍显示方框。**最稳妥的方案是仅用 ASCII/LaTeX 标签，彻底规避字体依赖。**

---

## 工作流二：设计（查表定尺寸）

### gm/ID 方法论核心思想

**gm/ID（跨导效率）是连接电路指标与器件尺寸的轴心量。**

传统设计方法依赖长沟道模型公式（gm = 2Id/Vov）计算尺寸，在先进工艺（≤ 180nm）下误差极大。gm/ID 方法的根本出发点是：放弃公式，改用仿真生成的设计图（查表），用 gm/ID 作为唯一自变量，把器件的所有关键性能参数统一表达出来：

```
gm/ID  ──►  Id/W   （电流密度图，决定 W）
       ──►  fT     （截止频率，决定速度）
       ──►  gm·ro  （本征增益，决定增益上限）
       ──►  Vgs    （唯一确定偏置点）
```

这四条曲线全部**与晶体管宽度 W 无关**——不同 W 的器件在 gm/ID 轴上对应完全相同的 Id/W、fT、gm·ro 值。这是方法论的基础：设计图只需针对单位宽度生成一次，之后对任意 W 都直接适用。

**gm/ID 是三大设计目标的权衡轴：**

| 设计优先目标 | gm/ID 取值方向 | 原因 |
|-------------|:-------------:|------|
| 高速（fT↑） | 低 gm/ID（强反型） | 高 Vov → 快 |
| 高增益（gm·ro↑） | 高 gm/ID（弱/中反型） | 更接近亚阈值 |
| 低功耗（Id↓，同 W） | 高 gm/ID | Id/W 随 gm/ID 升高而降低 |
| 最小面积（W↓，同 Id） | 低 gm/ID | Id/W 随 gm/ID 升高而降低 |

> 注意：面积与功耗的优化方向相反——这正是 gm/ID 设计中需要权衡的核心矛盾。

---

### 设计流程（五步）

```
① 选拓扑 → ② 定 L → ③ 选 gm/ID → ④ 算 gm / Id → ⑤ 查 Id/W → 得 W
```

**① 选择拓扑**
根据增益、带宽、摆幅要求确定电路结构（共源、差分对、共栅、Cascode 等）。

**② 确定沟道长度 L**
- 需要高速（高 fT）→ 选最小 L
- 需要高增益（高 gm·ro）→ 适当增大 L（每倍 L，gm·ro 约提升 2–4×，fT 相应降低）
- 先验证可达性：`tbl.lookup('gmro', gmid_target)` 查上限；不满足时先增大 L，再考虑 cascode 或多级拓扑
- PMOS 负载时需同时核查 PMOS 的 ro：有效增益 = gm_n × (ro_n ∥ ro_p)

**③ 选定 gm/ID**
根据优先目标在 fT–gm/ID 和 gm·ro–gm/ID 图上选取权衡点：
```python
tbl = GmIdTable('nmos45hp', W=1.0, L=0.045, vds=0.5)

# 决策前先查边界值
print(f"fT   @ gmid=6  : {tbl.lookup('ft',   6.0)/1e9:.1f} GHz")
print(f"fT   @ gmid=15 : {tbl.lookup('ft',  15.0)/1e9:.1f} GHz")
print(f"gmro @ gmid=6  : {tbl.lookup('gmro',  6.0):.1f}")
print(f"gmro @ gmid=15 : {tbl.lookup('gmro', 15.0):.1f}")
```

**④ 由电路指标推导所需 gm，再算 Id**
```python
# 示例：BW 和增益约束推导 gm（ro 感知，见设计示例节）
Rout = 1 / (2 * 3.14159 * BW * CL)   # RL∥ro，由带宽决定
gm   = Av / Rout                       # 由增益决定
Id   = gm / gmid                       # 由 gm/ID 决定
```

**⑤ 查 Id/W 图得 W，对齐 100nm 栅格**
```python
id_w    = tbl.lookup('id_w', gmid)              # µA/µm（W 无关量）
W_exact = Id / (id_w * 1e-6)                   # µm
W       = round(W_exact / 0.1) * 0.1           # 四舍五入到 100nm
# W     = math.ceil(W_exact / 0.1) * 0.1       # 或向上取整（保守余量）
```

取整后重算 Id = W × id_w 校核 Av 和 BW；ΔW < 5% 时偏差通常可忽略。

---

### API 参考：`GmIdTable`

```python
from design_gmoverid import GmIdTable, print_op

# 首次调用：自动运行 ngspice 并缓存到 logs/cache/（JSON）
# 再次调用：直接读缓存，约 0.05 s
tbl = GmIdTable('nmos180', W=10.0, L=0.18, vds=0.9)
```

**构造参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `model` | str | — | `MODEL_INFO` 中的键，如 `'nmos180'`、`'pmos45hp'` |
| `W` | float | — | 仿真参考宽度 [µm]（结果与 W 无关，任意值均可） |
| `L` | float | — | 沟道长度 [µm] |
| `vds` | float | VDD/2 | Vgs 扫描时固定的 Vds（NMOS）或 \|Vsd\|（PMOS）[V] |
| `force_resim` | bool | False | `True` 则忽略缓存，重新仿真 |

**查询单个量（W 无关，仅依赖 gm/ID）：**

```python
tbl.lookup('id_w', gmid)   # Id/W [µA/µm]  ← 由此算 W
tbl.lookup('ft',   gmid)   # 截止频率 fT [Hz]
tbl.lookup('gmro', gmid)   # 本征增益 gm·ro
tbl.lookup('vgs',  gmid)   # Vgs（或 |Vsg|）[V]  ← 偏置点
tbl.lookup('vov',  gmid)   # 过驱动电压 Vov [V]
tbl.lookup('gm',   gmid)   # 跨导 [S]（在参考宽度 W 下）
```

**定尺寸：固定 gm/ID + 一个约束**

```python
op = tbl.size(gmid=15.0, Id=100e-6)   # 由 Id 求 W
op = tbl.size(gmid=15.0, W=20.0)      # 由 W 求 Id
op = tbl.size(gmid=15.0, gm=1.5e-3)   # 由 gm 求 Id 和 W
print_op(op)
```

**约束定尺寸：自动寻优（最高 gm/ID = 最省电流）**

```python
op = tbl.size_from_ft(8e9,  W=20.0)    # fT ≥ 8 GHz，固定 W
op = tbl.size_from_gmro(35, Id=50e-6)  # gm·ro ≥ 35，固定 Id
```

- `size_from_ft`：适合已知宽度、需满足速度指标的场景（LNA 跨导管、OTA GBW）
- `size_from_gmro`：适合高增益级（建议固定 W，避免弱反型下 W 过大）

**`size()` 返回字典的键：**
```
model, L_um, W_um, Id_A, Vgs_V, Vov_V, gmid, gm_S, ft_Hz, gmro, id_w_Apm
```

---

### 各节点 gm/ID 典型设计参数

**nmos180（Vds = 0.9 V，L = 180 nm）**

| gm/ID [V⁻¹] | Id/W [µA/µm] | fT [GHz] | gm·ro | 适用场景 |
|:-----------:|:------------:|:--------:|:-----:|----------|
|  5–8  | 42–81 | 20–25 | 27–36 | 高速电路、采样开关 |
| 10–12 | 20–29 | 15–18 | 39    | OTA 输出级、驱动器 |
| 13–16 | 8–17  |  9–13 | 39–46 | OTA 输入差分对（平衡） |
| 18–20 |  3–6  |  4–6  | 53    | 低功耗模拟级、基准 |

**nmos45hp / nmos22hp（HP，最小 L）**

| 节点 | gm/ID [V⁻¹] | Id/W [µA/µm] | fT [GHz] | gm·ro | 说明 |
|------|:-----------:|:------------:|:--------:|:-----:|------|
| 45nm HP | 6–10 | 150–300 | 200–400 | 6–8 | CLM 强，增益低，需考虑 ro |
| 22nm HP | 6–10 | 200–500 | 400–700 | 3–4 | DIBL 极强，增益极低 |

> Vds 对 Id/W 有轻微影响（先进节点输出阻抗低）：初始设计时忽略，仿真后微调。

---

## 设计示例：45nm HP 共源放大器

**指标**（来自教材 5.2.1 节，40nm 工艺，用 PTM 45nm HP 作为代理模型）：

| 指标 | 值 |
|------|----|
| VDD | 1.1 V |
| 低频电压增益 Av | 2（线性，即 6 dB） |
| −3 dB 带宽 BW | 100 MHz |
| 负载电容 CL | 10 pF |
| 总电流 Id | ≤ 2 mA |
| 沟道长度 L | 45 nm（最小栅长） |
| 设计目标 | gm/ID = 10 V⁻¹（平衡速度与功耗） |

### 1. 推导设计约束（含 ro）

增益公式含 ro 项，不可忽略：

```
|A_DC| = gm·(RL ∥ ro)

1/|A_DC| = 1/(gm·RL) + 1/(gm·ro)

=> gm·RL = 1 / (1/Av − 1/(gm·ro))
```

45nm HP 的本征增益 gm·ro ≈ 7（由 `tbl.lookup('gmro', gmid)` 查表确认），代入：

```
gm·RL = 1 / (1/2 − 1/7) ≈ 2.80
```

带宽决定输出节点总阻抗（RL ∥ ro），即实际 Rout：

```
Rout = RL ∥ ro = 1 / (2π × BW × CL)
     = 1 / (2π × 100 MHz × 10 pF) ≈ 159 Ω

gm = Av / Rout = 2 / 159 ≈ 12.6 mA/V

RL = gm·RL / gm = 2.80 / 12.6 mS ≈ 222 Ω
```

> **为什么不能直接 RL = Rout？** Rout = 159Ω 是 RL∥ro，不是 RL 本身。RL 必须大于 Rout，由增益公式中 gm·ro 项反算得到。

### 2. 用 GmIdTable 定尺寸

```python
from design_gmoverid import GmIdTable
import math

VDD = 1.1;  Av = 2.0;  BW = 100e6;  CL = 10e-12

tbl = GmIdTable('nmos45hp', W=1.0, L=0.045, vds=0.5)

gmid = 10.0
gmro = tbl.lookup('gmro', gmid)   # => 7.11
id_w = tbl.lookup('id_w', gmid)   # => 155.4 µA/µm
vgs  = tbl.lookup('vgs',  gmid)   # => 0.499 V  (偏置点 Vgs)
vov  = tbl.lookup('vov',  gmid)   # => 0.244 V

# Step 1: 推导 gm 和 RL（ro 感知）
Rout   = 1 / (2 * 3.14159 * BW * CL)   # 159 Ω = RL∥ro
gm_RL  = 1 / (1/Av - 1/gmro)           # 2.80（含 ro 的增益约束）
gm     = Av / Rout                      # 12.6 mA/V
RL     = gm_RL / gm                     # 222 Ω

# Step 2: 计算 Id 和 W
Id      = gm / gmid                     # 1.26 mA
W_exact = Id / (id_w * 1e-6)           # 8.09 µm
W       = round(W_exact / 0.1) * 0.1   # => 8.1 µm（100nm 栅格）

# Step 3: 用取整后的 W 校核
Id_r  = W * id_w * 1e-6                # 1.259 mA
gm_r  = Id_r * gmid                    # 12.59 mA/V
ro_r  = gmro / gm_r                    # 565 Ω
Av_r  = gm_r * (RL * ro_r / (RL + ro_r))  # 2.00 ✓
Vd_DC = VDD - Id_r * RL                # 0.821 V  (余量 577 mV ≫ Vov 244 mV ✓)
```

### 3. 设计结果汇总

| 参数 | 值 |
|------|----|
| gm/ID | 10 V⁻¹ |
| **W / L** | **8.1 µm / 45 nm** |
| Id | 1.26 mA（< 2 mA ✓） |
| gm | 12.6 mA/V |
| gm·ro | 7.11 |
| RL | 222 Ω |
| Av（校核） | 2.00 ✓ |
| Vgs（偏置） | 0.499 V |
| Vd_DC | 0.821 V |

### 4. 后续仿真（交由 ngspice skill）

拿到 W、RL、Vgs 后，用 `ngspice` skill 搭建 `.control` block 网表并仿真：

- **DC 工作点**：核查 `@m1[id]`、`@m1[gm]`、`@m1[gds]`，与设计值比对
- **AC 频率响应**：`ac dec 200 1e5 1e10` → 读 `vdb(vout)` → 验证低频增益和 −3dB 频率
- **绘图**：用 `wrdata` 保存频率-增益数据，调 matplotlib 绘 Bode 幅频图

---

## 参考文档

详见 `references/conventions.md`：
- §1–5  项目结构、符号约定、MODEL_INFO、网表模板、数据字典键
- §6–7  扫描配置常量（NODE_CFG）、绘图约定与图件列表
- §8–9  物理合理性校验值、常见错误与修复
- §10   扩展 skill（新节点、新图类型、新沟道长度）
- §11   设计 API 完整参考（GmIdTable、print_op、缓存命名、单位约定）
