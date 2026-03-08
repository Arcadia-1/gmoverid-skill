# Transistor Model Parameters Reference

## Table of Contents
1. [PTM Parameter Tables](#1-ptm-parameter-tables)
2. [BSIM4 Noise Parameters](#2-bsim4-noise-parameters)
3. [BSIM-CMG Key Parameters (PTM-MG FinFET)](#3-bsim-cmg-key-parameters-ptm-mg-finfet)
4. [Adding a New Model](#4-adding-a-new-model)

---

## 1. PTM Parameter Tables

所有参数均从 `assets/models/` 中的文件直接提取。

### 1.1 PTM 180nm BSIM3v3（LEVEL=8，VDD=1.8V）文件：`ptm180.lib`

| 参数 | NMOS SVT | NMOS LVT | NMOS HVT | PMOS SVT |
|------|----------|----------|----------|----------|
| vth0 [V]     | 0.40   | 0.30   | 0.55   | −0.42   |
| u0 [cm²/Vs]  | 270    | 270    | 270    | 117.5   |
| cgso [F/m]   | 7.9e-10| 7.9e-10| 7.9e-10| 6.8e-10 |
| cgdo [F/m]   | 7.9e-10| 7.9e-10| 7.9e-10| 6.8e-10 |
| nch [cm⁻³]   | 2.35e17|2.35e17 |2.35e17 | 6.02e16 |
| tox [nm]     | 4.1    | 4.1    | 4.1    | 4.1     |

注：`ptm180.lib` 为单模型文件（model name `NMOS`/`PMOS`）；`nmos180.lib`/`pmos180.lib` 为含 SVT/LVT/HVT 三变体的格式化版本。

---

### 1.2 PTM 体硅传统 BSIM4（LEVEL=54）— 文件：`ptm130/90/65.lib`

每个文件同时包含 NMOS（model name `nmos`）和 PMOS（model name `pmos`）。

| 节点 | 极性 | vth0 [V] | u0 [m²/Vs] | toxe [nm] | cgso/cgdo [F/m] | ndep [cm⁻³] | VDD [V] |
|------|------|----------|------------|-----------|-----------------|-------------|---------|
| 130nm | NMOS | 0.378  | 0.059 | 2.25 | 2.4e-10 | 1.54e18 | 1.3 |
| 130nm | PMOS | −0.321 | 0.0084 | 2.25 | 2.4e-10 | — | 1.3 |
| 90nm  | NMOS | 0.397  | 0.055 | 2.05 | 1.9e-10 | 1.94e18 | 1.2 |
| 90nm  | PMOS | −0.339 | 0.0071 | 2.05 | 1.8e-10 | — | 1.2 |
| 65nm  | NMOS | 0.423  | 0.049 | 1.85 | 1.5e-10 | 2.54e18 | 1.1 |
| 65nm  | PMOS | −0.365 | 0.0057 | 1.85 | 1.5e-10 | — | 1.1 |

---

### 1.3 PTM 体硅 HP BSIM4（LEVEL=54）— 文件：`ptm45/32/22hp.lib` 及格式化版

每个 HP 文件包含 NMOS（`nmos`）和 PMOS（`pmos`）；格式化文件（`nmos45hp.lib` 等）使用描述性模型名（`nmos45hp` / `pmos45hp`）。

| 节点 | 极性 | vth0 [V] | u0 [m²/Vs] | toxe [nm] | cgso/cgdo [F/m] | ndep [cm⁻³] | VDD [V] |
|------|------|----------|------------|-----------|-----------------|-------------|---------|
| 45nm | NMOS | 0.469  | 0.054 | 1.25 | 1.1e-10 | 3.24e18 | 1.0 |
| 45nm | PMOS | −0.492 | 0.020 | 1.30 | 1.1e-10 | 2.44e18 | 1.0 |
| 32nm | NMOS | 0.494  | 0.050 | 1.15 | 8.5e-11 | 4.12e18 | 0.9 |
| 32nm | PMOS | −0.492 | 0.014 | 1.20 | 8.5e-11 | 3.07e18 | 0.9 |
| 22nm | NMOS | 0.503  | 0.040 | 1.05 | 7.0e-11 | 5.02e18 | 0.8 |
| 22nm | PMOS | −0.490 | 0.012 | 1.10 | 7.0e-11 | 3.70e18 | 0.8 |

---

### 1.4 PTM 体硅 LP BSIM4（LEVEL=54）— 文件：`ptm45/32/22lp.lib`

LP（Low Power）相比 HP：vth0 更高（约 +0.15 V）、泄漏更小、速度较慢、VDD 略高。

| 节点 | 极性 | vth0 [V] | u0 [m²/Vs] | toxe [nm] | VDD [V] |
|------|------|----------|------------|-----------|---------|
| 45nm | NMOS | 0.623  | 0.049 | 1.80 | 1.1 |
| 45nm | PMOS | −0.587 | 0.021 | 1.82 | 1.1 |
| 32nm | NMOS | 0.630  | 0.042 | 1.60 | 1.0 |
| 32nm | PMOS | −0.581 | 0.016 | 1.62 | 1.0 |
| 22nm | NMOS | 0.689  | 0.035 | 1.40 | 1.0 |
| 22nm | PMOS | −0.637 | 0.011 | 1.40 | 1.0 |

---

### 1.5 阈值提取方法

恒流法（Constant-current method）：Vth = Vgs at Id/(W/L) = 100 nA。

---

## 2. BSIM4 Noise Parameters

| 参数 | 含义 | 典型值 |
|------|------|--------|
| `fnoimod` | 闪烁噪声模型选择（0 或 1） | 1 |
| `tnoimod` | 热噪声模型选择（0 或 1） | 0 |
| `noia` | 闪烁噪声系数 A | 6.25e41（NMOS） |
| `noib` | 闪烁噪声系数 B | 3.125e26 |
| `noic` | 闪烁噪声系数 C | 8.75e9 |
| `em`   | 热噪声饱和场 | 4.1e7 |
| `ef`   | 闪烁噪声频率指数 | 1.0 |

闪烁噪声 PSD（BSIM4 fnoimod=1）：
```
Sid = (noia * exp(noia*Vds) + noib) * kT / (Cox * Leff²) * gm² / f^ef
```

---

## 3. BSIM-CMG Key Parameters（PTM-MG FinFET）

文件：`nmos/pmos{7/10/14/16/20}mg_{hp/lstp}.lib`，LEVEL=72，模型名 `nfet`/`pfet`。

### 3.1 几何参数（替代 W/L 的概念）

| 参数 | 含义 | 单位 |
|------|------|------|
| `TFIN`  | 鳍片厚度 | m |
| `HFIN`  | 鳍片高度 | m |
| `NF`（或`NFIN`）| 鳍片数量 | — |
| `EOT`   | 等效氧化层厚度 | m |
| `TOXP`  | 物理氧化层厚度 | m |
| `PHIG`  | 栅功函数（控制阈值电压） | eV |

有效宽度：`Weff = NFIN × (2 × HFIN + TFIN)`（双栅）

### 3.2 PTM-MG HP 关键参数（NFET）

| 节点 | VDD [V] | EOT [nm] | TOXP [nm] | U0 [m²/Vs] | TFIN [nm] | HFIN [nm] | PHIG [eV] |
|------|---------|----------|-----------|------------|-----------|-----------|-----------|
| 20nm | 0.90  | 0.84 | 1.40 | 0.038 | 15.0 | 28.0 | 4.375 |
| 16nm | 0.85  | 0.80 | 1.35 | 0.045 | 12.0 | 26.0 | — |
| 14nm | 0.80  | 0.75 | 1.30 | 0.052 | 10.0 | 23.0 | — |
| 10nm | 0.75  | 0.68 | 1.20 | 0.057 |  8.0 | 21.0 | — |
|  7nm | 0.70  | 0.62 | 1.15 | 0.065 |  6.5 | 18.0 | 4.424 |

LSTP 变体相比 HP：`PHIG` 增大（约 +0.2 eV），减小泄漏电流，速度略降。

### 3.3 实例化示例

```spice
* 加载 7nm HP FinFET
.include "models/nmos7mg_hp.lib"
.include "models/pmos7mg_hp.lib"

* NFIN=2 表示两条鳍片，等效 Weff = 2×(2×18+6.5)nm ≈ 85nm
M1  drain  gate  source  bulk  nfet  NFIN=2  L=7n
M2  drain  gate  source  bulk  pfet  NFIN=2  L=7n
```

---

## 4. Adding a New Model

### 4.1 使用 PTM 库中现有文件

```spice
* combined 文件（65/90/130/180/22/32/45nm）
.include "models/ptm45hp.lib"
M1 d g s b nmos W=1u L=45n    * model name = nmos
M2 d g s b pmos W=2u L=45n    * model name = pmos

* 格式化文件（带描述性模型名）
.include "models/nmos45hp.lib"
M1 d g s b nmos45hp W=1u L=45n
```

### 4.2 使用自定义 PDK .lib 文件

1. 将 `.lib` 文件复制到项目 `models/` 目录
2. 查看文件内的 `.model` 名（例如 `.model mynmos NMOS level=54`）
3. 记录关键参数：`vth0`、`toxe`（或 `tox`）、`cgso`/`cgdo`、VDD

### 4.3 将自定义模型注册到 gmoverid（可选）

如需在 `gmoverid` skill 中使用，在 `simulate_gmoverid.py` 的 `MODEL_INFO` 中添加：

```python
'my_model': dict(
    pol='nmos',           # 或 'pmos'
    vth0=...,             # 从 .lib 读取 [V]
    cgso=..., cgdo=...,  # 重叠电容 [F/m]
    nch=...,              # 沟道掺杂 [m⁻³] = cm⁻³ × 1e6
    mu=...,               # 迁移率 [m²/Vs]
    file=_mf('my_model.lib'),
    vdd=...,              # 电源电压 [V]
    vgs_stop=...,         # 扫描上限（通常 vdd + 0.2）
    vds_stop=...,
    tox=...,              # 氧化层厚度 [m]
)
```

### 4.4 创建新工艺节点的预测模型

参考 PTM 等比缩放规律：`toxe ∝ L`、`vth0` 缓慢下降、`u0` 每节点约降 20%。以现有 PTM `.lib` 文件为模板修改关键参数。
