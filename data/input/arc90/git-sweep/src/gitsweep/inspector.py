from git import Git

from .base import BaseOperation


class Inspector(BaseOperation):

    """
    Used to introspect a Git repository.

    """
    def merged_refs(self, skip=[]):
        """
        Returns a list of remote refs that have been merged into the main
        branch.

        The "main" branch may have a different name than main. The value of
        ``self.main_name`` is used to determine what this name is.
        """
        origin = self._origin

        main = self._main_ref(origin)
        refs = self._filtered_remotes(
            origin, skip=['HEAD', self.main_branch] + skip)
        merged = []

        for ref in refs:
            upstream = '{origin}/{main}'.format(
                origin=origin.name, main=main.remote_head)
            head = '{origin}/{branch}'.format(
                origin=origin.name, branch=ref.remote_head)
            cmd = Git(self.repo.working_dir)
            # Drop to the git binary to do this, it's just easier to work with
            # at this level.
            (retcode, stdout, stderr) = cmd.execute(
                ['git', 'cherry', upstream, head],
                with_extended_output=True, with_exceptions=False)
            if retcode == 0 and not stdout:
                # This means there are no commits in the branch that are not
                # also in the main branch. This is ready to be deleted.
                merged.append(ref)

        return merged
