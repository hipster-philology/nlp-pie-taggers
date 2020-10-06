import hashlib
from typing import Dict, Tuple, List
from collections import namedtuple, defaultdict
import csv

FileChecksum = namedtuple(
    "FileChecksum",
    # checksum, source_file and source_checksum are optional.
    field_names=("checksum", "source", "source_checksum"),
)
ModifiedFiles = namedtuple(
    "ModifiedFiles",
    field_names=["filename", "is_source", "checksum"]
)
FileList = List[str]


def md5sum(filename: str, blocksize: int = 65536) -> str:
    """ Compute the checksum of {filename} in chunks of {blocksize} bits

    :param filename: Filename
    :param blocksize: Size (in bits) for blocks [Avoid memory error]
    :return: Checksum as strin

    >>> md5sum("tests/test_checksum/file1.txt")
    'de0fa52e7c33b285257b47ff21e7b2f8'

    >>> md5sum("tests/test_checksum/file2.txt", blocksize=128)
    '7cbcc25fca397efe06506a1dc0d55a9e'

    """
    _hash = hashlib.md5()
    with open(filename, "rb") as f:
        for block in iter(lambda: f.read(blocksize), b""):
            _hash.update(block)
    return _hash.hexdigest()


def check_md5sum(filenames: Dict[str, str], blocksize: int = 65536) -> Dict[str, Tuple[str, bool]]:
    """ Compute the checksum of {filename} in chunks of {blocksize} bits

    :param filenames: Dictionary of filenames -> Checksum
    :param blocksize: Size (in bits) for blocks [Avoid memory error]
    :return: Dictionary(Filepath -> (New Hash, Bool of status if changed hash))

    >>> check_md5sum({"tests/test_checksum/file1.txt": 'de0fa52e7c33b285257b47ff21e7b2f8'})
    {'tests/test_checksum/file1.txt': ('de0fa52e7c33b285257b47ff21e7b2f8', True)}

    >>> check_md5sum({"tests/test_checksum/file2.txt": "not_the_right_checksum"})
    {'tests/test_checksum/file2.txt': ('7cbcc25fca397efe06506a1dc0d55a9e', False)}

    """
    out = {}
    for file, _hash in filenames.items():
        new_hash = md5sum(file, blocksize=blocksize)
        out[file] = (new_hash, new_hash == _hash)
    return out


def read_checksum_csv(filepath: str) -> Dict[str, FileChecksum]:
    """ Read the file at {filepath} and parse its content.

    :param filepath: CSV containing at least a key `input` but additionaly checksum, source and source_checksum
    :return: Parsed content as a dict with FileChecksum information

    >>> checksums = read_checksum_csv("tests/test_checksum/checksums.csv")
    >>> checksums["tests/test_checksum/file1.txt"] == FileChecksum(
    ...     checksum="de0fa52e7c33b285257b47ff21e7b2f8", source=None, source_checksum=None)
    True
    >>> checksums["tests/test_checksum/file2.txt"] == FileChecksum(
    ...     checksum="fake_checksum",
    ...     source="tests/test_checksum/source2.txt", source_checksum="c7289364c9c6fcd3c5e6974edfd3abb7")
    True

    """
    out = {}
    with open(filepath) as f:
        reader = csv.DictReader(f)
        for line in reader:
            out[line["input"]] = FileChecksum(
                checksum=line.get("checksum"),
                source=line.get("source"),
                source_checksum=line.get("source_checksum")
            )
    return out


