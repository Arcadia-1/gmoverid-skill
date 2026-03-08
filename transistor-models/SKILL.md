---
name: transistor-models
description: "完整 PTM（Predictive Technology Model）MOSFET 模型库，直接来自 mec.umn.edu/ptm，涵盖全部节点：体硅传统 180/130/90/65nm、体硅 HP/LP 45/32/22nm（BSIM4）、PTM-MG 多栅 FinFET 20/16/14/10/7nm（BSIM-CMG，HP + LSTP）。安装此 skill 后无需手动下载任何 PTM 模型文件。与 gmoverid skill 无依赖关系，可独立用于任何 ngspice/HSPICE 仿真项目。"
---

# Transistor Models Skill — 完整 PTM 库

**来源**：所有模型文件直接来自 [mec.umn.edu/ptm](https://mec.umn.edu/ptm)，免费用于学术研究。

---

## 模型库一览

### 体硅传统 BSIM4（LEVEL=54）— combined NMOS+PMOS

| 文件 | 节点 | VDD | 模型名 |
|------|------|-----|--------|
| `ptm65.lib`  | 65nm  | 1.1V | `nmos` / `pmos` |
| `ptm90.lib`  | 90nm  | 1.2V | `nmos` / `pmos` |
| `ptm130.lib` | 130nm | 1.3V | `nmos` / `pmos` |
| `ptm180.lib` | 180nm | 1.8V | `NMOS` / `PMOS` |

### 体硅 HP/LP BSIM4（LEVEL=54）— combined NMOS+PMOS

| 文件 | 节点 | 类型 | VDD | 模型名 |
|------|------|------|-----|--------|
| `ptm45hp.lib` | 45nm | HP | 1.0V | `nmos` / `pmos` |
| `ptm45lp.lib` | 45nm | LP | 1.1V | `nmos` / `pmos` |
| `ptm32hp.lib` | 32nm | HP | 0.9V | `nmos` / `pmos` |
| `ptm32lp.lib` | 32nm | LP | 1.0V | `nmos` / `pmos` |
| `ptm22hp.lib` | 22nm | HP | 0.8V | `nmos` / `pmos` |
| `ptm22lp.lib` | 22nm | LP | 1.0V | `nmos` / `pmos` |

### PTM-MG 多栅 FinFET BSIM-CMG（HP + LSTP）— 独立 NMOS/PMOS 文件

| 节点 | HP NMOS | HP PMOS | LSTP NMOS | LSTP PMOS |
|------|---------|---------|-----------|-----------|
| 20nm | `nmos20mg_hp.lib` | `pmos20mg_hp.lib` | `nmos20mg_lstp.lib` | `pmos20mg_lstp.lib` |
| 16nm | `nmos16mg_hp.lib` | `pmos16mg_hp.lib` | `nmos16mg_lstp.lib` | `pmos16mg_lstp.lib` |
| 14nm | `nmos14mg_hp.lib` | `pmos14mg_hp.lib` | `nmos14mg_lstp.lib` | `pmos14mg_lstp.lib` |
| 10nm | `nmos10mg_hp.lib` | `pmos10mg_hp.lib` | `nmos10mg_lstp.lib` | `pmos10mg_lstp.lib` |
|  7nm | `nmos7mg_hp.lib`  | `pmos7mg_hp.lib`  | `nmos7mg_lstp.lib`  | `pmos7mg_lstp.lib`  |

PTM-MG 文件中模型名为 `nfet`（NMOS）/ `pfet`（PMOS），BSIM-CMG 格式，需 ngspice LEVEL=72。

### ngspice 格式化文件（描述性模型名，供 gmoverid 集成）

| 文件 | 节点 | 模型名 |
|------|------|--------|
| `nmos180.lib` / `pmos180.lib` | 180nm | `nmos180` / `pmos180` |
| `nmos45hp.lib` / `pmos45hp.lib` | 45nm HP | `nmos45hp` / `pmos45hp` |
| `nmos22hp.lib` / `pmos22hp.lib` | 22nm HP | `nmos22hp` / `pmos22hp` |

这组文件已预配置 ngspice，可直接与 `gmoverid` skill 配合使用。

---

## ngspice 使用方法

### 加载 combined 文件（体硅节点）

```spice
* 加载 45nm HP（含 nmos 和 pmos 两个模型）
.include "models/ptm45hp.lib"

* 实例化 NMOS
M1  drain  gate  source  bulk  nmos  W=1u  L=45n
```

### 加载 PTM-MG FinFET

```spice
* 加载 7nm HP FinFET
.include "models/nmos7mg_hp.lib"
.include "models/pmos7mg_hp.lib"

* PTM-MG 模型名为 nfet / pfet
* 注意：PTM-MG 使用 NFIN（鳍片数）代替 W
M1  drain  gate  source  bulk  nfet  NFIN=1  L=7n
```

### 加载格式化文件（gmoverid 风格）

```spice
.include "models/nmos180.lib"
M1  d  g  s  b  nmos180  W=10u  L=180n
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
