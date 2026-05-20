import zipfile

z = zipfile.ZipFile('/tmp/app.zip')
items = sorted([(i.compress_size, i.filename) for i in z.infolist()], reverse=True)
total = sum(s for s, _ in items)

print("=== TOP 30 ARQUIVOS MAIORES (comprimido) ===")
print("Total app.zip: %.1f MB\n" % (total/1024/1024))
for size, name in items[:30]:
    print("%6.1f MB  %s" % (size/1024/1024, name))

print("\n=== ESTRUTURA RAIZ ===")
roots = {}
for size, name in items:
    parts = name.split('/')
    root = parts[0]
    roots[root] = roots.get(root, 0) + size
for r, s in sorted(roots.items(), key=lambda x: -x[1])[:10]:
    print("%6.1f MB  %s" % (s/1024/1024, r))

# Nível 2 do maior diretório raiz
biggest_root = max(roots, key=lambda x: roots[x])
print("\n=== SUBDIRS DE '%s' ===" % biggest_root)
sub = {}
for size, name in items:
    if name.startswith(biggest_root + '/'):
        rest = name[len(biggest_root)+1:]
        parts = rest.split('/')
        key = parts[0] if parts else '.'
        sub[key] = sub.get(key, 0) + size
for k, s in sorted(sub.items(), key=lambda x: -x[1])[:30]:
    print("%6.1f MB  %s" % (s/1024/1024, k))
