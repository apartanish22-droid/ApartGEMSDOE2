#!/usr/bin/env python3
"""Package static Pages files at both / and /docs/ for legacy-source compatibility."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def package(root: Path) -> Path:
    source = root / 'docs'
    cache = root / '.cache'
    dest = cache / 'pages-artifact'
    if not source.is_dir() or source.is_symlink() or cache.is_symlink() or dest.is_symlink():
        raise ValueError('Unsafe or missing Pages source/cache')
    if any(path.is_symlink() for path in source.rglob('*')):
        raise ValueError('Pages source must not contain symlinks')
    cache.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        if not dest.is_dir():
            raise ValueError('Pages artifact destination is not a directory')
        shutil.rmtree(dest)  # fixed scratch path under the repo's excluded .cache
    shutil.copytree(source, dest)
    shutil.copytree(source, dest / 'docs')
    return dest


if __name__ == '__main__':
    output = package(ROOT)
    print(f'Packaged identical static routes at {output} and {output / "docs"}.')
