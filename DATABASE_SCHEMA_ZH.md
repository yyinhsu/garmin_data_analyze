# Garmin 健康資料庫架構

資料儲存於 `./HealthData/DBs/`，共 5 個 SQLite 資料庫。

> **注意：** 若架構有變動，請同時更新 `DATABASE_SCHEMA.md` 與 `DATABASE_SCHEMA_ZH.md`。

---

## garmin.db — 基礎健康每日資料

### `daily_summary` — 每日總結（601 筆）

| 欄位 | 說明 |
|------|------|
| `day` | 日期（PK） |
| `hr_min` / `hr_max` | 全日心率最小/最大值 (bpm) |
| `rhr` | 靜止心率 (bpm) |
| `stress_avg` | 平均壓力分數（0–100） |
| `step_goal` / `steps` | 步數目標 / 實際步數 |
| `moderate_activity_time` | 中等強度運動時間 |
| `vigorous_activity_time` | 高強度運動時間 |
| `intensity_time_goal` | 強度時間目標 |
| `floors_up` / `floors_down` / `floors_goal` | 樓層數（上/下/目標） |
| `distance` | 移動距離（公里） |
| `calories_goal` / `calories_total` | 卡路里目標 / 總消耗 |
| `calories_bmr` | 基礎代謝卡路里 |
| `calories_active` | 主動消耗卡路里 |
| `calories_consumed` | 攝入卡路里 |
| `hydration_goal` / `hydration_intake` | 水分目標 / 攝入量（oz） |
| `sweat_loss` | 排汗量 |
| `spo2_avg` / `spo2_min` | 平均/最低血氧濃度 (%) |
| `rr_waking_avg` / `rr_max` / `rr_min` | 清醒呼吸率 平均/最大/最小（breaths/min） |
| `bb_charged` / `bb_max` / `bb_min` | Body Battery 充值/最大/最小 |
| `description` | 備註 |

---

### `sleep` — 每日睡眠（601 筆）

| 欄位 | 說明 |
|------|------|
| `day` | 日期（PK） |
| `start` / `end` | 睡眠開始/結束時間 |
| `total_sleep` | 總睡眠時長 |
| `deep_sleep` | 深層睡眠時長 |
| `light_sleep` | 淺層睡眠時長 |
| `rem_sleep` | REM 睡眠時長 |
| `awake` | 清醒時長 |
| `avg_spo2` | 睡眠中平均血氧 (%) |
| `avg_rr` | 睡眠中平均呼吸率 |
| `avg_stress` | 睡眠中平均壓力 |
| `score` | 睡眠分數（0–100） |
| `qualifier` | 睡眠品質評語（如 FAIR、GOOD） |

---

### `resting_hr` — 靜止心率（588 筆）

| 欄位 | 說明 |
|------|------|
| `day` | 日期（PK） |
| `resting_heart_rate` | 當日靜止心率 (bpm) |

---

### `stress` — 壓力時序（817,388 筆）

| 欄位 | 說明 |
|------|------|
| `timestamp` | 時間戳（每分鐘） |
| `stress` | 壓力值（0–100；負值表示靜止/睡眠） |

---

### `weight` — 體重（4 筆）

| 欄位 | 說明 |
|------|------|
| `day` | 日期 |
| `weight` | 體重（公斤） |

---

### `devices` — 裝置資訊（6 筆）

| 欄位 | 說明 |
|------|------|
| `serial_number` | 序號（PK） |
| `timestamp` | 最後同步時間 |
| `device_type` | 裝置類型（如 fitness_tracker） |
| `manufacturer` | 製造商 |
| `product` | 型號（如 VivoActive_5） |
| `hardware_version` | 硬體版本 |

---

### `sleep_events` — 睡眠事件（2,317 筆）

| 欄位 | 說明 |
|------|------|
| `timestamp` | 事件發生時間 |
| `event` | 事件類型 |
| `duration` | 持續時間 |

---

## garmin_activities.db — 運動活動資料

### `activities` — 活動記錄（615 筆）

