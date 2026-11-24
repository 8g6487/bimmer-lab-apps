# 由參考圖取一塊，變成 widget

這份是「截圖 → sprite widget」的操作步驟。以 `ref-foot.png`（離合器錶右下腳）為例，
換成你自己的參考圖時，只換量到的 box 和檔名。

## 0. 先決定值不值得截

| 情況 | 做法 |
| --- | --- |
| 靜態圖案、logo、照片質感（車仔、輪圈、指針錶面） | 截圖成 sprite |
| 會動、要跟信號變（轉速帶、油量液位、紅線） | 重畫（shader），截圖只可當底圖參考 |
| 圖裡面有會被信號改寫的字（「189 km」「N」） | 截圖可以，但要把字遮掉或裁掉；遮不掉就重畫 |
| 左右要鏡像 1:1（右側轉速錶） | 重畫；鏡像會把數字反過來，只能分別截兩張 |

## 1. 在原圖上量 box

在參考圖的原尺寸上量 `x0,y0,x1,y1`（含邊緣一點留白，方便對齊），不要先縮放再量。

換算到 cluster 面板（1920×720）的比例：

```
k = 1920 / 參考圖寬
x = round(x0 * k)      w = round((x1 - x0) * k)
y = round(y0 * k)      h = round((y1 - y0) * k)
```

例：`vis/ref-m3.png` 是 2930×1030，`k = 1920/2930 = 0.6554`。
這一步只是為了把 widget 擺到正確位置；bitmap 本身按原圖裁就好。

## 2. 裁切 + 去背

```bash
cd apps
python design/mk_sprite.py ../ref-foot.png \
    --name dial-foot \
    --box 300,90,800,640 \
    --key black --tol 22 \
    --kill-red-below 0.55 \
    --max 220
```

| 參數 | 作用 |
| --- | --- |
| `--box x0,y0,x1,y1` | 先裁再處理，座標是原圖像素 |
| `--key black` | 深色背景轉透明：`alpha = max(r,g,b)`，低於 `--tol` 視為全透明 |
| `--key luma` | 圖本身就是遮罩（黑底白圖）時用，alpha 取亮度 |
| `--tol 22` | 背景雜訊容忍度；畫面有漸層黑時調高，邊緣吸太多時調低 |
| `--gamma 0.8` | 讓半透明的邊緣更實；`1.2` 則更淡 |
| `--kill-red-below 0.55` | 把 box 高度 55% 以下的紅色（照片裡烘死的紅線）去色，留給主題自己畫紅線 |
| `--max 220` | 長邊上限，控制記憶體（見第 4 節） |
| `--tintable` | 轉成「白色 + alpha 遮罩」，之後用 widget 的 `color` 染色（圖示類） |

輸出：`apps/apps/cluster_themes/hud/sprites/dial-foot.json`
（這個 repo 是 `apps/apps/` 兩層，工具的 `--to` 已預設正確路徑。）

## 3. 先看圖，別急著進 app

把 json 還原成 png 檢查邊緣：

```bash
python -c "
import base64,json,zlib,io
from PIL import Image
m=json.load(io.open('apps/cluster_themes/hud/sprites/dial-foot.json',encoding='utf-8'))
im=Image.frombytes('RGBA',(m['w'],m['h']),zlib.decompress(base64.b64decode(m['z'])))
im.save('zz-preview.png'); print(im.size, im.getchannel('A').getextrema())"
```

要看的有三點：

- **邊緣有沒有黑邊**：有的話把 `--tol` 調高 5–10，或加 `--bleed 0.15` 把半透明壓成實心。
- **背景漸層有沒有留下灰塊**：參考圖背景不是純黑時，`--key black` 會留下淡影——改用 `--key luma --gamma 1.4`。
- **有沒有把字裁進來**：有就重新量 box，或回到第 0 節重畫。

## 4. 成本

每個 sprite 佔 `w × h × 8` bytes 的 pixel memory（不是檔案大小），主題上限 **16 MiB**。

| 尺寸 | 佔用 |
| --- | --- |
| 200×220 | 352 KB |
| 400×400 | 1.25 MiB |
| 800×800 | 5 MiB |

所以 `--max` 一般 256–512 就夠；sprite 會被拉伸到 widget 的 `w`×`h`，所以 `--max`
不要小於 widget 尺寸，否則在車上看到的是放大後的模糊。

## 5. 掛進 layout

編輯器：`⧉ Add` → type `sprite` → 在 Properties 填 `name`（檔名，不含 `.json`）與 `w`/`h`。

等價的 JSON（`hud/layouts/<theme>.json` 的 `widgets`）：

```json
{"id":"dial-foot","type":"sprite","name":"dial-foot","x":188,"y":470,"w":131,"h":144,"z":4}
```

- `x/y/w/h` 用第 1 節換算出來的面板座標。
- `z` 是疊放順序；數字越大越上面。
- 若做了 `--tintable`，加 `"color":[236,240,244]` 就會被染成該色。

## 6. 打包與驗收

```bash
python kit/tools/build.py cluster_themes
```

新的 sprite 是打包進 app 的（只改 layout 不用 build，app 會自己 reload）。

bench 要手動重開（`/restart` 不會讓出 8078 端口）：

```bash
taskkill -F -PID <pid>
nohup node bench/server.js cluster_themes > bench/bench.log 2>&1 &
```

驗收看三件事：

1. `/?only=1&clean=1` 截圖，看圖有沒有出現、位置對不對（重截時加 `?v=<n>` 避開 Chrome 快取）。
2. bench 首頁看 `pixels: x of 16 MiB`，確認沒爆表。
3. 把 `clean` 取消勾選，看 layer outline 是否只有一個框在圖上（多框＝你重複加了 widget）。

## 7. 什麼時候該停手

- 邊緣一圈光暈、黑底漸層怎麼樣都去不乾淨 → 這張圖不適合，改成重畫。
- 圖裡有會被信號改寫的內容（速度、檔位、里程）→ 裁掉那部分，或整塊重畫。
- 需要在左右兩側鏡像 → 分兩張截、分別量 box（右邊的數字不會被鏡像）。
- 你需要的其實是「跟信號一起動」→ sprite 做不到，回去改 shader（`apps/shared/shaders.js`）。

## 附：這幾個 sprite 是怎麼來的

| sprite | 來源 | 做法 |
| --- | --- | --- |
| `car-photo` | 車主手冊的 TPMS 照片 | 裁車仔、把綠色輪胎燈畫成中灰、放大 |
| `wheel` | 一個 5 輻輪圈圖示 | `--key luma --tintable`，白色遮罩 |
| `tach-m3-*`（已棄用） | `vis/ref-m3.png` 的轉速弧 | 被否決：靜態圖不能跟轉速動，改回 shader |
| 油量／水溫括號（已棄用） | 同上 | 同上，且裡面有 `189 km` 文字 |
