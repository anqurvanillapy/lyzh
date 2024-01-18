import sys

import lyzh.parsing as parsing
import lyzh.surf as surf

try:
    _, file, *_ = sys.argv
except ValueError:
    print("usage: lyzh FILE")
    sys.exit(1)

try:
    print(surf.parse_file(file))
except parsing.Error as e:
    print(f"{file}:{e}")
    sys.exit(1)
