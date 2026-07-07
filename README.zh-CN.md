<p align="center">
  <img src="openclaw.png" alt="gmoverid-skill" width="100%">
</p>

<h1 align="center">gmoverid-skill</h1>

<p align="center">
  <a href="https://github.com/Arcadia-1/gmoverid-skill/stargazers"><img src="https://img.shields.io/github/stars/Arcadia-1/gmoverid-skill?style=flat-square&color=f5c542&logo=github" alt="GitHub stars"></a>
  <a href="https://github.com/Arcadia-1/gmoverid-skill/network/members"><img src="https://img.shields.io/github/forks/Arcadia-1/gmoverid-skill?style=flat-square&color=f5c542" alt="GitHub forks"></a>
  <a href="https://github.com/Arcadia-1/gmoverid-skill/issues"><img src="https://img.shields.io/github/issues/Arcadia-1/gmoverid-skill?style=flat-square&color=3fb950" alt="Open Issues"></a>
  <a href="https://github.com/Arcadia-1/gmoverid-skill/commits/main"><img src="https://img.shields.io/github/last-commit/Arcadia-1/gmoverid-skill?style=flat-square&color=3fb950" alt="Last Commit"></a>
</p>

<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.x-blue.svg" alt="Python 3.x"></a>
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License: MIT">
  <a href="https://github.com/Arcadia-1/gmoverid-skill/pulls"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome"></a>
  <img src="https://img.shields.io/badge/ngspice-required-orange.svg" alt="ngspice required">
</p>

四个让 Agent 具有设计模拟电路能力的技能包：**ngspice 入门** / **gm/ID 设计** / **PTM 模型库** / **Sky130A PDK 工作流**。

> **如果你是人类**：下面有示例图片，可以直观了解每个技能的输出效果。

