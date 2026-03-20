import py_compile
files = ['database/database.py', 'main.py', 'views/medicao.py']
for f in files:
    try:
        py_compile.compile(f, doraise=True)
        print(f + ' ok')
    except Exception as e:
        print(f + ' error ' + str(e))
