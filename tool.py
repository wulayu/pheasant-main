import os


def get_files(path, rule):
    all = []
    for fpathe, dirs, fs in os.walk(path):  # os.walk获取所有的目录
        for f in fs:
            if f.endswith(rule):
                if "background" not in f or "thumbnail" not in f:
                    all.append(f)
    return all


if __name__ == "__main__":
    b = get_files(path='templates', rule=".jpg")
    for i in b:
        print(i)
