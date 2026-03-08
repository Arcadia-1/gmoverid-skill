---
name: transistor-models
description: "完整 PTM（Predictive Technology Model）MOSFET 模型库，直接来自 mec.umn.edu/ptm，涵盖全部节点：体硅传统 180/130/90/65nm、体硅 HP/LP 45/32/22nm（BSIM4）、PTM-MG 多栅 FinFET 20/16/14/10/7nm（BSIM-CMG，HP + LSTP）。安装此 skill 后无需手动下载任何 PTM 模型文件。与 gmoverid skill 无依赖关系，可独立用于任何 ngspice/HSPICE 仿真项目。"
---

# Transistor Models Skill — 完整 PTM 库

**来源**：所有模型文件直接来自 [PTM — Arizona State University (ptm.asu.edu)](https://ptm.asu.edu)，免费用于学术研究。

**引用文献**：
- 体硅节点（Bulk CMOS）：W. Zhao and Y. Cao, "New Generation of Predictive Technology Model for Sub-45 nm Early Design Exploration," *IEEE Trans. Electron Devices*, vol. 53, no. 11, pp. 2816–2823, Nov. 2006. doi: 10.1109/TED.2006.884077
- PTM-MG FinFET 节点：S. Sinha, G. Yeric, V. Chandra, B. Cline and Y. Cao, "Exploring sub-20nm FinFET design with Predictive Technology Models," *DAC 2012*, pp. 283–288. doi: 10.1145/2228360.2228414

---

## 目录结构

```
assets/models/
├── bulk_cmos/              — 体硅 Bulk CMOS（BSIM3v3 / BSIM4）
│   ├── ptm180.lib          — 180nm 传统
│   ├── ptm130.lib          — 130nm 传统
│   ├── ptm90.lib           — 90nm 传统
│   ├── ptm65.lib           — 65nm 传统
│   ├── ptm45hp.lib         — 45nm HP
│   ├── ptm45lp.lib         — 45nm LP
│   ├── ptm32hp.lib         — 32nm HP
│   ├── ptm32lp.lib         — 32nm LP
│   ├── ptm22hp.lib         — 22nm HP
│   └── ptm22lp.lib         — 22nm LP
└── finfet/
    ├── models              — PTM-MG 库入口（.LIB ptm{n}hp / ptm{n}lstp）
    ├── param.inc           — 共享参数（fin_height/fin_width/lg/vdd，按节点分 lib）
    ├── hp/                 — HP 节点：{7,10,14,16,20}nfet.pm / pfet.pm
    └── lstp/               — LSTP 节点：{7,10,14,16,20}nfet.pm / pfet.pm
```

---

## 模型库一览

### Bulk CMOS — 体硅传统（BSIM3v3/BSIM4，combined NMOS+PMOS）

| 文件 | 节点 | VDD | 模型名 |
|------|------|-----|--------|
| `bulk_cmos/ptm180.lib` | 180nm | 1.8V | `NMOS` / `PMOS` |
| `bulk_cmos/ptm130.lib` | 130nm | 1.3V | `nmos` / `pmos` |
| `bulk_cmos/ptm90.lib`  | 90nm  | 1.2V | `nmos` / `pmos` |
| `bulk_cmos/ptm65.lib`  | 65nm  | 1.1V | `nmos` / `pmos` |

### Bulk CMOS — 体硅 HP/LP（BSIM4，combined NMOS+PMOS）

| 文件 | 节点 | 类型 | VDD | 模型名 |
|------|------|------|-----|--------|
| `bulk_cmos/ptm45hp.lib` | 45nm | HP | 1.0V | `nmos` / `pmos` |
| `bulk_cmos/ptm45lp.lib` | 45nm | LP | 1.1V | `nmos` / `pmos` |
| `bulk_cmos/ptm32hp.lib` | 32nm | HP | 0.9V | `nmos` / `pmos` |
| `bulk_cmos/ptm32lp.lib` | 32nm | LP | 1.0V | `nmos` / `pmos` |
| `bulk_cmos/ptm22hp.lib` | 22nm | HP | 0.8V | `nmos` / `pmos` |
| `bulk_cmos/ptm22lp.lib` | 22nm | LP | 1.0V | `nmos` / `pmos` |

### FinFET — PTM-MG 多栅（BSIM-CMG）

入口文件：`finfet/models`，通过 `.lib` 标签选择节点和类型：

| 标签 | 节点 | 类型 | VDD |
|------|------|------|-----|
| `ptm20hp`   | 20nm | HP   | 0.9V |
| `ptm16hp`   | 16nm | HP   | 0.85V |
| `ptm14hp`   | 14nm | HP   | 0.8V |
| `ptm10hp`   | 10nm | HP   | 0.75V |
| `ptm7hp`    |  7nm | HP   | 0.7V |
| `ptm20lstp` | 20nm | LSTP | 0.9V |
| `ptm16lstp` | 16nm | LSTP | 0.85V |
| `ptm14lstp` | 14nm | LSTP | 0.8V |
| `ptm10lstp` | 10nm | LSTP | 0.75V |
| `ptm7lstp`  |  7nm | LSTP | 0.7V |

FinFET 模型名为 `nfet` / `pfet`，通过 subckt 封装，NFIN 控制鳍片数。

---

## ngspice 使用方法

### 加载 Bulk CMOS 文件

```spice
* 加载 45nm HP（含 nmos 和 pmos 两个模型）
.include "models/bulk_cmos/ptm45hp.lib"

* 实例化 NMOS
M1  drain  gate  source  bulk  nmos  W=1u  L=45n
```

### 加载 PTM-MG FinFET

```spice
* 加载 7nm HP FinFET
.include "models/finfet/nmos7mg_hp.lib"
.include "models/finfet/pmos7mg_hp.lib"

* PTM-MG 模型名为 nfet / pfet
* 注意：PTM-MG 使用 NFIN（鳍片数）代替 W
M1  drain  gate  source  bulk  nfet  NFIN=1  L=7n
```

---

## 模型分类速查

| 模型 | ngspice LEVEL | 适用节点 | 说明 |
|------|:------------:|----------|------|
| BSIM3v3 | 8 | 180nm–250nm | 成熟体硅 |
| BSIM4 | 54 | 65nm–22nm | 体硅 HP/LP |
| BSIM-CMG | 72 | 7nm–20nm | FinFET/多栅 |

---

## 关键参数速查

| 参数 | 含义 | 典型范围 |
|------|------|----------|
| `vth0` | 名义阈值电压 [V] | NMOS: 0.3–0.5；PMOS: −0.3 to −0.5 |
| `toxe` | 栅氧化层等效厚度 [m] | 1–4 nm（深亚微米） |
| `u0` | 低场迁移率 [m²/Vs] | NMOS: 0.03–0.05；PMOS: 0.01–0.02 |
| `vsat` | 饱和速度 [m/s] | 1e5–2.5e5 |

详细参数见 `references/model_params.md`。

---

## 自定义 PDK 模型

如有自己的 `.lib` 文件（工厂 PDK 或测量结果）：
1. 复制到项目 `models/` 目录
2. 查看文件内的 `.model` 名（例如 `.model mynmos NMOS level=54`）
3. 实例化时使用该名称：`M1 d g s b mynmos W=... L=...`
4. 根据 `vth0`、`tox` 等参数配置扫描范围