> **如果你是 AI Agent**：跳过图片，直接看 [安装](#安装) 说明。每个技能的完整指令在各自的 `SKILL.md`，可运行脚本和模型文件在 `assets/` 目录内。

## 技能总览

| 技能 | 定位 | 功能 |
|------|------|------|
| **ngspice** | 入门 | 9 类标准仿真示例（DC / AC / Tran / Noise），从零学 SPICE |
| **gmoverid** | 进阶 | gm/ID 表征仿真 + 设计 API，自动反查 W、Id、Vgs、fT、gm·ro |
| **transistor-models** | 模型库 | PTM 全系列模型文件（体硅 65–180nm、HP/LP 22–45nm、FinFET 7–20nm） |
| **sky130-pdk** | 开源 PDK 工作流 | 用 Volare 安装/定位 Sky130A，并运行 ngspice PVT + Monte Carlo smoke 测试 |

---

## 技能1：ngspice

9 个仿真示例，覆盖模拟电路入门核心知识点：

| # | 类型 | 描述 | 输出 |
|---|------|------|------|
| 1 | Tran | RC 充电电压与电流 | `tran_rc_charging.png` |
| 2 | DC | NMOS Id-Vds 族曲线 | `dc_nmos_iv.png` |
| 3 | AC | RC 低通滤波器频率响应 | `ac_rc_bw.png` |
| 4 | Noise | RC 滤波器输出噪声谱密度 | `ac_rc_bw.png` |
| 5 | Tran | 采样保持开关对比 | `sample_hold_compare.png` |
| 6 | Tran | kT/C 噪声时域统计 | `tran_ktc_noise_hist.png` |
| 7 | DC | NMOS 电流镜输出特性 | `dc_current_mirror.png` |
| 8 | AC | 共源放大器 Bode 图 | `ac_cs_amp_bode.png` |
| 9 | DC | 传输门导通电阻 | `dc_tgate_ron.png` |

运行方式见 [`ngspice/SKILL.md`](./ngspice/SKILL.md)，Agent 会自动部署资产并执行。

**NMOS Id-Vds 族曲线**

![NMOS Id-Vds](dc_nmos_iv.png)

**RC 低通滤波器频率响应**

![RC 低通滤波器](ac_rc_bw.png)

**RC 充电电压与电流**

![RC 充电](tran_rc_charging.png)

**kT/C 噪声时域统计**

![kT/C 噪声统计](tran_ktc_noise_hist.png)

---

## 技能2：gmoverid

每个工艺节点生成三套标准图：

**IV 特性图**（2×2）
- Id vs Vov 线性坐标：清晰显示阈值和饱和电流
- Id vs Vov 对数坐标：亚阈值斜率与约 7 个数量级动态范围
- Id vs Vgs（0 → VDD 全扫描）
- 输出特性 Id vs Vds（固定 Vgs 多条曲线）

![IV 特性图](gmoverid_iv_nmos45hp_L45nm.png)

**gm/ID 四象限特性图**（2×2）
- **gm/ID vs Vov**：完整的弱反型→强反型特性，含 BJT 极限 q/kT = 38.6 V⁻¹ 和 2/Vov 渐近线参考
- **Id/W vs gm/ID**（对数 Y 轴）：电流密度随偏置变化，跨越约 3 个数量级
- **fT vs gm/ID**：截止频率，PTM 180nm 峰值约 50 GHz，PTM 22nm HP 峰值超过 600 GHz
- **gm·ro vs gm/ID**：本征增益随偏置点的分布；180nm 在弱反型区（gm/ID ≈ 20）约 40–42，22nm HP 仅 2–4（短沟道效应显著）

![gm/ID 四象限特性图](gmoverid_nmos45hp_L45nm.png)

**栅电容图**
- Cgg / Cgs / Cgd / Cgb vs Vgs：展示截止区→阈值→强反型各工作区的电容分布与转换

**对比图**
- 沟道长度对比（L = 180 / 360 / 1000 nm）：长沟道显著提升 gm·ro（可达 ~140），但 fT 相应降低
- 跨节点对比（180nm SVT vs 22nm HP）：直观呈现工艺代际的速度–增益权衡

![栅电容图](gmid_nmos_caps_comp.png)

**设计 API**：给定 gm/ID 目标，自动反查 W、Id、Vgs、gm、fT、gm·ro

```python
from design_gmoverid import GmIdTable, print_op

tbl = GmIdTable('nmos180', W=10.0, L=0.18, vds=0.9)

op = tbl.size(gmid=15.0, Id=100e-6)   # 固定 gm/ID 和漏电流，求 W
op = tbl.size_from_ft(5e9, W=20.0)    # fT ≥ 5 GHz，取最省电的工作点
print_op(op)
```

首次调用自动运行 ngspice 仿真并缓存，再次调用直接读缓存。

内置 **180 / 45 / 22 nm** 三个 PTM 模型，装好即可仿真。如果需要更多工艺节点，可以安装 `transistor-models` 技能。

---

## 技能3：transistor-models

PTM（预测性晶体管模型，Predictive Technology Model）是亚利桑那州立大学（Arizona State University, ASU）维护的一套公开 SPICE 模型，用于在没有 PDK 的情况下做工艺探索和教学研究。这个技能把 [mec.umn.edu/ptm](https://mec.umn.edu/ptm) 上的全部模型打包进来：

- 体硅传统：180 / 130 / 90 / 65 nm
- 体硅 HP/LP：45 / 32 / 22 nm
- PTM-MG FinFET（多栅）：20 / 16 / 14 / 10 / 7 nm，HP + LSTP

与 `gmoverid` 相互独立。`gmoverid` 已内置常用节点；需要 32nm LP、7nm FinFET 等时再装这个补全。

按需从 `transistor-models/assets/models/` 复制 `.lib` 文件到项目 `models/` 目录：

```bash
cp transistor-models/assets/models/bulk_cmos/ptm32lp.lib <项目目录>/models/
cp transistor-models/assets/models/finfet/nmos7mg_hp.lib <项目目录>/models/
```

文件命名规则：
- `bulk_cmos/ptm{节点}{hp|lp}.lib` — 体硅 HP/LP，含 NMOS+PMOS（model name: `nmos` / `pmos`）
- `bulk_cmos/ptm{节点}.lib` — 体硅传统，含 NMOS+PMOS
- `finfet/{n|p}mos{节点}mg_{hp|lstp}.lib` — FinFET（model name: `nfet` / `pfet`）

详细参数表见 [`transistor-models/references/model_params.md`](./transistor-models/references/model_params.md)。

---

## 技能4：sky130-pdk

Sky130A 是真实的开源 PDK 工作流，不是 PTM 模型文件。这个技能不把 PDK 数据本体放进仓库，而是说明如何用 Volare/open_pdks 安装或定位 Sky130A，以及如何运行 ngspice PVT + Monte Carlo smoke 测试。

内置 smoke 示例：

- NMOS Id-Vgs：覆盖 `tt/ff/ss/fs/sf` process corners，并统计 MC 电流分布。
- 三级 CMOS ring oscillator：统计 process/MC 下的振荡频率。
- 五管 OTA：统计 process/MC 下的低频小信号增益。
- `ring_oscillator`、`ota-5t`、`amp-2s-miller` 三个独立电路目录，各自提供 `.scs` 和 ngspice `.spi` 示例，以及一个面向 Sky130 用户电路网表子集的 SCS-to-ngspice-Sky130 转换器。

典型安装：

```bash
python3 -m pip install --user volare
export PATH="$HOME/.local/bin:$PATH"
volare enable --pdk sky130 c6d73a35f524070e85faff4a6a9eef49553ebc2b
```

从克隆仓库直接跑 smoke：

```bash
git clone https://github.com/Arcadia-1/gmoverid-skill
cd gmoverid-skill/sky130-pdk
python3 assets/run_sky130_mos_iv_pvt_mc.py --mc-runs 3
python3 assets/run_sky130_ringosc_pvt_mc.py --mc-runs 3
python3 assets/run_sky130_five_transistor_ota_pvt_mc.py --mc-runs 3
```

直接跑 ngspice 示例：

```bash
export PDK_ROOT="$(volare path)/volare/sky130/versions/$(volare output --pdk sky130)"
cd gmoverid-skill/sky130-pdk/examples/ota-5t
ngspice -b tb.spi
```

典型模型入口：

```spice
.lib "$PDK_ROOT/sky130A/libs.tech/combined/continuous/sky130.lib.spice" tt
.lib "$PDK_ROOT/sky130A/libs.tech/combined/continuous/sky130.lib.spice" mc
```

运行方式见 [`sky130-pdk/SKILL.md`](./sky130-pdk/SKILL.md)。


## 版权声明

模型文件版权归亚利桑那州立大学（Arizona State University）PTM 项目所有，免费用于学术研究。使用时请引用：

- 体硅节点（Bulk CMOS）：
  > W. Zhao and Y. Cao, "New Generation of Predictive Technology Model for Sub-45 nm Early Design Exploration," *IEEE Transactions on Electron Devices*, vol. 53, no. 11, pp. 2816–2823, Nov. 2006. doi: [10.1109/TED.2006.884077](https://doi.org/10.1109/TED.2006.884077)

- PTM-MG FinFET 节点（仅限 `transistor-models` 中的 7–20nm 模型）：
  > S. Sinha, G. Yeric, V. Chandra, B. Cline and Y. Cao, "Exploring sub-20nm FinFET design with Predictive Technology Models," *DAC 2012*, pp. 283–288. doi: [10.1145/2228360.2228414](https://doi.org/10.1145/2228360.2228414)


---

## 安装

### 全局安装（所有项目可用，推荐）

```bash
git clone --depth 1 https://github.com/Arcadia-1/gmoverid-skill /tmp/gmoverid-skill \
  && cp -r /tmp/gmoverid-skill/{ngspice,gmoverid,transistor-models,sky130-pdk} ~/.claude/skills/ \
  && rm -rf /tmp/gmoverid-skill
```

### 项目级安装（仅当前项目可用）

```bash
git clone --depth 1 https://github.com/Arcadia-1/gmoverid-skill /tmp/gmoverid-skill \
  && mkdir -p .claude/skills \
  && cp -r /tmp/gmoverid-skill/{ngspice,gmoverid,transistor-models,sky130-pdk} .claude/skills/ \
  && rm -rf /tmp/gmoverid-skill
```

### 验证安装

在 Claude Code 中运行：

```
/skills
```

输出列表中应出现 `ngspice`、`gmoverid`、`transistor-models` 和 `sky130-pdk` 四个技能，说明安装成功。

> 如果你是 Agent，以上安装步骤由你代为执行，根据用户需求选择全局或项目级安装路径，无需用户手动操作。

## 环境要求

- [ngspice](http://ngspice.sourceforge.net/)（系统全局安装）
- Python 3，依赖：`numpy`、`matplotlib`、`scipy`；Sky130A PDK 安装推荐使用 `volare`

<p align="center">
  <a href="./README.md"><img alt="English README" src="https://img.shields.io/badge/README-English-blue?style=for-the-badge"></a>
</p>
