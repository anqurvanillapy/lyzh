import sys

import lyzh.parsing as parsing
import lyzh.surf as surf
import lyzh.conc.resolve as resolve

try:
    _, file, *_ = sys.argv
except ValueError:
    print("usage: lyzh FILE")
    sys.exit(1)

try:
    defs = surf.parse_file(file)
except parsing.Error as e:
    print(f"{file}:{e}")
    sys.exit(1)
except FileNotFoundError as e:
    print(e)
    sys.exit(1)

try:
    print(resolve.Resolver().resolve(defs))
except resolve.Error as e:
    print(f"{file}:{e}")
    sys.exit(1)
