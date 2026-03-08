---
name: gmoverid
description: "gm/ID 晶体管表征与设计方法学，基于 ngspice + Python。包含两个独立工作流：(1) 表征工作流 — 对任意 MOSFET 模型生成三套标准曲线：栅电容 Cgg/Cgs/Cgd/Cgb vs Vgs、gm/ID 四象限特性（gm/Id vs Vov、Id/W vs gm/Id、fT vs gm/Id、gm·ro vs Vds）、IV 特性（线性/对数 Id vs Vov、输出特性）；支持 180nm 单节点及 45/22nm HP 多节点流程，内置 PTM 模型文件（180/45/22nm），无需额外下载。(2) 设计工作流 — GmIdTable 类将仿真数据构建为查找表（缓存至 logs/cache/），提供 lookup()、size()、size_from_ft()、size_from_gmro() API，按 gm/ID 方法论对 NMOS/PMOS 定尺寸。仅依赖 ngspice skill。当需要搭建或扩展 gm/ID 表征项目、生成特性曲线、解读设计曲线、或按 gm/ID 方法对晶体管定尺寸时，使用本 skill。"
---

# gm/ID 表征与设计 Skill

**依赖**：`ngspice` skill（网表执行、wrdata 解析）。模型文件已内置，无需 `transistor-models` skill。

## 资产文件

```
assets/
├── simulate_gmoverid.py   — ngspice 仿真引擎、数据提取、解析电容、MODEL_INFO 注册表
├── plot_gmoverid.py       — 所有 matplotlib 绘图函数
├── run_gmoverid.py        — 180nm 单节点编排（SVT/LVT/HVT + 沟道长度扫描）
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

内置模型来自 [PTM — Arizona State University (ptm.asu.edu)](https://ptm.asu.edu)，免费用于学术研究。如需引用，请使用：W. Zhao and Y. Cao, "New Generation of Predictive Technology Model for Sub-45 nm Early Design Exploration," *IEEE Trans. Electron Devices*, vol. 53, no. 11, pp. 2816–2823, Nov. 2006. doi: 10.1109/TED.2006.884077。如需其他节点（65nm、90nm、130nm、32nm LP、PTM-MG FinFET 等），可安装 `transistor-models` skill（原始 PTM 文件，需自行配置 MODEL_INFO）或从 [mec.umn.edu/ptm](https://mec.umn.edu/ptm) 下载，复制到项目 `models/` 目录。

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
(1,0) fT [GHz]    vs gm/Id    | (1,1) gm·ro vs Vds (0→VDD)
```
- (0,0)(0,1)(1,0)：以 Vds 为参数；(1,1)：以 Vgs 偏置为参数
- gm/Id X 轴：xlim=[4,24]，每 2 V⁻¹ 一格

### 核心文件角色

| 文件 | 职责 |
|------|------|
| `simulate_gmoverid.py` | `run_vgs/vds/vsg/vsd_sweeps()` → 数据字典列表；`MODEL_INFO` 注册表；`compute_caps()` |
| `plot_gmoverid.py` | `plot_main()`、`plot_comparison()`、`plot_iv()`、`plot_caps()`、`plot_caps_comparison()`、`print_summary()` |
| `run_gmoverid.py` | 180nm：LVT/SVT/HVT + 沟道长度扫描对比 |
| `run_multinode.py` | 45/32/22/16nm HP：`NODE_CFG` 驱动逐节点扫描 + 跨节点对比图 |

### 新增工艺节点

