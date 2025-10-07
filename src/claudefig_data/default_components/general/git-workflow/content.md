## Git Workflow

### Branching Strategy

- **main/master**: Production-ready code only
- **develop**: Integration branch for features
- **feature/***: Feature development branches
- **bugfix/***: Bug fix branches
- **hotfix/***: Emergency production fixes
- **release/***: Release preparation branches

### Commit Conventions

**Commit Message Format:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Build process or auxiliary tool changes

**Examples:**
```
feat(auth): add OAuth2 login support

Implemented OAuth2 authentication flow with Google provider.
Includes token refresh and session management.

Closes #123
```

```
fix(api): handle null response in user endpoint

Added null check before accessing user.email to prevent crashes.
```

### Workflow Rules

- **Pull before push**: Always pull latest changes before pushing
- **Small commits**: Commit frequently with focused changes
- **Descriptive messages**: Explain what and why, not how
- **Review before merge**: All code requires review (via PRs)
- **Squash feature commits**: Clean up history before merging to main
- **Never force push** to shared branches (main, develop)
- **Delete merged branches**: Keep repository clean
