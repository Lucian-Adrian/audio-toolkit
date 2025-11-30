## Architecture


### Spec-Driven Development
Specs live **next to the code**, not in a wiki. They act as **Context Anchors** for AI agents.


**Workflow:**
1. **Context First** → Read `specs/00_context.md` to understand goals
2. **Requirements** → Check `specs/01_requirements.md` (EARS notation) before implementing
3. **Design** → Reference `specs/02_design.md` for architecture decisions
4. **Plan** → Follow `specs/03_plan.md` checklist for atomic tasks


**Before writing code, always:**
- Verify the task exists in `specs/03_plan.md`
- Check `specs/02_design.md` for interface contracts
- Update specs if requirements change


### Directory Structure
```
specs/                      # The "Brain" of the project
├── 00_context.md           # High-level goals & "vibe"
├── 01_requirements.md      # EARS notation requirements
├── 02_design.md            # Architecture, Schemas, & Interfaces
└── 03_plan




### Design Pattern




## Code Conventions


### Code Quality Criteria
- **KISS**: Keep it simple, stupid
- **DRY**: Don't repeat yourself
- **YAGNI**: You aren't gonna need it
- **SOLID**: Single responsibility, Open-closed, Liskov substitution, Interface segregation, Dependency inversion
- **Max 100 lines per file** - split large files into smaller modules, exceptions for frontend files
- **Separation of concerns**: Each module handles one concern
- **Modular design**: Reusable, testable, scalable components


### File Organization
- Separate each major component/concern per file
- Large code → split into smaller components, import in main file
- Document structure changes in `docs/file-structure.md`


### Code Standards
- Clean, readable code with clear reasoning
- Proper error handling and logging
- Security best practices
- Performance considerations
- Handle edge cases
- Future-proof: changes don't require huge refactoring
- Consistent coding style throughout


Criteria to write code:
- Follow best practices for documentation and code organization
- Ensure clarity and maintainability in both code and documentation
- Adhere to the project's architectural guidelines and contribution workflow
- KISS
- DRY
- Try to keep max 100 lines of code per file
- For large frontend code, split into smaller components and make the page a file that imports those components
- Separate each page per file, or if SPA, separate each major component per file or each major concern per folder, then each page or view per file that imports those components,
- Documenting the structure in docs/file_structure.md
- Use global styles and define them according to EVO Design System tokens
- YAGNI
- Separation of concerns
- Single responsibility principle
- Modular design
- Reusability
- Testability
- Scalability
- Maintainability
- Extensibility
- Performance considerations
- Security best practices
- Consistency in coding style and conventions
- Proper error handling
- Logging and monitoring
- Version control practices
- Design patterns
- SOLID principles
- Code smells
- Edge cases
- Real-world applicability
- Make it as easy as possible to understand the system and then apply changes to it
- Make it change proof, future proof, robust, adding changes does not require huge refactoring
- clean, readable code
- make it clearly articulated, using simple words and logically, so that it shows reasoning and thought put into it




# Example of abstract thinking process and reasoning logic
1. Core Architectural Principles
- think about this problem using TRIZ, teorya reshenya izobretatelnych zadach.
- find the core principles that can be applied to this problem
- find core issues and core solutions that can be applied generally
- Use Elon Musk 5 principles for a inventor company.
- First Principles Thinking
- Think outside the box
- Systems Thinking
- Modular Design
- Scalability
- Multi-Tenant & Multi-Location: Single Database instance. Data isolation
- think logically, shift problem logic as much to left (db) from back and front as possible
- zero trust principle
- DRY
- KISS
- SOLID
- Optimization
- Genericness (we do not want to tie our hands, we want to easily add mr business requests later on)
- Logic (shift as much as possible logic from front and back in DB)



## Development Guidelines

### Documentation First
- Document new features in the appropriate `docs/` subdirectory before implementation
- Update `changelog.md` with notable changes using semantic versioning
- Keep `docs/file_structure.md` current as the codebase evolves

### Code Organization
- Backend code → document in `docs/backend/`
- Frontend code → document in `docs/frontend/`
- Database changes → document in `docs/db/`
- Track milestones in `docs/progress/`

### Contribution Workflow
- Follow patterns documented in `contributing.md`
- Use descriptive commit messages referencing the affected component (e.g., `[backend] Add user authentication`)

## Notes for AI Agents

- This is a greenfield project - prioritize clean, maintainable patterns from the start
- When creating new components, update `docs/file_structure.md` accordingly
- Prefer Romanian language for user-facing content where appropriate (Moldova context)

Criteria to write code:
- Follow best practices for documentation and code organization
- Ensure clarity and maintainability in both code and documentation
- Adhere to the project's architectural guidelines and contribution workflow
- KISS
- DRY
- Design patterns
- SOLID principles
- Code smells
- Edge cases
- Real-world applicability
- Make it as easy as possible to understand the system and then apply changes to it
- Make it change proof, future proof, robust, adding changes does not require huge refactoring
- clean, readable code
- make it clearly articulated, using simple words and logically, so that it shows reasoning and thought put into it



# Example of abstract thinking process and reasoning logic
1. Core Architectural Principles
- think about this problem using TRIZ, teorya reshenya izobretatelnych zadach.
- find the core principles that can be applied to this problem
- find core issues and core solutions that can be applied generally
- Use Elon Musk 5 principles for a inventor company.
- First Principles Thinking
- Think outside the box
- Systems Thinking
- Modular Design
- Scalability
- Multi-Tenant & Multi-Location: Single Database instance. Data isolation
- think logically, shift problem logic as much to left (db) from back and front as possible
- zero trust principle
- DRY
- KISS
- SOLID
- Optimization
- Genericness (we do not want to tie our hands, we want to easily add mr business requests later on)
- Logic (shift as much as possible logic from front and back in DB)

2. Abstract Business Logic