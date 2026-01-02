# scripts/scripts.py
import os
import sys
from pathlib import Path
from typing import Any, Dict
from dotenv import load_dotenv

import django
from django.core.management import execute_from_command_line


def createdatabase() -> None:
    """创建数据库"""

    print("ℹ️ 检查数据库是否存在")
    try:
        import psycopg
        from psycopg import sql

        # 从 Django 配置获取数据库配置
        db_name: str = f"{os.environ.get('DATABASE_NAME')}"
        # 首先连接到 postgres 数据库来检查目标数据库是否存在
        conn_params: Dict[str, Any] = {
            "dbname": "postgres",
            "user": f"{os.environ.get('DATABASE_USER')}",
            "password": f"{os.environ.get('DATABASE_PASSWORD')}",
            "host": f"{os.environ.get('DATABASE_HOST')}",
            "port": f"{os.environ.get('DATABASE_PORT')}",
        }
        try:
            # 尝试连接到 postgres 数据库, 并设置自动提交
            with psycopg.connect(**conn_params, autocommit=True) as conn:
                with conn.cursor() as cur:
                    # 检查目标数据库是否存在
                    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
                    exists = cur.fetchone()
                    if not exists:
                        print(f"ℹ️ 开始创建数据库: {db_name}")
                        # 创建数据库
                        query = sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name))
                        cur.execute(query)
                        print("✅ 数据库创建成功")
                    else:
                        print("⚠️ 数据库已存在")
        except psycopg.Error as e:
            print(f"❌ 数据库连接/创建失败: {e}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ 检查/创建数据库时发生错误: {e}")
        sys.exit(1)


def migrate() -> None:
    """数据库迁移"""

    print("ℹ️ 开始数据库迁移")
    try:
        # 检查迁移
        execute_from_command_line(
            [
                "manage.py",
                "makemigrations",
            ]
        )
        # 执行迁移
        execute_from_command_line(
            [
                "manage.py",
                "migrate",
            ]
        )
        print("✅ 数据库迁移完成")
    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        sys.exit(1)


def createsuperuser() -> None:
    """创建超级用户"""

    print("ℹ️ 开始创建超级用户")
    try:
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import AbstractUser

        User: type[AbstractUser] = get_user_model()
        # 检查是否已存在超级用户
        if not User.objects.filter(is_superuser=True).exists():
            execute_from_command_line(
                [
                    "manage.py",
                    "createsuperuser",
                    "--username",
                    f"{os.environ.get('DJANGO_SUPERUSER_USERNAME')}",
                    "--email",
                    f"{os.environ.get('DJANGO_SUPERUSER_EMAIL')}",
                    "--noinput",
                ]
            )
            print("✅ 超级用户创建完成")
        else:
            print("⚠️ 超级用户已存在")
    except Exception as e:
        print(f"❌ 创建超级用户失败: {e}")
        sys.exit(1)


def initdatabase() -> None:
    """初始化数据库"""

    print("ℹ️ 开始初始化数据库")
    try:
        createdatabase()
        migrate()
        createsuperuser()
        print("✅ 数据库初始化完成")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        sys.exit(1)


def runserver() -> None:
    """启动开发服务器"""

    print("ℹ️ 开始启动开发服务器")
    try:
        execute_from_command_line(
            [
                "manage.py",
                "runserver",
                "0.0.0.0:30001",
            ]
        )
    except Exception as e:
        print(f"❌ 启动开发服务器失败: {e}")
        sys.exit(1)


def startapp(app_name: str) -> None:
    """创建新的 Django 应用"""

    print(f"ℹ️ 开始创建 {app_name} 应用")
    try:
        execute_from_command_line(
            [
                "manage.py",
                "startapp",
                app_name,
                "--template=./templates/app_template",
            ]
        )
        print(f"✅ 应用 {app_name} 创建完成")
    except Exception as e:
        print(f"❌ 创建应用 {app_name} 失败: {e}")
        sys.exit(1)


def test() -> None:
    """运行测试"""

    print("ℹ️ 开始运行测试")
    try:
        execute_from_command_line(
            [
                "manage.py",
                "test",
            ]
        )
        print("✅ 测试运行完成")
    except Exception as e:
        print(f"❌ 测试运行失败: {e}")
        sys.exit(1)


def collectstatic() -> None:
    """收集静态文件"""

    print("ℹ️ 开始收集静态文件")
    try:
        execute_from_command_line(
            [
                "manage.py",
                "collectstatic",
                "--clear",
                "--noinput",
            ]
        )
        print("✅ 静态文件收集完成")
    except Exception as e:
        print(f"❌ 静态文件收集失败: {e}")
        sys.exit(1)


def exportopenapi() -> None:
    print("ℹ️ 开始导出 openapi 文件")
    try:
        execute_from_command_line(
            [
                "manage.py",
                "export_openapi_schema",
                "--indent",
                "2",
                "--sorted",
                "--output",
                "./../frontend/src/lib/api/backend-api.json",
            ]
        )
        print("✅ 静态文件收集完成")
    except Exception as e:
        print(f"❌ 静态文件收集失败: {e}")
        sys.exit(1)


def main() -> None:
    # 添加项目根目录到 Python 路径
    sys.path.insert(0, str(Path(__file__).parent.parent))
    # 设置 Django 环境变量
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
    # 初始化 Django
    django.setup()
    # 解析命令行参数并执行对应函数
    if len(sys.argv) < 2:
        print("请指定要执行的函数名")
        sys.exit(1)
    function_name: str = sys.argv[1]
    if function_name == "migrate":
        migrate()
    elif function_name == "createsuperuser":
        createsuperuser()
    elif function_name == "initdatabase":
        initdatabase()
    elif function_name == "runserver":
        runserver()
    elif function_name == "startapp":
        if len(sys.argv) < 3:
            print("请指定应用名称")
            sys.exit(1)
        startapp(sys.argv[2])
    elif function_name == "test":
        test()
    elif function_name == "collectstatic":
        collectstatic()
    elif function_name == "exportopenapi":
        exportopenapi()
    else:
        print(f"未知函数: {function_name}")
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv()
    main()
