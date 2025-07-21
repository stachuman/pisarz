# Code Redundancy Reduction Plan for Pisarz

Based on comprehensive analysis, significant code duplication exists across the codebase (~15-25% reduction possible).

## Priority 1: High Impact (Immediate) 
**LLM Provider Consolidation** (Est. 120-150 lines saved)- already done.
- Extract common initialization patterns to BaseProvider- already done.
- Consolidate HTTP request logging (100+ duplicate lines)- already done.
- Unify provider configuration loading- already done.

**UI Card Widget Consolidation** (Est. 200+ lines saved)  
- Enhance BaseCard with badge creation, context menus, tooltips
- Create EntityCard base for character/location/scene cards (75-85% similar)
- Standardize mouse event handling and signal patterns

## Priority 2: Medium Impact  
**Dialog Pattern Consolidation** (Est. 150+ lines saved)
- Create EntityEditorMixin, SelectorDialogMixin  
- Standardize tab widget setup, form layouts, button patterns
- Ensure consistent BaseDialog inheritance

**Database Access Layer** (Est. 300-500 lines saved)
- Create BaseRepository with generic CRUD operations
- Implement QueryBuilder for dynamic updates  
- Consolidate connection management and error handling

## Priority 3: Lower Impact
**Import/Utility Consolidation** (Est. 150+ lines saved)
- Create core/common_imports.py for frequently used imports
- Extract LoggingMixin, SettingsMixin base classes
- Centralize constants in core/constants.py

## Implementation Approach:
- One pattern type per commit
- Maintain app functionality (`python main.py` always works)
- Verify no functionality regression after each consolidation