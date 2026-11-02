"""Build a short PDF from measured evaluation and integration results."""
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

root = Path(__file__).resolve().parents[1]
evaluation = json.loads((root / "output/intent-evaluation.json").read_text())
demo = json.loads((root / "output/demo-result.json").read_text())
if not demo["passed"]:
    raise RuntimeError("Integration demo has not passed; refusing to report success.")
font_path = Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
if font_path.exists():
    pdfmetrics.registerFont(TTFont("Japanese", str(font_path)))
    font = "Japanese"
else:
    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
    font = "HeiseiKakuGo-W5"
navy = colors.HexColor("#18374A")
teal = colors.HexColor("#087E8B")
style = ParagraphStyle("body", fontName=font, fontSize=9.2, leading=13, wordWrap="CJK", spaceAfter=5)
small = ParagraphStyle("small", parent=style, fontSize=8, leading=12)
heading = ParagraphStyle("heading", parent=style, fontSize=11.5, leading=16, textColor=teal, spaceBefore=8, spaceAfter=4, keepWithNext=True)
title = ParagraphStyle("title", parent=style, fontSize=19, leading=25, textColor=navy, spaceAfter=9, alignment=TA_LEFT)
story = []


def p(text, kind=style):
    story.append(Paragraph(text, kind))


def table(rows, widths):
    cells = [[Paragraph(str(value), small) for value in row] for row in rows]
    item = Table(cells, colWidths=widths, hAlign="LEFT")
    item.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E7F2F3")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C7D5DC")),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(item)
    story.append(Spacer(1, 6))


p("Physical AI 応用1講座 / 最終課題", small)
p("日本語の指示で動く AI 配送ロボット", title)
p("外部APIを使わず、小さな文章分類モデルとROS 2で地点間の自律移動を実現する。")
p("1. 目的とタスク", heading)
p("日本語の配送指示で差動二輪ロボットを受付（緑）または倉庫（橙）へ移動・停止させる。荷物は車体上の箱で表現し、把持や積み下ろしは対象にしない。")
table([
    ["入力", "機械学習", "制御・実行"],
    ["日本語の配送・停止指示<br/>ROS 2 /instruction", "文字TF-IDF +<br/>ロジスティック回帰<br/>受付 / 倉庫 / 停止", "目的地の選択 → 比例制御<br/>ROS 2 /cmd_vel → Gazebo<br/>/odom でシミュレータ実位置を取得"],
], [145, 155, 195])
p("2. 実行環境とAIの役割", heading)
p("Apple Silicon Mac / Docker（linux/arm64）/ Ubuntu 24.04 / ROS 2 Jazzy / Gazebo Harmonic。GUIはXvfbとnoVNCを使い、CPUで描画する。LLMや外部APIは利用しない。")
p("学習用の日本語指示48件（3クラス各16件）を手作りした。文字1〜3文字のTF-IDF特徴量からロジスティック回帰（C=8、最大反復1000）で3分類する。起動時にCPUで学習し、その後の入力には学習済みモデルで推論する。目的地が決まった後の走行制御には学習モデルを使わない。")
p("最大分類スコアが0.55未満、上位2クラスのスコア差が0.15未満、または学習語彙に含まれる文字の割合が50%未満なら棄却して停止する。語彙の判定は範囲外の文章にも既知クラスが割り当てられる問題への対策である。これらの条件で未知の指示を必ず検出できるわけではない。")
p("3. 実行結果", heading)
p(f"学習に使わない手作りの評価文12件では、分類正解 {evaluation['classification_correct']}/12件、しきい値を満たして正しく受理した件数 {evaluation['accepted_and_correct']}/12件となった。表現や目的地が限定された小規模な確認値であり、一般的な日本語理解性能を示す値ではない。")
arrivals = [event for event in demo["steps"] if event["phase"] == "arrived"]
rows = [["走行確認", "結果（ROS 2のオドメトリ）"]]
for event in arrivals:
    label = "受付" if event["label"] == "reception" else "倉庫"
    rows.append([label + "への移動", f"到着・停止 / x={event['position'][0]:.3f}, y={event['position'][1]:.3f} m"])
rows.append(["途中停止・再開 / 範囲外指示", "停止指示を受理し、再指示で到着 / 天気の質問を棄却"])
table(rows, [165, 330])
p("到着判定は目的地から15 cm以内。車輪の滑りによる積算位置のずれを避け、Gazeboの実位置をOdometryPublisherから取得する。走行状態、分類結果、座標はevents.jsonlとdemo-result.jsonに保存する。", small)
p("4. サンプルからの工夫と制約", heading)
p("課題掲載の「gazeboとROS2を連携してロボットを操作する」を参考に、差動二輪モデルと速度指令のブリッジという構成を採用した。キーボードによる操作から発展させ、日本語分類による目的地の選択、到着までの自動制御、低スコア指示の棄却、走行ログを追加した。モデル・制御ノード・分類用データを本作品用に作成した。")
p("走行場所は障害物のない平面とし、障害物回避、SLAM、把持は実装しない。実機には別の自己位置推定が必要である。学習文が少なく、否定文・複数目的地・未学習表現の誤分類が残る。改善案は指示データの拡充、未知指示・停止挙動の評価、障害物回避の追加である。")
p("5. 再現方法・参考資料", heading)
p("Docker Desktop起動後、docker compose up --build -dで環境を起動し、bash scripts/demo.shでデモを実行する。詳細手順と評価コマンドはREADME.mdに記載。", small)
p('<link href="https://qiita.com/N622/items/9d89f77d85d9da0af29e" color="#087E8B">参考サンプル：gazeboとROS2を連携してロボットを操作する（N622）</link><br/><link href="https://gazebosim.org/docs/harmonic/moving_robot/" color="#087E8B">Gazebo公式：Moving the robot</link>', small)

out = root / "output/pdf/説明資料_PAI最終課題.pdf"
out.parent.mkdir(parents=True, exist_ok=True)


def footer(canvas, doc):
    canvas.setFont(font, 8)
    canvas.setFillColor(navy)
    canvas.drawString(50, 27, "日本語の指示で動くAI配送ロボット")
    canvas.drawRightString(A4[0] - 50, 27, str(doc.page))


doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=50, rightMargin=50, topMargin=36, bottomMargin=42,
                        title="日本語の指示で動くAI配送ロボット", author="")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(out)
