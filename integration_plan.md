# Enhanced Character-Scene-Location Linking Implementation Plan

## Goal
Implement comprehensive character, scene, and location management system providing tri-directional linking capabilities from any perspective (character ↔ scene ↔ location), creating a complete story organization system.

## Current State Analysis (Updated after Phase 1 Implementation)

### ✅ Completed Systems:
- **Characters**: ✅ Full implementation (database, UI, linking)
- **Scenes**: ✅ Full implementation (database, UI, editor)  
- **Character-Scene Linking**: ✅ Complete bidirectional system
- **Locations**: ✅ **NEWLY IMPLEMENTED** - Full backend and UI system
- **Scene-Location Linking**: ✅ **NEWLY IMPLEMENTED** - Database schema and LocationManager methods
- **Character-Location Linking**: ✅ **NEWLY IMPLEMENTED** - Relationship management system
- **Location Management**: ✅ **NEWLY IMPLEMENTED** - Complete CRUD operations

### 🚧 Next Phase Systems:
- **Enhanced Scene Editor**: ❌ Scene context panel not yet implemented
- **Tri-directional Grid Views**: ❌ Enhanced cards with relationship info not implemented
- **Advanced Location Features**: ❌ Location selector dialogs and advanced linking UI not implemented
- **Scene Context Management**: ❌ In-editor character/location management not implemented

## ✅ Phase 1: Location System Foundation (COMPLETED)

### ✅ 1.1 Location Database Schema - IMPLEMENTED
**Completed**: Database migration version 3 with full schema:
- ✅ `locations` table with comprehensive fields (name, type, description, atmosphere, details, significance, notes)
- ✅ `plot_threads` table for story arcs and subplots  
- ✅ `scene_locations` linking table with role support (Primary/Secondary/Mentioned)
- ✅ `character_locations` linking table with relationship types (Lives/Works/Visits/Born)
- ✅ `scene_plot_threads` linking table for scene-plot connections
- ✅ Performance indexes for all tables

### ✅ 1.2 Location Core System - IMPLEMENTED
**Completed**: `core/location.py` with comprehensive LocationManager:
- ✅ Full CRUD operations: `create_location()`, `get_locations()`, `update_location()`, `delete_location()`
- ✅ Scene-location linking: `link_location_to_scene()`, `unlink_location_from_scene()`, `get_scene_locations()`
- ✅ Character-location linking: `link_character_to_location()`, `get_characters_at_location()`, `get_character_locations()`
- ✅ Plot thread management: `create_plot_thread()`, `get_plot_threads()`, `update_plot_thread()`
- ✅ Tri-directional relationship queries

### ✅ 1.3 Location UI Components - IMPLEMENTED
**Completed Files**:
- ✅ `ui/widgets/location_card.py` - Location display cards with scene/character counts
- ✅ `ui/widgets/locations_grid_view.py` - Grid view with search, filtering, CRUD operations
- ✅ `ui/widgets/location_editor_dialog.py` - Comprehensive tabbed location editor
- ✅ Project tree integration with location support
- ✅ Workspace integration with location grid view
- ✅ Main application integration with complete signal handling

### ✅ 1.4 Additional Completions
- ✅ **Database Migration**: `migrate_database.py` updated to version 3
- ✅ **Project Tree**: Location tree items, icons, and new location functionality
- ✅ **Workspace**: Dynamic location grid view initialization and management  
- ✅ **Main App**: Complete location lifecycle management and UI integration

## Phase 2: Enhanced Scene Editor with Character & Location Management (High Priority)

### 2.1 Unified Scene Context Panel
**Enhanced Scene Editor Layout**:
```
┌──────────────────┬─────────────────────────┐
│ Toolbar          │ Scene Context      [▼]  │
├──────────────────┼─────────────────────────┤
│                  │ 📍 LOCATION             │
│                  │ • Park (Primary)        │
│                  │ • Café (Secondary)      │
│                  │ [+ Add Location]        │
│ Main Text        │ ─────────────────────   │
│ Editor           │ 👥 CHARACTERS           │
│                  │ • John (Protagonist)    │
│                  │ • Mary (Supporting)     │
│                  │ • Tom (Minor)           │
│                  │ [+ Add Character]       │
│                  │ ─────────────────────   │
│                  │ 🔗 RELATIONSHIPS        │
│                  │ • John lives near Park  │
│                  │ • Mary works at Café    │
└──────────────────┴─────────────────────────┘
```

