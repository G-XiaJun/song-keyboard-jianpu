# song-keyboard-jianpu · 歌曲键盘简谱生成器

把一首歌的歌词逐字配上简谱数字和键盘字母，渲染成蓝色国风竖版 PNG 谱面。
一个汉字 = 一个简谱数字 = 一个带彩色方框的键盘字母。

## 长什么样

每一行谱是这样的三段式结构，每个字占一列：

```
     ⑤           ← 简谱数字（上方小圆点=高八度，下方=低八度）
   [ 窗 ]        ← 歌词彩色 chip
   ┌─────┐
   │  B  │       ← 键盘字母：大写粗体 + 彩色方框
   └─────┘
```

配色即八度：**橙=中音**（不按鼠标） · **蓝=高音**（右键） · **绿=低音**（左键） · **紫=半音**（中键）

默认键位是键盘最底行七个白键 `Z X C V B N M`，配合鼠标键切换八度。

## 快速开始

```bash
pip install Pillow

# 1. 校验谱面数据（字数 vs 音符数）
python scripts/audit_score.py examples/qilixiang.json

# 2. 渲染
python scripts/render_score.py examples/qilixiang.json -o score.png
```

自定义标题宽度等参数：

```bash
python scripts/render_score.py score.json -o score.png \
    --width 760 --cell-max 48 --no-footer
```

## 数据格式

```json
{
  "title": "《歌名》键盘谱",
  "subtitle": "歌手 · 原版简谱 · 一字一音 · 全曲",
  "sections": [
    {"name": "主 歌 一", "rows": [
      {"lyric": "窗外的麻雀在电线杆上多嘴",
       "notes": "5 1^ 7 1^ 1^ 1^ 1^ 7 6 7 6 5"}
    ]}
  ]
}
```

音符记号：

| 记号 | 含义 | 颜色 |
|---|---|---|
| `3` | 中音 | 橙 |
| `3^` | 高八度 | 蓝 |
| `_3` | 低八度 | 绿 |

**一个字必须对应一个音**，`audit_score.py` 会强制校验。

想换键位体系？在 JSON 里加 `key_map`：

```json
"key_map": {"1":"A", "2":"S", "3":"D", "4":"F", "5":"G", "6":"H", "7":"J"}
```

## 多来源比对

拿到两份不同来源的简谱时，先转成 JSON 再逐句比差异，比肉眼看快得多：

```bash
python scripts/audit_score.py source-a.json --compare source-b.json
```

只列有出入的句子，方便你去找第三个来源或直接听原曲判定。

## ⚠️ 最重要的一条：不要编旋律

这个 skill 是**渲染工具**，不负责生成旋律。旋律必须去查真实简谱，
并且至少两个独立来源交叉验证 —— 用户会拿去对着原曲弹，编的东西一弹就废。

具体查证策略和已知来源质量评级见 [`references/known-sources.md`](references/known-sources.md)。

## 作为 WorkBuddy Skill 安装

整个仓库直接放进 `~/.workbuddy/skills/` 即可，`SKILL.md` 会被自动识别。

## 目录结构

```
song-keyboard-jianpu/
├── SKILL.md                    # Skill 定义（给 Agent 读的工作流程）
├── README.md                   # 本文件
├── scripts/
│   ├── render_score.py         # 渲染引擎
│   └── audit_score.py          # 校验 + 多来源比对
├── references/
│   ├── known-sources.md        # 各来源可靠度 & 《七里香》实战记录
│   └── pitfalls.md             # 踩过的坑
└── examples/
    └── qilixiang.json          # 《七里香》28 行全曲参考数据
```
