#a Imports
import os, re, unittest
import lib.oscommand, lib.verbose

#a Useful functions
#f git_command
def git_command(options=None, cmd=None, **kwargs):
    return lib.oscommand.command(options=options,
                                     cmd="git %s"%(cmd),
                                     **kwargs)

#a Git url class
class GitUrl:
    host = None
    user = None
    port = None
    path = None
    path_dir = None
    path_leaf = None
    protocol = None
    repo_name = None
    def git_url(self):
        if (self.protocol is not None) or (self.user is not None) or (self.port is not None):
            url = self.host
            if self.user is not None: url = self.user+"@"+url
            if self.port is not None: url = url+":"+self.port
            return "%s://%s/%s"%(self.protocol, url, self.path)
        if self.host is not None:
            url = self.host
            if self.user is not None: url = self.user+"@"+url
            return "%%s/%s"%(url, self.path)
        return self.path
    def parse_path(self):
        (d,f) = os.path.split(self.path)
        if f=='': self.path = d
        (path_dir, path_leaf) = os.path.split(self.path)
        self.path_dir = path_dir
        self.path_leaf = path_leaf
        self.repo_name = path_leaf
        if path_leaf[-4:]=='.git': self.repo_name=path_leaf[:-4]
        pass
    def is_leaf(self):
        if self.host is not None: return False
        if self.path_dir != "": return False
        return True
    def make_relative_to(self, abs_url):
        self.host     = abs_url.host
        self.user     = abs_url.user
        self.port     = abs_url.port
        self.protocol = abs_url.protocol
        self.path     = os.path.join(abs_url.path_dir, self.path_leaf)
        self.parse_path()
        pass
    def __str__(self):
        return "host %s user %s port %s path %s"%(self.host, self.user, self.port, self.path)
    pass

#a GitRepo class
class GitRepo(object):
    """
    A Git repo object for a git repository within the local filesystem
    """
    #v Properties for git url parsing
    git_protocol_re  = r"(?P<protocol>ssh|git|http|https|ftp|ftps|file)"
    git_user_host_re = r"((?P<user>([a-zA-Z0-9_]*))@|)(?P<host>[a-zA-Z0-9_.]+)"
    git_opt_port_re  = r"(:(?P<port>([0-9]+))|)"
    git_path_re      = r"(?P<path>([a-zA-Z0-9~._\-/]+))"
    git_path_re      = r"(?P<path>([^:]+))"
    git_repo_url_re        = re.compile( git_protocol_re + r"://" + git_user_host_re + git_opt_port_re + r"/" + git_path_re )
    git_repo_host_path_re  = re.compile( git_user_host_re + ":" + git_path_re )
    git_repo_path_re       = re.compile( git_path_re )
    #f parse_git_url - classmethod to parse a URL to an object with host/user/port/path/protocol/repo_name properties
    @classmethod
    def parse_git_url(cls, git_url):
        x = GitUrl()
        match  = cls.git_repo_url_re.fullmatch(git_url)
        if not match: match = cls.git_repo_host_path_re.fullmatch(git_url)
        if not match: match = cls.git_repo_path_re.fullmatch(git_url)
        if not match:
            raise Exception("Failed to parse git URL '%s'"%git_url)
        d = match.groupdict()
        for k in ['protocol','host','user','port','path']:
            if k in d:
                if d[k]!="": setattr(x,k,d[k])
                pass
            pass
        x.parse_path()
        return x
    #f __init__
    def __init__(self, path, git_url=None, permit_no_remote=False):
        """
        Create the object from a given path

        The path is the local path directory for the repository
        Should chase the path to the toplevel (or do git root)
        Should find the git_url this was cloned from too
        """
        if path is None: path="."
        git_output = git_command(cwd=os.path.abspath(path),
                                 cmd="rev-parse --show-toplevel")
        self.path = os.path.realpath(git_output.strip())
        if git_url is None:
            try:
                git_output = git_command(cwd=self.path,
                                         cmd="remote get-url origin")
                pass
            except Exception as e:
                if not permit_no_remote: raise e
                git_url = ""
                pass
            git_url = git_output.strip()
            if git_url=="":
                git_url=None
                pass
            else:
                git_url = self.parse_git_url(git_url)
                pass
            pass
        self.git_url = git_url
        pass
    #f get_name
    def get_name(self):
        return self.path
    #f get_git_url
    def get_git_url(self):
        return self.git_url
    #f get_git_url_string
    def get_git_url_string(self):
        return self.git_url.git_url()
    #f get_path
    def get_path(self):
        return self.path
    #f is_modified
    def is_modified(self):
        """
        Return True if the git repo is modified since last commit
        """
        git_command(cmd="update-index -q --refresh",
                    cwd=self.path)
        output = git_command(cwd=self.path,
                             cmd="diff-index --name-only HEAD")
        output = output.strip()
        if len(output.strip()) > 0:
            return True
        return False
    #f get_cs
    def get_cs(self):
        """
        Get changeset of the git repo

        This is more valuable to the user if git repo is_modified() is false.
        """
        output = git_command(cmd="rev-parse HEAD",
                                  cwd=self.path)
        output = output.strip()
        if len(output.strip()) > 0: return output
        raise Exception("Failed to determine changeset for git repo '%s'"%(self.name))
    #f get_cs_history
    def get_cs_history(self, branch_name=""):
        """
        Get list of changesets of the git repo branch

        This is more valuable to the user if git repo is_modified() is false.
        """
        output = git_command(cmd="rev-list %s"%branch_name,
                                  cwd=self.path)
        output = output.strip()
        output = output.split("\n")
        if len(output) > 0: return output
        raise Exception("Failed to determine changeset history for git repo '%s'"%(self.name))
    #f fetch
    def fetch(self):
        """
        Fetch changes from upstream
        """
        output = git_command(cmd="fetch",
                             cwd=self.path,
                             stderr_output_indicates_error=False
        )
        output = output.strip()
        return(output)
    #f checkout_cs
    def checkout_cs(self, options, changeset):
        """
        Checkout changeset
        """
        output = git_command(options=options,
                             cmd="checkout %s"%(changeset),
                             cwd=self.path,
                             stderr_output_indicates_error=False)
        pass
    #f check_clone_permitted - check if can clone url to path
    @classmethod
    def check_clone_permitted(cls, repo_url, branch=None, dest=None):
        print("%s : %s : %s"%(repo_url, branch, dest))
        if os.path.exists(dest): raise Exception("Cannot clone to %s as it already exists"%(dest))
        dest_dir = os.path.dirname(dest)
        if not os.path.exists(dest_dir): raise Exception("Cannot clone to %s as the parent directory does not exist"%(dest))
        return True
    #f clone - clone from a Git URL (of a particular branch to a destination directory)
    @classmethod
    def clone(cls, options, repo_url, new_branch_name, branch=None, dest=None, bare=False, depth=None, changeset=None):
        """
        Clone a branch of a repo_url into a checkout directory
        bare checkouts are used in testing only
        """
        url = cls.parse_git_url(repo_url)
        if dest is None: dest=url.repo_name
        git_options = []
        if branch is not None: git_options.append( "--branch %s"%branch )
        if (bare is not None) and bare: git_options.append( "--bare")
        if changeset is not None: git_options.append( "--no-checkout")
        if depth is not None:   git_options.append( "--depth %s"%(depth))
        lib.verbose.info(options, "Git clone from '%s' to '%s' with options %s"%(repo_url, dest, " ".join(git_options)))
        try:
            git_output = git_command(options=options,
                                     cmd="clone %s %s %s" % (" ".join(git_options), repo_url, dest),
                                     stderr_output_indicates_error=False)
            pass
        except lib.oscommand.OSCommandError as e:
            raise Exception("Failed to perform git clone - %s"%(e.cmd.error_output()))
            pass
        git_command(options=options, cmd="branch --move upstream")
        if changeset is None:
            git_command(options=options, cmd="branch %s"%(new_branch_name))
            pass
        else:
            try:
                git_command(options=options, cmd="branch %s %s"%(new_branch_name, changeset))
                pass
            except:
                raise Exception("Failed to checkout required changeset - maybe depth is not large enough")
            pass
        git_output = git_command(options=options,
                                 cwd = dest,
                                 cmd = "checkout %s" % new_branch_name,
                                 stderr_output_indicates_error=False)
        pass
        return cls(dest, git_url=repo_url)
    #f filename - get filename of full path relative to repo in file system
    def filename(self, paths):
        if type(paths)!=list: paths=[paths]
        filename = self.path
        for p in paths: filename=os.path.join(filename,p)
        return filename
    #f All done
    pass

