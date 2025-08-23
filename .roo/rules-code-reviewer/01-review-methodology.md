# Code Review Methodology

## Comprehensive Review Framework

### Security-First Analysis
1. **Input Validation**: Check all user inputs are properly validated and sanitized
2. **Authentication/Authorization**: Verify proper access controls and permission checks
3. **Data Exposure**: Ensure sensitive data is not logged or exposed inappropriately
4. **Injection Vulnerabilities**: SQL injection, XSS, command injection prevention
5. **Cryptography**: Proper use of secure algorithms and key management

### Performance Assessment
1. **Algorithmic Complexity**: Identify inefficient algorithms or nested loops
2. **Database Queries**: N+1 problems, missing indexes, inefficient joins
3. **Memory Usage**: Memory leaks, excessive allocations, proper cleanup
4. **Caching Strategy**: Appropriate use of caching, cache invalidation
5. **Resource Management**: File handles, network connections, concurrent resources

### Code Quality Standards
1. **Readability**: Clear variable names, logical flow, appropriate comments
2. **Modularity**: Proper separation of concerns, single responsibility principle
3. **Error Handling**: Comprehensive error handling and graceful failure modes  
4. **Testing**: Adequate test coverage, meaningful test cases, edge case handling
5. **Documentation**: Code comments, API documentation, usage examples