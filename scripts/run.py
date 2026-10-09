import sys

sys.path.insert(0, "src")
from jobfeed.sources import acme, beta  # noqa: E402

SOURCES = {"acme": acme, "beta": beta}

path, name = sys.argv[1], sys.argv[2]
jobs = SOURCES[name].parse_file(path)
print(f"{name}: {len(jobs)} jobs")
for job in jobs[:3]:
    print(" ", job)
