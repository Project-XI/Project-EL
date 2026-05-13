import os
import git
from typing import Optional

class RepoCloner:
    """
    Handles cloning of GitHub repositories to a local directory.
    """
    
    @staticmethod
    def clone(repo_url: str, target_dir: str) -> Optional[str]:
        """
        Clones a repository and returns the path to the local directory.
        """
        try:
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            
            # Simple repo name extraction for unique folder
            repo_name = repo_url.split("/")[-1].replace(".git", "")
            clone_path = os.path.join(target_dir, repo_name)
            
            if os.path.exists(clone_path):
                print(f"Repo already exists at {clone_path}")
                return clone_path
            
            print(f"Cloning {repo_url} into {clone_path}...")
            git.Repo.clone_from(repo_url, clone_path)
            return clone_path
            
        except Exception as e:
            print(f"Error cloning repository: {e}")
            return None
