# gmoverid-skill

![Stars](https://img.shields.io/github/stars/Arcadia-1/gmoverid-skill?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=flat-square&logo=python&logoColor=white)
![ngspice](https://img.shields.io/badge/ngspice-required-orange?style=flat-square)

做模拟电路，绕不开晶体管定尺寸。这个库把 gm/ID 方法学的常用仿真和设计流程打包成技能包，装上就能直接用。

### gmoverid 能做什么

每个工艺节点生成三套标准图：

**IV 特性图**（2×2）
- Id vs Vov 线性坐标：清晰显示阈值和饱和电流
- Id vs Vov 对数坐标：亚阈值斜率与约 7 个数量级动态范围
- Id vs Vgs（0 → VDD 全扫描）
- 输出特性 Id vs Vds（固定 Vgs 多条曲线）

![IV 特性图](gmoverid/assets/plots/45nm/gmoverid_iv_nmos45hp_L45nm.png)

**gm/ID 四象限特性图**（2×2）
- **gm/ID vs Vov**：完整的弱反型→强反型特性，含 BJT 极限 q/kT = 38.6 V⁻¹ 和 2/Vov 渐近线参考
- **Id/W vs gm/ID**（对数 Y 轴）：电流密度随偏置变化，跨越约 3 个数量级
- **fT vs gm/ID**：截止频率，PTM 180nm 峰值约 50 GHz，PTM 22nm HP 峰值超过 600 GHz
- **gm·ro vs gm/ID**：本征增益随偏置点的分布；180nm 在弱反型区（gm/ID ≈ 20）约 40–42，22nm HP 仅 2–4（短沟道效应显著）

![gm/ID 四象限特性图](gmoverid/assets/plots/45nm/gmoverid_nmos45hp_L45nm.png)

**栅电容图**
- Cgg / Cgs / Cgd / Cgb vs Vgs：展示截止区→阈值→强反型各工作区的电容分布与转换

**对比图**
- 沟道长度对比（L = 180 / 360 / 1000 nm）：长沟道显著提升 gm·ro（可达 ~140），但 fT 相应降低
- 跨节点对比（180nm SVT vs 22nm HP）：直观呈现工艺代际的速度–增益权衡

**设计 API**：给定 gm/ID 目标，自动反查 W、Id、Vgs、gm、fT、gm·ro

![栅电容图](gmoverid/assets/plots/gmid_nmos_caps_comp.png)

内置 **180 / 45 / 22 nm** 三个 PTM 模型，装好即可仿真。如果需要更多工艺节点，可以安装 `transistor-models` skill。

### transistor-models 是什么

PTM（预测性晶体管模型，Predictive Technology Model）是亚利桑那州立大学（Arizona State University, ASU）维护的一套公开 SPICE 模型，用于在没有 PDK 的情况下做工艺探索和教学研究。模型由 UC Berkeley 的 BPTM 项目发展而来，随 Yu Cao 教授迁移至 ASU 后持续更新。这个 Skill 把 [mec.umn.edu/ptm](https://mec.umn.edu/ptm) 上的全部模型打包进来：

- 体硅传统：180 / 130 / 90 / 65 nm
- 体硅 HP/LP：45 / 32 / 22 nm
- PTM-MG FinFET（多栅）：20 / 16 / 14 / 10 / 7 nm，HP + LSTP

与 `gmoverid` 相互独立。`gmoverid` 已内置常用节点；需要 32nm LP、7nm FinFET 等时再装这个补全。

---

## 推荐使用 Agent 来安装和使用本技能

Agent 会自动处理依赖关系、环境配置和路径选择，确保技能能够无缝集成到你的工作流程中。如果你要手动操作，下面是详细的安装和使用说明。

---


将 Skill 复制到 Agent 的 skills 路径（以Claude Code 为例）：

安装到用户根目录（全局可用）

```bash
cp -r gmoverid          ~/.claude/skills/
cp -r transistor-models ~/.claude/skills/
```

或安装到项目目录（仅当前项目可用）
```bash
cp -r gmoverid          <项目路径>/.claude/skills/
cp -r transistor-models <项目路径>/.claude/skills/
```

Windows 将 `~/.claude` 替换为 `%USERPROFILE%\.claude`。

例如你的用户名是 `Alice`，路径就是 `C:\Users\Alice\.claude\skills\`。

## 环境要求

- [ngspice](http://ngspice.sourceforge.net/)（系统全局安装）
- Python 3，依赖：`numpy`、`matplotlib`、`scipy`

## 使用

### 表征仿真

```bash
# 部署到项目
cp -r gmoverid/assets/* <项目目录>/
mkdir -p <项目目录>/plots <项目目录>/logs

# 运行
python run_gmoverid.py      # 180nm NMOS/PMOS + 沟道长度扫描
python run_multinode.py     # 45nm / 22nm HP 多节点对比
```

### 设计参数

```python
from design_gmoverid import GmIdTable, print_op

tbl = GmIdTable('nmos180', W=10.0, L=0.18, vds=0.9)

op = tbl.size(gmid=15.0, Id=100e-6)   # 固定 gm/ID 和漏电流，求 W
op = tbl.size_from_ft(5e9, W=20.0)    # fT ≥ 5 GHz，取最省电的工作点
print_op(op)
```

首次调用自动运行 ngspice 仿真并缓存，再次调用直接读缓存。

### 使用 transistor-models

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

> 如果你是 Agent，以上安装和部署步骤由你代为执行，根据用户需求选择全局或项目级安装路径，无需用户手动操作。

---

## 版权声明

模型文件版权归亚利桑那州立大学（Arizona State University）PTM 项目所有，免费用于学术研究。使用时请引用：

- 体硅节点（Bulk CMOS）：
  > W. Zhao and Y. Cao, "New Generation of Predictive Technology Model for Sub-45 nm Early Design Exploration," *IEEE Transactions on Electron Devices*, vol. 53, no. 11, pp. 2816–2823, Nov. 2006. doi: [10.1109/TED.2006.884077](https://doi.org/10.1109/TED.2006.884077)

- PTM-MG FinFET 节点（仅限 `transistor-models` 中的 7–20nm 模型）：
  > S. Sinha, G. Yeric, V. Chandra, B. Cline and Y. Cao, "Exploring sub-20nm FinFET design with Predictive Technology Models," *DAC 2012*, pp. 283–288. doi: [10.1145/2228360.2228414](https://doi.org/10.1145/2228360.2228414)
