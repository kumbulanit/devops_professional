# Git Reference

## Setup
```bash
git config --global user.name "Name"           # stamped into every commit
git config --global user.email "you@work.com"  # must match GitHub to link commits
git config --global init.defaultBranch main
git config --global pull.rebase false          # pull = merge (explicit and safe)
git config --global alias.lg "log --oneline --graph --decorate --all"
git config --global credential.helper "cache --timeout=28800"
```

## The four areas
```
 working tree ──add──► index ──commit──► local repo ──push──► remote
              ◄restore─      ◄reset──             ◄fetch──
```

## Daily
| Command | Does |
|---|---|
| `git status` | What is changed, staged, untracked |
| `git diff` | Unstaged changes |
| `git diff --staged` | **What you are about to commit** — run it every time |
| `git add -p` | **Interactive staging**, hunk by hunk. Turns a messy tree into clean commits |
| `git commit -m "type: subject"` | Record the index |
| `git log --oneline --graph --decorate --all` | Readable history |
| `git show HEAD~2` | A specific commit and its diff |
| `git blame -L 40,60 file` | Who last changed these lines, and in which commit |

## Branching
```bash
git switch -c feature/PAY-142-add-probe   # create + switch (modern)
git switch main                             # switch
git branch -vv                              # branches + upstream + last commit
git branch -d old-branch                    # delete (safe: refuses if unmerged)
git branch -D old-branch                    # force delete
git push origin --delete old-branch         # delete the remote branch
git fetch --prune                           # drop remote-tracking refs that are gone
```

## Undo — pick by what has happened
| Situation | Command | Destructive? |
|---|---|---|
| Discard unstaged edits to a file | `git restore <file>` | **Yes, unrecoverable** |
| Unstage a file, keep the edits | `git restore --staged <file>` | No |
| Fix the last commit (**unpushed only**) | `git commit --amend` | Rewrites history |
| Undo a **pushed** commit | `git revert <sha>` | **No — safe on shared branches** |
| Move the branch back (**unpushed only**) | `git reset --hard <sha>` | **Yes** |
| Park work temporarily | `git stash push -m "wip"` / `git stash pop` | No |
| Recover a "lost" commit | `git reflog` then `git checkout <sha>` | No |

> **`revert` on anything shared. `reset` only on your own un-pushed work.**

## Merge strategies
| Command | Result |
|---|---|
| `git merge --ff-only b` | Move the pointer; fails if not possible. Good in scripts |
| `git merge b` | Merge commit with two parents. Safe on shared branches |
| `git merge --squash b` | One combined commit. **The GitHub Flow default** |
| `git rebase main` | Replay your commits on a new base. **Your own branch only** |
| `git push --force-with-lease` | Force-push that aborts if the remote moved |

## Conflicts
```bash
git merge origin/main            # conflict reported
git status                       # lists unmerged paths AND the next commands
grep -n '<<<<<<<' file           # find the markers
# edit: usually keep BOTH sides, then delete all three markers
grep -c '<<<<<<<' file           # MUST be 0
pytest                           # ALWAYS re-run tests after resolving
git add file && git commit --no-edit
git merge --abort                # get back to safety at any point
```

## Investigation
```bash
git log --follow -p file                       # a file's full history, across renames
git log --author="Name" --since="2 weeks ago"
git log --grep="PAY-142"                     # search commit messages
git log -S "function_name"                     # find commits that ADDED/REMOVED that string
git bisect start && git bisect bad && git bisect good <sha>   # binary-search a regression
git diff main...feature                        # what feature adds, vs the merge base
```

## Tags
```bash
git tag -a v1.2.0 -m "Release 1.2.0"   # ANNOTATED - use this for releases
git push origin v1.2.0                 # tags are NOT pushed by default
git push origin --tags
git describe --tags                    # nearest annotated tag + distance
```

## Conventional Commits
```
feat: add readiness probe endpoint          MINOR
fix: handle null latency in check payload   PATCH
feat!: drop v1 API                          MAJOR (! = breaking)
docs: · test: · refactor: · chore: · ci: · build: · perf:
```
Subject: imperative, ≤ 50 chars, no full stop. Blank line. Body explains **why**.

## Emergency
```bash
git reflog                        # every position HEAD has held — your safety net
git fsck --lost-found             # find dangling objects
git checkout -- .                 # discard ALL working-tree changes (destructive)
git clean -fd                     # delete untracked files/dirs (destructive; -n to preview)
```
