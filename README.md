# 日本語の指示で動く AI 配送ロボット

最終課題のサンプル「ROS2とGazeboの連携によるロボット操作」を参考に、日本語の指示を機械学習で分類し、2つの配達先へ自動で移動するタスクです。
Apple Silicon Mac + Docker で実行し、LLM・外部 API・GPU は使いません。

## 作品の内容

| 入力の例 | AI の分類 | ロボットの動作 |
| --- | --- | --- |
| この荷物を受付へ届けてください | reception | 緑の受付マーカーへ移動して停止 |
| 資材を倉庫まで運搬してほしい | warehouse | オレンジの倉庫マーカーへ移動して停止 |
| 停止して | stop | 移動を中断して停止 |
| 明日の天気を教えて | 学習語彙のカバー率不足で棄却 | 停止して指示を受け付けない |

AI は文字1〜3文字単位の TF-IDF + ロジスティック回帰です。48件の手作り指示文から学習し、入力文を推論して目的地を選びます。
その後は、Gazeboの実際の位置をROS 2の `/odom` へ渡し、単純な比例制御で走行します。車輪からの位置積算やSLAMによる自己位置推定は使いません。

最大スコア0.55以上・上位2クラスの差0.15以上・学習語彙に含まれる文字の割合50%以上を受理の条件にします。
限定された指示を3分類するモデルであり、汎用的な言語理解はできません。スコアは確率として校正しておらず、未知の指示や否定文を必ず検出できるわけではありません。
障害物回避・SLAM・荷物の把持は省略し、配送を荷物を載せた車体の地点間移動として表現します。

## 起動

Docker Desktop を起動し、この README があるフォルダで実行します。初回は数 GB のパッケージを取得する場合があります。

```bash
mkdir -p ros2_ws/src output
docker compose up --build -d
docker compose logs --tail 50 sim
```

ブラウザで <http://localhost:6080/vnc.html?autoconnect=1&resize=scale> を開きます。
青い配送ロボットと、緑・オレンジの配達先が表示されます。下のログ画面に `READY` が出るまで待ちます。
ROS パッケージは起動時に `colcon build` でビルドされます。

通信確認:

```bash
docker compose exec sim /ros_entrypoint.sh bash /work/scripts/check-sim.sh
```

Gazebo の時刻が ROS 2 の `/clock` に届くことを確認します。Compose の healthcheck はブラウザ用 HTTP サーバーのみ確認します。

## デモと自由な指示

```bash
bash scripts/demo.sh
```

受付への到着、倉庫への移動途中の停止・再開、倉庫への到着、範囲外の指示の棄却を順に確認します。失敗やタイムアウトは終了コードで通知します。

自分で指示する場合:

```bash
bash scripts/instruct.sh '書類を受付まで運んでください'
bash scripts/instruct.sh '荷物を倉庫に届けて'
bash scripts/instruct.sh '停止して'
```

学習に使わない12件の評価文で分類結果を調べる場合:

```bash
docker compose exec -T sim /ros_entrypoint.sh bash -c \
  'source /work/ros2_ws/install/setup.bash && ros2 run pai_delivery evaluate' \
  > output/intent-evaluation.json
```

12件は手作りの少数データです。この結果を一般的な日本語理解の性能として扱わないでください。
初回評価では分類ラベルは12/12件正解、スコア条件も満たして受理したのは11/12件でした。「いま停止をお願いします」は停止クラスを選びましたがスコア不足で棄却され、停止する動作になりました。
走行のイベントは `output/events.jsonl` に記録します。到着判定はGazeboの実位置に基づいて目的地から15 cm以内です。車輪の滑りで積算位置がずれたため、シミュレータの実位置を使うOdometryPublisherへ切り替えています。実機では別の自己位置推定が必要です。

停止と再起動:

```bash
docker compose down
docker compose up -d
```

`simulation/` と `scripts/` は Mac 側で編集できます。変更後は `docker compose restart sim` で読み直します。
`ros2_ws/src/` に ROS パッケージ、`output/` に結果を置きます。

## 動画とレポート

90秒の説明字幕付きMP4を自動で録画する場合:

```bash
docker compose exec -T sim bash /work/scripts/record-demo.sh
```

`output/pai-delivery-demo.mp4` に保存します。録画中はnoVNC上でカメラやウィンドウを操作しないでください。
提出用の動画タイトルはYouTubeへのアップロード時にOmnicampusアカウント名またはIDを含む指定形式へ設定します。

