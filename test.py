import sys
import pathlib

for path in sys.path:
    p_path = pathlib.Path(path)
    print(f'{path} {" Exists" if p_path.exists() else " Does NOT exist"}')
    r_path = path + "\\"
    for token in p_path.rglob("logging_helper.py"):
        python_file = str(token)
        tgt_module = python_file.replace(r_path,"").replace("\\",".")
        print(f'  {tgt_module}')