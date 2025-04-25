import os
import sys
import ctypes
import subprocess
import time
import shutil
import glob

# --- 配置 ---
SHOW_DELETED_FILES = True # 设置为 True 以显示正在删除的文件名，False 则只显示计数

def is_admin():
    """检查当前用户是否具有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def clear_screen():
    """清空控制台屏幕"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_large_title(title):
    """打印放大的标题"""
    clear_screen()
    width = 60
    print("\n" * 2) # 增加顶部空间
    print("  " + "#" * width)
    print("  #" + " " * (width - 2) + "#")
    # 计算标题居中所需的空格
    padding = (width - 2 - len(title.encode('gbk')) // 2 * 2) // 2 # GBK编码下中文占2字节
    print("  #" + " " * padding + title + " " * (width - 2 - padding - len(title.encode('gbk'))) + "#")
    print("  #" + " " * (width - 2) + "#")
    print("  " + "#" * width)
    print("\n" * 2) # 增加底部空间

def print_separator(char="=", length=60):
    """打印分隔线"""
    print(f"  {char * length}")

def print_step(step_num, total_steps, message):
    """打印步骤标题"""
    print_separator()
    print(f"  ---=== 步骤 {step_num}/{total_steps} ===---")
    print(f"  [*] {message}")
    print_separator()

def print_success(message):
    """打印成功信息"""
    print(f"\n  [√] {message}")

def print_info(message):
     """打印提示信息"""
     print(f"  [i] {message}")

def print_warning(message):
     """打印警告/注意信息"""
     print(f"  [!] {message}")

def print_error(message):
     """打印错误信息"""
     print(f"  [X] {message}")

def pause_briefly(seconds=1.5):
    """短暂暂停"""
    time.sleep(seconds)

def delete_item(item_path):
    """尝试删除单个文件或文件夹，返回 True 如果成功"""
    try:
        if os.path.isfile(item_path) or os.path.islink(item_path):
            os.remove(item_path)
            return True
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path, ignore_errors=True) # 忽略删除子目录时的错误
            return True
    except OSError:
        pass # 忽略错误
    return False

def clean_folder_contents(folder_path):
    """清理指定文件夹的内容，显示进度"""
    deleted_files = 0
    deleted_folders = 0
    errors = 0
    items_to_process = list(glob.glob(os.path.join(folder_path, '*'), recursive=False))
    total_items = len(items_to_process)
    count = 0

    if total_items == 0:
        print_info("文件夹为空或无内容可清理。")
        return deleted_files, deleted_folders, errors

    print_info(f"扫描到 {total_items} 个项目...")

    for item_path in items_to_process:
        count += 1
        base_name = os.path.basename(item_path)
        # 使用 \r 覆盖当前行来显示进度
        progress_text = f"  处理中 ({count}/{total_items}): {base_name[:40]}{'...' if len(base_name) > 40 else ''}"
        sys.stdout.write('\r' + progress_text + ' ' * (70 - len(progress_text))) # 清除旧内容
        sys.stdout.flush()

        is_dir = os.path.isdir(item_path)
        if delete_item(item_path):
            if is_dir:
                deleted_folders += 1
            else:
                deleted_files += 1
        else:
            errors += 1

    # 清理最后一行进度显示
    sys.stdout.write('\r' + ' ' * 70 + '\r')
    sys.stdout.flush()

    print_info(f"尝试删除 {deleted_files} 个文件, {deleted_folders} 个文件夹。")
    if errors > 0:
        print_warning(f"清理过程中遇到 {errors} 个错误 (可能是文件被占用)。")
    return deleted_files, deleted_folders, errors


def clean_temp_folders():
    """清理临时文件夹"""
    temp_folders = []
    user_temp = os.environ.get('TEMP')
    if user_temp and os.path.isdir(user_temp):
        temp_folders.append(user_temp)
    else:
         print_warning("未能获取用户 TEMP 环境变量。")

    windows_temp = r'C:\Windows\Temp'
    if os.path.isdir(windows_temp):
        temp_folders.append(windows_temp)
    else:
        print_warning(f"系统临时目录 {windows_temp} 不存在。")

    total_df, total_dd, total_e = 0, 0, 0
    for folder in temp_folders:
        print_info(f"\n---=== 清理目标: {folder} ===---")
        df, dd, e = clean_folder_contents(folder)
        total_df += df
        total_dd += dd
        total_e += e

    print_info("临时文件清理小结完成。")
    return total_df, total_dd, total_e