def check_checksum_from_file(filepath) -> Tuple[FileList, FileList]:
    """ Given a CSV of input and input's source file, track files which needs relemmatization.

    :param filepath: CSV containing at least a key `input` but additionaly checksum, source and source_checksum
    :return: (List of file needing relemmatization, List of sources which changed)

    >>> check_checksum_from_file("./tests/test_checksum/checksums.csv")
    (['tests/test_checksum/file2.txt', 'tests/test_checksum/file3.txt'], \
['tests/test_checksum/source3.txt'])

    """
    checksum_dict = read_checksum_csv(filepath)
    sources: Dict[str, str] = {}
    inputs: Dict[str, str] = {}
    source_to_input: Dict[str, List[str]] = defaultdict(list)  # Source filepath to input filepath map
    for filepath, filechecksum in checksum_dict.items():
        # Register the plain-text file itself
        inputs[filepath] = filechecksum.checksum

        # Register its source and map it to the plain-text file
        #    one source can create multiple files, so we have a list there.

        if filechecksum.source:
            sources[filechecksum.source] = filechecksum.source_checksum
            source_to_input[filechecksum.source].append(filepath)

    inputs: Dict[str, Tuple[str, bool]] = check_md5sum(inputs)
    sources: Dict[str, Tuple[str, bool]] = check_md5sum(sources)

    need_relemmatization: List[str] = []
    changed_sources: List[str] = []

    # Check sources files then
    for source_file, (_, status) in sources.items():
        if not status:
            need_relemmatization.extend(source_to_input[source_file])
            changed_sources.append(source_file)

    # Check plain-text files first
    for input_file, (_, status) in inputs.items():
        # Only add it if it was not already necessary because of source_file
        if input_file not in need_relemmatization and not status:
            need_relemmatization.append(input_file)

    return sorted(need_relemmatization), sorted(changed_sources)


def write_csv_checksums(filepath: str, lemmatized_files: List[str], _write=True, update_source=False,
                        ) -> Tuple[List[List[str]], List[ModifiedFiles]]:
    """

    :param filepath: CSV file containing the map
    :param lemmatized_files: File which have been lemmatized
    :param update_source: Update the source hash
    :param _write: Whether to write or not
    :return: CSV content as well as the list of modified files and their type

    >>> write_csv_checksums("./tests/test_checksum/checksums.csv", ['tests/test_checksum/file2.txt'], _write=False) == (
    ...     [
    ...         ['input', 'checksum', 'source', 'source_checksum'],
    ...         ['tests/test_checksum/file1.txt', 'de0fa52e7c33b285257b47ff21e7b2f8', '', ''],
    ...         ['tests/test_checksum/file2.txt', '7cbcc25fca397efe06506a1dc0d55a9e',
    ...             'tests/test_checksum/source2.txt', 'c7289364c9c6fcd3c5e6974edfd3abb7'],
    ...         ['tests/test_checksum/file3.txt', 'ed7c77f2ed00549a0219525d120a72be',
    ...             'tests/test_checksum/source3.txt', 'fake_checksum']
    ...     ],
    ...     [
    ...        ModifiedFiles('tests/test_checksum/file2.txt', checksum='7cbcc25fca397efe06506a1dc0d55a9e',
    ...            is_source=False),
    ...        ModifiedFiles('tests/test_checksum/source3.txt', checksum='d8203a2bd71947993eb72826b08eb11d',
    ...            is_source=True)
    ...     ]
    ... )
    True

    """
    checksum_dict = read_checksum_csv(filepath)
    rows = [
        ["input", "checksum", "source", "source_checksum"]
    ]
    modified_files = []
    sources_checksums: Dict[str, str] = {}
    for file, checksum in checksum_dict.items():
        # If we did not relemmatize, plainly add it to the new file
        if file not in lemmatized_files:
            _hash = checksum.checksum
        else:
            _hash = md5sum(file)
            modified_files.append(ModifiedFiles(
                filename=file,
                is_source=False,
                checksum=_hash
            ))

        source_hash = None
        if checksum.source:
            if checksum.source in sources_checksums:
                source_hash = sources_checksums[checksum.source]
            else:
                source_hash = sources_checksums[checksum.source] = md5sum(checksum.source)
                if checksum.source_checksum != source_hash:
                    modified_files.append(ModifiedFiles(
                        filename=checksum.source,
                        is_source=True,
                        checksum=source_hash
                    ))

        new_source_checksum = checksum.source_checksum
        if update_source:
            new_source_checksum = source_hash

        rows.append([
            file, _hash,
            checksum.source or "",
            new_source_checksum or ""
        ])

    if _write:
        with open(filepath, "w") as f:
            writer = csv.writer(f)
            writer.writerows(rows)
    return rows, modified_files
