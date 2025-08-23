### .roo/rules-git-manager/02-gitdoc-mastery.md
```markdown
# GitDoc Extension Mastery

## Advanced Configuration Strategies

### Context-Aware Settings
```json
{
  "gitDoc.autoCommitDelay": 30000,
  "gitDoc.commitValidationLevel": "error",
  "gitDoc.autopush": "onCommit", 
  "gitDoc.autoPull": "onPush",
  "gitDoc.pushMode": "forcePushWithLease",
  "gitDoc.ai.enabled": true,
  "gitDoc.ai.model": "gpt-4o",
  "gitDoc.ai.useEmojis": true,
  "gitDoc.excludeBranches": ["main", "master", "develop", "release/*", "hotfix/*"],
  "gitDoc.commitOnClose": true,
  "gitDoc.pullOnOpen": true
}
Dynamic File Pattern Management
bash# Documentation sprints
code --command gitDoc.enable
# Configure for docs: **/*.{md,mdx,rst,txt}

# Feature development  
# Configure for code: **/*.{js,ts,tsx,jsx,py,rs,go}

# Configuration updates
# Disable GitDoc, use manual commits for precision
Timeline Management Expertise
Strategic Commit Squashing

Identify Logical Units: Group related auto-commits by feature or fix
Preserve Meaningful Messages: Keep commits that represent significant milestones
Create Semantic History: Use squashing to tell clear story of development

Timeline Operations
```bash
# Squash exploration commits into feature commit
# Right-click oldest exploration commit → "Squash Version(s) Above"
# Provide meaningful commit message: "feat(auth): implement JWT authentication"

# Undo experimental changes
# Right-click problematic commit → "Undo Version"
# Creates safe revert commit

# Restore known good state
# Right-click stable commit → "Restore Version" 
# Forward-moving restoration

GitDoc Status Bar Management

Mirror Icon: Indicates active auto-commit mode
Syncing Animation: Shows push/pull operations in progress
Click to Disable: Quick toggle for precision work
Red Warning: Network issues or push conflicts

AI Commit Message Optimization
Custom Instructions for Different Contexts
```
```
json{
  "gitDoc.ai.customInstructions": "Use conventional commit format with type(scope): description. Focus on the 'why' not just the 'what'. Keep messages under 72 characters."
}

// For documentation work
{
  "gitDoc.ai.customInstructions": "Focus on documentation improvements. Use 'docs' type and describe content changes clearly."
}

// For refactoring
{
  "gitDoc.ai.customInstructions": "Use 'refactor' type and explain the improvement or optimization made."
}
```
## Message Quality Control

Review AI-generated messages before squashing
Manually override inappropriate auto-generated messages
Use Timeline view to edit commit messages during squashing
Maintain consistent team commit message style