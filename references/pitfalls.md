# 踩过的坑

## 1. 背景渐变底部泛粉红（渐变公式写错）

**现象**：蓝色调背景，越往下越偏粉/三文鱼色。

**原因**：最后一段插值写成
```python
r = int(COL_BOT[0] * (1 - t) + 140)      # ← 少了 t，红色分量一路飙升
```

**修法**：四段式**显式两端颜色**插值，永远写成 `A*(1-t) + B*t`：
```python
STOPS = [(0.00, GRAD_TOP), (0.30, GRAD_MID), (0.40, GRAD_LO), (1.00, GRAD_BOT)]
```
写渐变时顺手让三个分量都用同一条公式，别只给某个分量加常数。

## 2. pip install 装错环境

在这台机器上先确认 venv 位置，不要对着系统 Python 直接 `pip install`：
```bash
C:/Users/<user>/.workbuddy/binaries/python/envs/default/Scripts/python.exe -m pip install Pillow
C:/Users/<user>/.workbuddy/binaries/python/envs/default/Scripts/python.exe render_score.py ...
```

## 3. 中文歌词字数数错

**这是最容易出错也最致命的一环**——"秋刀鱼的滋味"是 6 个字还是 5 个字，肉眼数不一定对。

必须在代码里做强校验：
```python
if len(list(lyric)) != len(notes.split()):
    raise ValueError(...)
```
校验器 `scripts/audit_score.py` 会一次性列出所有行的字数/音符数，
比等 Python 逐条 raise 再改高效得多。

## 4. 长句溢出谱行

固定列宽（如 46px）在长句上会溢出。用自适应列宽：
```python
cell_w = min(CELL_MAX, AVAIL / n)
```
同时要保证**歌词 chip 宽度 < cell_w**，否则相邻字的 chip 会粘在一起。
经验值：`msyh 19px` 的汉字 chip 宽约 39px，所以 cell_w 别低于 42。

## 5. 字母被压到行底外 / 挤成一团

行高不够时字母会和歌词 chip 重叠。三段式布局的可用高度预算：

| 元素 | 起始 y（相对行顶） | 高度 |
|---|---|---|
| 简谱数字 | 10 | 26 |
| 八度圆点 | 数字上方 8px | 8 |
| 歌词 chip | 40 | 字高 + 12 |
| 字母方框 | ROW_H - 30 - 6 | 30 |

`ROW_H = 104` 刚好够。要加大字母就同步加 ROW_H。

## 6. 八度圆点位置

- 数字**正上方**小圆点 = 高八度
- 数字**正下方**小圆点 = 低八度
- PIL 里用 `draw.ellipse` 显式画，字体的上标点不可靠

## 7. 别把歌词按词组切分

用户要的是**一个字一个音**。一行应该是完整的歌词句
（如 `"窗外的麻雀在电线杆上多嘴"` 而不是拆成 `"窗外的麻雀"` / `"在电线杆上多嘴"`），
既省版面又好读。按歌词的自然句换行即可。
