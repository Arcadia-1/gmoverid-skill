---
name: ngspice
description: "ngspice 使用教程与仿真模板技能。提供九类标准仿真示例：(1) 瞬态 — RC 充电电压与电流；(2) DC — NMOS Id-Vds 族曲线；(3) AC — RC 低通滤波器频率响应；(4) 噪声 — RC 滤波器输出噪声谱密度与 kT/C；(5) 瞬态 — 采样保持开关对比；(6) 瞬态 — kT/C 噪声时域统计测量；(7) DC — NMOS 电流镜输出特性；(8) AC — 共源放大器频率响应；(9) DC — 传输门导通电阻。内置 PTM 180/45/22nm 模型。"
---

# ngspice 仿真教程 Skill

**依赖**：系统安装的 `ngspice`，Python 3 + `numpy`、`matplotlib`、`scipy`。

## 资产文件

```
assets/
├── ngspice_common.py                   — 共享工具：路径常量、runner、解析器、模板渲染
├── models/
│   ├── ptm180.lib                      — PTM 180nm BSIM3v3 模型
│   ├── ptm45hp.lib                     — PTM 45nm HP BSIM4 模型
│   └── ptm22hp.lib                     — PTM 22nm HP BSIM4 模型
├── netlist/
│   ├── tran_rc_charging.cir.tmpl       — 瞬态：RC 充电电压与电流
│   ├── dc_nmos_iv.cir.tmpl             — DC：NMOS Id-Vds 族曲线
│   ├── ac_rc_filter.cir.tmpl           — AC：RC 低通频率响应
│   ├── noise_rc_filter.cir.tmpl        — 噪声：RC 输出噪声谱密度
│   ├── tran_sample_hold_nmos.cir.tmpl  — 瞬态：180nm NMOS 采样保持
│   ├── tran_sample_hold_ideal.cir.tmpl — 瞬态：理想开关采样保持
│   ├── tran_ktc_noise.cir.tmpl         — 瞬态：kT/C 噪声时域统计
│   ├── dc_current_mirror.cir.tmpl      — DC：NMOS 电流镜
│   ├── ac_cs_amp.cir.tmpl              — AC：共源放大器频率响应
│   └── dc_tgate_ron.cir.tmpl           — DC：传输门导通电阻
├── simulate_tran_rc_charging.py         — RC 充电仿真引擎
├── plot_tran_rc_charging.py            — RC 充电绘图
├── run_tran_rc_charging.py             — RC 充电入口
├── simulate_dc_nmos_iv.py              — DC 族曲线仿真引擎
├── plot_dc_nmos_iv.py                  — DC 族曲线绘图
├── run_dc_nmos_iv.py                   — DC 族曲线入口
├── simulate_ac_rc_filter.py            — AC+噪声仿真引擎
├── plot_ac_rc_filter.py                — AC+噪声绘图
├── run_ac_rc_filter.py                 — AC+噪声入口
├── simulate_tran_sample_hold.py        — 采样保持仿真引擎
├── plot_tran_sample_hold.py            — 采样保持绘图
├── run_tran_sample_hold.py             — 采样保持入口
├── simulate_tran_ktc_noise.py          — kT/C 噪声仿真引擎
├── plot_tran_ktc_noise.py              — kT/C 噪声绘图
├── run_tran_ktc_noise.py               — kT/C 噪声入口
├── simulate_dc_current_mirror.py       — 电流镜仿真引擎
├── plot_dc_current_mirror.py           — 电流镜绘图
├── run_dc_current_mirror.py            — 电流镜入口
├── simulate_ac_cs_amp.py               — 共源放大器仿真引擎
├── plot_ac_cs_amp.py                   — 共源放大器绘图
├── run_ac_cs_amp.py                    — 共源放大器入口
├── simulate_dc_tgate_ron.py            — 传输门 Ron 仿真引擎
├── plot_dc_tgate_ron.py                — 传输门 Ron 绘图
├── run_dc_tgate_ron.py                 — 传输门 Ron 入口
├── logs/                               — 仿真日志（自动创建）
└── plots/                              — 输出图件（自动创建）
```

**命名规则**：网表模板以仿真类型开头（`dc_`、`ac_`、`noise_`、`tran_`），Python 文件同步命名（如 `run_dc_nmos_iv.py`）。

---

## 部署与运行

1. 将 `assets/` 下所有文件复制到项目目录
2. 运行任一入口脚本：

