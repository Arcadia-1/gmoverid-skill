---
name: ngspice
description: "ngspice 使用教程与仿真模板技能。提供四类标准仿真示例：(1) DC — NMOS Id-Vds 输出特性族曲线；(2) AC — RC 低通滤波器频率响应与 -3dB 带宽；(3) 噪声 — RC 滤波器输出噪声谱密度与 kT/C 噪声；(4) 瞬态 — 采样保持电路开关模型对比。每个示例均提供可验证的 sanity-check 数值。内置 PTM 180nm 模型文件。当需要学习 ngspice 仿真用法、搭建新仿真、编写网表模板、或验证仿真结果合理性时，使用本 skill。"
---

# ngspice 仿真教程 Skill

**依赖**：系统安装的 `ngspice`，Python 3 + `numpy`、`matplotlib`。

## 资产文件

```
assets/
├── ngspice_common.py            — 共享工具：路径常量、runner、解析器、模板渲染
├── verify_ngspice.py            — 验证 ngspice 安装（简单 RC 瞬态）
├── models/
│   └── ptm180.lib               — PTM 180nm NMOS BSIM3v3 模型
├── netlist/
│   ├── test_rc.cir              — 静态网表：verify_ngspice 专用
│   ├── nmos_dc_ids.cir.tmpl     — DC：NMOS Id-Vds 族曲线模板
│   ├── rc_ac.cir.tmpl           — AC：RC 低通频率响应模板
│   ├── rc_noise.cir.tmpl        — 噪声：RC 输出噪声谱密度模板
│   ├── sample_hold_nmos.cir.tmpl    — 瞬态：180nm NMOS 采样保持模板
│   └── sample_hold_ideal.cir.tmpl   — 瞬态：理想开关采样保持模板
├── simulate_dc.py               — DC 仿真引擎
├── plot_dc.py                   — DC 绘图
├── run_dc.py                    — DC 入口
├── simulate_rc_filter.py        — AC+噪声仿真引擎
├── plot_rc_filter.py            — AC+噪声绘图
├── run_rc_filter.py             — AC+噪声入口
├── simulate_sample_hold.py      — 瞬态仿真引擎
├── plot_sample_hold.py          — 瞬态绘图
├── run_sample_hold.py           — 瞬态入口
├── logs/                        — 仿真日志（自动创建）
└── plots/                       — 输出图件（自动创建）
```

---

## 部署与运行

1. 将 `assets/` 下所有文件复制到项目目录
2. 运行任一入口脚本：

```bash
python verify_ngspice.py      # 验证 ngspice 安装
python run_dc.py              # DC 族曲线
python run_rc_filter.py       # AC + 噪声
python run_sample_hold.py     # 采样保持
```

Windows 上设置 `PYTHONUTF8=1` 以避免 GBK 编码错误。

路径无需配置 — 全部通过 `Path(__file__).resolve().parent` 自动解析。

---

## 示例 1：DC — NMOS Id-Vds 族曲线

**电路**：PTM 180nm NMOS，W=10µm，L=0.18µm

**仿真**：`.dc Vds 0 1.8 0.01`，Vgs = {0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8} V

**输出**：`plots/nmos_dc_iv.png`

**Sanity checks**：
- Vgs = 0.4V（接近 Vth ≈ 0.4V）：Id ≈ 59 µA，刚导通（亚阈值/弱反型）
- Vgs = 0.6V，Vds = 0.9V（饱和区）：Id ≈ 561 µA，Id/W ≈ 56 µA/µm（中等反型）
- Vgs = 1.0V，Vds = 0.9V（饱和区）：Id ≈ 2.45 mA，Id/W ≈ 245 µA/µm（强反型）
- 饱和区明显可见（曲线在 Vds > Vgs - Vth 后趋于平坦）

**文件**：`nmos_dc_ids.cir.tmpl` → `simulate_dc.py` → `plot_dc.py` → `run_dc.py`

---

## 示例 2：AC — RC 低通滤波器带宽

**电路**：R + C 接地，AC 源幅度 1V

**配置**：
| 配置 | R | C | fc = 1/(2πRC) |
|------|---|---|---------------|
| 1 | 1 kΩ | 1 pF | **159.2 MHz** |
| 2 | 10 kΩ | 1 pF | **15.92 MHz** |