1. 将模型 `.lib` 复制到 `models/`（可从 [mec.umn.edu/ptm](https://mec.umn.edu/ptm) 下载或安装 `transistor-models` skill）
2. 在 `simulate_gmoverid.py` 的 `MODEL_INFO` 新增条目（见 conventions.md §3）
3. 在 `run_multinode.py` 的 `NODE_CFG` 新增条目

---

## 工作流二：设计（查表定尺寸）

### 核心类：`GmIdTable`

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
| `W` | float | — | 仿真参考宽度 [µm] |
| `L` | float | — | 沟道长度 [µm] |
| `vds` | float | VDD/2 | Vgs 扫描时固定的 Vds（NMOS）或 \|Vsd\|（PMOS）[V] |
| `force_resim` | bool | False | `True` 则忽略缓存，重新仿真 |

### 查询单个量

```python
tbl.lookup('id_w', gmid)   # Id/W [A/m] == [µA/µm]
tbl.lookup('ft',   gmid)   # 截止频率 fT [Hz]
tbl.lookup('gmro', gmid)   # 本征增益 gm·ro
tbl.lookup('vgs',  gmid)   # Vgs（或 |Vsg|）[V]
tbl.lookup('vov',  gmid)   # 过驱动电压 Vov [V]
tbl.lookup('gm',   gmid)   # 跨导 [S]（参考宽度 W 下）
```

### 定尺寸：固定 gm/ID，指定一个约束

```python
# 三种约束选其一
op = tbl.size(gmid=15.0, Id=100e-6)   # 由 Id 求 W
op = tbl.size(gmid=15.0, W=20.0)      # 由 W 求 Id
op = tbl.size(gmid=15.0, gm=1.5e-3)   # 由 gm 求 Id 和 W
print_op(op)
```

### 约束定尺寸：自动寻优

```python
# 在满足指标的前提下，自动取最高 gm/ID（最省电流）
op = tbl.size_from_ft(8e9,  W=20.0)    # fT ≥ 8 GHz，固定 W
op = tbl.size_from_gmro(35, Id=50e-6)  # gm·ro ≥ 35，固定 Id
```

- `size_from_ft`：适合已知宽度、需满足带宽指标的场景（如 LNA 跨导管、OTA GBW）
- `size_from_gmro`：适合低频高增益级（建议固定 W，避免弱反型下 W 过大）

### `size()` 返回字典

```
model, L_um, W_um, Id_A, Vgs_V, Vov_V, gmid, gm_S, ft_Hz, gmro, id_w_Apm
```

### `print_op(op)` 输出示例

```
════════════════════════════════════════════
  Transistor Operating Point
────────────────────────────────────────────
  Model    : nmos180       L = 180 nm
  gm/ID    : 15.0 V⁻¹      Vgs = 0.611 V   Vov = 0.152 V
────────────────────────────────────────────
  W        :  6.00 µm
  Id       :  66.67 µA    Id/W = 11.11 µA/µm
  gm       :  1.000 mS    fT   = 10.38 GHz
  gm·ro    : 45.6
════════════════════════════════════════════
```

### 缓存文件命名

位于 `logs/cache/`，`.` 替换为 `p`：
- `vgs_{model}_W{w:.2f}_L{l:.4f}_Vds{vds:.3f}.json`  （Vgs 扫描）
- `vds_{model}_W{w:.2f}_L{l:.4f}_{hash8}.json`        （Vds 扫描，hash 来自偏置列表）

### 典型设计参数（nmos180，Vds = 0.9 V）

| gm/ID [V⁻¹] | Id/W [µA/µm] | fT [GHz] | gm·ro | 适用场景 |
|:-----------:|:------------:|:--------:|:-----:|----------|
|  5–8  | 42–81 | 20–25 | 27–36 | 高速电路、采样开关 |
| 10–12 | 20–29 | 15–18 | 39    | OTA 输出级、驱动器 |
| 13–16 | 8–17  |  9–13 | 39–46 | OTA 输入差分对（平衡） |
| 18–20 |  3–6  |  4–6  | 53    | 低功耗模拟级、基准 |

---

## 参考文档

详见 `references/conventions.md`：
- §1–5  项目结构、符号约定、MODEL_INFO、网表模板、数据字典键
- §6–7  扫描配置常量（NODE_CFG）、绘图约定与图件列表
- §8–9  物理合理性校验值、常见错误与修复
- §10   扩展 skill（新节点、新图类型、新沟道长度）
- §11   设计 API 完整参考（GmIdTable、print_op、缓存命名、单位约定）
