# Phase 4.3: Batch Analyzer Plan

**Status**: Planning
**Target**: Automated project-wide analysis
**Priority**: High

## Overview

Phase 4.3 implements a batch analyzer that can automatically discover and analyze all SpringMVC components in a project, generating a comprehensive analysis report.

## Goals

1. **Automatic Discovery** - Scan project structure and detect all analyzable files
2. **Parallel Execution** - Analyze multiple files concurrently for performance
3. **Dependency Tracking** - Build relationship graph between components
4. **Comprehensive Reports** - Generate detailed analysis with statistics
5. **CLI Integration** - Provide `/analyze-all` slash command

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              Batch Analyzer                         │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │   Project   │→ │   Pattern    │→ │   File    │ │
│  │   Scanner   │  │   Detector   │  │   Filter  │ │
│  └─────────────┘  └──────────────┘  └───────────┘ │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │         Parallel Analysis Executor          │   │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐       │   │
│  │  │ JSP  │ │ Ctrl │ │ Svc  │ │ MyB  │ ...   │   │
│  │  └──────┘ └──────┘ └──────┘ └──────┘       │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ Dependency  │→ │   Report     │→ │   Export  │ │
│  │   Builder   │  │  Generator   │  │   (JSON)  │ │
│  └─────────────┘  └──────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────┘
```

## Components

### 1. Project Scanner

**Purpose**: Discover project structure and identify source directories

**Features**:
- Detect standard Maven/Gradle project layout
- Find webapp directory (JSP files)
- Find Java source directories
- Detect resource directories (MyBatis XML)

**Implementation**:
```python
class ProjectScanner:
    def scan(self, project_root: Path) -> ProjectStructure:
        """Scan project and return structure"""
        return ProjectStructure(
            webapp_dir=self._find_webapp_dir(),
            java_dirs=self._find_java_dirs(),
            resource_dirs=self._find_resource_dirs(),
            project_type=self._detect_project_type()
        )
```

### 2. Pattern Detector

**Purpose**: Identify file types and patterns

**Patterns**:
- **JSP Files**: `**/*.jsp`
- **Controllers**: `**/*Controller.java`
- **Services**: `**/*Service.java` or `@Service` annotation
- **MyBatis Mappers**: `**/*Mapper.java` + `**/*Mapper.xml`
- **Entities**: `**/*Entity.java`, `**/*DO.java`, `**/*DTO.java`

**Implementation**:
```python
class PatternDetector:
    PATTERNS = {
        'jsp': '**/*.jsp',
        'controller': '**/*Controller.java',
        'service': '**/*Service.java',
        'mapper_interface': '**/*Mapper.java',
        'mapper_xml': '**/*Mapper.xml',
    }

    def detect_files(self, project_structure: ProjectStructure) -> Dict[str, List[Path]]:
        """Detect all analyzable files by pattern"""
```

### 3. Parallel Analysis Executor

**Purpose**: Execute analysis tasks concurrently

**Features**:
- Async/await for parallel execution
- Worker pool with configurable size
- Progress tracking
- Error handling per file

**Implementation**:
```python
class ParallelAnalysisExecutor:
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.semaphore = asyncio.Semaphore(max_workers)

    async def execute_all(
        self,
        files: Dict[str, List[Path]],
        analyzers: Dict[str, BaseAnalyzer]
    ) -> BatchAnalysisResult:
        """Execute all analyses in parallel"""
        tasks = []
        for file_type, file_list in files.items():
            analyzer = analyzers[file_type]
            for file_path in file_list:
                tasks.append(self._analyze_file(analyzer, file_path))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return self._aggregate_results(results)
