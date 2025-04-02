import pandas as pd

# 读取两个Excel文件
df_volcano = pd.read_excel("火山-豆包语音大模型音色列表.xlsx")
df_info = pd.read_excel("音色信息.xlsx")

# 清理音色名称中的干扰字符（如括号和空格）
df_volcano["清理后名称"] = df_volcano["音色名称"].str.replace(r"（.*）", "", regex=True).str.strip()
df_info["清理后名称"] = df_info["音色名称"].str.replace(r'[\U0001F300-\U0001F9FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\u2600-\u26FF\u2700-\u27BF]', '', regex=True).str.strip()

# 合并数据，匹配头像URL
merged = pd.merge(
    df_volcano,
    df_info[["清理后名称", "头像url"]],
    on="清理后名称",
    how="left"
)

# 填充到火山头像url列
df_volcano["火山头像url"] = merged["头像url"]

# 保存结果
df_volcano.to_excel("火山-豆包语音大模型音色列表_带头像.xlsx", index=False)
print("处理完成！已保存为新文件。")