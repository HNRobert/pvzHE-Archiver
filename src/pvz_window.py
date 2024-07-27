import ctypes
import ctypes.wintypes

import win32con
import win32gui
import win32process

# Const
PROCESS_ALL_ACCESS = (0x000F0000 | 0x00100000 | 0xFFF)
MEM_COMMIT = 0x00001000
PAGE_EXECUTE_READWRITE = 0x40

# Load necessary functions from kernel32.dll
VirtualAllocEx = ctypes.windll.kernel32.VirtualAllocEx
WriteProcessMemory = ctypes.windll.kernel32.WriteProcessMemory
CreateRemoteThread = ctypes.windll.kernel32.CreateRemoteThread
WaitForSingleObject = ctypes.windll.kernel32.WaitForSingleObject
CloseHandle = ctypes.windll.kernel32.CloseHandle


def generate_save():
    pid = find_target_pid()
    if not pid:
        return None
    
    process_handle = get_process_handle(pid)

    if process_handle:
        result = _call_save(process_handle)
        print("Call save successful:", result)
        ctypes.windll.kernel32.CloseHandle(process_handle)
    else:
        print("Failed to obtain process handle")
    return result
    

def _call_save(process_handle):
    try:
        # Allocate memory in the game process
        mem_address = ctypes.windll.kernel32.VirtualAllocEx(
            process_handle, 0, 1024, win32con.MEM_COMMIT, win32con.PAGE_EXECUTE_READWRITE)
        if mem_address == 0:
            print("1")
            return False  # Failed to allocate memory

        # Prepare the assembly code
        code = bytearray([
            0x8B, 0x0D, 0xC0, 0x9E, 0x6A, 0x00,  # mov ecx, [0x006A9EC0]
            0x8B, 0x89, 0x68, 0x07, 0x00, 0x00,  # mov ecx, [ecx+0x768]
            0x51,                                # push ecx
            0xE8, 0x00, 0x00, 0x00, 0x00,        # call 0x408C30
            0xC3                                 # ret
        ])

        # Calculate the relative address for the call instruction
        call_address = 0x408C30 - (mem_address + 14) - 5
        code[14:18] = call_address.to_bytes(4, byteorder='little', signed=True)

        # Write the code to the allocated memory
        ctypes.windll.kernel32.WriteProcessMemory(
            process_handle, mem_address, bytes(code), len(code), 0)

        # Create a remote thread to execute the code
        thread_handle = ctypes.windll.kernel32.CreateRemoteThread(
            process_handle, None, 0, mem_address, None, 0, None)
        if thread_handle == 0:
            print("2")
            return False  # Failed to create remote thread

        # Wait for the thread to finish
        ctypes.windll.kernel32.WaitForSingleObject(thread_handle, 0xFFFFFFFF)

        # Clean up
        ctypes.windll.kernel32.CloseHandle(thread_handle)
        ctypes.windll.kernel32.VirtualFreeEx(
            process_handle, mem_address, 0, win32con.MEM_RELEASE)

        return True  # Call successful

    except TypeError:
        return False  # Other problems occurred

    finally:
        ctypes.windll.kernel32.CloseHandle(process_handle)

def get_process_handle(pid):
    PROCESS_ALL_ACCESS = 0x1F0FFF
    return ctypes.windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)


def enum_windows_callback(hwnd, pid_list):
    # 获取窗口标题
    length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
    if length > 0:
        title = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, title, length + 1)
        title = title.value
        target_text = ["pvz", "植物大战僵尸"]
        exclude_text = ["pvzHE-Archiver", "植物大战僵尸杂交版-存档管理工具"]

        # 检查标题是否包含目标关键词
        if any(_text in title for _text in target_text) and not(title in exclude_text):
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            pid_list.append((pid, title))

    return True


def find_target_pid():
    pid_list = []
    win32gui.EnumWindows(enum_windows_callback, pid_list)
    print(pid_list)
    return pid_list[0][0] if pid_list else None