```

### 4. Dependency Graph Builder

**Purpose**: Build relationships between components

**Relationships**:
- Controller → Service (via @Autowired)
- Service → Mapper (via @Autowired)
- Controller → JSP (via view name)
- Mapper Interface → Mapper XML

**Implementation**:
```python
class DependencyGraphBuilder:
    def build(self, analysis_results: BatchAnalysisResult) -> DependencyGraph:
        """Build dependency graph from analysis results"""
        graph = DependencyGraph()

        # Add nodes
        for result in analysis_results.all_results:
            graph.add_node(result.component_name, result.component_type)

        # Add edges (relationships)
        self._link_controllers_to_services(graph, analysis_results)
        self._link_services_to_mappers(graph, analysis_results)
        self._link_controllers_to_jsps(graph, analysis_results)
        self._link_mapper_interfaces_to_xml(graph, analysis_results)

        return graph
```

### 5. Report Generator

**Purpose**: Generate comprehensive analysis reports

**Report Sections**:
1. **Executive Summary**
   - Total components analyzed
   - Component type breakdown
   - Coverage statistics

2. **Component Details**
   - Per-component analysis results
   - Statistics for each type

3. **Dependency Analysis**
   - Component relationships
   - Dependency depth
   - Circular dependency detection

4. **Issues & Warnings**
   - Unmapped methods (MyBatis)
   - Missing views (Controllers)
   - Unused services

**Implementation**:
```python
class ReportGenerator:
    def generate(
        self,
        analysis_results: BatchAnalysisResult,
        dependency_graph: DependencyGraph
    ) -> AnalysisReport:
        """Generate comprehensive analysis report"""
        return AnalysisReport(
            summary=self._generate_summary(analysis_results),
            components=self._format_component_details(analysis_results),
            dependencies=self._analyze_dependencies(dependency_graph),
            issues=self._detect_issues(analysis_results, dependency_graph),
            statistics=self._calculate_statistics(analysis_results)
        )
```

## File Structure

```
mcp_server/tools/
├── batch_analyzer.py           # Main batch analyzer
├── project_scanner.py          # Project structure scanner
├── pattern_detector.py         # File pattern detection
├── parallel_executor.py        # Parallel execution engine
├── dependency_graph.py         # Dependency graph builder
└── report_generator.py         # Report generation

mcp_server/commands/
└── analyze_all_cmd.py          # /analyze-all command

tests/
├── test_batch_analyzer.py      # Batch analyzer tests
├── test_project_scanner.py     # Scanner tests
└── test_dependency_graph.py    # Graph tests
```

## Implementation Plan

### Step 1: Core Infrastructure (2 hours)

**Files to create**:
1. `tools/batch_analyzer.py` - Main orchestrator
2. `tools/project_scanner.py` - Project structure detection
3. `tools/pattern_detector.py` - File pattern matching

**Deliverables**:
- Project scanning working
- File detection by pattern
- Basic batch analyzer skeleton

### Step 2: Parallel Execution (1 hour)

**Files to create**:
1. `tools/parallel_executor.py` - Async execution engine

**Deliverables**:
- Parallel analysis working
- Progress tracking
- Error handling

### Step 3: Dependency Analysis (1.5 hours)

**Files to create**:
1. `tools/dependency_graph.py` - Graph builder

**Deliverables**:
- Dependency extraction from analysis results
- Graph building
- Relationship detection

### Step 4: Report Generation (1 hour)

**Files to create**:
1. `tools/report_generator.py` - Report formatter

**Deliverables**:
- Comprehensive report generation
- Statistics calculation
- JSON export

### Step 5: CLI Integration (0.5 hours)

**Files to create**:
1. `commands/analyze_all_cmd.py` - /analyze-all command

**Deliverables**:
- `/analyze-all` command working
- Command-line flags support
- Integration with batch analyzer

### Step 6: Testing (1 hour)

**Files to create**:
1. `tests/test_batch_analyzer.py`
2. `tests/test_dependency_graph.py`

**Deliverables**:
- Unit tests for all components
- Integration test for full batch analysis
- Test with sample project

**Total Estimated Time**: 7 hours

## CLI Command Design

### `/analyze-all` Command

**Syntax**:
```bash
/analyze-all [PROJECT_DIR] [OPTIONS]
```

**Arguments**:
- `PROJECT_DIR` - Project root directory (default: current directory)

**Options**:
- `--output`, `-o` - Output report file (default: `output/batch_analysis.json`)
- `--types`, `-t` - Component types to analyze (default: all)
  - Choices: `jsp`, `controller`, `service`, `mybatis`, `all`
- `--parallel`, `-p` - Number of parallel workers (default: 10)
- `--graph` - Include dependency graph (default: true)
- `--no-cache` - Force refresh all analyses

**Examples**:
```bash
# Analyze current project
/analyze-all