def clean_windows_update_cache():
    """清理 Windows 更新缓存"""
    cache_folder = r'C:\Windows\SoftwareDistribution'
    print_info(f"\n---=== 清理目标: {cache_folder} ===---")
    if not os.path.isdir(cache_folder):
        print_warning(f"更新缓存文件夹 {cache_folder} 不存在。")
        return 0, 0, 0

    # 停止 Windows Update 服务
    print_info("正在尝试停止 Windows Update 服务 (wuauserv)...")
    try:
        subprocess.run(['net', 'stop', 'wuauserv'], check=True, capture_output=True, timeout=30)
        print_info("服务已停止。")
    except subprocess.TimeoutExpired:
        print_error("停止服务超时！")
        return 0, 0, 1 # 标记为错误
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print_warning(f"停止服务失败 (可能已停止或权限不足)。")
        # 即使停止失败也尝试清理

    # 清理缓存文件夹内容
    df, dd, e = clean_folder_contents(cache_folder)

    # 启动 Windows Update 服务
    print_info("\n正在尝试启动 Windows Update 服务 (wuauserv)...")
    try:
        subprocess.run(['net', 'start', 'wuauserv'], check=True, capture_output=True, timeout=30)
        print_info("服务已启动。")
    except subprocess.TimeoutExpired:
         print_error("启动服务超时！")
         e += 1 # 标记为错误
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print_warning(f"启动服务失败 (可能已有其他进程启动或出现错误)。")

    print_info("Windows 更新缓存清理小结完成。")
    return df, dd, e

def clear_recycle_bin():
    """清空回收站 (使用 PowerShell 命令)"""
    print_info("正在尝试使用 PowerShell 清空回收站...")
    try:
        process = subprocess.run(
            ['powershell', '-Command', 'Clear-RecycleBin -Force -ErrorAction SilentlyContinue'],
            capture_output=True, text=True, check=False, encoding='gbk', errors='ignore', timeout=60
        )
        if process.returncode != 0:
            # 不再细分错误，因为各种情况都可能发生
            print_warning(f"清空回收站命令执行完毕，但返回代码非零 ({process.returncode})。")
            if process.stderr:
                print_warning(f"PowerShell 错误信息: {process.stderr.strip()}")
        else:
            print_info("清空回收站命令已成功执行。")
    except subprocess.TimeoutExpired:
        print_error("清空回收站超时！")
    except FileNotFoundError:
        print_error("无法执行 PowerShell 命令，请确保 PowerShell 可用。")
    except Exception as e:
        print_error(f"清空回收站时发生异常: {e}")

def run_disk_cleanup():
    """启动 Windows 磁盘清理工具"""
    print_info("正在启动 Windows 磁盘清理工具 (cleanmgr.exe)...")
    try:
        subprocess.Popen(['cleanmgr.exe', '/d', 'C:'])
        print_info("Windows 磁盘清理工具已启动，请在弹出窗口中操作。")
    except FileNotFoundError:
        print_error("无法启动 cleanmgr.exe，请检查文件是否存在。")
    except Exception as e:
        print_error(f"启动磁盘清理时发生异常: {e}")


# --- 主程序 ---
if __name__ == "__main__":
    if os.name == 'nt':
        os.system("title C盘清理工具 v1.2 (Python增强版)") # 设置标题

    # 强制使用 GBK 编码输出，以配合 chcp 936
    # sys.stdout.reconfigure(encoding='gbk', errors='ignore')
    # sys.stderr.reconfigure(encoding='gbk', errors='ignore') # 可能在某些环境下导致问题，暂时注释

    print_large_title("欢迎使用 C盘清理工具 (Python增强版)")
    print("  正在初始化并检查权限...")

    # 1. 检查管理员权限
    if not is_admin():
        clear_screen()
        print_large_title("!!! 权限错误 !!!")
        print_error("      请以管理员身份运行此脚本！")
        print("\n  操作方法：")
        print("  1. 关闭此窗口。")
        print("  2. 右键点击用于启动此脚本的 .bat 文件。")
        print("  3. 选择 “以管理员身份运行”。")
        print("\n  或者：")
        print("  1. 以管理员身份打开 CMD 或 PowerShell。")
        print(f"  2. 输入 python \"{os.path.abspath(__file__)}\" 并回车。")
        print_separator()
        input("\n  按 Enter 键退出...")
        sys.exit(1)

    print("  [√] 已获取管理员权限，清理即将开始...")
    pause_briefly(2) # 给用户时间看提示

    # --- 开始清理 ---
    print_large_title("开始执行清理任务")

    # 步骤 1: 清理临时文件
    print_step(1, 4, "清理系统和用户临时文件")
    clean_temp_folders()
    print_success("临时文件清理完成。")
    pause_briefly()

    # 步骤 2: 清理 Windows 更新缓存
    print_step(2, 4, "清理 Windows 更新缓存")
    clean_windows_update_cache()
    print_success("Windows 更新缓存清理完成。")
    pause_briefly()

    # 步骤 3: 清空回收站
    print_step(3, 4, "清空回收站")
    clear_recycle_bin()
    print_success("回收站清空操作已执行。")
    pause_briefly()

    # 步骤 4: 启动 Windows 磁盘清理工具
    print_step(4, 4, "启动 Windows 磁盘清理工具")
    print_warning("请在弹出的 Windows 磁盘清理窗口中手动选择要清理的项目，")
    print_warning("然后点击 \"确定\" 开始清理。")
    input("\n  按 Enter 键以启动磁盘清理工具...")
    run_disk_cleanup()
    print_separator()
    pause_briefly()


    # --- 结束 ---
    print_large_title("所有清理操作已启动/完成")
    print("  ║  请检查 Windows 磁盘清理工具是否仍在运行，       ║")
    print("  ║  并等待其完成（如果需要）。                      ║")
    print("  ║                                                  ║")
    print("  ==================================================")
    input("\n  感谢使用！按 Enter 键退出程序...")
    sys.exit(0)
