---
trigger: model_decision
description: Comprehensive ruleset for Git version control and GitHub collaboration workflows, covering repository management, branching strategies, security best practices, and team collaboration patterns
---

# Git/GitHub Rules

## Repository Setup and Configuration

- Always initialize repositories with a clear `.gitignore` file appropriate for the technology stack
- Configure user identity before first commit: `git config user.name` and `git config user.email`
- Set up branch protection rules on main/master branches to require reviews and prevent force pushes
- Use semantic versioning for releases and tag them appropriately: `git tag -a v1.0.0 -m "Release version 1.0.0"`
- Configure line ending handling consistently across platforms using `.gitattributes`: `* text=auto`
- Enable Git LFS for large files (>100MB) or binary assets: `git lfs track "*.psd"`

## Branching Strategy and Workflow

- Follow a consistent branching strategy (GitFlow, GitHub Flow, or Trunk-based development)
- Use descriptive branch naming conventions: `feature/add-user-auth`, `fix/navbar-crash`, `chore/update-deps`
- Create feature branches from the latest main/develop branch: `git checkout -b feature/new-feature main`
- Keep branches focused on single features or fixes to minimize merge conflicts
- Merge feature branches via Pull Requests, never directly to main
- Delete merged branches promptly to maintain repository cleanliness: `git branch -d feature/completed-feature`
- Regularly sync feature branches with main to avoid large conflicts: `git rebase main` or `git merge main`

## Commit Best Practices

- Write clear, descriptive commit messages following Conventional Commits format
- Use imperative mood in commit subjects: "Add user authentication" not "Added user authentication"
- Limit subject lines to 50 characters, detailed descriptions to 72 characters per line
- Make atomic commits - one logical change per commit
- Never commit sensitive data (API keys, passwords, credentials) - use environment variables instead
- Use `git add -p` for partial staging to create focused commits
- Amend commits when needed but never rewrite public history: `git commit --amend`
- Sign commits when required for security: `git commit -S`

### Conventional Commit Format
```
<type>: <description>

[optional body]

[optional footer(s)]
```
Types: feat, fix, docs, style, refactor, test, chore

## Pull Request and Code Review

- Create small, focused pull requests that are easy to review
- Write clear PR titles and descriptions explaining what changes and why
- Reference related issues in PR descriptions: "Fixes #123" or "Closes #456"
- Request reviews from appropriate team members before merging
- Address all review feedback before merging
- Use draft PRs for work-in-progress that needs early feedback
- Ensure all CI/CD checks pass before merging
- Squash commits when merging to maintain clean history (when appropriate)
- Use merge commits for feature integration to preserve branch context

## Security and Safety Practices

- Never commit credentials, API keys, or sensitive data
- Use `.env` files for environment variables and add them to `.gitignore`
- Enable branch protection rules requiring reviews and status checks
- Use signed commits for sensitive repositories
- Regularly audit commit history for accidentally committed secrets
- Use GitHub's secret scanning and dependency alerts
- Set up proper repository permissions using least privilege principle
- Enable two-factor authentication on GitHub accounts
- Use personal access tokens instead of passwords for Git operations
- Rotate access tokens regularly and revoke unused ones

## GitHub-Specific Features

- Use GitHub Issues for bug tracking and feature requests
- Link commits to issues using keywords: "fixes #123", "closes #456"
- Use GitHub Projects for project management and sprint planning
- Set up GitHub Actions for CI/CD workflows
- Use GitHub Releases for version management with changelog
- Configure repository webhooks for integration with external tools
- Use GitHub Pages for documentation hosting when appropriate
- Enable GitHub Discussions for community interaction
- Use GitHub Sponsors for open source project funding
- Configure repository topics and README for discoverability

## Merge and Conflict Resolution

- Always pull latest changes before pushing: `git pull origin main`
- Resolve merge conflicts manually and review all changes carefully
- Use three-way merge tools for complex conflicts: `git mergetool`
- Test thoroughly after resolving conflicts before committing
- Never use `git push --force` on shared branches
- Use `git push --force-with-lease` when force push is absolutely necessary
- Communicate with team before force pushing to any shared branch
- Use rebase for feature branches to maintain linear history: `git rebase main`
- Prefer merge commits for feature integration to preserve branch context

## Performance and Optimization

- Use `.gitignore` to exclude build artifacts, dependencies, and temporary files
- Configure Git LFS for large binary files and assets
- Use shallow clones for CI/CD when full history isn't needed: `git clone --depth 1`
- Regularly clean up local repository: `git gc` and `git prune`
- Use `git worktree` for working on multiple branches simultaneously
- Configure Git aliases for frequently used commands
- Use Git hooks for automated checks and formatting
- Monitor repository size and use `git filter-repo` for cleanup when needed

## Team Collaboration

- Establish clear commit message standards for the team
- Document branching strategy and workflow in repository README
- Use consistent code formatting and linting tools
- Set up pre-commit hooks for code quality checks
- Establish review requirements and response time expectations
- Use GitHub teams for permission management
- Document release processes and versioning strategy
- Maintain CHANGELOG.md for release notes
- Use GitHub templates for issues and pull requests

## Known Issues and Mitigations

### Merge Conflicts
- **Issue**: Conflicts occur when multiple developers modify same lines
- **Mitigation**: Frequent syncing with main branch, clear communication, small focused changes

### Accidental Force Push
- **Issue**: `git push --force` overwrites team members' work
- **Mitigation**: Use `--force-with-lease`, enable branch protection, team communication protocols

### Credential Exposure
- **Issue**: API keys and passwords committed to repository
- **Mitigation**: Comprehensive `.gitignore`, pre-commit hooks, regular secret scanning

### Large Repository Size
- **Issue**: Repository becomes slow due to large files or extensive history
- **Mitigation**: Git LFS for large files, regular cleanup, shallow clones for CI

### Wrong Branch Commits
- **Issue**: Committing changes to main instead of feature branch
- **Mitigation**: Branch protection rules, clear workflow documentation, Git aliases

### Lost Work from Rebasing
- **Issue**: Rebase operations can lose commits if done incorrectly
- **Mitigation**: Create backup branches before rebasing, understand rebase vs merge tradeoffs

### Incomplete Pull Requests
- **Issue**: PRs merged without proper review or testing
- **Mitigation**: Required reviews, status checks, clear acceptance criteria

## Emergency Procedures

### Recovering Lost Commits
```bash
git reflog                    # Find lost commit hash
git cherry-pick <commit-hash> # Restore specific commit
git reset --hard <commit-hash> # Reset to specific state
```

### Undoing Public Commits
```bash
git revert <commit-hash>     # Create new commit that undoes changes
git revert -m 1 <merge-hash> # Revert merge commit
```

### Fixing Committed Secrets
```bash
git filter-repo --path <file> --invert-paths # Remove file from history
# Then notify security team and rotate credentials
```

### Branch Recovery
```bash
git checkout -b recovery-branch <commit-hash> # Create branch from specific commit
git push origin recovery-branch               # Push recovery branch
```

## Best Practices Summary

1. **Always pull before push** to avoid conflicts
2. **Use meaningful commit messages** following conventional format
3. **Never commit secrets** - use environment variables
4. **Review all pull requests** before merging
5. **Protect main branches** with branch protection rules
6. **Keep repositories clean** with proper `.gitignore`
7. **Use feature branches** for all development work
8. **Test thoroughly** after resolving conflicts
9. **Document workflows** for team consistency
10. **Monitor security** with GitHub's built-in tools
