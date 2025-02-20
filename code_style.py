import subprocess
import os

def run_command(command):
    """Функция для выполнения команды в командной строке"""
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    print(stderr.decode(errors='ignore'))
    if stderr:
        print(stderr.decode(errors='ignore'))

def main():
    if not os.path.exists("env"):
        print("Создаю виртуальное окружение...")
        run_command("python -m venv env")
        run_command(".\\env\\Scripts\\activate && pip install -r requirements.txt")

    print("Сортировка импортов...")
    run_command(".\\env\\Scripts\\activate && .\\env\\Scripts\\isort .")

    print("Применение стиля кода...")
    run_command(".\\env\\Scripts\\activate && .\\env\\Scripts\\black --line-length 100 --skip-string-normalization --exclude ./env/ .")

    print("Проверка на ошибки стиля...")
    run_command(".\\env\\Scripts\\activate && .\\env\\Scripts\\flake8 --exclude=env/ . | findstr /v E501 | findstr /v E731")

if __name__ == "__main__":
    main()