動画は90秒程度を目安に、次の順で画面録画します。

1. 0〜15秒: 課題名、入力→AI分類→ROS 2→Gazeboという構成を説明。
2. 15〜40秒: 受付への指示、分類ログ、移動・到着を見せる。
3. 40〜65秒: 倉庫への指示、移動・到着を見せる。
4. 65〜80秒: 停止と範囲外の指示を試す。
5. 80〜90秒: サンプルからの追加点、制約を説明。

レポートは1〜2ページで、目的・構成・AIの学習/推論・実行結果・工夫点・制約・参考資料を書けば整理しやすくなります。
結果は実際に確認できた数値と動作を記載します。
サンプルのキーボード操作に対し、日本語分類による目的地選択、到着までの自動制御、判定スコアによる棄却を加えた点が工夫です。

`scripts/make-report.py` は実測JSONからPDFを作成する補助スクリプトです。実行するPython環境にはReportLabが必要です。
生成先は `output/pdf/説明資料_PAI最終課題.pdf`。提出前に指定のOmnicampusアカウント名またはIDを含むファイル名に変更します。

## 課題の提出条件

手元の「最終課題（10_19 改訂版）.pdf」に基づきます。Slack はブラウザ上の対象チャンネルで直近の投稿と個人情報に関する運営回答を確認しました。告知全件の確認はしていません。

- 締切: 2026年11月2日（月）10:00（講座案内の時刻。日本時間として計画）
- AI の利用は必須。推論だけでもよく、学習は任意。
- ロボットがタスクを実行する1〜3分の動画。2倍速を使う場合は明記。
- 使用コード一式を public の GitHub リポジトリで提出。
- PDF の指定名: `説明資料_PAI最終課題_omnicampusアカウント名.pdf`
- YouTube に少なくとも限定公開でアップロード。タイトル: `PAI最終課題_omnicampusアカウント名` またはアカウントID。
- omnicampus に PDF・GitHub URL・YouTube URL を提出。
- 個人情報を含めず、YouTube の設定などの詳細は課題 PDF の指示を確認する。
- Slack の運営回答では Git コミットの Author とメールアドレスも個人情報の対象。ZIP は Git 履歴を含まないため、GitHub に登録するときの作者設定は別途確認する。

動画とPDFの内容を確認し、アップロードとomnicampusでの最終提出を行います。
講義資料や宿題をそのまま public リポジトリに混ぜず、この作品に使うコードと再現手順を整理します。

```bash
python3 scripts/package-code.py
```

作品のソースだけを `output/pai-delivery-code.zip` にまとめます。

## 構成と参考資料

| 項目 | 選択 |
| --- | --- |
| コンテナ | Ubuntu 24.04 / linux/arm64 |
| ROS | ROS 2 Jazzy |
| シミュレータ | Gazebo Harmonic / ros_gz |
| GUI | Xvfb + noVNC、CPU 描画 / Ogre 1 |
| 通信 | `/instruction` → AI → `/cmd_vel`、Gazebo → `/odom` |

ROS の公式イメージは arm64 対応です。Gazebo の ARM 対応は best effort のため、この Mac での実行確認が必要です。
参考サンプルは Humble / Fortress のため、ここでは Jazzy / Harmonic のプラグイン名とブリッジに合わせています。

- [課題掲載の参考サンプル: gazeboとROS2を連携してロボットを操作する](https://qiita.com/N622/items/9d89f77d85d9da0af29e)
- [Gazebo 公式: Moving the robot](https://gazebosim.org/docs/harmonic/moving_robot/)
- [ROS / Gazebo の対応表](https://gazebosim.org/docs/harmonic/ros_installation/)
- [ROS 公式イメージのアーキテクチャ](https://github.com/docker-library/official-images/blob/master/library/ros)
- [Gazebo の対応プラットフォーム](https://gazebosim.org/docs/harmonic/install/)
- [Gazebo の CPU 描画と Ogre 切替](https://gazebosim.org/docs/harmonic/troubleshooting/)
- [Gazebo の実位置を配信する OdometryPublisher](https://gazebosim.org/api/sim/8/classgz_1_1sim_1_1systems_1_1OdometryPublisher.html)
- [Docker Desktop の GPU パススルー対応](https://docs.docker.com/desktop/features/gpu/)