| 欄位 | 說明 |
|------|------|
| `activity_id` | 活動 ID（PK） |
| `name` | 活動名稱（如 Running、Stair Stepper） |
| `type` | 類型 |
| `sport` / `sub_sport` | 運動類別 / 子類別 |
| `laps` | 分段數 |
| `start_time` / `stop_time` | 開始/結束時間 |
| `elapsed_time` / `moving_time` | 總時間 / 移動時間 |
| `distance` | 距離（公里） |
| `cycles` | 周期數（步、踏板等） |
| `avg_hr` / `max_hr` | 平均/最大心率 |
| `avg_rr` / `max_rr` | 平均/最大呼吸率 |
| `calories` | 卡路里消耗 |
| `avg_cadence` / `max_cadence` | 平均/最大節奏 |
| `avg_speed` / `max_speed` | 平均/最大速度 |
| `ascent` / `descent` | 上升/下降高度（公尺） |
| `max_temperature` / `min_temperature` / `avg_temperature` | 溫度（°C） |
| `start_lat` / `start_long` / `stop_lat` / `stop_long` | GPS 起終點座標 |
| `training_load` / `training_effect` / `anaerobic_training_effect` | 訓練負荷指標 |
| `hrz_1_hr` ~ `hrz_5_hr` | 各心率區間門檻 |
| `hrz_1_time` ~ `hrz_5_time` | 各心率區間停留時間 |
| `self_eval_feel` / `self_eval_effort` | 主觀感受 / 努力程度評分 |

---

### `steps_activities` — 步行/跑步詳情（32 筆）

| 欄位 | 說明 |
|------|------|
| `activity_id` | 關聯活動 ID（FK） |
| `steps` | 總步數 |
| `avg_pace` / `avg_moving_pace` / `max_pace` | 平均配速 / 移動配速 / 最快配速 |
| `avg_steps_per_min` / `max_steps_per_min` | 平均/最大步頻 |
| `avg_step_length` | 平均步幅 |
| `avg_vertical_ratio` / `avg_vertical_oscillation` | 垂直比率 / 垂直振幅 |
| `avg_gct_balance` / `avg_ground_contact_time` | 觸地平衡 / 觸地時間 |
| `avg_stance_time_percent` | 站立時間百分比 |
| `vo2_max` | 最大攝氧量估算 |

---

### `cycle_activities` — 騎車詳情（28 筆）

| 欄位 | 說明 |
|------|------|
| `activity_id` | 關聯活動 ID（FK） |
| `strokes` | 踏板次數 |
| `vo2_max` | 最大攝氧量估算 |

---

### `activity_laps` — 活動分段（649 筆）

每段 lap 的詳細指標，欄位與 `activities` 相同，附加：

| 欄位 | 說明 |
|------|------|
| `activity_id` | 關聯活動 ID（FK） |
| `lap` | 段落編號（從 0 開始） |

---

### `activity_records` — 逐秒記錄（1,348,434 筆）

| 欄位 | 說明 |
|------|------|
| `activity_id` | 關聯活動 ID（FK） |
| `record` | 記錄序號 |
| `timestamp` | 時間戳 |
| `position_lat` / `position_long` | GPS 座標 |
| `distance` | 當前累計距離 |
| `cadence` | 當前節奏 |
| `altitude` | 海拔（公尺） |
| `hr` | 當前心率 |
| `rr` | 當前呼吸率 |
| `speed` | 當前速度 |
| `temperature` | 溫度 |

---

## garmin_monitoring.db — 全天候背景監測

### `monitoring` — 活動類型監測（250,242 筆）

| 欄位 | 說明 |
|------|------|
| `timestamp` | 時間戳 |
| `activity_type` | 活動類型（walking、running、sedentary 等） |
| `intensity` | 強度等級（0–5） |
| `duration` | 當前時間段總長 |
| `distance` | 累計距離 |
| `cum_active_time` | 累計主動時間 |
| `active_calories` | 累計主動卡路里 |
| `steps` | 累計步數 |
| `strokes` | 累計划槳數 |
| `cycles` | 累計周期數 |

---

### `monitoring_hr` — 即時心率（658,267 筆）

| 欄位 | 說明 |
|------|------|
| `timestamp` | 時間戳（約每分鐘） |
| `heart_rate` | 心率 (bpm) |

---

### `monitoring_rr` — 即時呼吸率（558,811 筆）

