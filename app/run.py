import os
import sys

# Указываем путь к проекту
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

print("🚀 Запуск")
print("📁 Директория проекта:", project_dir)

# Проверяем наличие файлов
required_files = [
    "main.py",
    "models.py",
    "schemas.py",
    "database.py",
    "crud.py",
    "config.py",
    "RSA_fast.py",
    "templates",
    "static/css"
]

for file in required_files:
    path = os.path.join(project_dir, file)
    if os.path.exists(path):
        print(f"✅ {file}")
    else:
        print(f"❌ {file} - НЕ НАЙДЕН")

print("\n" + "="*50)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)