### 2.2 Scene Context Features
- **Location Management**: Primary/secondary location assignment
- **Character Management**: Character roles and presence
- **Smart Relationships**: Show character-location connections automatically
- **Context Validation**: Warn about inconsistencies (character in wrong location)
- **Quick Actions**: Add new location/character directly from scene

### 2.3 Scene Context Interactions
- **Drag & Drop**: Drag locations/characters from project tree to scene
- **Context Menus**: Right-click for quick actions (edit, remove, change role)
- **Auto-suggestions**: Suggest characters/locations based on scene content
- **Cross-references**: Click character/location to see other scenes they appear in

## Phase 3: Enhanced Grid Views with Tri-Directional Information (Medium Priority)

### 3.1 Scene Cards with Complete Context
**Enhanced Scene Card Layout**:
```
┌─────────────────────────────────────┐
│ Scene Title               [3👥][2📍] │
│ ─────────────────────────────────────│
│ Scene content preview...            │
│                                     │
│ 📍 Park, Café                       │
│ 👤John  👤Mary  👤Tom                │
│ 🔗 John@Park, Mary@Café             │
└─────────────────────────────────────┘
```

### 3.2 Character Cards with Location Context
**Enhanced Character Card**:
```
┌─────────────────────────────────────┐
│ Character Name           [5🎬][3📍] │
│ ─────────────────────────────────────│
│ Character description...            │
│                                     │
│ 📍 Lives: Downtown, Works: Office   │
│ 🎬 Appears in: Scene1, Scene2...    │
└─────────────────────────────────────┘
```

### 3.3 Location Cards (New)
**Location Card Layout**:
```
┌─────────────────────────────────────┐
│ Location Name            [4🎬][6👥] │
│ ─────────────────────────────────────│
│ Location description...             │
│                                     │
│ 🏢 Type: Indoor Office Building     │
│ 👥 John, Mary, Alice, Bob...        │
│ 🎬 Scenes: Meeting, Conflict...     │
└─────────────────────────────────────┘
```

### 3.4 Smart Filtering and Search
- **Cross-entity filtering**: "Show scenes with John at Park"
- **Relationship search**: "Find characters who work in Downtown"
- **Location-based organization**: Group scenes by location
- **Character journey tracking**: Follow character across locations

## Phase 4: Location Editor and Management (Medium Priority)

### 4.1 Location Editor Dialog
**Tabbed Interface**:
- **Basic Info**: Name, type, description, atmosphere
- **Details**: Physical description, layout, important features
- **Story Role**: Significance, symbolic meaning, recurring themes
- **Connections**: Characters associated, scenes taking place
- **Notes**: General notes, inspiration, references

### 4.2 Location Types and Categories
**Location Categories**:
- **Indoor**: Home, Office, Restaurant, Shop, etc.
- **Outdoor**: Park, Street, Forest, Beach, etc.
- **Mixed**: Campus, Mall, Apartment Building, etc.
- **Virtual**: Dream, Memory, Fantasy realm, etc.

**Location Attributes**:
- **Atmosphere**: Cozy, Tense, Mysterious, Welcoming, etc.
- **Time Period**: Modern, Historical, Futuristic, etc.
- **Access Level**: Public, Private, Restricted, etc.
- **Size**: Intimate, Large, Massive, etc.

### 4.3 Location Selector Dialog
**Multi-purpose picker for**:
- Adding locations to scenes
- Associating characters with locations  
- Bulk location operations
- Location relationship management

## Phase 5: Advanced Tri-Directional Features (Low Priority)

### 5.1 Story Mapping and Visualization
**Location-Scene Timeline**:
- Visual timeline showing scene progression across locations
- Character movement tracking between locations
- Location usage patterns and story pacing
- Identify overused/underused locations

**Character-Location Relationships**:
- Visual map of character-location associations
- Relationship types (lives, works, visits, avoids)
- Character territory mapping
- Conflict zones and safe spaces