| 欄位 | 說明 |
|------|------|
| `timestamp` | 時間戳 |
| `rr` | 呼吸率（breaths/min） |

---

### `monitoring_intensity` — 強度時間累積（6,385 筆）

| 欄位 | 說明 |
|------|------|
| `timestamp` | 時間戳（每 15 分鐘） |
| `moderate_activity_time` | 累計中等強度運動時間 |
| `vigorous_activity_time` | 累計高強度運動時間 |

---

### `monitoring_info` — 監測元資料（7,486 筆）

| 欄位 | 說明 |
|------|------|
| `timestamp` | 時間戳 |
| `file_id` | 原始 FIT 檔案 ID |
| `activity_type` | 活動類型 |
| `resting_metabolic_rate` | 靜止代謝率 |
| `cycles_to_distance` | 周期換算距離係數 |
| `cycles_to_calories` | 周期換算卡路里係數 |

---

## garmin_summary.db / summary.db — 彙整統計

> `garmin_summary.db` 與 `summary.db` 結構相同，皆包含以下四張表。

### 共用欄位（`days_summary` / `weeks_summary` / `months_summary` / `years_summary`）

| 欄位 | 說明 |
|------|------|
| `day` / `first_day` | 日期鍵（日報用 `day`，其餘用 `first_day`） |
| `hr_avg` / `hr_min` / `hr_max` | 心率 平均/最低/最高 |
| `rhr_avg` / `rhr_min` / `rhr_max` | 靜止心率 平均/最低/最高 |
| `inactive_hr_avg` / `inactive_hr_min` / `inactive_hr_max` | 非活動心率 |
| `weight_avg` / `weight_min` / `weight_max` | 體重（公斤） |
| `intensity_time` / `moderate_activity_time` / `vigorous_activity_time` | 強度/中等/高強度時間 |
| `intensity_time_goal` | 強度時間目標 |
| `steps` / `steps_goal` | 步數 / 步數目標 |
| `floors` / `floors_goal` | 樓層 / 目標 |
| `sleep_avg` / `sleep_min` / `sleep_max` | 睡眠時長 平均/最短/最長 |
| `rem_sleep_avg` / `rem_sleep_min` / `rem_sleep_max` | REM 睡眠 |
| `stress_avg` | 平均壓力分數 |
| `calories_avg` / `calories_bmr_avg` / `calories_active_avg` | 卡路里（總/基代/主動） |
| `calories_goal` / `calories_consumed_avg` | 卡路里目標 / 攝入 |
| `activities` / `activities_calories` / `activities_distance` | 活動次數 / 卡路里 / 距離 |
| `hydration_goal` / `hydration_avg` / `hydration_intake` | 水分目標/平均/攝入 |
| `sweat_loss_avg` / `sweat_loss` | 排汗量 |
| `spo2_avg` / `spo2_min` | 血氧平均/最低 |
| `rr_waking_avg` / `rr_max` / `rr_min` | 呼吸率 清醒均值/最大/最小 |
| `bb_max` / `bb_min` | Body Battery 最大/最小 |

| 資料表 | 時間粒度 | 筆數 |
|--------|---------|------|
| `days_summary` | 每日 | 588 |
| `weeks_summary` | 每週 | 112 |
| `months_summary` | 每月 | 20 |
| `years_summary` | 每年 | 3 |

---

## 資料規模總覽

| 資料庫 | 資料表 | 筆數 |
|--------|--------|------|
| garmin.db | daily_summary | 601 |
| garmin.db | sleep | 601 |
| garmin.db | resting_hr | 588 |
| garmin.db | stress | 817,388 |
| garmin.db | weight | 4 |
| garmin_activities.db | activities | 615 |
| garmin_activities.db | activity_records | 1,348,434 |
| garmin_activities.db | steps_activities | 32 |
| garmin_activities.db | cycle_activities | 28 |
| garmin_monitoring.db | monitoring | 250,242 |
| garmin_monitoring.db | monitoring_hr | 658,267 |
| garmin_monitoring.db | monitoring_rr | 558,811 |
| garmin_summary.db | days_summary | 588 |
| garmin_summary.db | weeks_summary | 112 |
| garmin_summary.db | months_summary | 20 |
| garmin_summary.db | years_summary | 3 |
