import pickle   # nosec


def to_file(obj, path):
    with open(path, 'wb') as writer:
        pickle.dump(obj, writer)    # nosec


def from_file(path):
    with open(path, 'rb') as reader:
        return pickle.load(reader)  # nosec
