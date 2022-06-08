from pathlib import Path
import fcntl


class Lock:
    def __init__(self, file):
        self.file = file

    def __enter__(self):
        fcntl.lockf(self.file, fcntl.LOCK_EX)

    def __exit__(self, exc_type, exc_value, traceback):
        fcntl.lockf(self.file, fcntl.LOCK_UN)


file_path = Path('convergence.txt').with_suffix('.dat')
file_path.touch(exist_ok=True)


if file_path.stat().st_size == 0:
    header = '# Convergence file\n'
    header += '#label num_nodes num_elems time_step ERROR\n'
    with open(file_path, 'w') as file:
        file.write(header)


with open(file_path, 'a') as file:
    with Lock(file):
        file.write('gj 300 150 1e-3 2.368e-1\n')