```bash
python run_tran_rc_charging.py    # RC 充电（最简单，可验证 ngspice 安装）
python run_dc_nmos_iv.py          # DC 族曲线
python run_ac_rc_filter.py        # AC + 噪声
python run_tran_sample_hold.py    # 采样保持
python run_tran_ktc_noise.py      # kT/C 噪声统计
python run_dc_current_mirror.py   # 电流镜
python run_ac_cs_amp.py           # 共源放大器
python run_dc_tgate_ron.py        # 传输门 Ron
```

Windows 上设置 `PYTHONUTF8=1` 以避免 GBK 编码错误。

路径无需配置 — 全部通过 `Path(__file__).resolve().parent` 自动解析。

---

## 示例 1：瞬态 — RC 充电电压与电流

**电路**：R + C 接地，DC 阶跃输入 1V，初始 Vcap=0

**配置**：
| 配置 | R | C | τ = RC |
|------|---|---|--------|
| 1 | 1 kΩ | 1 pF | **1 ns** |
| 2 | 10 kΩ | 1 pF | **10 ns** |

**仿真**：`.tran` 至 10τ（慢配置），UIC + IC=0

**输出**：`plots/tran_rc_charging.png`（上面板：电压，下面板：电流）

**Sanity checks**：
- V(out) = Vin × (1 - e^(-t/τ))，τ 处达到 63.2%
- I = Vin/R × e^(-t/τ)，初始电流 = 1V/1kΩ = 1mA（或 1V/10kΩ = 100µA）
- 5τ 后电容基本充满（>99%）

**文件**：`tran_rc_charging.cir.tmpl` → `simulate_tran_rc_charging.py` → `plot_tran_rc_charging.py` → `run_tran_rc_charging.py`

---

## 示例 2：DC — NMOS Id-Vds 族曲线

**电路**：PTM 180nm NMOS，W=10µm，L=0.18µm

**仿真**：`.dc Vds 0 1.8 0.01`，Vgs = {0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8} V

**输出**：`plots/nmos_dc_iv.png`

**Sanity checks**：
- Vgs = 0.4V（接近 Vth ≈ 0.4V）：Id ≈ 59 µA，刚导通（亚阈值/弱反型）
- Vgs = 0.6V，Vds = 0.9V（饱和区）：Id ≈ 561 µA，Id/W ≈ 56 µA/µm（中等反型）
- Vgs = 1.0V，Vds = 0.9V（饱和区）：Id ≈ 2.45 mA，Id/W ≈ 245 µA/µm（强反型）
- 饱和区明显可见（曲线在 Vds > Vgs - Vth 后趋于平坦）

**文件**：`dc_nmos_iv.cir.tmpl` → `simulate_dc_nmos_iv.py` → `plot_dc_nmos_iv.py` → `run_dc_nmos_iv.py`

---

## 示例 3：AC — RC 低通滤波器带宽

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

## 示例 4：噪声 — RC 滤波器输出噪声

**电路**：同 AC（R + C 接地）

**仿真**：`.noise v(out) Vin dec 100 1Meg 10G`

**输出**：`plots/rc_ac_bw.png`（下面板：噪声谱密度）

**Sanity checks**：
- 白噪声底底 = √(4kTR)：**4.07 nV/√Hz**（R=1kΩ），**12.87 nV/√Hz**（R=10kΩ）
- 积分噪声 = √(kT/C)：**64.3 µVrms**（C=1pF）— 经典 kT/C 噪声！
- 噪声带宽 = π/2 × fc（一阶滤波器）
- fc 以上噪声按 -20 dB/decade 衰减

> AC 和噪声共用一个入口脚本 `run_ac_rc_filter.py`（同一电路，自然教学流程）。

---

## 示例 5：瞬态 — 采样保持开关对比

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

**文件**：`tran_sample_hold_nmos/ideal.cir.tmpl` → `simulate_tran_sample_hold.py` → `plot_tran_sample_hold.py` → `run_tran_sample_hold.py`

---

## 示例 6：瞬态 — kT/C 噪声时域统计测量

**电路**：noisy R (400Ω, 等效开关 Ron) + Csamp，DC 输入 0.9V。使用 trnoise 电压源为电阻注入热噪声。

**原理**：电阻热噪声谱密度 4kTR 经 RC 带宽限制后，电容上噪声方差 = kT/C。从长瞬态仿真中每隔 5τ 采样一次 v(out)，获取 10000 个独立样本。