#a Unittest for Repo class
class RepoUnitTest(unittest.TestCase):
    def _test_git_url(self, url, host=None, user=None, port=None, path=None, protocol=None, repo_name=None):
        d = GitRepo.parse_git_url(url)
        self.assertEqual(d.host,host,"Mismatch in host")
        self.assertEqual(d.user,user,"Mismatch in user")
        self.assertEqual(d.port,port,"Mismatch in port")
        self.assertEqual(d.path,path,"Mismatch in path")
        self.assertEqual(d.protocol,protocol,"Mismatch in protocol")
        self.assertEqual(d.repo_name,repo_name,"Mismatch in repo_name")
        pass
    def _test_git_url_fails(self, *args):
        self.assertRaises(Exception, GitRepo.parse_git_url, *args)
        pass
    def test_paths(self):
        self._test_git_url("banana.git", host=None, user=None, port=None, path="banana.git", protocol=None, repo_name="banana")
        self._test_git_url("/path/to/banana.git", host=None, user=None, port=None, path="/path/to/banana.git", protocol=None, repo_name="banana")
        self._test_git_url("banana.git/", host=None, user=None, port=None, path="banana.git", protocol=None, repo_name="banana")
        self._test_git_url("/path/to/banana.git/", host=None, user=None, port=None, path="/path/to/banana.git", protocol=None, repo_name="banana")
        pass
    def test_urls(self):
        self._test_git_url("https://github.com/atthecodeface/grip.git", host="github.com", user=None, port=None, path="atthecodeface/grip.git", protocol="https", repo_name="grip")
        self._test_git_url("http://atthecodeface@github.com/atthecodeface/cdl_hardware.git", host="github.com", user="atthecodeface", port=None, path="atthecodeface/cdl_hardware.git", protocol="http", repo_name="cdl_hardware")
        self._test_git_url("ssh://login@server.com:12345/absolute/path/to/repository", host="server.com", user="login", port="12345", path="absolute/path/to/repository", protocol="ssh", repo_name="repository")
        self._test_git_url("ssh://login@server.com:12345/absolute/path/to/repository/", host="server.com", user="login", port="12345", path="absolute/path/to/repository", protocol="ssh", repo_name="repository")
        pass
    def test_host_paths(self):
        self._test_git_url("login@server.com:path/to/repository/from/home", host="server.com", user="login", port=None, path="path/to/repository/from/home", protocol=None, repo_name="home")
        self._test_git_url("login@server.com:path/to/repository/from/home/", host="server.com", user="login", port=None, path="path/to/repository/from/home", protocol=None, repo_name="home")
        pass
    def test_mismatches(self):
        self._test_git_url_fails("ssah://login@server.com:12345/absolute/path/to/repository")
        self._test_git_url_fails("ssh://login@server.com:12345:otherportisnotallowed/absolute/path/to/repository")
        pass
    pass


