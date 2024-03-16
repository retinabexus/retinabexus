import re

__all__ = [
    "GitVersion"
]


def parse(version):
    """
    Parse a version string and return either a :class:`GitVersion` object
    or throw an exception
    """
    return GitVersion(version)


class InvalidVersion(ValueError):
    """
    An invalid version was found, users should only pass in the output
    of a 'git describe' command
    """


class GitVersion(object):
    """
    Represents a version string generated by git. This string will be in the format
    v<marketing>.<major>.<minor>(-dev)
    where marjeting, major, and minor are integers and dev is an optional string
    that is only present for non-release builds.

    The marketing, major, and minor components are separated out and stored in
    appropriately named properties. The remaining parts of the string are combined
    in to the dev string property. In practice this string will consist of a leading
    'v' characters, plus whatever characters trailed the minor number. The devstring
    property will therefore always contain at least 1 character, a minimum of the
    leading 'v'. If the devstring contains /only/ a 'v' the version string is not
    considered to be a development build, but if the dev string is any longer
    the build is a development build and the 'isdev' property will return True.
    """

    def __hash__(self):
        return hash(self._key)

    def __lt__(self, other):
        return self._compare(other) < 0

    def __le__(self, other):
        return self._compare(other) <= 0

    def __eq__(self, other):
        return self._compare(other) == 0

    def __ge__(self, other):
        return self._compare(other) >= 0

    def __gt__(self, other):
        return self._compare(other) > 0

    def __ne__(self, other):
        return self._compare(other) != 0

    def _compare(self, other):
        if not isinstance(other, GitVersion):
            return NotImplemented

        if self.marketing != other.marketing:
            return self.marketing - other.marketing

        if self.major != other.major:
            return self.major - other.major

        return self.minor - other.minor

    def __str__(self):
        return self._version

    def __repr__(self):
        return "<GitVersion({0})>".format(self._version)

    def compare_dev_string(self, other):
        return self.devstring.compare(other.devstring)

    def _is_dev(self):
        """
        A dev string of consisting of a single 'v' character is not considered to be
        a development version. Due to the way we parse strings (see class description above)
        the leading and trailing characters of the input string are combined in to this 'dev string'.
        Our tagging stragegy means that releases are tagged with a leading 'v' (for example v2.2.17)
        which in turn means a release tag will end up leaving a single 'v' character in this devstring
        property. We just ignore this special case and don't consider it to be a development version
        """
        return len(self.devstring) > 0 and self.devstring != 'v'

    @property
    def marketing(self):
        return self._marketing

    @property
    def major(self):
        return self._major

    @property
    def minor(self):
        return self._minor

    @property
    def devstring(self):
        return self._devstring

    @property
    def isdev(self):
        return self._is_dev()

    """
    This regex separates out components of the input string into regex match groups. The components are

    leader - Any number of non-digit characters
    marketing - Integer (1 of more characters, 0-9)
    major - Integer
    minor - Integer
    dev - Any number of any characters

    Leading whitespace is stripped away, any trailing whitespace is included in the 'dev' group.

    Groups can be accessed by name of index after the regex has been successfully run.
    """
    _regex = re.compile(
        r"^\s*(?P<leader>[^0-9]*)(?P<marketing>[0-9]+)\.(?P<major>[0-9]+)\.(?P<minor>[0-9]+)(?P<dev>.*)$",
        re.VERBOSE | re.IGNORECASE,
    )

    def __init__(self, version):
        match = self._regex.search(version)
        if not match:
            raise InvalidVersion("Invalid version: '{0}'".format(version))

        self._version = version
        self._marketing = int(match.group("marketing"))
        self._major = int(match.group("major"))
        self._minor = int(match.group("minor"))
        self._devstring = ""
        if match.group("leader"):
            self._devstring = self._devstring + match.group("leader")
        if match.group("dev"):
            self._devstring = self._devstring + match.group("dev")