# Analyze specific project
/analyze-all /path/to/project

# Analyze only controllers and services
/analyze-all --types controller,service

# Custom output with 20 parallel workers
/analyze-all -o analysis/report.json -p 20

# Full analysis with dependency graph
/analyze-all --graph --output full_analysis.json
```

## Output Format

### Batch Analysis Report (JSON)

```json
{
  "project_root": "/path/to/project",
  "analyzed_at": "2025-10-04T22:00:00Z",
  "summary": {
    "total_components": 156,
    "by_type": {
      "jsp": 23,
      "controller": 18,
      "service": 24,
      "mybatis_mapper": 32,
      "entity": 59
    },
    "analysis_time_seconds": 3.45,
    "errors": 2
  },
  "components": {
    "controllers": [
      {
        "name": "UserController",
        "file": "src/main/java/com/example/controller/UserController.java",
        "endpoints": 8,
        "http_methods": {"GET": 4, "POST": 2, "PUT": 1, "DELETE": 1},
        "dependencies": ["UserService", "RoleService"]
      }
    ],
    "services": [...],
    "mappers": [...],
    "jsps": [...]
  },
  "dependencies": {
    "graph": {
      "nodes": [...],
      "edges": [...]
    },
    "statistics": {
      "total_relationships": 145,
      "max_depth": 4,
      "circular_dependencies": []
    }
  },
  "issues": [
    {
      "type": "warning",
      "component": "UserMapper",
      "message": "Method 'findByEmail' not mapped in XML",
      "severity": "medium"
    }
  ],
  "statistics": {
    "total_endpoints": 87,
    "total_sql_statements": 124,
    "total_transactional_methods": 45,
    "code_coverage": {
      "mybatis_mapping": "98%",
      "service_usage": "92%"
    }
  }
}
```

## Performance Targets

- **Small Project** (50 files): < 5 seconds
- **Medium Project** (200 files): < 15 seconds
- **Large Project** (500 files): < 30 seconds

**Optimization Strategies**:
1. Parallel execution (10 workers default)
2. Caching (reuse existing analysis results)
3. Smart scanning (skip non-source directories)
4. Incremental analysis (only changed files)

## Success Criteria

1. ✅ Successfully scans Maven/Gradle projects
2. ✅ Detects all 4 component types (JSP, Controller, Service, MyBatis)
3. ✅ Analyzes 200+ files in < 15 seconds
4. ✅ Builds accurate dependency graph
5. ✅ Generates comprehensive JSON report
6. ✅ `/analyze-all` command working
7. ✅ Error handling for corrupt files
8. ✅ 100% test coverage

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large projects timeout | High | Configurable parallel workers, timeouts |
| Circular dependencies | Medium | Detection and warning in report |
| Memory exhaustion | Medium | Stream processing, batch size limits |
| Inconsistent file patterns | Low | Configurable patterns, fallback detection |

## Next Steps After 4.3

1. **Phase 4.4**: Integration tests for full MCP server
2. **Phase 4.5**: Complete documentation and polish
3. **Phase 5**: Knowledge graph visualization (Neo4j)

---

**Created**: 2025-10-04
**Estimated Effort**: 7 hours
**Status**: Ready to implement