**仿真**：`.ac dec 100 1Meg 10G`

**输出**：`plots/rc_ac_bw.png`（上面板：增益曲线）

**Sanity checks**：
- -3dB 点与理论 fc 吻合：159.2 MHz（1kΩ），15.92 MHz（10kΩ）
- fc 以上 -20 dB/decade 滚降斜率（一阶滤波器特征）
- 低频增益 = 0 dB（AC 源幅度 1V）

---

## 示例 3：噪声 — RC 滤波器输出噪声

**电路**：同 AC（R + C 接地）

**仿真**：`.noise v(out) Vin dec 100 1Meg 10G`

**输出**：`plots/rc_ac_bw.png`（下面板：噪声谱密度）

**Sanity checks**：
- 白噪声底底 = √(4kTR)：**4.07 nV/√Hz**（R=1kΩ），**12.87 nV/√Hz**（R=10kΩ）
- 积分噪声 = √(kT/C)：**64.3 µVrms**（C=1pF）— 经典 kT/C 噪声！
- 噪声带宽 = π/2 × fc（一阶滤波器）
- fc 以上噪声按 -20 dB/decade 衰减

> AC 和噪声共用一个入口脚本 `run_rc_filter.py`（同一电路，自然教学流程）。

---

## 示例 4：瞬态 — 采样保持开关对比

**电路**：NMOS 开关（180nm W=4µm）+ Csamp=1pF，10MHz 正弦输入，100MHz 时钟

**仿真**：`.tran 0.1n 250n`

**输出**：`plots/sample_hold_compare.png`

**模型对比**：
| 模型 | Ron | 特征 |
|------|-----|------|
| 180nm NMOS | ~400 Ω | 真实寄生效应 |
| 理想开关 SPICE subckt | 50 Ω | 无寄生 |

**Sanity checks**：
- 保持电压在开关 OFF 时保持平坦（1pF 电容电荷守恒）
- 180nm NMOS Ron ≈ 400Ω → 采集时间常数 τ = Ron × C = 400 × 1p = 0.4 ns
- 时钟馈通（ΔV = Cov/Csamp × Vclk）在时钟沿处可见为微小阶跃
- 理想开关无时钟馈通和电荷注入

---

## 共享模块：ngspice_common.py

| 函数/常量 | 用途 |
|-----------|------|
| `BASE_DIR`, `NETLIST_DIR`, `MODEL_DIR`, `LOG_DIR`, `PLOT_DIR` | 路径常量，`Path(__file__).resolve().parent` |
| `strip_ansi(text)` | 去除 ANSI 颜色码 |
| `find_ngspice()` | 优先 `ngspice_con`，回退 `ngspice` |
| `run_ngspice(netlist, log, timeout)` | 批模式执行：`-b`，`stdin=DEVNULL`，Windows `CREATE_NO_WINDOW` |
| `parse_print_table(log_path)` | 解析 `.print` 表格输出 → ndarray |
| `parse_wrdata(data_path)` | 解析 `wrdata` 两列输出 → ndarray |
| `spath(p)` | `str(p).replace('\\', '/')` 用于网表路径 |
| `render_template(tmpl_name, **kw)` | 读取 `.cir.tmpl`，`str.format(**kw)` 填充占位符 |

---

## 网表模板约定

- 使用 Python `str.format()` 占位符：`{R}`、`{model_path}`
- **永远不要在 SPICE 注释行中放 `{...}`** — 会被解析为占位符并报 KeyError
- 路径使用 `spath()` 转换为正斜杠（Windows 兼容）
- 临时网表写入 `tempfile.NamedTemporaryFile(suffix='.cir')` 后执行

---

## 绘图规范

- 不调用 `plt.show()`，使用 `fig.savefig(path, dpi=150, bbox_inches='tight')`
- 图件保存至 `plots/`
- 轴标签用 ASCII + LaTeX（如 `$V_{DS}$`、`$I_D$`）
- 不在 matplotlib 标签中写中文

---

## 参考文档

详见 `references/conventions.md`：
- §1  项目结构与路径约定
- §2  ngspice 运行模式与命令行参数
- §3  网表模板占位符列表
- §4  输出解析格式
- §5  物理 sanity-check 值速查表
- §6  常见错误与修复
