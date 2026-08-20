# データの圧縮③ ハフマン符号化

『大学入学共通テスト「情報Ⅰ」対策問題集』（技術評論社, ISBN 978-4-297-15084-6）pp.171-174 連動Webアプリ。

**公開URL**: https://technical-reviewer-information1.github.io/huffman/

## このアプリでできること

| STEP | 内容 |
|---|---|
| 1 | 文章、または文字と出現回数からデータを決める |
| 2 | **自分でカードを2枚選んでハフマン木を組み立てる**（誤った選択にはその場で理由を返す）／お手本の再生 |
| 3 | 完成した木から符号表を読む（左=0・右=1） |
| 4 | 固定長符号とのビット数比較・圧縮率 |
| 5 | 符号化／復号を試す・木を1文字ずつたどる・確認クイズ |

## 技術

- 静的HTML / CSS / JavaScript のみ。ビルド不要・外部CDN不使用・通信なし
- GitHub Pages で配信（Python・Streamlit 不要）
- スマートフォン／タブレット／PC 対応

```
index.html
css/style.css   共通スタイル（全アプリ共通）
css/app.css     このアプリ固有
js/huffman.js   アルゴリズム本体
js/tree.js      木のSVG描画
js/app.js       画面制御
```

`streamlit_app.py` は旧版（Streamlit Community Cloud 用）です。

---
Created by Dit-Lab.(Daiki ITO) / Supported by Tomoaki ATSUMI
