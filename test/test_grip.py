#a Imports
import os
from pathlib import Path

from .test_lib.filesystem import FileSystem, FileContent
from .test_lib.loggable import TestLog
from .test_lib.unittest import TestCase
from .test_lib.git import Repository as GitRepository
from .test_lib.grip import Repository as GripRepoBuild


from typing import List, Optional, Any, ClassVar

#a Test classes
#c Basic grip test case
class BasicTest(TestCase):
    #v class properties
    cls_fs      : ClassVar[FileSystem]
    cls_d1      : ClassVar[GitRepository]
    cls_d1_bare : ClassVar[GitRepository]
    cls_d2      : ClassVar[GitRepository]
    cls_d2_bare : ClassVar[GitRepository]
    cls_g       : ClassVar[GripRepoBuild]
    cls_g_bare  : ClassVar[GitRepository]
    #f setUpClass - invoked for all tests to use
    @classmethod
    def setUpClass(cls) -> None:
        TestCase.setUpSubClass(cls)
        try:
            fs = FileSystem(cls._logger)
            cls.cls_fs = fs
            cls.cls_d1       = GitRepository(name="d_1",fs=fs,parent_dirs=[],log=cls._logger).git_init(GitRepository.add_readme)
            cls.cls_d1_bare  = cls.cls_d1.bare_clone()
            cls.cls_d2       = GitRepository(name="d_2",fs=fs,parent_dirs=[],log=cls._logger).git_init(GitRepository.add_readme)
            cls.cls_d2_bare  = cls.cls_d2.bare_clone()
            cls.cls_g        = GripRepoBuild(name="grip_1",fs=fs,log=cls._logger).git_init()
            cls.cls_g_bare   = cls.cls_g.bare_clone()
        except:
            cls._logger.tidy()
            raise
        cls._logger.tidy()
        pass
    #f tearDownClass - invoked when all tests completed
    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.cls_fs.cleanup()
        except:
            TestCase.tearDownSubClass(cls)
            raise
        TestCase.tearDownSubClass(cls)
        pass
    #f test_git_clone
    def test_git_clone(self) -> None:
        fs = FileSystem(log=self._logger)
        d2 = GitRepository(name="grip_repo_one_clone",fs=fs,log=self._logger).git_clone(clone=self.cls_d1_bare.path, bare=False)
        d2.append_to_file(["Readme.txt"], content=FileContent("Appended text"))
        d2.git_command("commit -a -m 'appended text to readme'")
        d2.git_command_allow_stderr("push", )
        fs.cleanup()
        pass
    #f test_grip_interrogate
    def test_grip_interrogate(self) -> None:
        fs = FileSystem(log=self._logger)
        g = GripRepoBuild(name="grip_repo_one_clone",fs=fs,log=self._logger)
        g.git_clone(clone=self.cls_g_bare.path)
        g.grip_command("configure")
        grip_root = g.grip_command("root")
        checkout_path = os.path.realpath(g.path)
        self.assertEqual(grip_root, checkout_path, "Output of grip root and the actual checkout git path should match")
        grip_root = g.grip_command("root .grip/")
        self.assertEqual(grip_root, checkout_path, "Output of grip root and the actual checkout git path should match")
        grip_root = g.grip_command("root .grip/grip.toml")
        self.assertEqual(grip_root, checkout_path, "Output of grip root and the actual checkout git path should match")
        grip_root = g.grip_command("root .grip")
        self.assertEqual(grip_root, checkout_path, "Output of grip root and the actual checkout git path should match")
        grip_root = g.grip_command("root d1")
        self.assertEqual(grip_root, checkout_path, "Output of grip root and the actual checkout git path should match")
        fs.cleanup()
        pass
    #f test_grip_configure
    def test_grip_configure(self) -> None:
        fs = FileSystem(log=self._logger) # "test_configure")
        g = GripRepoBuild(name="grip_repo_one_clone",fs=fs,log=self._logger)
        g.git_clone(clone=self.cls_g_bare.path)
        g.grip_command("configure")
        fs.log_hashes(reason="post grip configure", path=Path("grip_repo_one_clone/.grip"), glob="*", depth=-1, use_full_name=False)
        #print(os_command(options=g.options, cmd="cat .grip/grip.toml", cwd=g.path))
        self.assertTrue(os.path.isdir(fs.abspath(["grip_repo_one_clone"])), "git clone of bare grip repo should create grip_repo_one_clone directory")
        self.assertTrue(os.path.isdir(fs.abspath(["grip_repo_one_clone" , ".grip"])), "git clone of bare grip repo should create .grip directory")
        self.assertTrue(os.path.isdir(fs.abspath(["grip_repo_one_clone", "d1"])), "grip configure in grip repo should create d1 directory")
        #print(os_command(options=g.options, cmd="ls -lagtrR", cwd=g.path))
        fs.cleanup()
        pass
    pass