### 5.2 Smart Story Analysis
**Consistency Checking**:
- Character location conflicts (can't be in two places at once)
- Scene location logic (indoor scene described with outdoor elements)
- Character-location relationship validation
- Timeline and geography consistency

**Story Suggestions**:
- Suggest new scenes based on underused character-location combinations
- Recommend location visits for character development
- Identify missing location descriptions
- Suggest character interactions at specific locations

### 5.3 Export and Sharing
**Story Bible Generation**:
- Complete location catalog with descriptions
- Character-location relationship maps
- Scene breakdown by location
- Location appearance frequency statistics

**Reference Materials**:
- Location reference sheets for consistent descriptions
- Character location history and associations
- Scene-location-character cross-reference tables

## Implementation Strategy

### Database Migration (Version 3)
```sql
-- Add to migration_database.py
CREATE TABLE locations (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    type TEXT,
    description TEXT,
    atmosphere TEXT,
    details TEXT,
    significance TEXT,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE TABLE scene_locations (
    scene_id INTEGER,
    location_id INTEGER,
    role TEXT,
    PRIMARY KEY (scene_id, location_id),
    FOREIGN KEY(scene_id) REFERENCES scenes(id),
    FOREIGN KEY(location_id) REFERENCES locations(id)
);

CREATE TABLE character_locations (
    character_id INTEGER,
    location_id INTEGER,
    relationship_type TEXT,
    description TEXT,
    PRIMARY KEY (character_id, location_id),
    FOREIGN KEY(character_id) REFERENCES characters(id),
    FOREIGN KEY(location_id) REFERENCES locations(id)
);

-- Performance indexes
CREATE INDEX idx_locations_project_id ON locations(project_id);
CREATE INDEX idx_scene_locations_scene_id ON scene_locations(scene_id);
CREATE INDEX idx_scene_locations_location_id ON scene_locations(location_id);
CREATE INDEX idx_character_locations_character_id ON character_locations(character_id);
CREATE INDEX idx_character_locations_location_id ON character_locations(location_id);
```

### UI Architecture
**Scene Editor Enhancement**:
1. Replace single character panel with tabbed context panel
2. Add location tab alongside characters tab
3. Add relationships tab showing character-location connections
4. Implement collapsible/expandable sections

**Grid View Enhancements**:
1. Add location badge/counter to scene and character cards
2. Implement hover tooltips with relationship details
3. Add filtering by location, character, or combinations
4. Create location grid view matching character/scene patterns

### Backend Services
**LocationManager**: Mirror CharacterManager functionality
**Enhanced SceneManager**: Add location relationship methods
**Enhanced CharacterManager**: Add location relationship methods
**CrossReferenceService**: Handle tri-directional relationships

## User Experience Workflows

### Primary: "I'm writing a scene in a specific location"
1. **Open scene editor** → Context panel shows current location (if set)
2. **Set location**: Click "Add Location" → Select or create location
3. **Add characters**: Characters automatically filtered by location relationships
4. **Write scene**: Context panel shows relevant characters and location details
5. **Smart suggestions**: System suggests characters who frequent this location

### Secondary: "I want to see all scenes that happen at the office"
1. **Location grid view** → Click "Office" location card
2. **Filter results** → Shows all scenes at office with character lists
3. **Quick navigation** → Click scene to open editor with location context
4. **Relationship view** → See which characters work/visit office

### Tertiary: "I want to develop a character's relationship with a place"
1. **Character editor** → Locations tab shows associated places
2. **Add location** → Select location and relationship type (lives/works/visits)
3. **Scene suggestions** → System suggests scenes to develop this relationship
4. **Cross-reference** → See other characters who share this location

## Benefits of Tri-Directional System

1. **Complete Story Universe**: Characters, scenes, and locations fully interconnected
2. **Consistency Management**: Automatic checking and validation across all elements
3. **Rich Context**: Writers always see relevant information while writing
4. **Story Development**: Smart suggestions based on relationship gaps
5. **Organization**: Complex stories become manageable with proper linking
6. **Visual Storytelling**: Maps and timelines show story structure clearly

This comprehensive system creates a complete writing environment where every story element is connected and accessible from multiple perspectives, supporting both discovery writers and meticulous planners.

## Updated Implementation Priority

### ✅ Phase 1 (COMPLETED) - Location System Foundation
- ✅ Location database schema and migration (Version 3)
- ✅ LocationManager core system with full CRUD and linking
- ✅ Complete location UI components (cards, grid view, editor dialog)
- ✅ Project tree integration with location support
- ✅ Workspace and main application integration

### ✅ Phase 2 (COMPLETED) - Enhanced Scene Editor
**Primary Goal**: Implement scene context panel for in-editor character/location management

**✅ Completed Tasks**:
1. ✅ **Scene Context Panel**: Added collapsible side panel to scene editor with toggle button
2. ✅ **Location Management**: Quick add/remove locations from scene with role assignment
3. ✅ **Character Management**: Quick add/remove characters from scene with role assignment
4. ✅ **Relationship Display**: Shows character-location connections within scene context
5. ✅ **Quick Actions**: Create new location/character directly from scene editor

**✅ Completed Files**:
- ✅ `core/embedded_editor.py` - Added context panel integration with horizontal splitter
- ✅ `ui/widgets/scene_context_panel.py` - Complete context management widget with sections
- ✅ `ui/widgets/location_selector_dialog.py` - Location picker dialog with role selection
- ✅ `ui/widgets/character_selector_dialog.py` - Character picker dialog with role selection
- ✅ Updated `ui/widgets/workspace.py` - Context panel initialization and signal passing
- ✅ Updated `main.py` - Complete signal handling and context panel integration

**✅ Key Features Implemented**:
- **Collapsible Context Panel**: Toggle on/off with toolbar button (📝)
- **Real-time Scene Context**: Shows current scene's characters and locations
- **Role-based Linking**: Primary/Secondary roles for locations, Character roles for scenes
- **Relationship Visualization**: Displays character-location connections within scene
- **Quick Actions**: Add existing or create new characters/locations from scene editor
- **Complete Signal Chain**: Full integration from context panel to main application

### 🎯 Phase 3 (MEDIUM PRIORITY - NEXT FOCUS) - Enhanced Grid Views  
**Primary Goal**: Add tri-directional information to all grid cards

**Immediate Tasks**:
1. **Enhanced Scene Cards**: Add location badges and character counts to scene cards
2. **Enhanced Character Cards**: Add location relationships display to character cards  
3. **Enhanced Location Cards**: ✅ Already implemented with scene/character counts
4. **Smart Filtering**: Cross-entity filtering ("Show scenes with John at Park")
5. **Relationship Tooltips**: Hover details for character-location connections

**Files to Modify**:
- `ui/widgets/scene_card.py` - Add location/character indicators
- `ui/widgets/character_card.py` - Add location relationship display
- `ui/widgets/scenes_grid_view.py` - Enhanced filtering capabilities
- `ui/widgets/characters_grid_view.py` - Cross-entity search and filtering

### 🚀 Phase 4 (LOW PRIORITY) - Advanced Features
**Primary Goal**: Story analysis and visualization tools

**Tasks**:
1. **Story Mapping**: Visual timeline of character movement across locations
2. **Consistency Checking**: Validate character-location relationships
3. **Smart Suggestions**: Recommend scenes based on unused character-location combinations
4. **Export Enhancement**: Include location data in story bible generation

## ✅ PHASE 2 COMPLETION SUMMARY

### What Was Accomplished
Phase 2 has been **successfully completed**, implementing a comprehensive scene context management system that transforms the writing experience in Pisarz. 

### Key Achievements
1. **🎯 Scene Context Panel**: Fully functional collapsible side panel with three sections
2. **🔗 Tri-directional Linking**: Complete character ↔ scene ↔ location relationship management
3. **⚡ Real-time Integration**: Live updates when adding/removing characters and locations
4. **🎨 Professional UI**: Polished interface with role selection and relationship visualization
5. **🔧 Complete Signal Chain**: Full integration from UI to database layer

### User Experience Transformation
Writers can now:
- **See Scene Context**: View all characters and locations in current scene at a glance
- **Quick Management**: Add/remove characters and locations without leaving the editor
- **Role Assignment**: Set specific roles (Primary/Secondary locations, Character roles)
- **Relationship Awareness**: See which characters are associated with which locations
- **Efficient Workflow**: Create new entities directly from the scene editor

### Technical Implementation Quality
- **Robust Architecture**: Clean separation of concerns with proper signal handling
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Database Integration**: Efficient use of existing LocationManager and CharacterManager
- **UI Polish**: Professional styling with proper hover states and visual feedback

## Next Steps (Phase 3 Focus)

### Priority: Enhanced Grid Views
The next logical enhancement is to bring the tri-directional relationship information to the grid views, making the scene/character/location browsing experience as rich as the scene editor context.

**Immediate Benefits**:
1. **Scene Cards**: Show location badges and character counts
2. **Character Cards**: Display location relationships  
3. **Smart Filtering**: Cross-entity searches like "scenes with John at Park"
4. **Rich Context**: Full story universe visibility from any view

This completes the foundation for a comprehensive story organization system where every element is connected and accessible from multiple perspectives.