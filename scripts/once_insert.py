import sqlite3

db_path = "../userdata/events_data_1021.db"  # 或你的 PM.get_env("EVENTS_DBNEW_PATH")
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# 检查是否已存在列
cur.execute("PRAGMA table_info(events)")
columns = [col[1] for col in cur.fetchall()]


to_add = {"ner_extract":None,
        "schema_version":1}


for key, value in to_add.items():
    if key not in columns:
        cur.execute(f"ALTER TABLE events ADD COLUMN {key} INTEGER DEFAULT {value};")
        conn.commit()
        print(f"✅ 已新增字段 {key}，默认值为 {value}。")
    else:
        print(f"⚠️ 字段 {key} 已存在，无需新增。")

conn.close()