**配置**：
| Csamp | τ = RC | √(kT/C) 理论值 |
|-------|--------|----------------|
| 1 pF  | 0.4 ns | **64.3 µVrms** |
| 100 fF | 0.04 ns | **203.5 µVrms** |

**输出**：`plots/tran_ktc_noise_hist.png`（噪声轨迹 + 直方图 + 拟合高斯 + 统计摘要）

**Sanity checks**：
- 1 pF：测量 σ ≈ 64 µV（±10% 统计波动）
- 100 fF：测量 σ ≈ 203 µV（±10% 统计波动）
- 直方图呈高斯分布，拟合线与理论 √(kT/C) 吻合
- 测量/理论比值在 0.85–1.15 之间

**文件**：`tran_ktc_noise.cir.tmpl` → `simulate_tran_ktc_noise.py` → `plot_tran_ktc_noise.py` → `run_tran_ktc_noise.py`

---

## 示例 7：DC — NMOS 电流镜输出特性

**电路**：PTM 180nm NMOS 1:1 电流镜，M1 二极管连接（参考端），M2 输出端

**参数**：W=10µm，L=0.5µm（较长沟道提高镜像精度），Iref=100µA

**仿真**：`.dc Vout 0 1.8 0.01`

**输出**：`plots/dc_current_mirror.png`（Iout vs Vout + 镜像比）

**Sanity checks**：
- Vout > Vov (≈0.2V) 时 M2 饱和：Iout ≈ 100 µA
- 沟道长度调制导致 Iout 随 Vout 微增（斜率 ≈ 1/ro）
- 输出电阻 ro ≈ VA/Id ≈ 50–100 kΩ
- Vout < Vov 时 M2 进入线性区：Iout < Iref

**文件**：`dc_current_mirror.cir.tmpl` → `simulate_dc_current_mirror.py` → `plot_dc_current_mirror.py` → `run_dc_current_mirror.py`

---

## 示例 8：AC — 共源 NMOS 放大器频率响应

**电路**：PTM 180nm NMOS 共源放大器，电阻负载 + 负载电容

**参数**：W=10µm，L=0.18µm，Vgs=0.6V，Rd=2kΩ，CL=1pF，VDD=1.8V

**仿真**：`.ac dec 100 1k 100G`

**输出**：`plots/ac_cs_amp_bode.png`（增益 Bode 图 + 相位）

**Sanity checks**：
- 直流增益 |Av| = gm × Rd ≈ 12.9 dB
- -3dB 频率 ≈ 132 MHz（理论 1/(2πRdCL) ≈ 80 MHz，实际因 MOSFET 寄生电容偏高）
- 低频相位 ≈ 180°（反相放大器）
- 高频增益以 -20 dB/decade 滚降（单极点）

**文件**：`ac_cs_amp.cir.tmpl` → `simulate_ac_cs_amp.py` → `plot_ac_cs_amp.py` → `run_ac_cs_amp.py`

---

## 示例 9：DC — 传输门导通电阻

**电路**：NMOS + PMOS 互补传输门，W/L=100，全部导通（clk=VDD, clkb=0）

**方法**：施加 10mV 跨压，扫描 Vpass，Ron = 10mV / I

**技术节点对比**：
| 节点 | VDD | L | W | 模型 |
|------|-----|---|---|------|
| 180nm | 1.8V | 0.18µm | 18µm | PTM BSIM3v3 |
| 45nm HP | 1.0V | 45nm | 4.5µm | PTM BSIM4 |
| 22nm HP | 0.8V | 22nm | 2.2µm | PTM BSIM4 |

**输出**：`plots/dc_tgate_ron.png`（Ron vs Vpass，对数坐标，3条曲线）

**Sanity checks**：
- 180nm：Min Ron ≈ 38 Ω，Vpass 中间范围阻值最低
- 45nm HP：Min Ron ≈ 52 Ω
- 22nm HP：Min Ron ≈ 103 Ω（低 VDD 限制栅驱动）
- Ron 在 Vpass 接近 0 和 VDD 时升高（分别 NMOS/PMOS 关断）
- 传输门互补结构保证全范围导通

**文件**：`dc_tgate_ron.cir.tmpl` → `simulate_dc_tgate_ron.py` → `plot_dc_tgate_ron.py` → `run_dc_tgate_ron.py`

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

- 模板文件名以仿真类型开头：`dc_`、`ac_`、`noise_`、`tran_`
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
