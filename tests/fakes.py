class FakeHasher(object):
    def __init__(self):
        self.file_paths = {}
    def __call__(self, file_path):
        return self.file_paths.get(file_path, 0)
    def change_file(self, file_path):
        self.file_paths[file_path] = self.file_paths.get(file_path, 0) + 1

class FakeErrorHasher(object):
    def __call__(self, path):
        raise IOError(
            "OSError: [Errno 2] No such file or directory: '%s'" %
            path
        )
        
